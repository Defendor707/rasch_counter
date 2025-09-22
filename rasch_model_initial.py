import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import expit
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial
import os
import warnings
warnings.filterwarnings('ignore')

# Server quvvati optimizatsiyasi - adaptive CPU ishlatish
NUM_CORES = os.cpu_count() or 6

def get_cpu_load():
    try:
        with open('/proc/loadavg', 'r') as f:
            load = float(f.read().split()[0])
        return load
    except:
        return 0.0

# Adaptive worker count based on current load
current_load = get_cpu_load()
if current_load > NUM_CORES * 1.2:  # Load juda yuqori
    MAX_WORKERS = max(2, int(NUM_CORES * 0.5))  # 50% ishlatish
elif current_load > NUM_CORES * 0.8:
    MAX_WORKERS = max(3, int(NUM_CORES * 0.6))  # 60% ishlatish
else:
    MAX_WORKERS = min(int(NUM_CORES * 0.8), 4)  # 80% ishlatish

# Numpy/BLAS sozlamalari
os.environ['OMP_NUM_THREADS'] = str(MAX_WORKERS)
os.environ['MKL_NUM_THREADS'] = str(MAX_WORKERS)
os.environ['OPENBLAS_NUM_THREADS'] = str(MAX_WORKERS)
os.environ['VECLIB_MAXIMUM_THREADS'] = str(MAX_WORKERS)
os.environ['NUMEXPR_NUM_THREADS'] = str(MAX_WORKERS)

