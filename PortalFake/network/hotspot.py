import os
import subprocess
import netifaces
import tempfile
import time
from typing import Optional, Tuple, List

class Hotspot:
    def __init__(self):
        self.interface = None
        self.ssid = None
        self.password = None
        self.hostapd_conf = None
        self.dnsmasq_conf = None
        self.is_running = False
        self.hostapd_proc = None
        self.dnsmasq_proc = None
    
    def detect_wifi_interface(self) -> Optional[str]:
        """
        Detecta automaticamente a interface WiFi disponível no sistema.
        
        Returns:
            Nome da interface WiFi ou None se não for encontrada
        """
        interfaces = netifaces.interfaces()
        
        # Procura por interfaces wireless
        for interface in interfaces:
            # Verifica se é uma interface wireless usando iw
            try:
                result = subprocess.run(
                    ['iw', interface, 'info'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    return interface
            except Exception:
                continue
        
        return None
    
    def setup(self, ssid: str, password: Optional[str] = None, interface: Optional[str] = None) -> bool:
        """
        Configura o hotspot WiFi.
        
        Args:
            ssid: Nome da rede WiFi
            password: Senha da rede (None para redes abertas)
            interface: Interface de rede (se None, será detectada automaticamente)
            
        Returns:
            True se a configuração foi bem-sucedida, False caso contrário
        """
        # Verificar privilégios de root
        if os.geteuid() != 0:
            print("Erro: Este programa precisa ser executado como root (sudo)")
            return False
        
        # Detectar interface WiFi
        self.interface = interface or self.detect_wifi_interface()
        if not self.interface:
            print("Erro: Nenhuma interface WiFi detectada")
            return False
        
        self.ssid = ssid
        self.password = password
        
        # Verificar dependências
        if not self._check_dependencies():
            print("Erro: Dependências não estão instaladas")
            return False
        
        return True
    
    def _check_dependencies(self) -> bool:
        """
        Verifica se as dependências necessárias estão instaladas.
        
        Returns:
            True se todas as dependências estão instaladas, False caso contrário
        """
        try:
            # Verificar hostapd
            hostapd_check = subprocess.run(
                ['which', 'hostapd'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )
            
            # Verificar dnsmasq
            dnsmasq_check = subprocess.run(
                ['which', 'dnsmasq'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )
            
            if hostapd_check.returncode != 0 or dnsmasq_check.returncode != 0:
                return False
            
            return True
        except Exception:
            return False
    
    def _create_hostapd_config(self) -> str:
        """
        Cria o arquivo de configuração para o hostapd.
        
        Returns:
            Caminho do arquivo de configuração
        """
        config = [
            f"interface={self.interface}",
            f"ssid={self.ssid}",
            "driver=nl80211",
            "hw_mode=g",
            "channel=7",
            "ieee80211n=1",
            "wmm_enabled=1",
            "ignore_broadcast_ssid=0",
        ]
        
        if self.password and len(self.password) >= 8:
            config.extend([
                "auth_algs=1",
                "wpa=2",
                "wpa_key_mgmt=WPA-PSK",
                "rsn_pairwise=CCMP",
                f"wpa_passphrase={self.password}"
            ])
        
        fd, config_path = tempfile.mkstemp(prefix="hostapd_", suffix=".conf")
        with os.fdopen(fd, 'w') as f:
            f.write("\n".join(config))
        
        self.hostapd_conf = config_path
        return config_path
    
    def _create_dnsmasq_config(self) -> str:
        """
        Cria o arquivo de configuração para o dnsmasq.
        
        Returns:
            Caminho do arquivo de configuração
        """
        config = [
            f"interface={self.interface}",
            "dhcp-range=192.168.42.10,192.168.42.50,12h",
            "dhcp-option=3,192.168.42.1",
            "dhcp-option=6,192.168.42.1",
            "server=8.8.8.8",
            "log-queries",
            "address=/#/192.168.42.1"  # Redirect all DNS queries to the captive portal
        ]
        
        fd, config_path = tempfile.mkstemp(prefix="dnsmasq_", suffix=".conf")
        with os.fdopen(fd, 'w') as f:
            f.write("\n".join(config))
        
        self.dnsmasq_conf = config_path
        return config_path
    
    def start(self) -> bool:
        """
        Inicia o hotspot WiFi.
        
        Returns:
            True se o hotspot foi iniciado com sucesso, False caso contrário
        """
        if self.is_running:
            return True
        
        try:
            # Configurar interface de rede
            subprocess.run(['ip', 'link', 'set', self.interface, 'down'], check=True)
            subprocess.run(['ip', 'addr', 'flush', 'dev', self.interface], check=True)
            subprocess.run(['ip', 'link', 'set', self.interface, 'up'], check=True)
            subprocess.run(['ip', 'addr', 'add', '192.168.42.1/24', 'dev', self.interface], check=True)
            
            # Iniciar hostapd
            hostapd_conf = self._create_hostapd_config()
            self.hostapd_proc = subprocess.Popen(
                ['hostapd', hostapd_conf],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Dar tempo para o hostapd iniciar
            time.sleep(2)
            
            # Verificar se o hostapd está em execução
            if self.hostapd_proc.poll() is not None:
                stderr = self.hostapd_proc.stderr.read().decode('utf-8')
                print(f"Erro ao iniciar hostapd: {stderr}")
                return False
            
            # Configurar NAT
            subprocess.run(['sysctl', '-w', 'net.ipv4.ip_forward=1'], check=True)
            
            # Configurar iptables para NAT
            subprocess.run([
                'iptables', '-t', 'nat', '-A', 'POSTROUTING',
                '-o', 'eth0', '-j', 'MASQUERADE'
            ], check=True)
            
            # Redirecionar todo o tráfego HTTP para o portal cativo
            subprocess.run([
                'iptables', '-t', 'nat', '-A', 'PREROUTING',
                '-i', self.interface, '-p', 'tcp', '--dport', '80',
                '-j', 'DNAT', '--to-destination', '192.168.42.1:5000'
            ], check=True)
            
            # Iniciar dnsmasq
            dnsmasq_conf = self._create_dnsmasq_config()
            self.dnsmasq_proc = subprocess.Popen(
                ['dnsmasq', '-C', dnsmasq_conf, '-d'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Dar tempo para o dnsmasq iniciar
            time.sleep(2)
            
            # Verificar se o dnsmasq está em execução
            if self.dnsmasq_proc.poll() is not None:
                stderr = self.dnsmasq_proc.stderr.read().decode('utf-8')
                print(f"Erro ao iniciar dnsmasq: {stderr}")
                self.stop()
                return False
            
            self.is_running = True
            return True
            
        except Exception as e:
            print(f"Erro ao iniciar hotspot: {str(e)}")
            self.stop()
            return False
    
    def stop(self) -> bool:
        """
        Para o hotspot WiFi.
        
        Returns:
            True se o hotspot foi parado com sucesso, False caso contrário
        """
        try:
            # Parar processos
            if self.hostapd_proc:
                self.hostapd_proc.terminate()
                self.hostapd_proc.wait()
                self.hostapd_proc = None
            
            if self.dnsmasq_proc:
                self.dnsmasq_proc.terminate()
                self.dnsmasq_proc.wait()
                self.dnsmasq_proc = None
            
            # Limpar arquivos temporários
            if self.hostapd_conf and os.path.exists(self.hostapd_conf):
                os.unlink(self.hostapd_conf)
                self.hostapd_conf = None
                
            if self.dnsmasq_conf and os.path.exists(self.dnsmasq_conf):
                os.unlink(self.dnsmasq_conf)
                self.dnsmasq_conf = None
            
            # Limpar configurações de rede
            subprocess.run(['iptables', '-t', 'nat', '-F'], check=True)
            subprocess.run(['sysctl', '-w', 'net.ipv4.ip_forward=0'], check=True)
            subprocess.run(['ip', 'addr', 'flush', 'dev', self.interface], check=True)
            
            self.is_running = False
            return True
        except Exception as e:
            print(f"Erro ao parar hotspot: {str(e)}")
            return False
    
    def get_client_leases(self) -> List[dict]:
        """
        Obtém a lista de clientes conectados ao hotspot.
        
        Returns:
            Lista de clientes com seus endereços MAC e IPs
        """
        clients = []
        
        if not self.is_running:
            return clients
        
        try:
            # Verificar arquivo de leases do dnsmasq
            leases_file = '/var/lib/misc/dnsmasq.leases'
            if os.path.exists(leases_file):
                with open(leases_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            client = {
                                'mac': parts[1],
                                'ip': parts[2],
                                'hostname': parts[3]
                            }
                            clients.append(client)
        except Exception as e:
            print(f"Erro ao obter clientes: {str(e)}")
        
        return clients
