#!/usr/bin/env python3
"""
Rasch Counter Web Application
Modern web interface for Rasch model-based test analysis
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from flask import Flask, render_template, render_template_string, request, jsonify, send_file, session, redirect, url_for
from werkzeug.utils import secure_filename
import io
import threading
import time
from datetime import datetime

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from services.analysis_service import analysis_service

# Telegram bot qo'llanmasi HTML
TELEGRAM_GUIDE_HTML = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Telegram Bot Qo'llanmasi - Rasch Counter</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2rem;
            opacity: 0.9;
        }
        
        .content {
            background: white;
            border-radius: 15px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }
        
        .section {
            margin-bottom: 40px;
        }
        
        .section h2 {
            color: #667eea;
            font-size: 2rem;
            margin-bottom: 20px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .feature {
            background: #f8f9ff;
            padding: 25px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        
        .feature h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }
        
        .commands {
            background: #2d3748;
            color: white;
            padding: 25px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .commands h3 {
            color: #68d391;
            margin-bottom: 15px;
        }
        
        .command-item {
            margin: 10px 0;
            padding: 10px;
            background: #4a5568;
            border-radius: 5px;
        }
        
        .command {
            background: #667eea;
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-weight: bold;
        }
        
        .steps {
            display: grid;
            gap: 20px;
            margin: 30px 0;
        }
        
        .step {
            background: #f7fafc;
            padding: 25px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        
        .step h3 {
            color: #667eea;
            margin-bottom: 15px;
        }
        
        .example-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .example-table th,
        .example-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .example-table th {
            background: #667eea;
            color: white;
            font-weight: bold;
        }
        
        .example-table tr:hover {
            background: #f7fafc;
        }
        
        .telegram-link {
            display: inline-block;
            background: #0088cc;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            margin: 10px 0;
            transition: background 0.3s;
        }
        
        .telegram-link:hover {
            background: #006699;
        }
        
        .back-link {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 8px;
            margin: 20px 0;
            transition: background 0.3s;
        }
        
        .back-link:hover {
            background: #5a67d8;
        }
        
        .footer {
            text-align: center;
            color: white;
            margin-top: 40px;
            opacity: 0.8;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2rem;
            }
            
            .content {
                padding: 20px;
            }
            
            .features {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Telegram Bot Qo'llanmasi</h1>
            <p>Rasch Counter Botni qanday ishlatishni o'rganing</p>
        </div>
        
        <div class="content">
            <a href="/" class="back-link">← Asosiy sahifaga qaytish</a>
            
            <div class="section">
                <h2>📊 Bot haqida</h2>
                <p>Rasch Counter Bot - bu test natijalarini Rasch psychometric model orqali tahlil qilib, talabalarning bilim darajasini aniq baholashga yordam beruvchi professional bot.</p>
                
                <div class="features">
                    <div class="feature">
                        <h3>🔬 Ilmiy Tahlil</h3>
                        <p>1PL IRT (Item Response Theory) model yoki Rasch model asosida talabalarning qobiliyati va savollarning qiyinlik darajasini aniqlab beradi.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>📈 Batafsil Hisobot</h3>
                        <p>Excel va PDF formatda to'liq statistik tahlil, grafiklar va baholar taqsimoti bilan hisobot tayyorlaydi.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>⚡ Tez Ishlov</h3>
                        <p>Minglab talaba ma'lumotlarini bir necha soniyada qayta ishlab, natijalarni darhol taqdim etadi.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>🏆 UZBMB Standartlari</h3>
                        <p>O'zbekiston Bilim va Malakalarni Baholash Agentligi standartlari bo'yicha baholar taqsimlaydi.</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🚀 Qanday boshlash?</h2>
                
                <div class="steps">
                    <div class="step">
                        <h3>1. Telegram botni oching</h3>
                        <p>Quyidagi tugma orqali botni ishga tushiring va /start buyrug'ini yuboring.</p>
                        <a href="https://t.me/rasch_counter_bot" class="telegram-link">🤖 Botni ochish</a>
                    </div>
                    
                    <div class="step">
                        <h3>2. Excel faylni tayyorlang</h3>
                        <p>Test natijalarini quyidagi formatda Excel faylga kiriting:</p>
                        <table class="example-table">
                            <thead>
                                <tr>
                                    <th>Talaba ID</th>
                                    <th>Savol 1</th>
                                    <th>Savol 2</th>
                                    <th>Savol 3</th>
                                    <th>...</th>
                                    <th>Savol N</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Talaba001</td>
                                    <td>1</td>
                                    <td>0</td>
                                    <td>1</td>
                                    <td>...</td>
                                    <td>1</td>
                                </tr>
                                <tr>
                                    <td>Talaba002</td>
                                    <td>0</td>
                                    <td>1</td>
                                    <td>0</td>
                                    <td>...</td>
                                    <td>1</td>
                                </tr>
                            </tbody>
                        </table>
                        <p><strong>Eslatma:</strong> 1 = to'g'ri javob, 0 = noto'g'ri javob</p>
                    </div>
                    
                    <div class="step">
                        <h3>3. Faylni botga yuboring</h3>
                        <p>Tayyorlagan Excel faylni botga yuboring. Bot avtomatik ravishda tahlilni boshlaydi.</p>
                    </div>
                    
                    <div class="step">
                        <h3>4. Natijalarni oling</h3>
                        <p>Tahlil tugagach, bot sizga quyidagi ma'lumotlarni beradi:</p>
                        <ul>
                            <li>📊 Umumiy statistika</li>
                            <li>📈 Baholar taqsimoti</li>
                            <li>📋 Batafsil Excel hisobot</li>
                            <li>📑 PDF format hisobot</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>⌨️ Bot buyruqlari</h2>
                
                <div class="commands">
                    <h3>Asosiy buyruqlar:</h3>
                    <div class="command-item">
                        <span class="command">/start</span> - Botni ishga tushirish va salomlashish
                    </div>
                    <div class="command-item">
                        <span class="command">/help</span> - Yordam va qo'llanma olish
                    </div>
                    <div class="command-item">
                        <span class="command">/namuna - Namuna tahlil ko'rish (100 talaba x 55 savol)
                    </div>
                    <div class="command-item">
                        <span class="command">/ball</span> - Ikki Excel fayldan o'rtacha ball hisoblash
                    </div>
                    <div class="command-item">
                        <span class="command">/cancel</span> - Joriy jarayonni bekor qilish
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>📋 Fayl talablari</h2>
                
                <div class="features">
                    <div class="feature">
                        <h3>📁 Fayl formati</h3>
                        <p>.xlsx yoki .xls formatda Excel fayl bo'lishi kerak.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>📊 Ma'lumotlar tuzilishi</h3>
                        <p>Birinchi ustun - talaba ID/nomi, qolgan ustunlar - savol javoblari (0/1).</p>
                    </div>
                    
                    <div class="feature">
                        <h3>🔢 Javoblar formati</h3>
                        <p>Faqat 0 (noto'g'ri) va 1 (to'g'ri) qiymatlar ishlatiladi.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>⚖️ Fayl hajmi</h3>
                        <p>Maksimal 50MB gacha fayllar qabul qilinadi.</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>🏆 Baholar tizimi</h2>
                <p>Bot O'zbekiston Bilim va Malakalarni Baholash Agentligi standartlari bo'yicha baholar beradi:</p>
                
                <table class="example-table">
                    <thead>
                        <tr>
                            <th>Baho</th>
                            <th>Ball oralig'i</th>
                            <th>Tavsif</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>A+</strong></td>
                            <td>70+ ball</td>
                            <td>1-daraja (Oliy Imtiyozli)</td>
                        </tr>
                        <tr>
                            <td><strong>A</strong></td>
                            <td>65-69.9 ball</td>
                            <td>1-daraja (Oliy)</td>
                        </tr>
                        <tr>
                            <td><strong>B+</strong></td>
                            <td>60-64.9 ball</td>
                            <td>2-daraja (Yuqori Imtiyozli)</td>
                        </tr>
                        <tr>
                            <td><strong>B</strong></td>
                            <td>55-59.9 ball</td>
                            <td>2-daraja (Yuqori)</td>
                        </tr>
                        <tr>
                            <td><strong>C+</strong></td>
                            <td>50-54.9 ball</td>
                            <td>3-daraja (O'rtacha Imtiyozli)</td>
                        </tr>
                        <tr>
                            <td><strong>C</strong></td>
                            <td>45-49.9 ball</td>
                            <td>3-daraja (O'rtacha)</td>
                        </tr>
                        <tr>
                            <td><strong>NC</strong></td>
                            <td>45 dan kam</td>
                            <td>Qoniqarsiz</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>❓ Tez-tez so'raladigan savollar</h2>
                
                <div class="features">
                    <div class="feature">
                        <h3>Q: Bot qancha talaba ma'lumotlarini qayta ishlay oladi?</h3>
                        <p>A: Bot minglab talaba ma'lumotlarini qayta ishlay oladi. Ammo fayl hajmi 50MB dan oshmasligi kerak.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>Q: Savollar soni qancha bo'lishi kerak?</h3>
                        <p>A: Kamida 10 ta savol bo'lishi tavsiya etiladi. Savollar ko'p bo'lsa, tahlil natijasi aniqroq bo'ladi.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>Q: Bot qanday tahlil qiladi?</h3>
                        <p>A: Bot Rasch model (1PL IRT) asosida talabalarning qobiliyati va savollarning qiyinlik darajasini hisoblaydi.</p>
                    </div>
                    
                    <div class="feature">
                        <h3>Q: Hisobotlarni qayerdan olish mumkin?</h3>
                        <p>A: Tahlil tugagach, bot sizga Excel va PDF formatda hisobotlarni yuboradi.</p>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>📞 Yordam va qo'llab-quvvatlash</h2>
                <p>Agar bot bilan bog'liq muammolar yuzaga kelsa yoki qo'shimcha yordam kerak bo'lsa:</p>
                <ul>
                    <li>Botda /help buyrug'ini yuboring</li>
                    <li>Namuna fayl olish uchun /namuna buyrug'ini ishlating</li>
                    <li>Web ilovadan foydalanish uchun <a href="/">asosiy sahifaga</a> o'ting</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2025 Rasch Counter Bot. Barcha huquqlar himoyalangan.</p>
        </div>
    </div>
</body>
</html>
"""

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'rasch-counter-web-app-2025')

