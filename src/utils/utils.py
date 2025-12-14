import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

# Yangilangan BBM standartlari bo'yicha daraja tavsiflar 
GRADE_DESCRIPTIONS = {
    'A+': 'A+ daraja (70 balldan yuqori): Test sinovlarida ushbu fandan belgilangan maksimal ball beriladi.',
    'A': 'A daraja (65–69.9 ball): Test sinovlarida ushbu fandan belgilangan maksimal ball beriladi.',
    'B+': 'B+ daraja (60–64.9 ball): Test sinovlarida ushbu fandan belgilangan maksimal ballga nisbatan proporsional ball beriladi.',
    'B': 'B daraja (55–59.9 ball): Test sinovlarida ushbu fandan belgilangan maksimal ballga nisbatan proporsional ball beriladi.',
    'C+': 'C+ daraja (50–54.9 ball): Test sinovlarida ushbu fandan belgilangan maksimal ballga nisbatan proporsional ball beriladi.',
    'C': 'C daraja (46–49.9 ball): Test sinovlarida ushbu fandan belgilangan maksimal ballga nisbatan proporsional ball beriladi.',
    'NC': 'NC daraja (46 balldan past): Test sinovlarini o\'tkazish uchun minimal ball to\'planmagan, sertifikat berilmaydi.'
}

# Grade colors for visualization - updated to match PDF colors in screenshot
GRADE_COLORS = {
    'A+': '#00CC00',  # Yashil (A+ daraja) - yangi skrinshot
    'A': '#00CC00',   # Yashil (A daraja) - yangi skrinshot
    'B+': '#FF9900',  # Naranja (B+ daraja) - yangi skrinshot
    'B': '#3366FF',   # Ko'k (B daraja) - yangi skrinshot 
    'C+': '#3366FF',  # Ko'k (C+ daraja) - yangi skrinshot
    'C': '#3366FF',   # Ko'k (C daraja) - yangi skrinshot
    'D': '#FF0000',   # Qizil (D daraja)
    'NC': '#FF0000',  # Qizil
    'F': '#FF0000'    # Qizil
}

def display_grade_distribution(grade_counts):
    """
    Display a bar chart showing the distribution of grades.
    
    Parameters:
    - grade_counts: Dictionary with counts of each grade
    """
    # Define grade order for consistent display (BBM standards)
    grade_order = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'NC']
    
    # Prepare data ensuring all grades are represented
    grades = []
    counts = []
    colors = []
    
    for grade in grade_order:
        if grade in grade_counts:
            grades.append(grade)
            counts.append(grade_counts[grade])
            colors.append(GRADE_COLORS[grade])
        else:
            grades.append(grade)
            counts.append(0)
            colors.append(GRADE_COLORS[grade])
    
    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create the bar chart
    bars = ax.bar(grades, counts, color=colors)
    
    # Add count labels on top of each bar
    for i, bar in enumerate(bars):
        height = bar.get_height()
        if height > 0:  # Only add label if there are students with this grade
            ax.text(
                bar.get_x() + bar.get_width()/2.,
                height + 0.1,
                str(height),
                ha='center',
                va='bottom',
                fontweight='bold'
            )
    
    # Customize the chart
    ax.set_ylim(0, max(counts) * 1.2 if counts else 10)  # Add some space above the highest bar
    ax.set_xlabel('Grade', fontsize=12)
    ax.set_ylabel('Number of Students', fontsize=12)
    ax.set_title('Distribution of Grades', fontsize=14, fontweight='bold')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Display the chart in Streamlit
    st.pyplot(fig)

def calculate_statistics(results_df):
    """
    Calculate various statistics from the results DataFrame.
    
    Parameters:
    - results_df: DataFrame with processed results
    
    Returns:
    - stats: Dictionary containing statistics
    """
    stats = {
        'total_students': len(results_df),
        'avg_ability': results_df['Ability'].mean(),
        'median_ability': results_df['Ability'].median(),
        'max_ability': results_df['Ability'].max(),
        'min_ability': results_df['Ability'].min(),
        'std_ability': results_df['Ability'].std(),
        'avg_raw_score': results_df['Raw Score'].mean(),
        'pass_rate': (results_df['Grade'] != 'NC').mean() * 100
    }
    
    return stats
