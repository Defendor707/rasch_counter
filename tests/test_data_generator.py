"""
Test data generator for Rasch Counter Bot
Bu fayl testlar uchun turli ma'lumotlar yaratadi
"""
import numpy as np
import pandas as pd
from typing import Tuple, Optional

class TestDataGenerator:
    """Test ma'lumotlari generatori"""
    
    @staticmethod
    def generate_simple_data(n_students: int = 5, n_questions: int = 5) -> pd.DataFrame:
        """Oddiy test ma'lumotlari yaratish"""
        np.random.seed(42)
        
        # Random javoblar
        data = np.random.randint(0, 2, (n_students, n_questions))
        
        # Student ismlari
        student_names = [f"Student_{i+1:02d}" for i in range(n_students)]
        
        # DataFrame yaratish
        df_data = {'Student Name': student_names}
        for i in range(n_questions):
            df_data[f'Q{i+1}'] = data[:, i]
        
        return pd.DataFrame(df_data)
    
    @staticmethod
    def generate_realistic_data(n_students: int = 100, n_questions: int = 20) -> pd.DataFrame:
        """Realistik test ma'lumotlari yaratish"""
        np.random.seed(42)
        
        # Talaba qobiliyatlari (theta)
        student_abilities = np.random.normal(0, 1, n_students)
        
        # Savol qiyinliklari (beta)
        question_difficulties = np.random.normal(0, 1, n_questions)
        
        # Ehtimolliklar hisoblash (Rasch model)
        logits = student_abilities[:, np.newaxis] - question_difficulties[np.newaxis, :]
        probabilities = 1 / (1 + np.exp(-logits))
        
        # Javoblar yaratish
        data = np.random.binomial(1, probabilities)
        
        # Student ismlari
        student_names = [f"Student_{i+1:03d}" for i in range(n_students)]
        
        # DataFrame yaratish
        df_data = {'Student Name': student_names}
        for i in range(n_questions):
            df_data[f'Q{i+1}'] = data[:, i]
        
        return pd.DataFrame(df_data)
    
    @staticmethod
    def generate_edge_case_data() -> dict:
        """Chekka holatlar uchun ma'lumotlar"""
        cases = {}
        
        # 1. Barcha javoblar to'g'ri
        cases['all_correct'] = pd.DataFrame({
            'Student Name': ['Perfect_1', 'Perfect_2'],
            'Q1': [1, 1],
            'Q2': [1, 1],
            'Q3': [1, 1]
        })
        
        # 2. Barcha javoblar noto'g'ri
        cases['all_wrong'] = pd.DataFrame({
            'Student Name': ['Failing_1', 'Failing_2'],
            'Q1': [0, 0],
            'Q2': [0, 0],
            'Q3': [0, 0]
        })
        
        # 3. Faqat bitta talaba
        cases['single_student'] = pd.DataFrame({
            'Student Name': ['Lonely_Student'],
            'Q1': [1],
            'Q2': [0],
            'Q3': [1],
            'Q4': [0],
            'Q5': [1]
        })
        
        # 4. Faqat bitta savol
        cases['single_question'] = pd.DataFrame({
            'Student Name': ['Student_1', 'Student_2', 'Student_3'],
            'Q1': [1, 0, 1]
        })
        
        # 5. Bo'sh ma'lumotlar
        cases['empty_data'] = pd.DataFrame({
            'Student Name': [],
            'Q1': [],
            'Q2': []
        })
        
        # 6. Noto'g'ri ma'lumotlar
        cases['invalid_data'] = pd.DataFrame({
            'Student Name': ['Student_1', 'Student_2'],
            'Q1': ['a', 'b'],  # Harflar
            'Q2': [1, 0]
        })
        
        return cases
    
    @staticmethod
    def generate_large_dataset(n_students: int = 1000, n_questions: int = 50) -> pd.DataFrame:
        """Katta ma'lumotlar to'plami yaratish"""
        np.random.seed(42)
        
        # Realistik qobiliyat taqsimoti
        student_abilities = np.random.normal(0, 1.5, n_students)
        question_difficulties = np.random.normal(0, 1, n_questions)
        
        # Ehtimolliklar
        logits = student_abilities[:, np.newaxis] - question_difficulties[np.newaxis, :]
        probabilities = 1 / (1 + np.exp(-logits))
        
        # Javoblar
        data = np.random.binomial(1, probabilities)
        
        # Student ismlari
        student_names = [f"Student_{i+1:04d}" for i in range(n_students)]
        
        # DataFrame
        df_data = {'Student Name': student_names}
        for i in range(n_questions):
            df_data[f'Q{i+1}'] = data[:, i]
        
        return pd.DataFrame(df_data)
    
    @staticmethod
    def generate_performance_test_data() -> dict:
        """Performance test uchun ma'lumotlar"""
        datasets = {}
        
        # Turli o'lchamdagi ma'lumotlar
        sizes = [
            (10, 5),    # Kichik
            (50, 10),   # O'rta
            (100, 20),  # Katta
            (500, 30),  # Juda katta
            (1000, 50)  # Maksimal
        ]
        
        for n_students, n_questions in sizes:
            key = f"{n_students}_students_{n_questions}_questions"
            datasets[key] = TestDataGenerator.generate_realistic_data(n_students, n_questions)
        
        return datasets

# Test data fixtures
def get_test_data():
    """Test ma'lumotlarini olish"""
    generator = TestDataGenerator()
    
    return {
        'simple': generator.generate_simple_data(),
        'realistic': generator.generate_realistic_data(),
        'edge_cases': generator.generate_edge_case_data(),
        'large': generator.generate_large_dataset(),
        'performance': generator.generate_performance_test_data()
    }

if __name__ == "__main__":
    # Test ma'lumotlarini yaratish va ko'rsatish
    generator = TestDataGenerator()
    
    print("🧪 Test Data Generator")
    print("=" * 50)
    
    # Oddiy ma'lumotlar
    simple_data = generator.generate_simple_data()
    print(f"Simple data: {simple_data.shape}")
    print(simple_data.head())
    print()
    
    # Realistik ma'lumotlar
    realistic_data = generator.generate_realistic_data(10, 5)
    print(f"Realistic data: {realistic_data.shape}")
    print(realistic_data.head())
    print()
    
    # Chekka holatlar
    edge_cases = generator.generate_edge_case_data()
    print("Edge cases:")
    for name, data in edge_cases.items():
        print(f"  {name}: {data.shape}")
    print()
    
    # Performance test ma'lumotlari
    perf_data = generator.generate_performance_test_data()
    print("Performance test data:")
    for name, data in perf_data.items():
        print(f"  {name}: {data.shape}")
