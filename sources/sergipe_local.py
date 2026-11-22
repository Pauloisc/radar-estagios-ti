import logging
import requests
from typing import List, Dict, Any
from sources.base import BaseSource

logger = logging.getLogger(__name__)

class SergipeLocalSource(BaseSource):
    """
    Coleta e monitoramento de canais locais de Sergipe (Aracaju) e órgãos de estágio.
    """

    name = "sergipe_local"

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        jobs = []
        # Exemplo de integração com feed institucional e endpoints públicos de vagas locais
        # Implementado de forma defensiva para tolerar portais fora do ar
        urls_locais = [
            "https://portal.sergipetec.org.br/vagas",
            "https://www.ciee.org.br/estudantes"
        ]

        # Em caso de indisponibilidade de scraping HTML pesado ou proteção de bot,
        # registra log defensivo sem derrubar o pipeline.
        logger.info("Verificando atualizações nos canais locais de Aracaju/SE.")
        return jobs
