import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class BaseSource(ABC):
    """Classe base para fontes de vagas."""

    name: str = "base"

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

    @abstractmethod
    def fetch_jobs(self) -> List[Dict[str, Any]]:
        """
        Retorna uma lista de dicionários representando as vagas coletadas.
        Cada dicionário deve possuir ao menos:
        - titulo (str)
        - empresa (str)
        - cidade (str)
        - estado (str)
        - modalidade (str: presencial, hibrido, remoto)
        - url (str)
        - descricao (str)
        - horario (str opcional)
        - id_fonte (str opcional)
        - fonte (str)
        """
        pass
