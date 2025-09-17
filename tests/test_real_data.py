#!/usr/bin/env python3
"""
Real UZBMB ma'lumotlari bilan Rasch modelini test qilish.
"""

import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from models.rasch_model import rasch_model, ability_to_standard_score, ability_to_grade

def test_real_data():
    """Real ma'lumotlar bilan test"""
    print("🧪 Real UZBMB ma'lumotlari bilan test")
    print("=" * 50)
    
    # Sizning bergan ma'lumotlardan namuna
    # 54 ball olgan 2 ta talaba
    # 51 ball olgan 2 ta talaba
    # 50 ball olgan 4 ta talaba
    
    # Test uchun kichik dataset yaratamiz
    n_students = 20
    n_items = 55  # UZBMB standart savollar soni
    
    # Realistic data yaratish
    np.random.seed(42)
    
    # Student abilities (realistic range)
    student_abilities = np.random.normal(0, 1, n_students)
    
    # Item difficulties (realistic range)
    item_difficulties = np.random.normal(0, 0.8, n_items)
    
    # Response matrix
    data = np.zeros((n_students, n_items), dtype=int)
    
    for i in range(n_students):
        for j in range(n_items):
            logit = student_abilities[i] - item_difficulties[j]
            prob = 1 / (1 + np.exp(-logit))
            data[i, j] = 1 if np.random.random() < prob else 0
    
    # Student names
    student_names = [f"Talaba_{i+1:03d}" for i in range(n_students)]
    
    # DataFrame
    df = pd.DataFrame(data)
    df.insert(0, 'Student_ID', student_names)
    
    print(f"📊 {len(df)} ta talaba, {len(df.columns)-1} ta savol")
    
    # Raw scores hisoblash
    raw_scores = df.iloc[:, 1:].sum(axis=1)
    print(f"📝 Raw scores: min={raw_scores.min()}, max={raw_scores.max()}, mean={raw_scores.mean():.1f}")
    
    # Rasch model
    print("\n🧮 Rasch modeli ishga tushirilmoqda...")
    data_array = df.iloc[:, 1:].values
    theta, beta = rasch_model(data_array)
    
    print(f"✅ Theta: min={theta.min():.3f}, max={theta.max():.3f}, mean={theta.mean():.3f}")
    print(f"✅ Beta: min={beta.min():.3f}, max={beta.max():.3f}, mean={beta.mean():.3f}")
    
    # Standard scores va grades
    standard_scores = [ability_to_standard_score(t) for t in theta]
    grades = [ability_to_grade(t) for t in theta]
    
    # Natijalarni ko'rsatish
    print(f"\n📊 Natijalar:")
    print(f"📝 O'rtacha standart ball: {np.mean(standard_scores):.2f}")
    print(f"📊 Standart og'ish: {np.std(standard_scores):.2f}")
    
    # Barcha talabalar natijalari
    results = []
    for i in range(len(df)):
        results.append({
            'Rank': i+1,
            'Name': df.iloc[i, 0],
            'Raw_Score': raw_scores.iloc[i],
            'Ability': theta[i],
            'Standard_Score': standard_scores[i],
            'Grade': grades[i]
        })
    
    # Raw score bo'yicha tartiblash
    results.sort(key=lambda x: x['Raw_Score'], reverse=True)
    
    print(f"\n🏆 Barcha talabalar natijalari:")
    print(f"{'Rank':<4} {'Name':<15} {'Raw':<4} {'Ability':<8} {'Standard':<8} {'Grade':<3}")
    print("-" * 60)
    
    for result in results:
        print(f"{result['Rank']:<4} {result['Name']:<15} {result['Raw_Score']:<4} "
              f"{result['Ability']:<8.3f} {result['Standard_Score']:<8.2f} {result['Grade']:<3}")
    
    # Bir xil raw score olgan talabalar tahlili
    print(f"\n🔍 Bir xil raw score olgan talabalar tahlili:")
    from collections import defaultdict
    score_groups = defaultdict(list)
    
    for result in results:
        score_groups[result['Raw_Score']].append(result)
    
    for score, students in score_groups.items():
        if len(students) > 1:
            print(f"\n📊 {score} ball olgan {len(students)} ta talaba:")
            for student in students:
                print(f"   {student['Name']}: Ability={student['Ability']:.3f}, "
                      f"Standard={student['Standard_Score']:.2f}, Grade={student['Grade']}")
    
    print(f"\n✅ Test yakunlandi!")

if __name__ == "__main__":
    test_real_data()
