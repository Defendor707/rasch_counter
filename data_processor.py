import pandas as pd
import numpy as np
import io
import os
import re
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import cpu_count
from rasch_model import rasch_model, ability_to_grade, ability_to_standard_score
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import PyPDF2
import warnings
warnings.filterwarnings('ignore')

# Server quvvati optimizatsiyasi - 80% CPU ishlatish
NUM_CORES = cpu_count() or 6
MAX_WORKERS = min(int(NUM_CORES * 0.8), 4)  # Load yuqori bo'lgani uchun 4 ga cheklash

# CPU load monitoring va adaptive optimization
def get_cpu_load():
    try:
        with open('/proc/loadavg', 'r') as f:
            load = float(f.read().split()[0])
        return load
    except:
        return 0.0

# Adaptive worker count based on current load
current_load = get_cpu_load()
if current_load > NUM_CORES * 1.2:  # Agar load juda yuqori bo'lsa
    MAX_WORKERS = max(2, int(NUM_CORES * 0.6))  # 60% ishlatish
elif current_load > NUM_CORES * 0.8:
    MAX_WORKERS = max(3, int(NUM_CORES * 0.7))  # 70% ishlatish
else:
    MAX_WORKERS = min(int(NUM_CORES * 0.8), 4)  # 80% ishlatish

# Numpy/BLAS performans sozlamalari
os.environ['OPENBLAS_NUM_THREADS'] = str(MAX_WORKERS)
os.environ['MKL_NUM_THREADS'] = str(MAX_WORKERS)
os.environ['OMP_NUM_THREADS'] = str(MAX_WORKERS)
os.environ['VECLIB_MAXIMUM_THREADS'] = str(MAX_WORKERS)
os.environ['NUMEXPR_NUM_THREADS'] = str(MAX_WORKERS)

