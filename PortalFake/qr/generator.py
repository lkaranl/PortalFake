import qrcode
from typing import Optional, Any

def generate_wifi_qr(ssid: str, password: Optional[str] = None, security: str = 'WPA') -> Any:
    """
    Gera um QR code com as credenciais de uma rede WiFi.
    
    Args:
        ssid: Nome da rede WiFi
        password: Senha da rede (None para redes abertas)
        security: Tipo de segurança (WPA, WEP, None para rede aberta)
    
    Returns:
        Objeto de imagem PIL com o QR code
    """
    if not password:
        security = 'nopass'
        wifi_string = f"WIFI:S:{ssid};T:{security};;"
    else:
        wifi_string = f"WIFI:S:{ssid};T:{security};P:{password};;"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    qr.add_data(wifi_string)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def save_qr_image(img: Any, file_path: str = 'wifi_qr.png') -> str:
    """
    Salva a imagem do QR code em um arquivo.
    
    Args:
        img: Objeto de imagem PIL com o QR code
        file_path: Caminho para salvar a imagem
        
    Returns:
        Caminho do arquivo salvo
    """
    img.save(file_path)
    return file_path

def display_qr_terminal(ssid: str, password: Optional[str] = None, security: str = 'WPA') -> None:
    """
    Exibe o QR code no terminal.
    
    Args:
        ssid: Nome da rede WiFi
        password: Senha da rede (None para redes abertas)
        security: Tipo de segurança (WPA, WEP, None para rede aberta)
    """
    img = generate_wifi_qr(ssid, password, security)
    
    # Salvamos temporariamente e exibimos as informações no terminal
    save_qr_image(img)
    
    print(f"QR Code para conexão WiFi:")
    print(f"SSID: {ssid}")
    print(f"Senha: {'<sem senha>' if not password else password}")
    print(f"Segurança: {'Aberta' if not password else security}")
    print(f"Imagem salva em: wifi_qr.png")
