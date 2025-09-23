#!/usr/bin/env python3
"""
Public Website for Rasch Counter Bot
Foydalanuvchilarga botni qanday ishlatishni ko'rsatuvchi sayt
"""

from flask import Flask, render_template_string
import os

app = Flask(__name__)

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rasch Counter Bot - Yo'riqnoma</title>
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
            padding: 20px;
            border-radius: 10px;
            font-family: 'Courier New', monospace;
            margin: 20px 0;
        }
        
        .commands h3 {
            color: #4fd1c7;
            margin-bottom: 15px;
        }
        
        .command-item {
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid #4a5568;
        }
        
        .command-item:last-child {
            border-bottom: none;
        }
        
        .command {
            color: #68d391;
            font-weight: bold;
        }
        
        .steps {
            counter-reset: step-counter;
        }
        
        .step {
            counter-increment: step-counter;
            background: #f7fafc;
            margin: 15px 0;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            position: relative;
        }
        
        .step::before {
            content: counter(step-counter);
            position: absolute;
            left: -15px;
            top: 15px;
            background: #667eea;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        
        .telegram-link {
            display: inline-block;
            background: #0088cc;
            color: white;
            padding: 15px 30px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: bold;
            margin: 20px 0;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(0, 136, 204, 0.3);
        }
        
        .telegram-link:hover {
            background: #006699;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 136, 204, 0.4);
        }
        
        .example-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .example-table th,
        .example-table td {
            padding: 12px 15px;
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
            <h1>🎓 Rasch Counter Bot</h1>
            <p>Test natijalarini professional tahlil qiluvchi bot</p>
        </div>
        
        <div class="content">
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
                        <h3>Telegram botni oching</h3>
                        <p>Quyidagi tugma orqali botni ishga tushiring va /start buyrug'ini yuboring.</p>
                        <a href="https://t.me/rasch_counter_bot" class="telegram-link">🤖 Botni ochish</a>
                    </div>
                    
                    <div class="step">
                        <h3>Excel faylni tayyorlang</h3>
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
                        <h3>Faylni botga yuboring</h3>
                        <p>Tayyorlagan Excel faylni botga yuboring. Bot avtomatik ravishda tahlilni boshlaydi.</p>
                    </div>
                    
                    <div class="step">
                        <h3>Natijalarni oling</h3>
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
                        <span class="command">/matrix</span> - Namuna Excel fayl olish (100 talaba x 55 savol)
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
                            <td>3-daraja (O'rta Imtiyozli)</td>
                        </tr>
                        <tr>
                            <td><strong>C</strong></td>
                            <td>46-49.9 ball</td>
                            <td>3-daraja (O'rta)</td>
                        </tr>
                        <tr>
                            <td><strong>NC</strong></td>
                            <td>&lt;46 ball</td>
                            <td>4-daraja (Sertifikatsiz)</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>💬 Yordam va qo'llab-quvvatlash</h2>
                <p>Savollar yoki takliflar uchun:</p>
                <ul>
                    <li>📱 Telegram guruh: <a href="https://t.me/rasch_counter">t.me/rasch_counter</a></li>
                    <li>🤖 Bot: <a href="https://t.me/rasch_counter_bot">@rasch_counter_bot</a></li>
                    <li>📧 Texnik yordam: /help buyrug'i orqali</li>
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2025 Rasch Counter Bot | Professional Test Analysis Tool</p>
            <p>O'zbekiston Bilim va Malakalarni Baholash Agentligi standartlari asosida</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    """Ana sahifa - bot haqida to'liq ma'lumot"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    """Sayt ishlayotganligini tekshirish"""
    return {"status": "ok", "message": "Public website is running"}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
