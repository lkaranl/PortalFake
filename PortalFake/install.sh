#!/bin/bash

# PortalFake - Script de instalação
# Este script instala as dependências necessárias para o projeto PortalFake

# Verificar se está sendo executado como root
if [ "$EUID" -ne 0 ]; then
  echo "Este script precisa ser executado como root (sudo)."
  exit 1
fi

echo "=== Instalando PortalFake ==="
echo

# Detectar a distribuição
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    echo "Não foi possível detectar a distribuição Linux."
    exit 1
fi

echo "Distribuição detectada: $DISTRO"

# Instalar dependências do sistema
echo "Instalando dependências do sistema..."

case $DISTRO in
    ubuntu|debian)
        apt-get update
        apt-get install -y hostapd dnsmasq python3 python3-pip python3-venv iw net-tools
        ;;
    fedora)
        dnf update -y
        dnf install -y hostapd dnsmasq python3 python3-pip iw net-tools
        ;;
    *)
        echo "Distribuição não suportada: $DISTRO"
        echo "Por favor, instale manualmente: hostapd dnsmasq python3 python3-pip iw net-tools"
        ;;
esac

# Parar e desabilitar serviços que podem interferir
echo "Parando e desabilitando serviços que podem interferir..."
systemctl stop hostapd dnsmasq 2>/dev/null || true
systemctl disable hostapd dnsmasq 2>/dev/null || true

# Criar ambiente virtual Python
echo "Configurando ambiente virtual Python..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

. venv/bin/activate

# Instalar dependências Python
echo "Instalando dependências Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Criar arquivo .env de exemplo se não existir
if [ ! -f ".env" ]; then
    echo "Criando arquivo .env de exemplo..."
    cat > .env << EOF
# Configurações do PortalFake
# Remova o comentário e edite conforme necessário

# WIFI_SSID=PortalFake
# WIFI_PASSWORD=senha_secreta
# WIFI_INTERFACE=wlan0
EOF
fi

echo
echo "=== Instalação concluída! ==="
echo
echo "Para executar o PortalFake:"
echo "1. Ative o ambiente virtual: source venv/bin/activate"
echo "2. Execute o programa: sudo -E python3 main.py --ssid \"Nome-da-Rede\" [--password \"senha\"]"
echo "   Ou use: sudo -E python3 main.py --ssid \"Nome-da-Rede\" --open (para rede aberta)"
echo
echo "Certifique-se de ter uma interface WiFi compatível com o modo AP."
echo