def preprocess_exam_data(df):
    """
    Preprocess exam data to standardize format:
    1. Identify student name/ID column
    2. Identify question columns based on patterns
    3. Remove unnecessary columns
    4. Clean data values to 0s and 1s
    5. Remove rows without student names
    
    Parameters:
    - df: Original DataFrame with raw exam data
    
    Returns:
    - cleaned_df: DataFrame with standardized columns and values
    """
    # Create a copy to avoid modifying the original DataFrame
    processed_df = df.copy()
    
    # STEP 1: Identify student ID/name column
    id_column = None
    id_column_keywords = ['student', 'name', 'id', 'ism', 'familiya', 'номи', 'исм', 'фамилия', 'names']
    exclude_keywords = ['n0', 'no', '№', '#', 'number']
    
    # XUSUSIY HOLAT - 504, 505, 506... kabi ketma-ket raqamlar birinchi ustunda bo'lsa, 
    # u holda ikkinchi ustunni ism-familiya deb olishimiz kerak
    # Agar PDF formatdagi chiziqli ro'yxatda birinchi ustun tartib raqami bo'lsa
    # First check if this is one of the special 'sequential ID number' cases
    is_sequential_id_case = False
    if len(processed_df.columns) >= 2:
        # Check if the first column contains sequential numeric IDs (like 504, 505, 506...)
        first_col = processed_df.columns[0]
        first_col_values = processed_df[first_col].dropna().astype(str).tolist()
        # Check at least 5 values to be sure (or all if there are fewer)
        check_len = min(5, len(first_col_values))
        
        if check_len > 0:
            # Filter only numeric values
            numeric_values = [int(v) for v in first_col_values[:check_len] if str(v).strip().isdigit()]
            
            # If all are numeric and have 3 or more digits, likely sequential IDs like in screenshot
            if len(numeric_values) == check_len and all(len(str(v)) >= 3 for v in numeric_values):
                # Also check if they are roughly sequential
                is_sequential = True
                if len(numeric_values) > 1:
                    # Check if the values increase somewhat sequentially
                    numeric_values.sort()
                    # Assume sequential if average difference between consecutive numbers is < 10
                    diffs = [numeric_values[i+1] - numeric_values[i] for i in range(len(numeric_values)-1)]
                    avg_diff = sum(diffs) / len(diffs) if diffs else 0
                    is_sequential = 1 <= avg_diff <= 10
                
                if is_sequential:
                    # This is likely the case in the screenshot where first column is just sequential IDs
                    is_sequential_id_case = True
                    # Take the second column as the name/ID column directly
                    id_column = processed_df.columns[1]
    
    # Only proceed with the normal logic if we haven't identified a special case
    if not is_sequential_id_case:
        # Regular logic for identifying ID column by name...
        # First check column names for keywords
        for col in processed_df.columns:
            col_lower = str(col).lower().strip()
            
            # Skip columns that are likely numbering/ordering columns
            if col_lower in exclude_keywords or col_lower == 'n' or col_lower == 'no':
                continue
                
            # Check if this is likely an ID column based on keywords
            if any(keyword in col_lower for keyword in id_column_keywords):
                # Verify that this column contains valid student names/IDs (not just numbers like 0, 1)
                valid_name_column = True
                
                # Get non-empty values from this column
                col_values = processed_df[col].dropna().astype(str).tolist()
                
                # Skip if no values
                if not col_values:
                    continue
                    
                # Check if the column values look like valid names (not just 0, 1, or single digits)
                invalid_values = ['0', '1', 'true', 'false', 'yes', 'no', 'y', 'n']
                # If more than 50% of values are just single digits or invalid values, skip this column
                invalid_count = sum(1 for v in col_values if str(v).strip().lower() in invalid_values or
                                  (str(v).strip().isdigit() and len(str(v).strip()) <= 1))
                
                if invalid_count / len(col_values) > 0.5:
                    valid_name_column = False
                    
                if valid_name_column:
                    id_column = col
                    break
        
        # If no obvious ID column by name, look at content - assuming student names are text, not numbers
        if id_column is None:
            # First check if all columns contain mostly just numbers - the "all numeric columns" case
            all_numeric_columns = True
            for col in processed_df.columns:
                col_values = processed_df[col].dropna().astype(str).tolist()
                if len(col_values) > 0:
                    numeric_count = sum(1 for v in col_values if str(v).strip().isdigit())
                    if numeric_count / len(col_values) < 0.8:  # If less than 80% are numbers, not a pure numeric column
                        all_numeric_columns = False
                        break
            
            # If all columns are numeric (like in the screenshot), take the second column as ID column
            if all_numeric_columns and len(processed_df.columns) >= 2:
                id_column = processed_df.columns[1]
            else:
                # Normal case - try to find the best column based on content
                best_name_column = None
                max_name_score = -1
                
                for col in processed_df.columns:
                    # Skip already known non-name columns
                    col_lower = str(col).lower().strip()
                    if col_lower in exclude_keywords or col_lower == 'n' or col_lower == 'no':
                        continue
                        
                    # Look at all non-empty values to determine if this looks like a name column
                    col_values = processed_df[col].dropna().astype(str).tolist()
                    
                    # Skip if no values
                    if not col_values:
                        continue
                    
                    # Skip columns that have all pure numeric values with 3+ digits
                    if all(str(v).strip().isdigit() and len(str(v).strip()) >= 3 for v in col_values):
                        continue
                    
                    # Calculate a "name score" based on characteristics of typical student names
                    # Higher score = more likely to be a name column
                    
                    # 1. Text length should be reasonable for a name (not too short, not too long)
                    avg_len = sum(len(str(v).strip()) for v in col_values) / len(col_values)
                    length_score = 0
                    if 5 <= avg_len <= 30:  # Typical name length range
                        length_score = 2.0
                    elif avg_len > 3:  # Short but could be initials or abbreviations
                        length_score = 1.0
                        
                    # 2. Should contain some letters (not just numbers)
                    contains_letters = sum(1 for v in col_values if any(c.isalpha() for c in str(v)))
                    letter_score = contains_letters / len(col_values)
                    
                    # 3. Shouldn't be mostly 0s, 1s or very short values
                    invalid_values = ['0', '1', 'true', 'false', 'yes', 'no', 'y', 'n']
                    invalid_count = sum(1 for v in col_values if str(v).strip().lower() in invalid_values or
                                      (str(v).strip().isdigit() and len(str(v).strip()) <= 1))
                    valid_score = 1.0 - (invalid_count / len(col_values))
                    
                    # 4. Penalty for pure numeric columns
                    numeric_penalty = 0
                    if all(str(v).strip().isdigit() for v in col_values):
                        numeric_penalty = 2.0
                    
                    # Total score for this column
                    name_score = length_score + 2*letter_score + 3*valid_score - numeric_penalty
                    
                    # Update best column if this one has a higher score
                    if name_score > max_name_score:
                        max_name_score = name_score
                        best_name_column = col
                
                # Use the best scoring column if found
                if best_name_column is not None and max_name_score > 2.0:  # Threshold for accepting a column
                    id_column = best_name_column
        
        # If we still can't find a name column, use the second column if available, otherwise first column
        if id_column is None:
            if len(processed_df.columns) > 1:
                # Use second column as student names are often in the second column after numbering
                id_column = processed_df.columns[1]
            else:
                # Fallback to first column
                id_column = processed_df.columns[0]
        
        # Final verification - make sure the column doesn't contain mostly 0s and 1s or all digits
        # If it does, try to find a better column
        col_values = processed_df[id_column].dropna().astype(str).tolist()
        if col_values:
            # Check if over 80% of values are pure numbers with 3+ digits (likely IDs not names)
            pure_number_count = sum(1 for v in col_values if str(v).strip().isdigit() and len(str(v).strip()) >= 3)
            if pure_number_count / len(col_values) > 0.8:
                # This column is mostly 3+ digit numbers, might not be names
                # Try to find a better alternative (especially if there's a second column)
                if len(processed_df.columns) > 1:
                    second_col = processed_df.columns[1]
                    if second_col != id_column:
                        id_column = second_col  # Use second column
    
    # STEP 2: Identify question columns
    question_columns = []
    pattern_prefixes = ['q', 'savol', 'question', 'сав']
    numeric_pattern = r'^\d+$'  # Matches columns that are just numbers (1, 2, 3...)
    exclude_keywords = ['exam', 'total', 'rank', 'ball', 'foiz', 'daraja', 'percentage']
    
    # Group columns by their base name (Q1Option, Q1Key would be grouped under Q1)
    column_groups = {}
    
    for col in processed_df.columns:
        col_str = str(col).lower()
        
        # Skip the ID column
        if col == id_column:
            continue
            
        # Skip columns with exclude keywords
        if any(keyword in col_str for keyword in exclude_keywords):
            continue
        
        # Check for numeric column names (1, 2, 3...)
        if re.match(numeric_pattern, col_str):
            question_columns.append(col)
            continue
        
        # Check for columns with Q1, Q2 patterns or other prefixes
        for prefix in pattern_prefixes:
            if col_str.startswith(prefix):
                # Extract the number if it's a pattern like Q1, Q2...
                match = re.search(r'(\d+)', col_str)
                if match:
                    base_name = prefix + match.group(1)
                    if base_name not in column_groups:
                        column_groups[base_name] = []
                    column_groups[base_name].append(col)
                    break
        
        # If the column name contains "mark" or "key" without a number, try to associate it
        if "mark" in col_str or "key" in col_str or "option" in col_str:
            # See if we can find a number in the column name
            match = re.search(r'(\d+)', col_str)
            if match:
                base_name = "q" + match.group(1)
                if base_name not in column_groups:
                    column_groups[base_name] = []
                column_groups[base_name].append(col)
    
    # Process column groups - pick the best column from each group (prefer 'mark' over others)
    for base_name, cols in column_groups.items():
        if len(cols) > 0:
            # Prefer columns with 'mark' in the name if available
            mark_cols = [c for c in cols if 'mark' in str(c).lower()]
            if mark_cols:
                question_columns.append(mark_cols[0])
            else:
                # Otherwise take the first column in the group
                question_columns.append(cols[0])
    
    # If we didn't find any valid question columns, check for columns with mostly binary (0/1) values
    if not question_columns:
        binary_columns = []
        for col in processed_df.columns:
            if col == id_column:
                continue
            if any(keyword in str(col).lower() for keyword in exclude_keywords):
                continue
                
            # Try to convert to numeric
            numeric_values = pd.to_numeric(processed_df[col], errors='coerce')
            # Count how many values are 0 or 1
            binary_count = ((numeric_values == 0) | (numeric_values == 1)).sum()
            # If more than 70% are 0s or 1s, consider it a question column
            if binary_count / len(processed_df) > 0.7:
                binary_columns.append((col, binary_count))
        
        # Sort by binary count (descending) and take top columns
        binary_columns.sort(key=lambda x: x[1], reverse=True)
        question_columns.extend([col for col, _ in binary_columns])
    
    # Sort question columns to maintain order (if they are numbers or have numbers in them)
    # The sort should preserve the order of duplicate column numbers (e.g., 36, 36, 37, 37)
    def extract_number(col_name):
        match = re.search(r'(\d+)', str(col_name))
        if match:
            return int(match.group(1))
        return float('inf')  # Put columns without numbers at the end
    
    # Sort the question columns by their extracted numbers
    # This will keep duplicate numbers together in the original order they appeared
    # For example: 1, 2, 3, 4, ..., 36, 36, 37, 37, ..., 44, 44, 45, 45
    question_columns.sort(key=extract_number)
    
    # STEP 3: Create a new DataFrame with only the columns we want
    selected_columns = [id_column] + question_columns
    cleaned_df = processed_df[selected_columns].copy()
    
    # STEP 4: Clean up row data
    # Remove rows where student ID/name is empty, NaN, or invalid (just 0 or 1)
    cleaned_df = cleaned_df.dropna(subset=[id_column])
    
    # Filter out rows where the ID column is empty or just contains invalid values (0, 1, etc)
    invalid_id_values = ['0', '1', 'true', 'false', 'yes', 'no', 'y', 'n', '(ism familya)']
    cleaned_df = cleaned_df[
        (~cleaned_df[id_column].astype(str).str.strip().isin(invalid_id_values)) &  # Not just 0, 1, "ism familya" etc.
        (cleaned_df[id_column].astype(str).str.strip() != '') &  # Not empty
        (~cleaned_df[id_column].astype(str).str.strip().str.isdigit() | 
         (cleaned_df[id_column].astype(str).str.strip().str.len() > 1))  # Not just a single digit
    ]
    
    # YANGI QO'SHIMCHA: Ism-familya belgilangan qatorda kamida 1ta javob bo'lishi kerak
    # Aks holda bu o'quvchi emas, adashib qo'shilgan yozuv
    
    # Har bir qator uchun tekshirish - kamida 1ta "1" qiymati bo'lishi kerak
    rows_with_answers = []
    
    for idx, row in cleaned_df.iterrows():
        # Faqat savol ustunlarini tekshiramiz (ID ustunidan tashqari)
        answers = row[question_columns]
        
        # Agar kamida 1ta "1" (to'g'ri javob) bo'lsa, bu qatorni saqlash
        if (answers == 1).sum() >= 1:
            rows_with_answers.append(idx)
    
    # Faqat kamida 1ta javob bergan o'quvchilarni qoldirish
    cleaned_df = cleaned_df.loc[rows_with_answers]
    
    # STEP 5: Clean and standardize question data values to 0s and 1s
    # Convert all empty/NaN values to 0 as requested
    for col in question_columns:
        # First try to interpret letter grades as 1s and 0s
        # Common mappings: 'A', 'B', 'C', 'D', etc. might represent answers
        
        # Get unique values to determine what kind of column this is
        unique_vals = cleaned_df[col].dropna().unique()
        
        # Special processing for letter grades
        if all(isinstance(val, str) for val in unique_vals if pd.notna(val)):
            # If values are strings like A, B, C, D, convert to 1s and 0s
            # For now, treat any value as 1 (can be customized based on specific rules)
            cleaned_df[col] = cleaned_df[col].apply(
                lambda x: 1 if pd.notna(x) and str(x).strip() != '' else 0
            )
        else:
            # For numeric values, convert to numeric and fill NaNs with 0
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0)
            
            # Check if values are already 0s and 1s
            unique_numeric = cleaned_df[col].unique()
            if set(unique_numeric).issubset({0, 1}):
                # Already 0s and 1s, just ensure they are integers
                cleaned_df[col] = cleaned_df[col].astype(int)
            else:
                # For other numeric values (like scaled scores), convert to binary
                # Values > 0 become 1, others become 0
                cleaned_df[col] = cleaned_df[col].apply(lambda x: 1 if x > 0 else 0)
    
    return cleaned_df, id_column, question_columns

