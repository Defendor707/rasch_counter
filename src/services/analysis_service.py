#!/usr/bin/env python3
"""
Rasch Analysis Service
Umumiy API service - bot va web app uchun
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
import sys

# Add src directory to Python path
src_dir = Path(__file__).parent.parent
sys.path.insert(0, str(src_dir))

from data_processing.data_processor import process_exam_data, prepare_excel_for_download, prepare_pdf_for_download
from models.rasch_model import rasch_model, ability_to_grade, ability_to_standard_score

logger = logging.getLogger(__name__)

class RaschAnalysisService:
    """
    Umumiy Rasch Analysis Service
    Bot va Web app uchun bir xil API
    """
    
    def __init__(self):
        self.sessions = {}  # Active sessions
        
    def create_session(self, session_id=None):
        """Yangi session yaratish"""
        if not session_id:
            session_id = f"session_{int(datetime.now().timestamp())}"
        
        self.sessions[session_id] = {
            'status': 'created',
            'progress': 0,
            'message': 'Session yaratildi',
            'results': None,
            'timestamp': datetime.now().isoformat()
        }
        
        return session_id
    
    def process_file(self, file_path_or_df, session_id, progress_callback=None):
        """
        Excel fayl yoki DataFrame ni qayta ishlash
        
        Args:
            file_path_or_df: Excel fayl yo'li yoki pandas DataFrame
            session_id: Session ID
            progress_callback: Progress callback function
        """
        try:
            # Session status yangilash
            self.sessions[session_id]['status'] = 'processing'
            self.sessions[session_id]['progress'] = 5
            self.sessions[session_id]['message'] = 'Ma\'lumotlar o\'qilmoqda...'
            
            # DataFrame olish
            if isinstance(file_path_or_df, str) or isinstance(file_path_or_df, Path):
                df = pd.read_excel(file_path_or_df)
            else:
                df = file_path_or_df
            
            # Progress callback
            def internal_progress_callback(percent, message):
                self.sessions[session_id]['progress'] = percent
                self.sessions[session_id]['message'] = message
                if progress_callback:
                    progress_callback(percent, message)
            
            # Ma'lumotlarni qayta ishlash
            results_df, ability_estimates, grade_counts, df_cleaned, item_difficulties = process_exam_data(
                df, internal_progress_callback
            )
            
            # Fix item difficulties format for all files
            if isinstance(item_difficulties, np.ndarray):
                # Convert to list without clipping to preserve variation
                item_difficulties = item_difficulties.tolist()
            
            # Natijalarni saqlash
            results = {
                'results_df': results_df,
                'ability_estimates': ability_estimates,
                'grade_counts': grade_counts,
                'df_cleaned': df_cleaned,
                'item_difficulties': item_difficulties,
                'timestamp': datetime.now().isoformat()
            }
            
            self.sessions[session_id]['results'] = results
            self.sessions[session_id]['status'] = 'completed'
            self.sessions[session_id]['progress'] = 100
            self.sessions[session_id]['message'] = 'Tahlil yakunlandi!'
            
            return True
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            self.sessions[session_id]['status'] = 'error'
            self.sessions[session_id]['progress'] = 0
            self.sessions[session_id]['message'] = f'Xatolik: {str(e)}'
            return False
    
    def get_status(self, session_id):
        """Session statusini olish"""
        if session_id not in self.sessions:
            return {'error': 'Session topilmadi'}
        
        session = self.sessions[session_id]
        return {
            'status': session['status'],
            'progress': session['progress'],
            'message': session['message']
        }
    
    def get_results(self, session_id, format='json'):
        """
        Natijalarni olish
        
        Args:
            session_id: Session ID
            format: 'json', 'summary', 'detailed'
        """
        if session_id not in self.sessions:
            return {'error': 'Session topilmadi'}
        
        session = self.sessions[session_id]
        if not session['results']:
            return {'error': 'Natijalar topilmadi'}
        
        results = session['results']
        
        if format == 'json':
            return self._format_json_results(results)
        elif format == 'summary':
            return self._format_summary_results(results)
        elif format == 'detailed':
            return self._format_detailed_results(results)
        else:
            return {'error': 'Noto\'g\'ri format'}
    
    def _format_json_results(self, results):
        """JSON format uchun natijalar"""
        # Item difficulties list yaratish
        item_difficulties_list = []
        for i, difficulty in enumerate(results['item_difficulties']):
            # Normalize for display purposes - scale extreme values to reasonable range
            raw_difficulty = float(difficulty)
            
            # Normalize extreme values to reasonable range
            if abs(raw_difficulty) > 10:
                # Scale to [-3, 3] range while preserving relative differences
                try:
                    # Find min and max values
                    all_values = [float(d) for d in results['item_difficulties'] if d is not None]
                    if all_values:
                        min_val = min(all_values)
                        max_val = max(all_values)
                        val_range = max_val - min_val
                        
                        if val_range > 0:
                            # Normalize to [-3, 3] range
                            normalized = ((raw_difficulty - min_val) / val_range) * 6 - 3
                            display_difficulty = normalized
                        else:
                            display_difficulty = 0.0
                    else:
                        display_difficulty = raw_difficulty
                except (ValueError, TypeError):
                    display_difficulty = raw_difficulty
            else:
                display_difficulty = raw_difficulty
            
            # Clip to reasonable range
            display_difficulty = np.clip(display_difficulty, -3, 3)
            
            item_difficulties_list.append({
                'Question': f'Savol {i+1}',
                'Difficulty': round(display_difficulty, 3),
                'Difficulty_Level': 'Oson' if display_difficulty < -0.5 else 'O\'rta' if display_difficulty < 0.5 else 'Qiyin'
            })
        
        # Qiyinlik bo'yicha tartiblash
        item_difficulties_list.sort(key=lambda x: x['Difficulty'])
        
        # Convert item_difficulties to numpy array for calculations
        item_diffs_array = np.array(results['item_difficulties'])
        
        # Safe calculations for summary
        try:
            if len(results['results_df']) > 0 and 'Standard Score' in results['results_df'].columns:
                avg_score = float(results['results_df']['Standard Score'].mean())
                highest_score = float(results['results_df']['Standard Score'].max())
                lowest_score = float(results['results_df']['Standard Score'].min())
                std_deviation = float(results['results_df']['Standard Score'].std())
            else:
                avg_score = highest_score = lowest_score = std_deviation = 0.0
        except Exception:
            avg_score = highest_score = lowest_score = std_deviation = 0.0
        
        # Safe calculations for item difficulties
        try:
            if len(item_diffs_array) > 0:
                item_min = float(item_diffs_array.min())
                item_max = float(item_diffs_array.max())
                item_mean = float(item_diffs_array.mean())
                item_std = float(item_diffs_array.std())
            else:
                item_min = item_max = item_mean = item_std = 0.0
        except Exception:
            item_min = item_max = item_mean = item_std = 0.0
        
        # Convert numpy arrays to lists for JSON serialization
        results_df_list = results['results_df'].to_dict('records') if hasattr(results['results_df'], 'to_dict') else results['results_df']
        ability_estimates_list = results['ability_estimates'].tolist() if hasattr(results['ability_estimates'], 'tolist') else results['ability_estimates']
        # Convert df_cleaned to dict for JSON serialization
        df_cleaned_dict = results['df_cleaned'].to_dict('records') if hasattr(results['df_cleaned'], 'to_dict') else results['df_cleaned']
        item_difficulties_list_raw = results['item_difficulties'].tolist() if hasattr(results['item_difficulties'], 'tolist') else results['item_difficulties']
        
        return {
            'summary': {
                'total_students': len(results['results_df']),
                'total_questions': len(results['item_difficulties']),
                'grade_distribution': results['grade_counts'],
                'average_score': avg_score,
                'highest_score': highest_score,
                'lowest_score': lowest_score,
                'std_deviation': std_deviation
            },
            'item_difficulties': {
                'min': item_min,
                'max': item_max,
                'mean': item_mean,
                'std': item_std,
                'items': item_difficulties_list
            },
            'results_df': results_df_list,
            'ability_estimates': ability_estimates_list,
            'grade_counts': results['grade_counts'],
            'df_cleaned': df_cleaned_dict,  # Convert to dict for JSON
            'item_difficulties': item_difficulties_list_raw,
            'timestamp': results['timestamp'],
            # Bot uchun to'g'ridan-to'g'ri kirish
            'total_students': len(results['results_df']),
            'total_questions': len(results['item_difficulties']),
            'grade_distribution': results['grade_counts'],
            'average_score': avg_score,
            'highest_score': highest_score,
            'lowest_score': lowest_score,
            'std_deviation': std_deviation
        }
    
    def _format_summary_results(self, results):
        """Telegram bot uchun qisqa format"""
        grade_counts = results['grade_counts']
        total_students = len(results['results_df'])
        
        # A+/A baholar
        top_grades = grade_counts.get('A+', 0) + grade_counts.get('A', 0)
        # O'tgan talabalar
        passing_grades = (top_grades + grade_counts.get('B+', 0) + 
                         grade_counts.get('B', 0) + grade_counts.get('C+', 0) + 
                         grade_counts.get('C', 0))
        # O'tmagan talabalar
        failing_count = grade_counts.get('NC', 0)
        
        # Foizlar
        top_percent = (top_grades/total_students*100) if total_students > 0 else 0
        pass_rate = (passing_grades/total_students*100) if total_students > 0 else 0
        fail_percent = (failing_count/total_students*100) if total_students > 0 else 0
        
        return {
            'total_students': total_students,
            'top_grades_count': top_grades,
            'top_grades_percent': round(top_percent, 2),
            'passing_count': passing_grades,
            'pass_rate': round(pass_rate, 2),
            'failing_count': failing_count,
            'fail_percent': round(fail_percent, 2),
            'grade_distribution': grade_counts
        }
    
    def _format_detailed_results(self, results):
        """Batafsil format"""
        # Item difficulties ni normalize qilish (bot uchun ham)
        normalized_difficulties = []
        for difficulty in results['item_difficulties']:
            raw_difficulty = float(difficulty)
            
            # Normalize extreme values to reasonable range
            if abs(raw_difficulty) > 10:
                try:
                    all_values = [float(d) for d in results['item_difficulties'] if d is not None]
                    if all_values:
                        min_val = min(all_values)
                        max_val = max(all_values)
                        val_range = max_val - min_val
                        
                        if val_range > 0:
                            normalized = ((raw_difficulty - min_val) / val_range) * 6 - 3
                            normalized_difficulties.append(normalized)
                        else:
                            normalized_difficulties.append(0.0)
                    else:
                        normalized_difficulties.append(raw_difficulty)
                except (ValueError, TypeError):
                    normalized_difficulties.append(raw_difficulty)
            else:
                normalized_difficulties.append(raw_difficulty)
        
        return {
            'results_df': results['results_df'],
            'ability_estimates': results['ability_estimates'],
            'grade_counts': results['grade_counts'],
            'df_cleaned': results['df_cleaned'],
            'item_difficulties': normalized_difficulties,
            'timestamp': results['timestamp']
        }
    
    def get_item_difficulties_text(self, session_id):
        """Telegram bot uchun savol qiyinliklari matni"""
        if session_id not in self.sessions:
            return "❌ Session topilmadi."
        
        session = self.sessions[session_id]
        if not session['results']:
            return "❌ Natijalar topilmadi."
        
        beta_values = session['results']['item_difficulties']
        
        if len(beta_values) == 0:
            return "❌ Savol qiyinliklari ma'lumotlari topilmadi."
        
        # Savol qiyinliklarini tayyorlash
        text = "📊 Savol Qiyinliklari:\n\n"
        
        # Savol qiyinliklarini tartiblash
        sorted_items = []
        for i, difficulty in enumerate(beta_values):
            difficulty_level = "Oson" if difficulty < -0.5 else "O'rta" if difficulty < 0.5 else "Qiyin"
            sorted_items.append((i+1, difficulty, difficulty_level))
        
        # Qiyinlik bo'yicha tartiblash
        sorted_items.sort(key=lambda x: x[1])
        
        # Eng oson 10 ta savol
        text += "🟢 Eng Oson Savollar:\n"
        for i, (q_num, diff, level) in enumerate(sorted_items[:10]):
            emoji = "🟢" if level == "Oson" else "🟡" if level == "O'rta" else "🔴"
            text += f"{emoji} Savol {q_num}: {diff:.3f} ({level})\n"
        
        # Eng qiyin 10 ta savol
        text += "\n🔴 Eng Qiyin Savollar:\n"
        for i, (q_num, diff, level) in enumerate(sorted_items[-10:]):
            emoji = "🟢" if level == "Oson" else "🟡" if level == "O'rta" else "🔴"
            text += f"{emoji} Savol {q_num}: {diff:.3f} ({level})\n"
        
        # Umumiy statistika
        avg_difficulty = np.mean(beta_values)
        min_difficulty = np.min(beta_values)
        max_difficulty = np.max(beta_values)
        
        text += f"\n📈 Umumiy Statistika:\n"
        text += f"• O'rtacha qiyinlik: {avg_difficulty:.3f}\n"
        text += f"• Eng oson savol: {min_difficulty:.3f}\n"
        text += f"• Eng qiyin savol: {max_difficulty:.3f}\n"
        text += f"• Jami savollar: {len(beta_values)} ta"
        
        return text
    
    def get_excel_file(self, session_id):
        """Excel fayl olish"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        if not session['results']:
            return None
        
        results = session['results']
        return prepare_excel_for_download(
            results['results_df'], 
            results['df_cleaned'], 
            results['item_difficulties']
        )
    
    def get_pdf_file(self, session_id):
        """PDF fayl olish"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        if not session['results']:
            return None
        
        results = session['results']
        return prepare_pdf_for_download(results['results_df'])
    
    def create_sample_matrix(self):
        """
        Namuna matrix yaratish va tahlil qilish
        50 talaba va 55 savol bilan to'liq tahlil
        """
        np.random.seed(42)
        n_students = 50
        n_questions = 55
        
        # Create realistic sample data matrix
        sample_data = []
        
        # Student IDs
        student_ids = [f'Talaba{i+1:03d}' for i in range(n_students)]
        
        # Question columns
        question_columns = [f'Savol_{i+1}' for i in range(n_questions)]
        
        # Create realistic item difficulties (same for all students)
        # Create diverse difficulties: some easy, some medium, some hard
        item_difficulties = []
        for i in range(n_questions):
            if i < n_questions // 3:  # Easy questions
                item_difficulties.append(np.random.normal(-1, 0.3))
            elif i < 2 * n_questions // 3:  # Medium questions
                item_difficulties.append(np.random.normal(0, 0.3))
            else:  # Hard questions
                item_difficulties.append(np.random.normal(1, 0.3))
        item_difficulties = np.array(item_difficulties)
        
        # Create realistic data with different ability levels
        for i in range(n_students):
            # Simulate student ability
            if i < 5:  # Top students
                ability = np.random.normal(1.5, 0.5)
            elif i < 15:  # Good students
                ability = np.random.normal(0.5, 0.5)
            elif i < 35:  # Average students
                ability = np.random.normal(0, 0.5)
            else:  # Below average students
                ability = np.random.normal(-0.5, 0.5)
            
            # Calculate probabilities using the same item difficulties
            logits = ability - item_difficulties
            probabilities = 1 / (1 + np.exp(-logits))
            
            # Generate responses
            responses = np.random.binomial(1, probabilities)
            
            # Create row data
            row = [student_ids[i]] + responses.tolist()
            sample_data.append(row)
        
        # Create DataFrame
        columns = ['Talaba_ID'] + question_columns
        df = pd.DataFrame(sample_data, columns=columns)
        
        # Create session and process
        session_id = self.create_session()
        
        # Process the sample data through full analysis
        success = self.process_file(df, session_id)
        
        if success:
            return session_id
        else:
            return None
    
    def create_sample_results(self):
        """Namuna natijalar yaratish (legacy method for web app)"""
        return self.create_sample_matrix()

# Global service instance
analysis_service = RaschAnalysisService()