# Configuration
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
RESULTS_FOLDER = Path(__file__).parent / 'results'
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# Create directories
UPLOAD_FOLDER.mkdir(exist_ok=True)
RESULTS_FOLDER.mkdir(exist_ok=True)

# Global variables for processing status
processing_status = {}
processing_results = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_file_async(file_path, session_id):
    """Process file in background thread using analysis service"""
    def progress_callback(percent, message):
        processing_status[session_id] = {
            'status': 'processing',
            'progress': percent,
            'message': message
        }
    
    # Create session in analysis service
    analysis_service.create_session(session_id)
    
    # Process file
    success = analysis_service.process_file(file_path, session_id, progress_callback)
    
    if success:
        processing_status[session_id] = {
            'status': 'completed',
            'progress': 100,
            'message': 'Tahlil yakunlandi!'
        }
    else:
        status = analysis_service.get_status(session_id)
        processing_status[session_id] = status

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/telegram-guide')
def telegram_guide():
    """Telegram bot qo'llanmasi"""
    return render_template_string(TELEGRAM_GUIDE_HTML)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'Fayl tanlanmagan'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Fayl tanlanmagan'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Faqat Excel fayllar (.xlsx, .xls) qabul qilinadi'}), 400
    
    try:
        # Generate session ID
        session_id = f"session_{int(time.time())}_{id(file)}"
        session['session_id'] = session_id
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = UPLOAD_FOLDER / filename
        file.save(file_path)
        
        # Start processing in background
        thread = threading.Thread(target=process_file_async, args=(file_path, session_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': 'Fayl yuklandi va tahlil boshlandi'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': f'Yuklash xatoligi: {str(e)}'}), 500