def process_exam_data(df, progress_callback=None):
    """
    Tezlashtirilgan va aniq Rasch modeli qayta ishlash algoritmi.
    Katta ma'lumotlar uchun optimallashtirilgan.
    
    Parameters:
    - df: Ma'lumotlar jadvalи
    - progress_callback: Progress yangilanish funksiyasi
    
    Returns:
    - results_df: Natijalar jadvali
    - ability_estimates: Qobiliyat baholari
    - grade_counts: Baholar soni
    - original_df: Asl ma'lumotlar
    - item_difficulties: Savol qiyinliklari
    """
    if progress_callback:
        progress_callback(5, "Ma'lumotlar tahlil qilinmoqda...")
    
    # Tezkor preprocessing
    df_cleaned, id_column, question_columns = preprocess_exam_data(df)
    
    # Ma'lumotlarni NumPy array sifatida olish (tezroq)
    student_ids = df_cleaned[id_column].values.astype(str)
    response_data = df_cleaned[question_columns].values.astype(np.int8)  # int8 xotira tejaydi
    
    if progress_callback:
        progress_callback(20, "Rasch modeli ishga tushirilmoqda...")
    
    n_students, n_questions = response_data.shape
    
    # Parallel processing bilan adaptiv chunking
    if n_students > 1000:
        # Server quvvatining 80% ishlatish uchun optimal chunk size
        optimal_chunk = max(n_students // MAX_WORKERS, 800)
        ability_estimates, item_difficulties = rasch_model(
            response_data, 
            max_students=optimal_chunk
        )
    else:
        ability_estimates, item_difficulties = rasch_model(response_data)
    
    if progress_callback:
        progress_callback(50, "Baholar hisoblanmoqda...")
    
    # Parallel baholash mexanizmi (BBM standartlariga muvofiq)
    def fast_parallel_grade(abilities):
        if len(abilities) == 0:
            return np.array([])
        
        # Parallel processing uchun chunk_grade funksiyasi
        def chunk_grade(ability_chunk):
            scores = np.array([ability_to_standard_score(a) for a in ability_chunk], dtype=np.float32)
            grades = np.full(len(scores), 'NC', dtype='<U3')
            
            # Vectorized grading
            grades[scores >= 85] = 'A+'
            grades[(scores >= 75) & (scores < 85)] = 'A'
            grades[(scores >= 65) & (scores < 75)] = 'B+'
            grades[(scores >= 55) & (scores < 65)] = 'B'
            grades[(scores >= 45) & (scores < 55)] = 'C+'
            grades[(scores >= 35) & (scores < 45)] = 'C'
            
            return grades
        
        # Parallel processing agar talabalar ko'p bo'lsa
        if len(abilities) > 5000:
            chunk_size = max(len(abilities) // MAX_WORKERS, 1000)
            chunks = [abilities[i:i+chunk_size] for i in range(0, len(abilities), chunk_size)]
            
            try:
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    results = list(executor.map(chunk_grade, chunks))
                return np.concatenate(results)
            except Exception:
                # Fallback to sequential
                return chunk_grade(abilities)
        else:
            return chunk_grade(abilities)
    
    grades = fast_parallel_grade(ability_estimates)
    
    # Tezkor raw scores hisoblash
    raw_scores = np.sum(response_data, axis=1, dtype=np.int16)
    
    # Standard scores hisoblash (vectorized)
    standard_scores = np.clip((ability_estimates + 4) / 8 * 100, 0, 100)
    
    if progress_callback:
        progress_callback(75, "Natijalar tizimlashtirilmoqda...")
    
    # Natijalar jadvali yaratish
    results_df = pd.DataFrame({
        'Student ID': student_ids,
        'Raw Score': raw_scores,
        'Ability': ability_estimates.astype(np.float32),
        'Standard Score': standard_scores.astype(np.float32),
        'Grade': grades
    })
    
    # Tartiblash: Baholar bo'yicha va ballari bo'yicha
    grade_order_map = {'A+': 0, 'A': 1, 'B+': 2, 'B': 3, 'C+': 4, 'C': 5, 'NC': 6}
    results_df['Grade_Order'] = results_df['Grade'].apply(lambda x: grade_order_map.get(x, 6))
    
    # Tartiblash
    results_df = results_df.sort_values(by=['Grade_Order', 'Standard Score'], 
                                      ascending=[True, False])
    
    if progress_callback:
        progress_callback(90, "Yakuniy natijalar tayyorlanmoqda...")
    
    # O'rindiqlar qo'shish
    rank_list = list(range(1, len(results_df) + 1))
    results_df.insert(1, 'Rank', rank_list)
    
    # Vaqtinchalik ustunni o'chirish
    results_df = results_df.drop(columns=['Grade_Order'])
    
    # Count occurrences of each grade - ensure all grades are included
    all_grades = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'NC']
    grade_counts = {}
    for grade in all_grades:
        grade_counts[grade] = int((results_df['Grade'] == grade).sum())
    
    # Debug info for grade distribution
    total_students = len(results_df)
    if progress_callback:
        grade_summary = ", ".join([f"{g}:{grade_counts[g]}" for g in all_grades if grade_counts[g] > 0])
        progress_callback(95, f"Baholar taqsimoti: {grade_summary}")
    
    # Progress complete
    if progress_callback:
        progress_callback(100, "Tahlil yakunlandi!")
    
    # Return updated results including the cleaned dataframe and item difficulties
    return results_df, ability_estimates, grade_counts, df_cleaned, item_difficulties

# FAOLSIZLANTIRILGAN: Keraksiz takroriy funksiya
# def prepare_simplified_excel_old(results_df, title="Nazorat Ballari"):

def prepare_simplified_excel(results_df, title="Nazorat Ballari"):
    """
    Prepare a simplified Excel file with just student names and scores.
    
    Parameters:
    - results_df: DataFrame with processed results
    - title: Title for the sheet
    
    Returns:
    - excel_data: BytesIO object containing Excel file data
    """
    # Copy the dataframe to avoid modifying the original
    df = results_df.copy()
    
    # Sort by Standard Score in descending order
    df = df.sort_values(by='Standard Score', ascending=False).reset_index(drop=True)
    
    # Keep only Student ID and Standard Score columns
    simplified_df = df[['Student ID', 'Standard Score']].copy()
    simplified_df.columns = ['Ism Familiya', 'Ball']
    
    # Create a BytesIO object
    excel_data = io.BytesIO()
    
    # Create a Pandas Excel writer using the BytesIO object
    with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
        # Write the DataFrame to an Excel sheet
        simplified_df.to_excel(writer, sheet_name=title, index=False)
        
        # Get the workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets[title]
        
        # Define header format
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4B8BBE',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        # Format the header row
        for col_num, value in enumerate(simplified_df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Set column widths
        worksheet.set_column('A:A', 35)  # Ism Familiya
        worksheet.set_column('B:B', 12)  # Ball
        
        # Format score column with 1 decimal place
        score_format = workbook.add_format({'num_format': '0.0', 'border': 1})
        for row_num in range(len(simplified_df)):
            worksheet.write(row_num+1, 1, simplified_df['Ball'].iloc[row_num], score_format)
    
    # Reset the pointer to the beginning of the BytesIO object
    excel_data.seek(0)
    
    return excel_data

def prepare_simplified_excel(results_df, title="Nazorat Ballari"):
    """
    Prepare a simplified Excel file with just student names and scores.
    
    Parameters:
    - results_df: DataFrame with processed results
    - title: Title for the sheet
    
    Returns:
    - excel_data: BytesIO object containing Excel file data
    """
    # Copy the dataframe to avoid modifying the original
    df = results_df.copy()
    
    # Keep only necessary columns
    simplified_df = pd.DataFrame()
    simplified_df['Talaba'] = df['Student ID']
    simplified_df['Ball'] = df['Standard Score']
    
    # Sort by score in descending order
    simplified_df = simplified_df.sort_values(by='Ball', ascending=False).reset_index(drop=True)
    
    # Create a BytesIO object
    excel_data = io.BytesIO()
    
    # Create a Pandas Excel writer using the BytesIO object
    with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
        # Write the DataFrame to an Excel sheet
        simplified_df.to_excel(writer, sheet_name=title, index=False)
        
        # Get the workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets[title]
        
        # Define cell formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4B8BBE',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        # Format the header row
        for col_num, value in enumerate(simplified_df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Set column widths
        worksheet.set_column('A:A', 35)  # Student name (Ism-familiya uchun kattaroq kenglik)
        worksheet.set_column('B:B', 10)  # Score
    
    # Reset the pointer to the beginning of the BytesIO object
    excel_data.seek(0)
    
    return excel_data

def prepare_excel_with_charts(results_df, grade_counts, ability_estimates, data_df=None, beta_values=None):
    """
    Prepare an Excel file containing both results and charts/diagrams.
    
    Parameters:
    - results_df: DataFrame with processed results
    - grade_counts: Dictionary with counts of each grade
    - ability_estimates: Array of ability estimates
    - data_df: DataFrame containing raw student responses (optional)
    - beta_values: Array of item difficulty parameters (optional)
    
    Returns:
    - excel_data: BytesIO object containing Excel file data with charts
    """
    import matplotlib.pyplot as plt
    import numpy as np
    
    # Copy the dataframe to avoid modifying the original
    df = results_df.copy()
    
    # Add Rank column if not already present
    if 'Rank' not in df.columns:
        df['Rank'] = range(1, len(df) + 1)
    
    # Sort by Standard Score in descending order
    df = df.sort_values(by='Standard Score', ascending=False).reset_index(drop=True)
    
    # Reorder columns
    cols = df.columns.tolist()
    student_id_idx = cols.index('Student ID')
    rank_idx = cols.index('Rank')
    cols.pop(rank_idx)
    cols.insert(student_id_idx, 'Rank')
    df = df[cols]
    
    # Create a BytesIO object for the Excel file
    excel_data = io.BytesIO()
    
    # Create a Pandas Excel writer
    with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
        # Write the results to the first sheet
        df.to_excel(writer, sheet_name='Natijalar', index=False)
        
        # Create a sheet for charts
        workbook = writer.book
        chart_sheet = workbook.add_worksheet('Diagrammalar')
        
        # Format settings
        title_format = workbook.add_format({
            'bold': True, 
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        # 1. Create Grade Distribution Chart
        grade_order = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'NC']
        grade_colors = {
            'A+': '#1E8449',  # Dark Green
            'A': '#28B463',   # Green
            'B+': '#58D68D',  # Light Green
            'B': '#3498DB',   # Blue
            'C+': '#5DADE2',  # Light Blue
            'C': '#F4D03F',   # Yellow
            'NC': '#E67E22',  # Orange
        }
        
        # Prepare data for grade chart
        grades = []
        counts = []
        colors = []
        
        for grade in grade_order:
            if grade in grade_counts:
                count = grade_counts[grade]
                grades.append(grade)
                counts.append(count)
                colors.append(grade_colors.get(grade, '#CCCCCC'))
        
        # Create a chart object for grade distribution
        grade_chart = workbook.add_chart({'type': 'column'})
        
        # Create a temp sheet for grade data
        workbook.add_worksheet('_temp_grades').hide()
        temp_grades = writer.sheets['_temp_grades']
        
        # Write grade data to temp sheet
        for i, (grade, count) in enumerate(zip(grades, counts)):
            temp_grades.write(i, 0, grade)
            temp_grades.write(i, 1, count)
        
        # Add a title to the chart
        grade_chart.set_title({'name': 'Baholar taqsimoti'})
        
        # Add the series
        grade_chart.add_series({
            'name': 'Talabalar soni',
            'categories': '=_temp_grades!$A$1:$A$' + str(len(grades)),
            'values': '=_temp_grades!$B$1:$B$' + str(len(grades)),
            'points': [{'fill': {'color': color}} for color in colors],
        })
        
        # Set axes labels
        grade_chart.set_x_axis({'name': 'Baholar'})
        grade_chart.set_y_axis({'name': 'Talabalar soni'})
        
        # Insert chart into the chart sheet
        chart_sheet.merge_range('A1:H1', 'BAHOLAR TAQSIMOTI', title_format)
        chart_sheet.insert_chart('A2', grade_chart, {'x_scale': 1.5, 'y_scale': 1.2})
        
        # 2. Create Ability Distribution Chart (using column chart instead of histogram)
        ability_chart = workbook.add_chart({'type': 'column'})
        
        # Create temp sheet for ability data
        workbook.add_worksheet('_temp_ability').hide()
        temp_ability = writer.sheets['_temp_ability']
        
        # Prepare ability data for bins
        if ability_estimates is not None and len(ability_estimates) > 0:
            abilities = np.array(ability_estimates)
            bin_width = 0.5
            min_val = np.floor(min(abilities))
            max_val = np.ceil(max(abilities))
            bins = np.arange(min_val, max_val + bin_width, bin_width)
            hist, _ = np.histogram(abilities, bins=bins)
            
            # Create bin labels for x-axis (use middle of bin)
            bin_labels = [(bins[i] + bins[i+1])/2 for i in range(len(bins)-1)]
            
            # Write bin data
            for i, (count, bin_label) in enumerate(zip(hist, bin_labels)):
                temp_ability.write(i, 0, f"{bin_label:.1f}")
                temp_ability.write(i, 1, count)
            
            # Add a title to the chart
            ability_chart.set_title({'name': 'Talabalar qobiliyat taqsimoti'})
            
            # Add the series
            ability_chart.add_series({
                'name': 'Talabalar soni',
                'categories': '=_temp_ability!$A$1:$A$' + str(len(hist)),
                'values': '=_temp_ability!$B$1:$B$' + str(len(hist)),
                'fill': {'color': '#3498DB'},
            })
            
            # Set axes labels
            ability_chart.set_x_axis({'name': 'Qobiliyat (Theta)'})
            ability_chart.set_y_axis({'name': 'Talabalar soni'})
            
            # Insert chart into the chart sheet
            chart_sheet.merge_range('A25:H25', 'TALABALAR QOBILIYAT TAQSIMOTI', title_format)
            chart_sheet.insert_chart('A26', ability_chart, {'x_scale': 1.5, 'y_scale': 1.2})
        
        # 3. Create Item Difficulty Analysis Chart (if data is available)
        if data_df is not None and beta_values is not None and len(beta_values) > 0:
            # Create temp sheet for item difficulty data
            workbook.add_worksheet('_temp_item_diff').hide()
            temp_item_diff = writer.sheets['_temp_item_diff']
            
            # Calculate correct answer percentages
            percentages = []
            question_numbers = []
            
            for i in range(len(beta_values)):
                # Find the corresponding column in data_df
                if i+1 < len(data_df.columns):
                    question_numbers.append(i+1)
                    col_name = data_df.columns[i+1]  # +1 because first column is student ID
                    correct_count = data_df[col_name].sum()
                    total_count = len(data_df)
                    percentages.append(100 * correct_count / total_count if total_count > 0 else 0)
            
            # Sort by difficulty
            difficulty_with_index = [(beta, i+1, percent) for i, (beta, percent) 
                                    in enumerate(zip(beta_values, percentages))]
            difficulty_with_index.sort(key=lambda x: x[0], reverse=True)
            
            # Write data for chart
            for i, (diff, q_num, percent) in enumerate(difficulty_with_index):
                temp_item_diff.write(i, 0, f"Q{q_num}")
                temp_item_diff.write(i, 1, diff)
                temp_item_diff.write(i, 2, percent)
            
            if len(difficulty_with_index) > 0:
                # Create chart for item difficulty
                item_chart = workbook.add_chart({'type': 'scatter'})
                
                # Add a title to the chart
                item_chart.set_title({'name': 'Savollar qiyinligi tahlili'})
                
                # Add the series for difficulty
                item_chart.add_series({
                    'name': 'Qiyinlik',
                    'categories': '=_temp_item_diff!$A$1:$A$' + str(len(difficulty_with_index)),
                    'values': '=_temp_item_diff!$B$1:$B$' + str(len(difficulty_with_index)),
                    'marker': {'type': 'circle', 'size': 8, 'fill': {'color': '#E74C3C'}},
                })
                
                # Set axes labels
                item_chart.set_x_axis({'name': 'Savol raqami'})
                item_chart.set_y_axis({'name': 'Qiyinlik darajasi'})
                
                # Insert chart into the chart sheet
                chart_sheet.merge_range('A50:H50', 'SAVOLLAR QIYINLIGI TAHLILI', title_format)
                chart_sheet.insert_chart('A51', item_chart, {'x_scale': 1.5, 'y_scale': 1.2})
                
                # Create a second chart for correct answer percentages
                percent_chart = workbook.add_chart({'type': 'column'})
                
                # Add a title to the chart
                percent_chart.set_title({'name': "To'g'ri javoblar foizi"})
                
                # Add the series for percentages
                percent_chart.add_series({
                    'name': "To'g'ri javoblar %",
                    'categories': '=_temp_item_diff!$A$1:$A$' + str(len(difficulty_with_index)),
                    'values': '=_temp_item_diff!$C$1:$C$' + str(len(difficulty_with_index)),
                    'fill': {'color': '#2ECC71'},
                })
                
                # Set axes labels
                percent_chart.set_x_axis({'name': 'Savol raqami'})
                percent_chart.set_y_axis({
                    'name': "To'g'ri javoblar foizi",
                    'min': 0,
                    'max': 100,
                })
                
                # Insert chart into the chart sheet
                chart_sheet.merge_range('A75:H75', "TO'G'RI JAVOBLAR FOIZI", title_format)
                chart_sheet.insert_chart('A76', percent_chart, {'x_scale': 1.5, 'y_scale': 1.2})
        
        # Format the results sheet
        results_sheet = writer.sheets['Natijalar']
        
        # Define cell formats for headers and different grades
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4B8BBE',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })

        # Format column headers
        for col_num, value in enumerate(df.columns.values):
            results_sheet.write(0, col_num, value, header_format)
        
        # Add detailed statistics on a new sheet
        stats_sheet = workbook.add_worksheet('Statistika')
        
        # Define formats
        bold_format = workbook.add_format({'bold': True})
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4B8BBE',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        section_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E9F1F7',
            'border': 1,
            'align': 'left',
            'valign': 'vcenter'
        })
        
        # Calculate basic statistics
        total_students = len(df)
        avg_std_score = df['Standard Score'].mean()
        avg_raw_score = df['Raw Score'].mean()
        
        # Calculate passing percentage (students with grade other than NC)
        passing_students = total_students - grade_counts.get('NC', 0)
        passing_percent = (passing_students / total_students) * 100 if total_students > 0 else 0
        
        # General statistics section
        stats_sheet.merge_range('A1:C1', 'UMUMIY STATISTIKA', header_format)
        
        # Top Header
        stats_text_header = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'font_color': '#1E3A8A',
            'align': 'left',
            'indent': 1
        })
        
        stats_sheet.merge_range('A2:C2', '📊 STATISTIKA:', stats_text_header)
        
        # Rows with emojis
        stats_sheet.write('A3', '👥 Jami talabalar soni:', bold_format)
        stats_sheet.write('B3', total_students)
        
        stats_sheet.write('A4', '📝 O\'rtacha standart ball:', bold_format)
        stats_sheet.write('B4', f"{avg_std_score:.1f}")
        
        stats_sheet.write('A5', '📝 O\'rtacha xom ball:', bold_format)
        stats_sheet.write('B5', f"{avg_raw_score:.2f}")
        
        stats_sheet.write('A6', '✅ O\'tish foizi:', bold_format)
        stats_sheet.write('B6', f"{passing_percent:.1f}%")
        
        # Grade distribution section
        stats_sheet.merge_range('A8:C8', 'BAHOLAR TAQSIMOTI', header_format)
        
        # Baholar taqsimoti header
        stats_sheet.merge_range('A9:C9', '📑 BAHOLAR TAQSIMOTI:', stats_text_header)
        
        stats_sheet.write('A10', 'Baho', bold_format)
        stats_sheet.write('B10', 'Talabalar soni', bold_format)
        stats_sheet.write('C10', 'Foiz', bold_format)
        
        row = 11
        for i, grade in enumerate(grade_order):
            if grade in grade_counts:
                count = grade_counts[grade]
                percentage = (count / total_students) * 100 if total_students > 0 else 0
                stats_sheet.write(f'A{row}', grade)
                stats_sheet.write(f'B{row}', count)
                stats_sheet.write(f'C{row}', f"{percentage:.1f}%")
                row += 1
                
        # Format grade table with borders
        border_format = workbook.add_format({'border': 1})
        stats_sheet.conditional_format(f'A10:C{row-1}', {'type': 'no_blanks', 'format': border_format})
        
        # If item difficulties are available, add question analysis
        if data_df is not None and beta_values is not None and len(beta_values) > 0:
            # Calculate difficulty with question numbers and percentages
            question_analysis = []
            
            for i in range(len(beta_values)):
                if i+1 < len(data_df.columns):
                    q_num = i+1
                    col_name = data_df.columns[i+1]  # +1 because first column is student ID
                    correct_count = data_df[col_name].sum()
                    total_count = len(data_df)
                    percent_correct = 100 * correct_count / total_count if total_count > 0 else 0
                    question_analysis.append((q_num, beta_values[i], percent_correct))
            
            # Sort by difficulty (most difficult first)
            question_analysis.sort(key=lambda x: x[1], reverse=True)
            
            # Most difficult questions
            row += 2
            stats_sheet.merge_range(f'A{row}:C{row}', '🔴 ENG QIYIN 5 TA SAVOL', header_format)
            row += 1
            stats_sheet.write(f'A{row}', 'Savol', bold_format)
            stats_sheet.write(f'B{row}', 'Qiyinlik', bold_format)
            stats_sheet.write(f'C{row}', 'To\'g\'ri javoblar %', bold_format)
            row += 1
            
            # Top 5 most difficult questions
            for i in range(min(5, len(question_analysis))):
                q_num, difficulty, percent = question_analysis[i]
                stats_sheet.write(f'A{row}', f"#{q_num}")
                stats_sheet.write(f'B{row}', f"{difficulty:.2f}")
                stats_sheet.write(f'C{row}', f"{percent:.1f}%")
                row += 1
            
            # Most ideal (average) questions
            # Find questions with difficulty closest to 0
            question_analysis.sort(key=lambda x: abs(x[1]))
            
            row += 2
            stats_sheet.merge_range(f'A{row}:C{row}', '🟡 ENG IDEAL (O\'RTACHA) 5 TA SAVOL', header_format)
            row += 1
            stats_sheet.write(f'A{row}', 'Savol', bold_format)
            stats_sheet.write(f'B{row}', 'Qiyinlik', bold_format)
            stats_sheet.write(f'C{row}', 'To\'g\'ri javoblar %', bold_format)
            row += 1
            
            # Top 5 most ideal questions (closest to 0 difficulty)
            for i in range(min(5, len(question_analysis))):
                q_num, difficulty, percent = question_analysis[i]
                stats_sheet.write(f'A{row}', f"#{q_num}")
                stats_sheet.write(f'B{row}', f"{difficulty:.2f}")
                stats_sheet.write(f'C{row}', f"{percent:.1f}%")
                row += 1
            
            # Easiest questions
            question_analysis.sort(key=lambda x: x[1])
            
            row += 2
            stats_sheet.merge_range(f'A{row}:C{row}', '🟢 ENG OSON 5 TA SAVOL', header_format)
            row += 1
            stats_sheet.write(f'A{row}', 'Savol', bold_format)
            stats_sheet.write(f'B{row}', 'Qiyinlik', bold_format)
            stats_sheet.write(f'C{row}', 'To\'g\'ri javoblar %', bold_format)
            row += 1
            
            # Top 5 easiest questions
            for i in range(min(5, len(question_analysis))):
                q_num, difficulty, percent = question_analysis[i]
                stats_sheet.write(f'A{row}', f"#{q_num}")
                stats_sheet.write(f'B{row}', f"{difficulty:.2f}")
                stats_sheet.write(f'C{row}', f"{percent:.1f}%")
                row += 1
        
    # Ensure the file is properly closed and flushed
    excel_data.seek(0)
    return excel_data