def rasch_model(data, max_students=None):
    """
    Tezlashtirilgan va aniq Rasch modeli implementatsiyasi.
    
    Parameters:
    - data: Numpy array (qatorlar: talabalar, ustunlar: savollar)
    - max_students: Maksimal talabalar soni (katta ma'lumotlar uchun)
                  
    Returns:
    - theta: Talabalar qobiliyati baholari
    - beta: Savollar qiyinligi baholari
    """
    n_students, n_items = data.shape
    
    # Katta ma'lumotlar uchun tezkor usul
    if max_students and n_students > max_students:
        return _process_large_dataset(data, max_students)
    
    # Tezkor boshlang'ich baholar
    student_scores = np.sum(data, axis=1, dtype=np.float32)
    item_scores = np.sum(data, axis=0, dtype=np.float32)
    
    # Ekstremal qiymatlarni oldini olish
    epsilon = 0.01
    
    # Boshlang'ich qobiliyat baholari (tezkor formula)
    student_props = np.clip((student_scores + epsilon) / (n_items + 2*epsilon), epsilon, 1-epsilon)
    initial_theta = np.log(student_props / (1 - student_props))
    
    # Boshlang'ich qiyinlik baholari (tezkor formula)
    item_props = np.clip((item_scores + epsilon) / (n_students + 2*epsilon), epsilon, 1-epsilon)
    initial_beta = -np.log(item_props / (1 - item_props))
    
    # Ekstremal holatlarni tekshirish
    extreme_students = (student_scores <= 0.5) | (student_scores >= n_items - 0.5)
    extreme_items = (item_scores <= 0.5) | (item_scores >= n_students - 0.5)
    
    # Tezkor algoritm uchun yaxshi ma'lumotlarni saralash
    valid_students = ~extreme_students
    valid_items = ~extreme_items
    
    # Agar barcha ma'lumotlar ekstremal bo'lsa, oddiy baholarni qaytarish
    if not np.any(valid_students) or not np.any(valid_items):
        return initial_theta, initial_beta
    
    # Saralangan ma'lumotlar
    filtered_data = data[np.ix_(valid_students, valid_items)].astype(np.float32)
    
    # Tezlashtirilgan Newton-Raphson usuli
    def fast_estimate_theta_beta(data, max_iter=50):
        """Tezkor va aniq Newton-Raphson algoritmi"""
        n_students, n_items = data.shape
        
        # Boshlang'ich baholar
        theta = np.random.normal(0, 0.5, n_students).astype(np.float32)
        beta = np.random.normal(0, 0.5, n_items).astype(np.float32)
        
        for iteration in range(max_iter):
            # Ehtimolliklarni hisoblash (tezlashtirilgan)
            theta_expanded = theta[:, np.newaxis]  # (n_students, 1)
            beta_expanded = beta[np.newaxis, :]    # (1, n_items)
            
            # Logit farqlarini hisoblash
            logits = theta_expanded - beta_expanded
            logits = np.clip(logits, -20, 20)  # Raqamli barqarorlik
            
            # Sigmoid funksiya (expit tezroq)
            p = expit(logits)
            
            # Gradientlar va Hessianlar
            residuals = data - p
            
            # Theta uchun yangilanish
            theta_grad = np.sum(residuals, axis=1)
            theta_hess = np.sum(p * (1 - p), axis=1) + 0.1  # regularizatsiya
            theta_update = theta_grad / theta_hess
            theta += 0.5 * theta_update  # adaptiv qadam
            
            # Beta uchun yangilanish
            beta_grad = -np.sum(residuals, axis=0)
            beta_hess = np.sum(p * (1 - p), axis=0) + 0.1  # regularizatsiya
            beta_update = beta_grad / beta_hess
            beta += 0.5 * beta_update  # adaptiv qadam
            
            # Konvergensiya tekshiruvi
            if np.max(np.abs(theta_update)) < 0.001 and np.max(np.abs(beta_update)) < 0.001:
                break
        
        return theta, beta
    
    # Tezkor baholash
    optimized_theta_valid, optimized_beta_valid = fast_estimate_theta_beta(filtered_data)
    
    # To'liq massivlarni yaratish
    theta = np.zeros(n_students, dtype=np.float32)
    beta = np.zeros(n_items, dtype=np.float32)
    
    # Haqiqiy baholarni to'ldirish
    theta[valid_students] = optimized_theta_valid
    beta[valid_items] = optimized_beta_valid
    
    # Handle extreme cases
    # For extreme students, use the maximum/minimum valid values without adding/subtracting
    if np.any(extreme_students):
        if np.any(student_scores == n_items):  # Perfect scores
            max_valid_theta = np.max(theta[valid_students]) if np.any(valid_students) else 0
            theta[student_scores == n_items] = max_valid_theta  # Eng yuqori qiymat
            
        if np.any(student_scores == 0):  # Zero scores
            min_valid_theta = np.min(theta[valid_students]) if np.any(valid_students) else 0
            theta[student_scores == 0] = min_valid_theta  # Eng past qiymat
    
    # For extreme items, use the maximum/minimum valid values without adding/subtracting
    if np.any(extreme_items):
        if np.any(item_scores == n_students):  # All correct
            min_valid_beta = np.min(beta[valid_items]) if np.any(valid_items) else 0
            beta[item_scores == n_students] = min_valid_beta  # Eng past qiyinlik
            
        if np.any(item_scores == 0):  # All wrong
            max_valid_beta = np.max(beta[valid_items]) if np.any(valid_items) else 0
            beta[item_scores == 0] = max_valid_beta  # Eng yuqori qiyinlik
    
    # Center abilities to have mean 0
    theta = theta - np.mean(theta)
    
    return theta, beta

def _process_chunk_parallel(args):
    """Parallel chunk processing uchun worker funksiya"""
    chunk_data, beta = args
    return _estimate_theta_given_beta(chunk_data, beta)