@app.route('/status/<session_id>')
def get_status(session_id):
    """Get processing status"""
    if session_id not in processing_status:
        return jsonify({'error': 'Session topilmadi'}), 404
    
    return jsonify(processing_status[session_id])

@app.route('/results/<session_id>')
def get_results(session_id):
    """Get processing results"""
    results_data = analysis_service.get_results(session_id, format='json')
    
    if 'error' in results_data:
        return jsonify(results_data), 404
    
    return jsonify(results_data)

@app.route('/download/<session_id>/<file_type>')
def download_file(session_id, file_type):
    """Download results file"""
    try:
        if file_type == 'excel':
            excel_data = analysis_service.get_excel_file(session_id)
            if not excel_data:
                return jsonify({'error': 'Natijalar topilmadi'}), 404
            
            return send_file(
                excel_data,
                as_attachment=True,
                download_name=f'rasch_results_{session_id}.xlsx',
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        elif file_type == 'pdf':
            pdf_data = analysis_service.get_pdf_file(session_id)
            if not pdf_data:
                return jsonify({'error': 'Natijalar topilmadi'}), 404
            
            return send_file(
                pdf_data,
                as_attachment=True,
                download_name=f'rasch_results_{session_id}.pdf',
                mimetype='application/pdf'
            )
        else:
            return jsonify({'error': 'Noto\'g\'ri fayl turi'}), 400
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({'error': f'Yuklab olish xatoligi: {str(e)}'}), 500

@app.route('/api/sample')
def get_sample_results():
    """Generate sample results for demonstration"""
    try:
        # Create sample session using analysis service
        session_id = analysis_service.create_sample_results()
        results_data = analysis_service.get_results(session_id, format='json')
        
        return jsonify({
            'success': True,
            'session_id': session_id,  # Add session_id for downloads
            'results': results_data,
            'message': 'Namuna natijalar yaratildi'
        })
        
    except Exception as e:
        logger.error(f"Sample results error: {e}")
        return jsonify({'error': f'Namuna natijalar yaratish xatoligi: {str(e)}'}), 500

if __name__ == '__main__':
    # Load environment variables
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    # Run the app
    port = int(os.environ.get('WEB_PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"🌐 Web app ishga tushirilmoqda...")
    print(f"📍 URL: http://localhost:{port}")
    print(f"🔧 Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
