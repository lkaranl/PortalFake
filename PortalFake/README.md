# PortalFake

PortalFake é uma aplicação para criar um ponto de acesso WiFi (hotspot) com portal cativo para captura de credenciais.

## Recursos

- Detecção automática de interfaces WiFi
- Criação de hotspot (com ou sem senha)
- Geração de QR Code para conexão rápida
- Portal cativo que captura e-mail/senha
- Registro de tentativas de login em CSV ou SQLite

## Diagrama de Fluxo

```
+-------------+     +-----------+     +-----------------+
| Dispositivo |---->| PortalFake|---->| Ponto de Acesso |
| do Usuário  |     | (Hotspot) |     | (Internet)      |
+-------------+     +-----------+     +-----------------+
                          |
                          v
                  +----------------+
                  | Portal Cativo  |
                  | (Página Login) |
                  +----------------+
                          |
                          v
                  +----------------+
                  | Log de Acessos |
                  | (CSV/SQLite)   |
                  +----------------+
```

## Requisitos

- Sistema Operacional: Linux (Ubuntu 22.04 ou Fedora 40)
- Privilégios de root (sudo)
- Python 3.10 ou superior
- Interface WiFi compatível com modo AP

## Dependências do Sistema

- hostapd
- dnsmasq
- iw
- net-tools
- python3-pip
- python3-venv

## Instalação

1. Clone este repositório:

```bash
git clone https://github.com/seu-usuario/PortalFake.git
cd PortalFake
```

2. Execute o script de instalação (requer privilégios de root):

```bash
sudo ./install.sh
```

## Uso

1. Ative o ambiente virtual:

```bash
source venv/bin/activate
```

2. Execute o programa como root:

```bash
# Rede com senha
sudo -E python main.py --ssid "IFRO-Guest" --password "12345678"

# Rede aberta (sem senha)
sudo -E python main.py --ssid "IFRO-Guest" --open
```

### Opções disponíveis:

- `--ssid NOME`: Define o nome da rede WiFi
- `--password SENHA`: Define a senha da rede WiFi (mínimo 8 caracteres)
- `--open`: Cria uma rede aberta (sem senha)
- `--interface INTERFACE`: Especifica manualmente a interface WiFi
- `--log-type [csv|sqlite]`: Define o formato de log (padrão: csv)

### Configuração via arquivo .env:

Você também pode configurar através do arquivo .env:

```
WIFI_SSID=IFRO-Guest
WIFI_PASSWORD=12345678
WIFI_INTERFACE=wlan0
```

## Estrutura do Projeto

```
PortalFake/
├── main.py           # Ponto de entrada do programa
├── requirements.txt  # Dependências Python
├── install.sh        # Script de instalação
├── network/          # Módulos para gerenciar interfaces de rede e hotspot
├── portal/           # Aplicação web do portal cativo
├── qr/               # Geração de QR Code
└── utils/            # Utilidades gerais
```

## Funcionamento

1. O programa detecta a interface WiFi disponível no sistema
2. Configura a interface como ponto de acesso usando hostapd
3. Configura DHCP e DNS usando dnsmasq
4. Gera e exibe um QR Code para conexão rápida
5. Inicia um servidor web (Flask) para o portal cativo
6. Quando um cliente se conecta à rede WiFi:
   - Qualquer acesso web é redirecionado para o portal cativo
   - O cliente deve fornecer um e-mail e senha para acessar a internet
   - Os dados fornecidos são registrados em CSV ou SQLite

## Resolução de Problemas

### O hotspot não inicia

- Verifique se sua placa WiFi suporta o modo AP: `iw list | grep AP`
- Certifique-se de que hostapd está instalado: `which hostapd`
- Verifique se não há outros serviços usando a interface WiFi
- Execute com sudo: `sudo -E python main.py ...`

### Clientes conectam mas não veem o portal cativo

- Verifique se dnsmasq está em execução: `ps aux | grep dnsmasq`
- Teste acesso manual ao portal: `http://192.168.42.1:5000`
- Verifique regras iptables: `sudo iptables -t nat -L -n -v`

### O QR Code não funciona

- Certifique-se de que o SSID e a senha estão corretos
- Alguns dispositivos mais antigos podem não suportar QR Codes para WiFi

## Segurança

Este programa foi criado apenas para fins educacionais e teste de segurança. Uso indevido para capturar credenciais de usuários sem permissão pode ser ilegal.

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo LICENSE para detalhes.
