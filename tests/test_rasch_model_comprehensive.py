"""
Comprehensive tests for Rasch model implementation
Bu fayl Rasch modelning barcha xususiyatlarini sinab ko'radi
"""
import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from models.rasch_model import rasch_model, ability_to_grade, ability_to_standard_score

class TestRaschModel:
    """Rasch model uchun to'liq test sinflari"""
    
    def test_basic_functionality(self):
        """Asosiy funksionallikni tekshirish"""
        # Oddiy test ma'lumotlari
        data = np.array([
            [1, 0, 1, 0],  # Talaba 1: 2 ta to'g'ri
            [0, 1, 1, 1],  # Talaba 2: 3 ta to'g'ri
            [1, 1, 0, 0],  # Talaba 3: 2 ta to'g'ri
        ])
        
        theta, beta = rasch_model(data)
        
        # Asosiy tekshiruvlar
        assert len(theta) == 3, "Theta uzunligi noto'g'ri"
        assert len(beta) == 4, "Beta uzunligi noto'g'ri"
        assert not np.isnan(theta).any(), "Theta'da NaN qiymatlar bor"
        assert not np.isnan(beta).any(), "Beta'da NaN qiymatlar bor"
        assert not np.isinf(theta).any(), "Theta'da cheksiz qiymatlar bor"
        assert not np.isinf(beta).any(), "Beta'da cheksiz qiymatlar bor"
    
    def test_edge_cases(self):
        """Chekka holatlarni tekshirish"""
        
        # 1. Barcha javoblar to'g'ri
        all_correct = np.array([[1, 1, 1], [1, 1, 1]])
        theta, beta = rasch_model(all_correct)
        assert len(theta) == 2
        assert len(beta) == 3
        
        # 2. Barcha javoblar noto'g'ri
        all_wrong = np.array([[0, 0, 0], [0, 0, 0]])
        theta, beta = rasch_model(all_wrong)
        assert len(theta) == 2
        assert len(beta) == 3
        
        # 3. Faqat bitta talaba
        single_student = np.array([[1, 0, 1, 0, 1]])
        theta, beta = rasch_model(single_student)
        assert len(theta) == 1
        assert len(beta) == 5
        
        # 4. Faqat bitta savol
        single_question = np.array([[1], [0], [1]])
        theta, beta = rasch_model(single_question)
        assert len(theta) == 3
        assert len(beta) == 1
    
    def test_large_dataset(self):
        """Katta ma'lumotlar to'plamini tekshirish"""
        # 100 ta talaba, 20 ta savol
        np.random.seed(42)
        data = np.random.randint(0, 2, (100, 20))
        
        theta, beta = rasch_model(data, max_students=50)
        
        assert len(theta) == 100
        assert len(beta) == 20
        assert not np.isnan(theta).any()
        assert not np.isnan(beta).any()
    
    def test_convergence(self):
        """Konvergensiyani tekshirish"""
        data = np.array([
            [1, 0, 1, 0, 1],
            [0, 1, 1, 1, 0],
            [1, 1, 0, 1, 1],
            [0, 0, 1, 0, 1],
        ])
        
        theta, beta = rasch_model(data)
        
        # Qiymatlar maqbul diapazonda bo'lishi kerak
        assert np.all(theta > -10), "Theta juda kichik"
        assert np.all(theta < 10), "Theta juda katta"
        assert np.all(beta > -10), "Beta juda kichik"
        assert np.all(beta < 10), "Beta juda katta"
    
    def test_ability_to_grade(self):
        """Ability'dan grade'ga o'tishni tekshirish"""
        # Turli ability qiymatlari
        abilities = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        grades = ability_to_grade(abilities)
        
        assert len(grades) == len(abilities)
        assert all(grade in ['A+', 'A', 'B+', 'B', 'C+', 'C', 'NC'] for grade in grades)
        
        # Yuqori ability -> yuqori grade
        high_ability = ability_to_grade(np.array([3.0]))
        assert high_ability[0] in ['A+', 'A']
        
        # Past ability -> past grade
        low_ability = ability_to_grade(np.array([-3.0]))
        assert low_ability[0] in ['C', 'NC']
    
    def test_ability_to_standard_score(self):
        """Ability'dan standard score'ga o'tishni tekshirish"""
        abilities = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        scores = ability_to_standard_score(abilities)
        
        assert len(scores) == len(abilities)
        assert all(0 <= score <= 100 for score in scores)
        
        # Yuqori ability -> yuqori score
        high_ability = ability_to_standard_score(np.array([3.0]))
        assert high_ability[0] >= 80
        
        # Past ability -> past score
        low_ability = ability_to_standard_score(np.array([-3.0]))
        assert low_ability[0] < 50

