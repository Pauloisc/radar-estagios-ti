import os
from pathlib import Path
from typing import Any, Dict
import yaml
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env caso exista
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

def load_yaml(file_path: Path) -> Dict[str, Any]:
    """Carrega com segurança um arquivo YAML."""
    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

class Settings:
    """Configurações centralizadas da aplicação."""
    
    # Caminhos
    BASE_DIR = BASE_DIR
    CONFIG_DIR = BASE_DIR / "config"
    DATA_DIR = BASE_DIR / "data"
    
    # Arquivos YAML
    PROFILE_PATH = CONFIG_DIR / "profile.yaml"
    CONFIG_PATH = CONFIG_DIR / "config.yaml"
    
    def __init__(self):
        self.profile = load_yaml(self.PROFILE_PATH)
        self.config = load_yaml(self.CONFIG_PATH)
        
        # Cria diretório de dados se não existir
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Variáveis de Ambiente / Secrets
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        self.GMAIL_SENDER_EMAIL = os.getenv("GMAIL_SENDER_EMAIL", "")
        self.GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
        self.NOTIFICATION_TARGET_EMAIL = os.getenv(
            "NOTIFICATION_TARGET_EMAIL", 
            self.profile.get("usuario", {}).get("email", "pauloitalo061@gmail.com")
        )
        self.AI_PROVIDER = os.getenv("AI_PROVIDER", "gemini")
        self.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        # Banco de dados
        db_rel = self.config.get("geral", {}).get("banco_sqlite", "data/jobs_history.db")
        self.DB_PATH = self.BASE_DIR / db_rel
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

settings = Settings()
