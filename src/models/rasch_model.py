"""
Rasch Modeli - IRT (Item Response Theory) implementatsiyasi
Kutubxonalarsiz, to'liq Python da yozilgan
Bizning dasturdan ko'chirilgan to'liq va ishonchli versiya
"""
import math
import numpy as np

def sigmoid(x):
    """Sigmoid funksiya"""
    if x > 700:
        return 1.0
    if x < -700:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))

def rasch_probability(theta, beta):
    """
    Rasch modeli ehtimollik funksiyasi
    P(X=1|theta, beta) = sigmoid(theta - beta)
    theta: talaba qobiliyati
    beta: savol qiyinligi
    """
    return sigmoid(theta - beta)

def estimate_ability(responses, difficulties, max_iter=50, theta_min=-4.0, theta_max=4.0, threshold=0.001):
    """
    Talaba qobiliyatini baholash (MLE)
    responses: javoblar ro'yxati (0 yoki 1)
    difficulties: savol qiyinliklari
    """
    # Boshlang'ich qiymat
    theta = 0.0
    
    # To'liq to'g'ri yoki noto'g'ri javoblar uchun
    total = sum(responses)
    n = len(responses)
    
    if total == 0:
        return theta_min
    if total == n:
        return theta_max
    
    # Newton-Raphson iteratsiyasi
    for _ in range(max_iter):
        # Gradient va Hessian hisoblash
        gradient = 0.0
        hessian = 0.0
        
        for r, b in zip(responses, difficulties):
            p = rasch_probability(theta, b)
            gradient += (r - p)
            hessian -= p * (1 - p)
        
        if abs(hessian) < 1e-10:
            break
        
        # Yangilash
        delta = gradient / hessian
        theta -= delta
        
        # Chegaralash
        theta = max(theta_min, min(theta_max, theta))
        
        if abs(delta) < threshold:
            break
    
    return theta

def estimate_difficulty(responses_matrix):
    """
    Savol qiyinliklarini baholash
    responses_matrix: talabalar x savollar matritsasi
    """
    n_students = len(responses_matrix)
    n_questions = len(responses_matrix[0]) if responses_matrix else 0
    
    difficulties = []
    
    for j in range(n_questions):
        # Savolga to'g'ri javob berganlar soni
        correct = sum(responses_matrix[i][j] for i in range(n_students))
        proportion = correct / n_students if n_students > 0 else 0.5
        
        # Proportion dan qiyinlikka o'tkazish (logit)
        if proportion <= 0.01:
            proportion = 0.01
        if proportion >= 0.99:
            proportion = 0.99
        
        difficulty = -math.log(proportion / (1 - proportion))
        difficulties.append(difficulty)
    
    return difficulties

def ability_to_score(theta, difficulties, responses, max_score=100):
    """
    Qobiliyatni ballga o'tkazish (0-100) - weighted scoring
    
    Har bir savol uchun qiyinlikka qarab ball beriladi:
    - Qiyin savol to'g'ri javoblansa - ko'proq ball
    - Oson savol to'g'ri javoblansa - kamroq ball
    """
    if not difficulties or not responses:
        # Oddiy sigmoid agar qiyinliklar yo'q bo'lsa
        normalized = sigmoid(theta)
        score = normalized * max_score
        # 0-100 orasida cheklash
        score = max(0.0, min(100.0, score))
        return round(score, 1)
    
    n_questions = len(difficulties)
    
    # Savol og'irliklarini hisoblash (qiyinlikka qarab)
    # Qiyinroq savol = ko'proq og'irlik
    min_diff = min(difficulties)
    max_diff = max(difficulties)
    diff_range = max_diff - min_diff if max_diff != min_diff else 1
    
    # Og'irliklar: 1 dan 3 gacha (osondan qiyinga)
    weights = []
    for d in difficulties:
        # Normalize qiyinlik 0-1 orasiga
        norm_diff = (d - min_diff) / diff_range
        # Og'irlik: 1 (eng oson) dan 3 (eng qiyin) gacha
        weight = 1 + 2 * norm_diff
        weights.append(weight)
    
    # Weighted ball hisoblash
    total_weight = sum(weights)
    weighted_score = 0
    
    for response, weight in zip(responses, weights):
        if response == 1:  # To'g'ri javob
            weighted_score += weight
    
    # 0-100 ga o'tkazish
    score = (weighted_score / total_weight) * max_score
    
    # 0-100 orasida cheklash
    score = max(0.0, min(100.0, score))
    
    return round(score, 1)