class TestDataProcessor:
    """Data processor uchun testlar"""
    
    def test_excel_processing(self):
        """Excel faylini qayta ishlashni tekshirish"""
        from data_processing.data_processor import process_exam_data
        
        # Test ma'lumotlari
        test_data = pd.DataFrame({
            'Student Name': ['Ali', 'Vali', 'Soli'],
            'Q1': [1, 0, 1],
            'Q2': [0, 1, 1],
            'Q3': [1, 1, 0],
            'Q4': [0, 0, 1]
        })
        
        results_df, ability_estimates, grade_counts, data_df, beta_values = process_exam_data(test_data)
        
        # Asosiy tekshiruvlar
        assert len(results_df) == 3, "Natijalar soni noto'g'ri"
        assert len(ability_estimates) == 3, "Ability estimates soni noto'g'ri"
        assert len(beta_values) == 4, "Beta values soni noto'g'ri"
        assert 'Student ID' in results_df.columns, "Student ID ustuni yo'q"
        assert 'Ability' in results_df.columns, "Ability ustuni yo'q"
        assert 'Grade' in results_df.columns, "Grade ustuni yo'q"

class TestBotFunctionality:
    """Bot funksionalligi uchun testlar"""
    
    def test_grade_descriptions(self):
        """Grade tavsiflarini tekshirish"""
        from config.settings import GRADE_DESCRIPTIONS
        
        expected_grades = ['A+', 'A', 'B+', 'B', 'C+', 'C', 'NC']
        
        for grade in expected_grades:
            assert grade in GRADE_DESCRIPTIONS, f"{grade} tavsifi yo'q"
            assert len(GRADE_DESCRIPTIONS[grade]) > 0, f"{grade} tavsifi bo'sh"
    
    def test_error_handling(self):
        """Xatolik boshqarishni tekshirish"""
        from utils.error_handling import safe_divide, validate_excel_file
        
        # Safe divide test
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(0, 0) == 0.0
        
        # Excel validation test
        # Bu yerda haqiqiy Excel fayl yaratish kerak
        # Hozircha asosiy funksionallikni tekshiramiz
        assert callable(validate_excel_file)
        assert callable(safe_divide)

class TestPerformance:
    """Performance testlar"""
    
    def test_memory_usage(self):
        """Xotira ishlatishni tekshirish"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Katta ma'lumotlar bilan test
        data = np.random.randint(0, 2, (1000, 50))
        theta, beta = rasch_model(data)
        
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = mem_after - mem_before
        
        # Xotira o'sishi 100 MB dan kam bo'lishi kerak
        assert memory_increase < 100, f"Juda ko'p xotira ishlatildi: {memory_increase:.2f} MB"
    
    def test_execution_time(self):
        """Ishlash vaqtini tekshirish"""
        import time
        
        data = np.random.randint(0, 2, (100, 20))
        
        start_time = time.time()
        theta, beta = rasch_model(data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # 5 soniyadan kam vaqt ketishi kerak
        assert execution_time < 5.0, f"Juda uzoq vaqt ketdi: {execution_time:.2f} soniya"

# Pytest fixtures
@pytest.fixture
def sample_data():
    """Test uchun namuna ma'lumotlar"""
    return np.array([
        [1, 0, 1, 0, 1],
        [0, 1, 1, 1, 0],
        [1, 1, 0, 1, 1],
        [0, 0, 1, 0, 1],
        [1, 1, 1, 0, 0]
    ])

@pytest.fixture
def sample_dataframe():
    """Test uchun namuna DataFrame"""
    return pd.DataFrame({
        'Student Name': ['Ali', 'Vali', 'Soli', 'Doni', 'Eli'],
        'Q1': [1, 0, 1, 0, 1],
        'Q2': [0, 1, 1, 0, 1],
        'Q3': [1, 1, 0, 1, 1],
        'Q4': [0, 1, 1, 0, 0],
        'Q5': [1, 0, 1, 1, 0]
    })

# Parametrized tests
@pytest.mark.parametrize("n_students,n_questions", [
    (10, 5),
    (50, 10),
    (100, 20),
    (200, 30)
])
def test_different_sizes(n_students, n_questions):
    """Turli o'lchamdagi ma'lumotlar uchun test"""
    data = np.random.randint(0, 2, (n_students, n_questions))
    theta, beta = rasch_model(data)
    
    assert len(theta) == n_students
    assert len(beta) == n_questions
    assert not np.isnan(theta).any()
    assert not np.isnan(beta).any()

if __name__ == "__main__":
    # Testlarni ishga tushirish
    pytest.main([__file__, "-v"])