def _process_large_dataset(data, max_students=2000):
    """
    Parallel processing bilan katta ma'lumotlarni qayta ishlash.
    Server quvvatining 80% ishlatadi.
    
    Parameters:
    - data: To'liq ma'lumotlar
    - max_students: Chunk hajmi
    
    Returns:
    - theta, beta: Birlashtirilgan natijalar
    """
    n_students, n_items = data.shape
    
    # Optimal chunk size
    optimal_chunk_size = min(max_students, max(n_students // MAX_WORKERS, 500))
    n_chunks = int(np.ceil(n_students / optimal_chunk_size))
    
    # Initial beta estimate
    sample_size = min(1000, n_students)
    sample_indices = np.random.choice(n_students, sample_size, replace=False)
    sample_data = data[sample_indices]
    _, initial_beta = rasch_model(sample_data)
    
    # Prepare chunks for parallel processing
    chunks = []
    chunk_indices = []
    for i in range(n_chunks):
        start_idx = i * optimal_chunk_size
        end_idx = min(start_idx + optimal_chunk_size, n_students)
        chunk_data = data[start_idx:end_idx]
        chunks.append((chunk_data, initial_beta))
        chunk_indices.append((start_idx, end_idx))
    
    # Parallel processing
    all_theta = np.zeros(n_students, dtype=np.float32)
    
    try:
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            chunk_results = list(executor.map(_process_chunk_parallel, chunks))
        
        # Combine results
        for i, (chunk_theta, (start_idx, end_idx)) in enumerate(zip(chunk_results, chunk_indices)):
            all_theta[start_idx:end_idx] = chunk_theta
            
    except Exception:
        # Fallback to sequential processing
        for i, ((chunk_data, beta), (start_idx, end_idx)) in enumerate(zip(chunks, chunk_indices)):
            chunk_theta = _estimate_theta_given_beta(chunk_data, beta)
            all_theta[start_idx:end_idx] = chunk_theta
    
    # Refine beta with parallel processing
    final_beta = _estimate_beta_given_theta_parallel(data, all_theta)
    
    # Center abilities
    all_theta = all_theta - np.mean(all_theta)
    
    return all_theta, final_beta

def _estimate_beta_given_theta_parallel(data, theta):
    """Parallel beta estimation"""
    n_students, n_items = data.shape
    beta = np.zeros(n_items, dtype=np.float32)
    
    # Parallel processing for beta calculation
    def process_item(j):
        item_responses = data[:, j].astype(np.float32)
        item_score = np.sum(item_responses)
        
        if item_score == 0:
            return 3.0
        elif item_score == n_students:
            return -3.0
        else:
            prop = (item_score + 0.5) / (n_students + 1)
            beta_j = -np.log(prop / (1 - prop))
        
        # Newton-Raphson refinement
        for _ in range(8):
            logits = np.clip(theta - beta_j, -15, 15)
            p = expit(logits)
            residual = item_responses - p
            gradient = -np.sum(residual)
            hessian = np.sum(p * (1 - p)) + 0.01
            
            if hessian > 0:
                update = gradient / hessian
                beta_j += 0.8 * update
                if abs(update) < 0.005:
                    break
        
        return beta_j
    
    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            beta = list(executor.map(process_item, range(n_items)))
        beta = np.array(beta, dtype=np.float32)
    except Exception:
        # Fallback sequential
        for j in range(n_items):
            beta[j] = process_item(j)
    
    return beta

def _estimate_theta_given_beta(data, beta):
    """Tezkor talaba qobiliyatlarini baholash (beta berilgan)"""
    n_students, n_items = data.shape
    theta = np.zeros(n_students, dtype=np.float32)
    
    # Har bir talaba uchun tezkor Newton-Raphson
    for i in range(n_students):
        student_responses = data[i].astype(np.float32)
        
        # Boshlang'ich baholash (student score asosida)
        raw_score = np.sum(student_responses)
        if raw_score == 0:
            theta_i = -3.0
        elif raw_score == n_items:
            theta_i = 3.0
        else:
            # Logit transformatsiya
            prop = (raw_score + 0.5) / (n_items + 1)
            theta_i = np.log(prop / (1 - prop))
        
        # Newton-Raphson iteratsiyalari (tezkor)
        for _ in range(10):  # Kamroq iteratsiya, tezlik uchun
            # Ehtimolliklar
            logits = theta_i - beta
            logits = np.clip(logits, -15, 15)  # Kichikroq chegaralar
            p = expit(logits)
            
            # Gradient va Hessian
            residual = student_responses - p
            gradient = np.sum(residual)
            hessian = np.sum(p * (1 - p)) + 0.01  # kichik regularizatsiya
            
            # Yangilanish
            if hessian > 0:
                update = gradient / hessian
                theta_i += 0.7 * update  # kichik qadam
                
                # Konvergensiya tekshiruvi
                if abs(update) < 0.01:
                    break
        
        theta[i] = theta_i
    
    return theta

def _estimate_beta_given_theta(data, theta):
    """Tezkor savol qiyinliklarini baholash (theta berilgan)"""
    n_students, n_items = data.shape
    beta = np.zeros(n_items, dtype=np.float32)
    
    # Har bir savol uchun tezkor Newton-Raphson
    for j in range(n_items):
        item_responses = data[:, j].astype(np.float32)
        
        # Boshlang'ich baholash (item score asosida)
        item_score = np.sum(item_responses)
        if item_score == 0:
            beta_j = 3.0  # Juda qiyin
        elif item_score == n_students:
            beta_j = -3.0  # Juda oson
        else:
            # Logit transformatsiya
            prop = (item_score + 0.5) / (n_students + 1)
            beta_j = -np.log(prop / (1 - prop))  # Minus chunki yuqori prop = past qiyinlik
        
        # Newton-Raphson iteratsiyalari (tezkor)
        for _ in range(10):  # Kamroq iteratsiya
            # Ehtimolliklar
            logits = theta - beta_j
            logits = np.clip(logits, -15, 15)
            p = expit(logits)
            
            # Gradient va Hessian
            residual = item_responses - p
            gradient = -np.sum(residual)  # Minus chunki beta uchun
            hessian = np.sum(p * (1 - p)) + 0.01
            
            # Yangilanish
            if hessian > 0:
                update = gradient / hessian
                beta_j += 0.7 * update
                
                # Konvergensiya
                if abs(update) < 0.01:
                    break
        
        beta[j] = beta_j
    
    return beta

def ability_to_standard_score(ability):
    """
    Convert ability estimate to standard score using the formula: T = 50 + 10Z
    Where Z = (θ - μ)/σ
    
    Parameters:
    - ability: The student's ability estimate (θ)
    
    Returns:
    - standard_score: Standardized score (T)
    """
    # Calculate Z-score: (ability - mean) / std_dev
    # Since the theta values are centered around 0 (mean=0),
    # we can simplify Z = ability / std_dev
    # Assuming std_dev = 1 for Rasch standardization
    z_score = ability  # This is already a standardized value in Rasch model
    
    # Apply the formula T = 50 + 10Z
    standard_score = 50 + (10 * z_score)
    
    # Ensure the score is in a reasonable range (0-100)
    return max(0, min(100, standard_score))

def ability_to_grade(ability, thresholds=None, min_passing_percent=60):
    """
    Aniq va optimallashtirilgan BBM standartlariga ko'ra baholarni tayinlash.
    
    Parameters:
    - ability: Talabaning qobiliyat bahosi
    - thresholds: Baho chegaralari (ixtiyoriy)
    - min_passing_percent: Minimal o'tish foizi
    
    Returns:
    - grade: Tayinlangan baho
    """
    # Qobiliyatni normal taqsimotga o'tkazish (aniqroq)
    # Rasch model logit scale: -4 dan +4 gacha
    # Uni 0-100 gacha o'zgartirish
    
    # Sigma = 1.5 (kengaytirilgan taqsimot)
    # Mu = 0 (markazlashtirilgan)
    normalized_ability = (ability + 4) / 8 * 100
    normalized_ability = np.clip(normalized_ability, 0, 100)
    
    # BBM standartlariga muvofiq aniq chegaralar
    # Real test natijalariga asoslangan optimallashtirilgan taqsimot
    
    # Top 8-12% - A+ (eng yaxshi natija)
    if normalized_ability >= 88:
        return 'A+'
    # Next 12-15% - A (a'lo natija)  
    elif normalized_ability >= 78:
        return 'A'
    # Next 15-18% - B+ (yaxshi natija)
    elif normalized_ability >= 68:
        return 'B+'
    # Next 18-20% - B (qoniqarli natija)
    elif normalized_ability >= 58:
        return 'B'
    # Next 15-18% - C+ (yetarli natija)
    elif normalized_ability >= 48:
        return 'C+'
    # Next 12-15% - C (minimal qoniqarli)
    elif normalized_ability >= 40:
        return 'C'
    # Bottom 15-20% - NC (nomaqbul)
    else:
        return 'NC'
