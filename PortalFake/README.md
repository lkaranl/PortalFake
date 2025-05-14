# PortalFake

PortalFake é uma aplicação para criar um ponto de acesso WiFi (hotspot) com portal cativo para captura de credenciais.

## Recursos

- Detecção automática de interfaces WiFi
- Criação de hotspot (com ou sem senha)
- Geração de QR Code para conexão rápida
- Portal cativo que captura e-mail/senha
- Registro de tentativas de login em CSV ou SQLite
- Integração com NetworkManager para melhor compatibilidade
- Redirecionamento de tráfego HTTP e HTTPS para o portal cativo
- Gerenciamento automático de serviços DNS conflitantes

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
- rfkill
- NetworkManager
- lsof
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
5. Inicia um servidor web (Flask) na porta 80 para o portal cativo
6. Configura redirecionamento de tráfego HTTP (80) e HTTPS (443) para o portal
7. Quando um cliente se conecta à rede WiFi:
   - Qualquer acesso web é redirecionado para o portal cativo
   - O cliente deve fornecer um e-mail e senha para acessar a internet
   - Os dados fornecidos são registrados em CSV ou SQLite

## Resolução de Problemas

### O hotspot não inicia

- Verifique se o WiFi está bloqueado: `rfkill list`
- Para desbloquear o WiFi: `sudo rfkill unblock wifi`
- Verifique se sua placa WiFi suporta o modo AP: `iw list | grep AP`
- Certifique-se de que hostapd está instalado: `which hostapd`
- Verifique se não há outros serviços usando a interface WiFi
- Execute com sudo: `sudo -E python main.py ...`

### Erro "Operation not possible due to RF-kill"

Este erro ocorre quando o hardware WiFi está bloqueado:

```
RTNETLINK answers: Operation not possible due to RF-kill
```

Para resolver:
1. Execute: `sudo rfkill unblock all`
2. Certifique-se de que o WiFi está ligado fisicamente (botão/switch no computador)
3. Verifique o estado do NetworkManager: `nmcli radio wifi`
4. Ative o WiFi com: `nmcli radio wifi on`

### Erro "Failed to create listening socket for port 53"

Este erro ocorre porque outro serviço DNS (como systemd-resolved) já está usando a porta 53:

```
dnsmasq: failed to create listening socket for port 53: Endereço já em uso
```

O programa tentará parar automaticamente o serviço conflitante. Se ainda assim ocorrer o erro, você pode manualmente:

1. Verificar qual processo está usando a porta 53: `sudo lsof -i :53`
2. Parar o serviço systemd-resolved: `sudo systemctl stop systemd-resolved`
3. Reiniciar o programa

Após encerrar o programa, o serviço DNS original será reiniciado automaticamente.

### Erro ao iniciar o servidor web na porta 80

Esta porta requer privilégios de root. Certifique-se de executar o programa com `sudo`.

Se outro serviço estiver usando a porta 80, você receberá um erro. Verifique com:
```
sudo netstat -tulpn | grep :80
```

Para liberar a porta, pare o serviço que a está usando:
```
sudo systemctl stop apache2   # se for o Apache
sudo systemctl stop nginx     # se for o Nginx
```

### Clientes conectam mas não veem o portal cativo

- Verifique se dnsmasq está em execução: `ps aux | grep dnsmasq`
- Teste acesso manual ao portal: `http://192.168.42.1` (porta 80)
- Verifique regras iptables: `sudo iptables -t nat -L -n -v`

### O QR Code não funciona

- Certifique-se de que o SSID e a senha estão corretos
- Alguns dispositivos mais antigos podem não suportar QR Codes para WiFi

## Segurança

Este programa foi criado apenas para fins educacionais e teste de segurança. Uso indevido para capturar credenciais de usuários sem permissão pode ser ilegal.

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo LICENSE para detalhes.