def prepare_excel_for_download(results_df):
    """
    Prepare the results DataFrame as an Excel file for download.
    
    Parameters:
    - results_df: DataFrame with processed results
    
    Returns:
    - excel_data: BytesIO object containing Excel file data
    """
    # Copy the dataframe to avoid modifying the original
    df = results_df.copy()
    
    # Add Rank column if not already present
    if 'Rank' not in df.columns:
        df['Rank'] = range(1, len(df) + 1)
    
    # OTM percentage calculation removed as per client request
    
    # Sort by Standard Score in descending order
    df = df.sort_values(by='Standard Score', ascending=False).reset_index(drop=True)
    
    # Reorder columns to put 'Rank' before 'Student ID'
    cols = df.columns.tolist()
    student_id_idx = cols.index('Student ID')
    rank_idx = cols.index('Rank')
    
    # Remove 'Rank' from its current position
    cols.pop(rank_idx)
    # Insert 'Rank' before 'Student ID'
    cols.insert(student_id_idx, 'Rank')
    
    # Apply new column order
    df = df[cols]
    
    # Create a BytesIO object
    excel_data = io.BytesIO()
    
    # Create a Pandas Excel writer using the BytesIO object
    with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
        # Write the DataFrame to an Excel sheet
        df.to_excel(writer, sheet_name='Rasch Model Results', index=False)
        
        # Get the workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Rasch Model Results']
        
        # Define cell formats for different grades
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4B8BBE',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        # Grade-specific formats (per user request)
        grade_formats = {
            'A+': workbook.add_format({'bg_color': '#006400', 'font_color': 'white', 'border': 1}),  # Dark green
            'A': workbook.add_format({'bg_color': '#28B463', 'font_color': 'white', 'border': 1}),  # Green
            'B+': workbook.add_format({'bg_color': '#1A237E', 'font_color': 'white', 'border': 1}),  # Dark blue
            'B': workbook.add_format({'bg_color': '#3498DB', 'font_color': 'white', 'border': 1}),  # Blue
            'C+': workbook.add_format({'bg_color': '#8D6E63', 'font_color': 'white', 'border': 1}),  # Brown
            'C': workbook.add_format({'bg_color': '#F4D03F', 'font_color': 'black', 'border': 1}),  # Yellow
            'NC': workbook.add_format({'bg_color': '#E74C3C', 'font_color': 'white', 'border': 1})   # Red
        }
        
        # Format the header row
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Format the grade column and apply conditional formatting
        grade_col = df.columns.get_loc('Grade')
        score_col = df.columns.get_loc('Standard Score')
        
        # Apply formatting to each row based on grade
        for row_num, row_data in enumerate(df.values):
            # Get values from the row using iloc to avoid attribute errors
            grade = df.iloc[row_num]['Grade']
            
            if grade in grade_formats:
                worksheet.write(row_num+1, grade_col, grade, grade_formats[grade])
        
        # Set column widths
        worksheet.set_column('A:A', 6)   # Rank (No ustuni uchun kichikroq kenglik)
        worksheet.set_column('B:B', 30)  # Student ID (Ism-familiya uchun kattaroq kenglik)
        worksheet.set_column('C:C', 10)  # Raw Score
        worksheet.set_column('D:D', 12)  # Ability
        worksheet.set_column('E:E', 12)  # Standard Score
        worksheet.set_column('F:F', 8)   # Grade
    
    # Reset the pointer to the beginning of the BytesIO object
    excel_data.seek(0)
    
    return excel_data

