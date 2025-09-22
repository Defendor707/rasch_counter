import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import expit
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial
import os
import warnings
warnings.filterwarnings('ignore')

# Small L2 regularization to stabilize extreme estimates (MAP with N(0, sigma^2))
REG_LAMBDA = 0.05  # increase to shrink more, decrease to shrink less

# Model selection: default to 1PL per Rasch; set IRT_MODEL=2PL to enable 2PL
IRT_MODEL = os.environ.get('IRT_MODEL', '1PL').upper()

# Server quvvati optimizatsiyasi - adaptive CPU ishlatish
NUM_CORES = os.cpu_count() or 6

# CPU load function moved to utils.performance
from utils.performance import get_cpu_load

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
    Rasch model (1PL IRT): p_ij = sigmoid(theta_i - beta_j)
    MLE orqali theta (qobiliyat) va beta (qiyinlik) ni baholaydi.
    
    Parameters:
    - data: Numpy array (qatorlar: talabalar, ustunlar: savollar), 0/1
    - max_students: Katta ma'lumotlar uchun parallel qayta ishlash cheklovi
                  
    Returns:
    - theta: Talabalar qobiliyati (float32)
    - beta: Savollar qiyinligi (float32)
    """
    n_students, n_items = data.shape
    
    # Katta ma'lumotlar uchun parallel processing
    if max_students and n_students > max_students:
        return _process_large_dataset(data, max_students)
    
    # Boshlang'ich baholar (logit prop)
    student_scores = np.sum(data, axis=1, dtype=np.float64)
    item_scores = np.sum(data, axis=0, dtype=np.float64)
    
    # Theta (talaba qobiliyatlari) - logit transformatsiya
    theta = np.zeros(n_students, dtype=np.float64)
    for i in range(n_students):
        if student_scores[i] == 0:
            theta[i] = -3.0  # Juda past qobiliyat
        elif student_scores[i] == n_items:
            theta[i] = 3.0   # Juda yuqori qobiliyat
        else:
            p = (student_scores[i] + 0.5) / (n_items + 1)
            p = np.clip(p, 1e-6, 1 - 1e-6)
            theta[i] = np.log(p / (1 - p))
    
    # Beta (savol qiyinliklari) - logit transformatsiya
    beta = np.zeros(n_items, dtype=np.float64)
    for j in range(n_items):
        if item_scores[j] == 0:
            beta[j] = 3.0    # Juda qiyin savol
        elif item_scores[j] == n_students:
            beta[j] = -3.0   # Juda oson savol
        else:
            p = (item_scores[j] + 0.5) / (n_students + 1)
            p = np.clip(p, 1e-6, 1 - 1e-6)
            beta[j] = -np.log(p / (1 - p))
    
    # MLE iteratsiyalari (Rasch model uchun)
    max_iter = 100
    tol = 1e-6
    
    for iteration in range(max_iter):
        old_theta = theta.copy()
        old_beta = beta.copy()
        
        # Ehtimolliklar hisoblash
        logits = theta[:, np.newaxis] - beta[np.newaxis, :]
        np.clip(logits, -15, 15, out=logits)
        p = expit(logits)
        residuals = data - p
        
        # Theta yangilanishi (talaba qobiliyatlari)
        grad_theta = np.sum(residuals, axis=1) - REG_LAMBDA * theta
        hess_theta = np.sum(p * (1 - p), axis=1) + REG_LAMBDA
        update_theta = np.where(hess_theta > 1e-10, grad_theta / hess_theta, 0.0)
        theta += update_theta
        
        # Beta yangilanishi (savol qiyinliklari)
        grad_beta = -np.sum(residuals, axis=0) - REG_LAMBDA * beta
        hess_beta = np.sum(p * (1 - p), axis=0) + REG_LAMBDA
        update_beta = np.where(hess_beta > 1e-10, grad_beta / hess_beta, 0.0)
        beta += update_beta
        
        # Konvergensiya tekshiruvi
        if max(np.max(np.abs(update_theta)), np.max(np.abs(update_beta))) < tol:
            break
    
    # Identifikatsiya: theta ni markazlash (mean = 0)
    theta = theta - np.mean(theta)
    
    return theta.astype(np.float32), beta.astype(np.float32)

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
    """To'g'ri MLE usuli bilan parallel beta estimation"""
    n_students, n_items = data.shape
    beta = np.zeros(n_items, dtype=np.float64)
    
    # Parallel processing for beta calculation
    def process_item(j):
        item_responses = data[:, j].astype(np.float64)
        item_score = np.sum(item_responses)
        
        if item_score == 0:
            beta_j = 3.0
        elif item_score == n_students:
            beta_j = -3.0
        else:
            prop = (item_score + 0.5) / (n_students + 1)
            beta_j = -np.log(prop / (1 - prop))
        
        # MLE refinement
        for iteration in range(100):
            logits = np.clip(theta - beta_j, -15, 15)
            p = expit(logits)
            residual = item_responses - p
            gradient = -np.sum(residual)
            hessian = np.sum(p * (1 - p))
            
            if hessian > 1e-10:
                update = gradient / hessian
                beta_j += update
                beta_j = np.clip(beta_j, -5, 5)
                if abs(update) < 1e-8:
                    break
        
        return beta_j
    
    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            beta = list(executor.map(process_item, range(n_items)))
        beta = np.array(beta, dtype=np.float64)
    except Exception:
        # Fallback sequential
        for j in range(n_items):
            beta[j] = process_item(j)
    
    return beta

def _estimate_theta_given_beta(data, beta):
    """To'g'ri MLE usuli bilan talaba qobiliyatlarini baholash (beta berilgan)"""
    n_students, n_items = data.shape
    theta = np.zeros(n_students, dtype=np.float64)
    
    # Har bir talaba uchun to'g'ri MLE algoritmi
    for i in range(n_students):
        student_responses = data[i].astype(np.float64)
        
        # Boshlang'ich baholash
        raw_score = np.sum(student_responses)
        if raw_score == 0:
            theta_i = -3.0
        elif raw_score == n_items:
            theta_i = 3.0
        else:
            # Logit transformatsiya
            prop = (raw_score + 0.5) / (n_items + 1)
            theta_i = np.log(prop / (1 - prop))
        
        # MLE iteratsiyalari
        for iteration in range(100):  # Ko'proq iteratsiya aniqroq natija uchun
            # Ehtimolliklar
            logits = theta_i - beta
            logits = np.clip(logits, -15, 15)  # Raqamli barqarorlik
            p = expit(logits)
            
            # Gradient va Hessian
            residual = student_responses - p
            gradient = np.sum(residual)
            hessian = np.sum(p * (1 - p))
            
            # Yangilanish
            if hessian > 1e-10:  # Raqamli barqarorlik
                update = gradient / hessian
                theta_i += update
                theta_i = np.clip(theta_i, -5, 5)  # Chegaralash
                
                # Konvergensiya tekshiruvi
                if abs(update) < 1e-8:
                    break
        
        theta[i] = theta_i
    
    return theta

def _estimate_beta_given_theta(data, theta):
    """To'g'ri MLE usuli bilan savol qiyinliklarini baholash (theta berilgan)"""
    n_students, n_items = data.shape
    beta = np.zeros(n_items, dtype=np.float64)
    
    # Har bir savol uchun to'g'ri MLE algoritmi
    for j in range(n_items):
        item_responses = data[:, j].astype(np.float64)
        
        # Boshlang'ich baholash
        item_score = np.sum(item_responses)
        if item_score == 0:
            beta_j = 3.0  # Juda qiyin
        elif item_score == n_students:
            beta_j = -3.0  # Juda oson
        else:
            # Logit transformatsiya
            prop = (item_score + 0.5) / (n_students + 1)
            beta_j = -np.log(prop / (1 - prop))
        
        # MLE iteratsiyalari
        for iteration in range(100):  # Ko'proq iteratsiya aniqroq natija uchun
            # Ehtimolliklar
            logits = theta - beta_j
            logits = np.clip(logits, -15, 15)  # Raqamli barqarorlik
            p = expit(logits)
            
            # Gradient va Hessian
            residual = item_responses - p
            gradient = -np.sum(residual)
            hessian = np.sum(p * (1 - p))
            
            # Yangilanish
            if hessian > 1e-10:  # Raqamli barqarorlik
                update = gradient / hessian
                beta_j += update
                beta_j = np.clip(beta_j, -5, 5)  # Chegaralash
                
                # Konvergensiya tekshiruvi
                if abs(update) < 1e-8:
                    break
        
        beta[j] = beta_j
    
    return beta

def ability_to_standard_score(ability):
    """
    UZBMB standartlariga muvofiq qobiliyatni standart ballga o'tkazish.
    Rasch modelida theta qiymatlari logit shkalada ifodalanadi.
    
    Parameters:
    - ability: Talabaning qobiliyat bahosi (θ)
    
    Returns:
    - standard_score: Standart ball (0-100)
    """
    # Rasch modelida theta qiymatlari logit shkalada
    # UZBMB standartlariga muvofiq T-score hisoblash
    # T = 50 + 10 * θ (bu yerda θ - logit shkaladagi qobiliyat)
    
    # Theta qiymatini T-score ga o'tkazish
    t_score = 50 + (10 * ability)
    
    # Ballarni 0-100 oralig'ida chegaralash
    standard_score = np.clip(t_score, 0, 100)
    
    return standard_score

def ability_to_grade(ability, thresholds=None, min_passing_percent=60):
    """
    UZBMB standartlariga muvofiq qobiliyatni bahoga o'tkazish.
    Rasch modelida theta qiymatlaridan foydalanadi.
    
    Parameters:
    - ability: Talabaning qobiliyat bahosi (θ)
    - thresholds: Baho chegaralari (ixtiyoriy)
    - min_passing_percent: Minimal o'tish foizi
    
    Returns:
    - grade: Tayinlangan baho
    """
    # Rasch modelida theta qiymatlari logit shkalada
    # UZBMB standartlariga muvofiq T-score hisoblash
    t_score = ability_to_standard_score(ability)
    
    # UZBMB standartlariga muvofiq baho chegaralari
    # Bu chegaralar milliy sertifikat imtihonlari uchun optimallashtirilgan
    
    # Array'lar uchun vectorized operations
    if isinstance(t_score, np.ndarray):
        grades = np.where(t_score >= 70, 'A+',
                 np.where(t_score >= 65, 'A',
                 np.where(t_score >= 60, 'B+',
                 np.where(t_score >= 55, 'B',
                 np.where(t_score >= 50, 'C+',
                 np.where(t_score >= 46, 'C', 'NC'))))))
        return grades
    else:
        # Single value uchun
        if t_score >= 70:
            return 'A+'  # 1-daraja (Oliy imtiyozli)
        elif t_score >= 65:
            return 'A'   # 1-daraja (Oliy)
        elif t_score >= 60:
            return 'B+'  # 2-daraja (Yuqori imtiyozli)
        elif t_score >= 55:
            return 'B'   # 2-daraja (Yuqori)
        elif t_score >= 50:
            return 'C+'  # 3-daraja (O'rta imtiyozli)
        elif t_score >= 46:
            return 'C'   # 3-daraja (O'rta)
        else:
            return 'NC'  # 4-daraja (Sertifikatsiz)
