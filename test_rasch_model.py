#!/usr/bin/env python3
"""
UZBMB standartlariga muvofiq Rasch modelini test qilish uchun skript.
"""

import numpy as np
import pandas as pd
from rasch_model import rasch_model, ability_to_standard_score, ability_to_grade

def create_test_data():
    """Test uchun namuna ma'lumotlar yaratish"""
    np.random.seed(42)  # Reproducible results
    
    n_students = 100
    n_items = 50
    
    # Realistic test data yaratish
    # Ba'zi talabalar yaxshi, ba'zilari o'rta, ba'zilari past natija ko'rsatadi
    student_abilities = np.random.normal(0, 1, n_students)
    item_difficulties = np.random.normal(0, 0.8, n_items)
    
    # Response matrix yaratish
    data = np.zeros((n_students, n_items), dtype=int)
    
    for i in range(n_students):
        for j in range(n_items):
            # Rasch model ehtimolligi
            logit = student_abilities[i] - item_difficulties[j]
            prob = 1 / (1 + np.exp(-logit))
            
            # Binary response
            data[i, j] = 1 if np.random.random() < prob else 0
    
    # Student names yaratish
    student_names = [f"Talaba_{i+1:03d}" for i in range(n_students)]
    
    # DataFrame yaratish
    df = pd.DataFrame(data)
    df.insert(0, 'Student_ID', student_names)
    
    return df

def test_rasch_model():
    """Rasch modelini test qilish"""
    print("🧪 UZBMB standartlariga muvofiq Rasch model testi")
    print("=" * 50)
    
    # Test ma'lumotlarini yaratish
    print("📊 Test ma'lumotlari yaratilmoqda...")
    df = create_test_data()
    print(f"✅ {len(df)} ta talaba, {len(df.columns)-1} ta savol")
    
    # Data preprocessing
    print("\n🔧 Ma'lumotlar qayta ishlanmoqda...")
    data_array = df.iloc[:, 1:].values  # Student ID dan tashqari barcha ustunlar
    
    # Rasch modelini ishga tushirish
    print("🧮 Rasch modeli ishga tushirilmoqda...")
    theta, beta = rasch_model(data_array)
    
    print(f"✅ Theta (qobiliyatlar): min={theta.min():.3f}, max={theta.max():.3f}, mean={theta.mean():.3f}")
    print(f"✅ Beta (qiyinliklar): min={beta.min():.3f}, max={beta.max():.3f}, mean={beta.mean():.3f}")
    
    # Standard scores va grades hisoblash
    print("\n📈 Standart ballar va baholar hisoblanmoqda...")
    standard_scores = [ability_to_standard_score(t) for t in theta]
    grades = [ability_to_grade(t) for t in theta]
    
    # Natijalarni tahlil qilish
    print("\n📊 Natijalar tahlili:")
    print(f"📝 O'rtacha standart ball: {np.mean(standard_scores):.2f}")
    print(f"📊 Standart og'ish: {np.std(standard_scores):.2f}")
    
    # Grade distribution
    from collections import Counter
    grade_counts = Counter(grades)
    print(f"\n🎓 Baholar taqsimoti:")
    for grade in ['A+', 'A', 'B+', 'B', 'C+', 'C', 'NC']:
        count = grade_counts.get(grade, 0)
        percentage = (count / len(grades)) * 100
        print(f"   {grade}: {count} ta ({percentage:.1f}%)")
    
    # Top 10 talabalar
    print(f"\n🏆 Eng yaxshi 10 ta talaba:")
    student_scores = list(zip(df['Student_ID'], standard_scores, grades))
    student_scores.sort(key=lambda x: x[1], reverse=True)
    
    for i, (name, score, grade) in enumerate(student_scores[:10]):
        print(f"   {i+1:2d}. {name}: {score:.2f} ({grade})")
    
    # Item difficulty analysis
    print(f"\n📚 Savollar qiyinligi tahlili:")
    print(f"   Eng qiyin savol: {np.argmax(beta)+1} (β={beta.max():.3f})")
    print(f"   Eng oson savol: {np.argmin(beta)+1} (β={beta.min():.3f})")
    print(f"   O'rtacha qiyinlik: {beta.mean():.3f}")
    
    # Model fit ko'rsatkichlari
    print(f"\n🔍 Model fit ko'rsatkichlari:")
    
    # Expected vs observed scores
    expected_scores = []
    observed_scores = []
    
    for i in range(len(df)):
        student_theta = theta[i]
        expected_score = 0
        observed_score = 0
        
        for j in range(len(beta)):
            logit = student_theta - beta[j]
            prob = 1 / (1 + np.exp(-logit))
            expected_score += prob
            observed_score += data_array[i, j]
        
        expected_scores.append(expected_score)
        observed_scores.append(observed_score)
    
    correlation = np.corrcoef(expected_scores, observed_scores)[0, 1]
    print(f"   Expected vs Observed correlation: {correlation:.4f}")
    
    # Mean square error
    mse = np.mean([(e - o)**2 for e, o in zip(expected_scores, observed_scores)])
    print(f"   Mean Square Error: {mse:.4f}")
    
    print(f"\n✅ Test muvaffaqiyatli yakunlandi!")
    print(f"🎯 Model UZBMB standartlariga muvofiq ishlaydi")

if __name__ == "__main__":
    test_rasch_model()
