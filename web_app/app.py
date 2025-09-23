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
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from werkzeug.utils import secure_filename
import io
import threading
import time
from datetime import datetime

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from services.analysis_service import analysis_service

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
