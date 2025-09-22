"""
Production server uchun maxsus optimizatsiya va xatolarni hal qilish
"""
import os
import logging
import numpy as np
import psutil
from typing import Tuple, Optional
from functools import wraps

logger = logging.getLogger(__name__)

def detect_environment() -> str:
    """
    Muhitni aniqlash (test/production)
    """
    # Production server belgilari
    if os.path.exists('/proc/loadavg'):
        try:
            with open('/proc/loadavg', 'r') as f:
                load = float(f.read().split()[0])
            cpu_count = os.cpu_count() or 4
            
            # Agar load yuqori bo'lsa, production deb hisoblaymiz
            if load > cpu_count * 0.5:
                return 'production'
        except:
            pass
    
    # Environment variable orqali
    env = os.environ.get('ENVIRONMENT', 'test').lower()
    return env

def get_optimal_workers() -> int:
    """
    Muhitga qarab optimal worker sonini aniqlash
    """
    env = detect_environment()
    cpu_count = os.cpu_count() or 4
    
    if env == 'production':
        # Production: konservativ yondashuv
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        if memory_gb < 2:
            return 1  # Juda kam xotira
        elif memory_gb < 4:
            return 2  # Kam xotira
        elif memory_gb < 8:
            return min(3, cpu_count // 2)  # O'rta xotira
        else:
            return min(4, cpu_count // 2)  # Ko'p xotira
    else:
        # Test: aggressive yondashuv
        return min(int(cpu_count * 0.8), 4)

def get_optimal_chunk_size(n_students: int) -> int:
    """
    Talabalar soniga qarab optimal chunk size
    """
    env = detect_environment()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    if env == 'production':
        # Production: kichik chunk size
        if memory_gb < 2:
            return min(500, n_students // 4)
        elif memory_gb < 4:
            return min(1000, n_students // 3)
        else:
            return min(1500, n_students // 2)
    else:
        # Test: katta chunk size
        return min(2000, n_students)

def safe_rasch_calculation(data: np.ndarray, max_students: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Xavfsiz Rasch model hisoblash - production uchun optimallashtirilgan
    """
    try:
        n_students, n_items = data.shape
        
        # Kichik ma'lumotlar uchun oddiy usul
        if n_students <= 500:
            return _simple_rasch(data)
        
        # Katta ma'lumotlar uchun chunked usul
        optimal_chunk = get_optimal_chunk_size(n_students)
        return _chunked_rasch(data, optimal_chunk)
        
    except Exception as e:
        logger.error(f"Rasch calculation error: {str(e)}")
        # Fallback: oddiy usul
        return _simple_rasch(data)

def _simple_rasch(data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Yaxshilangan Rasch model (kichik ma'lumotlar uchun)
    """
    n_students, n_items = data.shape
    
    # Boshlang'ich baholar
    student_scores = np.sum(data, axis=1, dtype=np.float64)
    item_scores = np.sum(data, axis=0, dtype=np.float64)
    
    # Theta (talaba qobiliyatlari) - yaxshilangan initialization
    theta = np.zeros(n_students, dtype=np.float64)
    for i in range(n_students):
        if student_scores[i] == 0:
            theta[i] = -3.0
        elif student_scores[i] == n_items:
            theta[i] = 3.0
        else:
            p = (student_scores[i] + 0.5) / (n_items + 1)
            p = np.clip(p, 1e-6, 1 - 1e-6)
            theta[i] = np.log(p / (1 - p))
    
    # Beta (savol qiyinliklari) - yaxshilangan initialization
    beta = np.zeros(n_items, dtype=np.float64)
    for j in range(n_items):
        if item_scores[j] == 0:
            beta[j] = 3.0
        elif item_scores[j] == n_students:
            beta[j] = -3.0
        else:
            p = (item_scores[j] + 0.5) / (n_students + 1)
            p = np.clip(p, 1e-6, 1 - 1e-6)
            beta[j] = -np.log(p / (1 - p))
    
    # Yaxshilangan MLE iteratsiyalari
    max_iter = 100  # Ko'proq iteratsiya aniqroq natija uchun
    tol = 1e-8      # Kichikroq tolerance aniqroq natija uchun
    reg_lambda = 0.01  # Reduced regularization for better differentiation
    
    for iteration in range(max_iter):
        old_theta = theta.copy()
        old_beta = beta.copy()
        
        # Ehtimolliklar hisoblash
        logits = theta[:, np.newaxis] - beta[np.newaxis, :]
        np.clip(logits, -15, 15, out=logits)  # Kattaroq range raqamli barqarorlik uchun
        p = 1 / (1 + np.exp(-logits))
        residuals = data - p
        
        # Theta yangilanishi (regularization bilan)
        grad_theta = np.sum(residuals, axis=1) - reg_lambda * theta
        hess_theta = np.sum(p * (1 - p), axis=1) + reg_lambda
        update_theta = np.where(hess_theta > 1e-10, grad_theta / hess_theta, 0.0)
        theta += update_theta
        theta = np.clip(theta, -10, 10)  # Chegaralash
        
        # Beta yangilanishi (regularization bilan)
        grad_beta = -np.sum(residuals, axis=0) - reg_lambda * beta
        hess_beta = np.sum(p * (1 - p), axis=0) + reg_lambda
        update_beta = np.where(hess_beta > 1e-10, grad_beta / hess_beta, 0.0)
        beta += update_beta
        beta = np.clip(beta, -10, 10)  # Chegaralash
        
        # Konvergensiya tekshiruvi
        theta_change = np.max(np.abs(theta - old_theta))
        beta_change = np.max(np.abs(beta - old_beta))
        max_change = max(theta_change, beta_change)
        
        if max_change < tol:
            logger.info(f"Simple Rasch converged after {iteration + 1} iterations")
            break
    
    # To'g'ri identifikatsiya - faqat beta ni center qilish
    # Theta ni center qilmaslik kerak, chunki bu talabalar orasidagi farqni yo'qotadi
    beta = beta - np.mean(beta)  # Faqat beta ni center qilish
    
    return theta.astype(np.float32), beta.astype(np.float32)

def _chunked_rasch(data: np.ndarray, chunk_size: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Chunked Rasch model (katta ma'lumotlar uchun)
    """
    n_students, n_items = data.shape
    
    # Chunk soni
    n_chunks = int(np.ceil(n_students / chunk_size))
    
    # Boshlang'ich beta (sample orqali)
    sample_size = min(1000, n_students)
    sample_indices = np.random.choice(n_students, sample_size, replace=False)
    sample_data = data[sample_indices]
    _, initial_beta = _simple_rasch(sample_data)
    
    # Theta hisoblash (chunk by chunk)
    all_theta = np.zeros(n_students, dtype=np.float32)
    
    for i in range(n_chunks):
        start_idx = i * chunk_size
        end_idx = min(start_idx + chunk_size, n_students)
        chunk_data = data[start_idx:end_idx]
        
        try:
            chunk_theta, _ = _simple_rasch(chunk_data)
            all_theta[start_idx:end_idx] = chunk_theta
        except Exception as e:
            logger.warning(f"Chunk {i} failed, using fallback: {str(e)}")
            # Fallback: oddiy ball
            chunk_scores = np.sum(chunk_data, axis=1)
            chunk_theta = (chunk_scores - np.mean(chunk_scores)) / np.std(chunk_scores + 1e-6)
            all_theta[start_idx:end_idx] = chunk_theta
    
    # Beta hisoblash (to'liq ma'lumotlar bilan)
    try:
        final_beta = _estimate_beta_safe(data, all_theta)
    except Exception as e:
        logger.warning(f"Beta estimation failed, using initial: {str(e)}")
        final_beta = initial_beta
    
    return all_theta, final_beta

def _estimate_beta_safe(data: np.ndarray, theta: np.ndarray) -> np.ndarray:
    """
    Xavfsiz beta hisoblash
    """
    n_students, n_items = data.shape
    beta = np.zeros(n_items, dtype=np.float64)
    
    for j in range(n_items):
        item_responses = data[:, j].astype(np.float64)
        item_score = np.sum(item_responses)
        
        if item_score == 0:
            beta[j] = 3.0
        elif item_score == n_students:
            beta[j] = -3.0
        else:
            prop = (item_score + 0.5) / (n_students + 1)
            beta[j] = -np.log(prop / (1 - prop))
        
        # MLE refinement (kamroq iteratsiya)
        for iteration in range(20):  # Production uchun kamroq
            logits = np.clip(theta - beta[j], -10, 10)
            p = 1 / (1 + np.exp(-logits))
            residual = item_responses - p
            gradient = -np.sum(residual)
            hessian = np.sum(p * (1 - p))
            
            if hessian > 1e-8:
                update = gradient / hessian
                beta[j] += update
                beta[j] = np.clip(beta[j], -5, 5)
                if abs(update) < 1e-6:
                    break
    
    return beta.astype(np.float32)

def production_safe_processing(func):
    """
    Production uchun xavfsiz processing decorator
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Memory tekshirish
            if not check_memory_available():
                logger.warning("Low memory, using conservative processing")
                kwargs['max_students'] = 500
            
            # CPU load tekshirish
            if get_cpu_load() > os.cpu_count() * 0.8:
                logger.warning("High CPU load, reducing workers")
                kwargs['max_workers'] = 1
            
            return func(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Production processing error: {str(e)}")
            # Fallback processing
            if 'data' in kwargs:
                return _simple_rasch(kwargs['data'])
            raise
    
    return wrapper

def check_memory_available() -> bool:
    """
    Xotira mavjudligini tekshirish
    """
    try:
        memory = psutil.virtual_memory()
        return memory.available > 200 * 1024 * 1024  # 200MB
    except:
        return True

def get_cpu_load() -> float:
    """
    CPU load olish
    """
    try:
        with open('/proc/loadavg', 'r') as f:
            return float(f.read().split()[0])
    except:
        return 0.0
