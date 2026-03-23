import logging
import os
from logging.handlers import RotatingFileHandler

# Diretório para os logs
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, "sigdt.log")

def setup_logging():
    # Formatador: Data - Nome - Nível - Mensagem
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Handler para arquivo com rotação (5MB por arquivo, mantém 5 backups)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # Handler para console (útil para desenvolvimento/docker)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    # Configuração do logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Evitar duplicidade de logs se setup for chamado mais de uma vez
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    logging.info("Sistema de Logging Inicializado com Rotação de Arquivos.")

def get_logger(name):
    return logging.getLogger(name)
