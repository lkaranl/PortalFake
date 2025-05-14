import os
import csv
import sqlite3
import datetime
from typing import Dict, Any, Optional

class Logger:
    def __init__(self, log_type: str = 'csv', db_path: Optional[str] = None):
        """
        Inicializa o logger para registrar tentativas de login.
        
        Args:
            log_type: Tipo de log ('csv' ou 'sqlite')
            db_path: Caminho para o banco de dados SQLite (se log_type='sqlite')
        """
        self.log_type = log_type
        
        if log_type == 'sqlite':
            self.db_path = db_path or 'login_attempts.db'
            self._init_db()
        else:  # csv
            self.csv_path = 'login_attempts.csv'
            if not os.path.exists(self.csv_path):
                with open(self.csv_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['timestamp', 'mac_address', 'ip_address', 'email', 'result'])
    
    def _init_db(self):
        """Inicializa o banco de dados SQLite se necessário."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            mac_address TEXT,
            ip_address TEXT,
            email TEXT,
            result TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_attempt(self, mac_address: str, ip_address: str, email: str, result: str):
        """
        Registra uma tentativa de login.
        
        Args:
            mac_address: Endereço MAC do cliente
            ip_address: Endereço IP atribuído
            email: E-mail fornecido
            result: Resultado (sucesso/erro)
        """
        timestamp = datetime.datetime.now().isoformat()
        
        if self.log_type == 'sqlite':
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO login_attempts (timestamp, mac_address, ip_address, email, result) VALUES (?, ?, ?, ?, ?)',
                (timestamp, mac_address, ip_address, email, result)
            )
            
            conn.commit()
            conn.close()
        else:  # csv
            with open(self.csv_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, mac_address, ip_address, email, result])
    
    def get_logs(self, limit: int = 100) -> list:
        """
        Obtém logs recentes.
        
        Args:
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de tentativas de login
        """
        if self.log_type == 'sqlite':
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM login_attempts ORDER BY timestamp DESC LIMIT ?', (limit,))
            rows = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return rows
        else:  # csv
            logs = []
            with open(self.csv_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= limit:
                        break
                    logs.append(row)
            return logs