def prepare_pdf_for_download(results_df, title="REPETITSION TEST NATIJALARI"):
    """
    Prepare the results DataFrame as a PDF file for download.
    
    Parameters:
    - results_df: DataFrame with processed results
    - title: Title for the PDF document
    
    Returns:
    - pdf_data: BytesIO object containing PDF file data
    """
    from reportlab.lib.units import mm
    from reportlab.lib.fonts import addMapping
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    # Prepare PDF file
    pdf_data = io.BytesIO()
    
    # Create PDF document with landscape orientation
    doc = SimpleDocTemplate(
        pdf_data,
        pagesize=landscape(A4),
        rightMargin=10*mm,
        leftMargin=10*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
        title=title
    )
    
    # Register fonts (for better display of Uzbek/Russian characters)
    try:
        # Default to built-in fonts if custom fonts fail
        pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
        addMapping('DejaVuSans', 0, 0, 'DejaVuSans')
        addMapping('DejaVuSans', 1, 0, 'DejaVuSans-Bold')
        base_font = 'DejaVuSans'
    except:
        # Use built-in fonts if custom fonts are not available
        base_font = 'Helvetica'
    
    # Initialize elements list for the PDF
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Title style with improved appearance
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=10,
        fontName=f'{base_font}-Bold',
        textColor=colors.HexColor("#1F497D")
    )
    
    # Add title with date (only date without time)
    from datetime import datetime
    today = datetime.now().strftime("%d.%m.%Y")
    full_title = f"{title}<br/><font size=10>Sana: {today}</font>"
    elements.append(Paragraph(full_title, title_style))
    elements.append(Spacer(1, 8*mm))
    
    # Get grade descriptions for the footer
    grade_descriptions = {
        'A+': '1-Daraja (Oliy Imtiyozli)',
        'A': '1-Daraja (Oliy)',
        'B+': '2-Daraja (Yuqori Imtiyozli)', 
        'B': '2-Daraja (Yuqori)',
        'C+': '3-Daraja (O\'rta Imtiyozli)',
        'C': '3-Daraja (O\'rta)',
        'NC': '4-Daraja (Sertifikatsiz)'
    }
    
    # Sort the dataframe by scores in descending order for better presentation
    results_df_sorted = results_df.sort_values(by='Standard Score', ascending=False).reset_index(drop=True)
    
    # Add a rank column if not present
    if 'Rank' not in results_df_sorted.columns:
        results_df_sorted['Rank'] = range(1, len(results_df_sorted) + 1)
    
    # Column widths optimized for landscape
    col_widths = [8*mm, 60*mm, 20*mm, 15*mm]
    
    # Prepare table header
    table_data = [["NO", "ISM FAMILIYA", "BALL", "DARAJA"]]
    
    # Process section data if available
    section_data_available = False
    section_columns = []
    
    try:
        # Check if section mapping exists
        mapping_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'section_mapping.xlsx')
        if os.path.exists(mapping_path):
            # Read section mapping file
            section_mapping = pd.read_excel(mapping_path)
            
            if 'section' in section_mapping.columns and 'question_id' in section_mapping.columns:
                # Get unique sections
                sections = section_mapping['section'].unique()
                
                # Only proceed if we have sections
                if len(sections) > 0:
                    section_data_available = True
                    
                    # Add section headers
                    for section in sections:
                        table_data[0].append(f"{section}")
                        section_columns.append(section)
                        col_widths.append(20*mm)
    except Exception as e:
        print(f"Error loading section data: {e}")
        section_data_available = False
    
    # Add data rows
    for i, row in results_df_sorted.iterrows():
        score = row['Standard Score']
        grade = row['Grade']
        
        # Get grade description
        grade_desc = grade_descriptions.get(grade, "")
        
        # Prepare row data
        row_data = [
            str(row['Rank']) if 'Rank' in row else str(i+1),  # Rank
            str(row['Student ID']),       # Ism familiya
            f"{row['Standard Score']:.1f}",  # BALL
            grade                         # DARAJA
        ]
        
        # Add section scores if available
        if section_data_available and section_columns:
            # Calculate section scores is not implemented fully here
            # This would require original student responses which we may not have
            # Instead we'll just add placeholder values
            for section in section_columns:
                row_data.append("-")
        
        # Add the complete row to table data
        table_data.append(row_data)
    
    # Create table
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Define table style with improved appearance
    base_style = [
        # Header style
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4472C4")),  # Dark blue header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), f'{base_font}-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        
        # Row styles
        ('FONTNAME', (0, 1), (-1, -1), base_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (1, -1), 'CENTER'),  # № and Rank columns centered
        ('ALIGN', (3, 1), (5, -1), 'CENTER'),  # Score, percentage and grade columns centered
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),    # Name column left aligned
        
        # Grid lines
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]
    
    # Apply grade-specific colors for entire rows
    for i in range(1, len(table_data)):
        grade_col = 3  # The 'DARAJA' column index
        grade = table_data[i][grade_col]
        
        # Define colors for grades and rows (per user request)
        if grade == 'A+':
            # To'q yashil
            grade_color = colors.HexColor("#006400")  # Dark green
            row_color = colors.HexColor("#E8F5E9")    # Light green background
            base_style.append(('BACKGROUND', (0, i), (-1, i), row_color))
            base_style.append(('BACKGROUND', (grade_col, i), (grade_col, i), grade_color))
            base_style.append(('TEXTCOLOR', (grade_col, i), (grade_col, i), colors.white))
        
        elif grade == 'A':
            # Yashil
            grade_color = colors.HexColor("#28B463")  # Green
            row_color = colors.HexColor("#ECFBEE")    # Very light green background
            base_style.append(('BACKGROUND', (0, i), (-1, i), row_color))
            base_style.append(('BACKGROUND', (grade_col, i), (grade_col, i), grade_color))
            base_style.append(('TEXTCOLOR', (grade_col, i), (grade_col, i), colors.white))
        
        elif grade == 'B+':
            # To'q ko'k
            grade_color = colors.HexColor("#1A237E")  # Dark blue
            row_color = colors.HexColor("#E8EAF6")    # Light blue background
            base_style.append(('BACKGROUND', (0, i), (-1, i), row_color))
            base_style.append(('BACKGROUND', (grade_col, i), (grade_col, i), grade_color))
            base_style.append(('TEXTCOLOR', (grade_col, i), (grade_col, i), colors.white))
        
        elif grade == 'B':
            # Ko'k
            grade_color = colors.HexColor("#3498DB")  # Blue
            row_color = colors.HexColor("#E8EAF6")    # Light blue background
            base_style.append(('BACKGROUND', (0, i), (-1, i), row_color))
            base_style.append(('BACKGROUND', (grade_col, i), (grade_col, i), grade_color))
            base_style.append(('TEXTCOLOR', (grade_col, i), (grade_col, i), colors.white))
        
        elif grade == 'C+':
            # Jigar rang
            grade_color = colors.HexColor("#8D6E63")  # Brown
            row_color = colors.HexColor("#EFEBE9")    # Light brown background
            base_style.append(('BACKGROUND', (0, i), (-1, i), row_color))
            base_style.append(('BACKGROUND', (grade_col, i), (grade_col, i), grade_color))
            base_style.append(('TEXTCOLOR', (grade_col, i), (grade_col, i), colors.white))
        
        elif grade == 'C':
            # Sariq
            grade_color = colors.HexColor("#F4D03F")  # Yellow
            row_color = colors.HexColor("#FFF8E1")    # Light yellow background
            base_style.append(('BACKGROUND', (0, i), (-1, i), row_color))
            base_style.append(('BACKGROUND', (grade_col, i), (grade_col, i), grade_color))
            base_style.append(('TEXTCOLOR', (grade_col, i), (grade_col, i), colors.black))
        
        elif grade == 'NC':
            # Qizil
            grade_color = colors.HexColor("#E74C3C")  # Red
            row_color = colors.HexColor("#FFEBEE")    # Light red background
            base_style.append(('BACKGROUND', (0, i), (-1, i), row_color))
            base_style.append(('BACKGROUND', (grade_col, i), (grade_col, i), grade_color))
            base_style.append(('TEXTCOLOR', (grade_col, i), (grade_col, i), colors.white))
            
        else:
            # Default for any other grade
            base_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor("#FFFFFF")))
            base_style.append(('BACKGROUND', (grade_col, i), (grade_col, i), colors.HexColor("#9E9E9E")))
            base_style.append(('TEXTCOLOR', (grade_col, i), (grade_col, i), colors.white))
    
    # Apply style to table
    table.setStyle(TableStyle(base_style))
    
    # Add the table to the elements
    elements.append(table)
    
    # Summary information is not needed
    
    # Add footer with contact info
    elements.append(Spacer(1, 15*mm))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_LEFT,
        fontName=base_font,
        textColor=colors.HexColor("#666666")
    )
    
    footer_text = """
    <b>Rasch Model Test Analysis</b><br/>
    Telegram: @rasch_counter_bot<br/>
    Yaratilgan sana: {}
    """.format(datetime.now().strftime("%d.%m.%Y"))
    
    elements.append(Paragraph(footer_text, footer_style))
    
    # Build the PDF
    try:
        doc.build(elements)
        pdf_data.seek(0)
        return pdf_data
    except Exception as e:
        print(f"Error building PDF: {e}")
        # In case of error, return a simplified PDF
        pdf_data = io.BytesIO()
        doc = SimpleDocTemplate(pdf_data, pagesize=landscape(A4))
        elements = [Paragraph("PDF yaratishda xatolik yuz berdi.", styles['Heading1'])]
        doc.build(elements)
        pdf_data.seek(0)
        return pdf_data