def score_to_grade(score, grade_scales=None):
    """
    UZBMB standartlari bo'yicha baho
    """
    if grade_scales is None:
        # UZBMB standartlari
        grade_scales = {
            "A+": 70,
            "A": 65,
            "B+": 60,
            "B": 55,
            "C+": 50,
            "C": 46,
            "NC": 0
        }
    
    if score >= grade_scales["A+"]:
        return "A+"
    elif score >= grade_scales["A"]:
        return "A"
    elif score >= grade_scales["B+"]:
        return "B+"
    elif score >= grade_scales["B"]:
        return "B"
    elif score >= grade_scales["C+"]:
        return "C+"
    elif score >= grade_scales["C"]:
        return "C"
    else:
        return "NC"


# ============================================================================
# rasch_counter loyihasi uchun moslashtirilgan funksiyalar
# ============================================================================

def rasch_model(data, max_students=None):
    """
    Rasch model (1PL IRT): p_ij = sigmoid(theta_i - beta_j)
    MLE orqali theta (qobiliyat) va beta (qiyinlik) ni baholaydi.
    
    Parameters:
    - data: Numpy array (qatorlar: talabalar, ustunlar: savollar), 0/1
    - max_students: Katta ma'lumotlar uchun parallel qayta ishlash cheklovi (e'tiborsiz)
                  
    Returns:
    - theta: Talabalar qobiliyati (numpy array)
    - beta: Savollar qiyinligi (numpy array)
    """
    # Numpy array ni list ga o'tkazish
    if isinstance(data, np.ndarray):
        responses_matrix = data.tolist()
    else:
        responses_matrix = data
    
    n_students = len(responses_matrix)
    n_questions = len(responses_matrix[0]) if responses_matrix else 0
    
    # 1. Savol qiyinliklarini baholash
    difficulties = estimate_difficulty(responses_matrix)
    
    # 2. Har bir talaba uchun qobiliyatni baholash
    thetas = []
    for i in range(n_students):
        responses = responses_matrix[i]
        theta = estimate_ability(responses, difficulties)
        thetas.append(theta)
    
    # Numpy array ga o'tkazish
    theta_array = np.array(thetas, dtype=np.float32)
    beta_array = np.array(difficulties, dtype=np.float32)
    
    return theta_array, beta_array

def ability_to_standard_score(ability):
    """
    UZBMB standartlariga muvofiq qobiliyatni standart ballga o'tkazish.
    Rasch modelida theta qiymatlari logit shkalada ifodalanadi.
    
    Parameters:
    - ability: Talabaning qobiliyat bahosi (θ)
    
    Returns:
    - standard_score: Standart ball (0-100)
    """
    # Qobiliyatni ballga o'tkazish (weighted scoring)
    # Bu yerda faqat qobiliyat berilgan, shuning uchun oddiy transformatsiya
    # Real ball hisoblash uchun responses va difficulties kerak,
    # lekin u yerdagi kod faqat ability ni kutadi
    
    # Oddiy sigmoid transformatsiya
    normalized = sigmoid(ability)
    score = normalized * 100
    
    # 0-100 orasida cheklash
    score = max(0.0, min(100.0, score))
    
    return round(score, 1)

def ability_to_grade(ability, thresholds=None, min_passing_percent=60):
    """
    UZBMB standartlariga muvofiq qobiliyatni bahoga o'tkazish.
    Rasch modelida theta qiymatlaridan foydalanadi.
    
    Parameters:
    - ability: Talabaning qobiliyat bahosi (θ)
    - thresholds: Baho chegaralari (ixtiyoriy, e'tiborsiz)
    - min_passing_percent: Minimal o'tish foizi (e'tiborsiz)
    
    Returns:
    - grade: Tayinlangan baho
    """
    # Qobiliyatni ballga o'tkazish
    score = ability_to_standard_score(ability)
    
    # Bahoga o'tkazish
    grade = score_to_grade(score)
    
    return grade
