import logging
import requests
from typing import List, Dict, Any
from sources.base import BaseSource

logger = logging.getLogger(__name__)

class GupySource(BaseSource):
    """
    Coleta vagas da API pública de busca do Gupy (vagas abertas em TI, Aracaju e Remoto).
    """

    name = "gupy"
    BASE_URL = "https://employers-api.gupy.io/api/v1/jobs"

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        jobs = []
        termos = [
            ("estagio ti", "Aracaju", False),
            ("estagio desenvolvimento", "Aracaju", False),
            ("estagio tecnologia", "Aracaju", False),
            ("estagio", "Aracaju", False),
            ("estagio desenvolvedor", "", True),
            ("estagio ti", "", True),
            ("estagio frontend", "", True),
            ("estagio backend", "", True),
            ("estagio python", "", True),
            ("estagio react", "", True)
        ]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        for term, city, is_remote in termos:
            params = {
                "jobName": term,
                "type": "internship",
                "limit": 15
            }
            if city:
                params["city"] = city
            if is_remote:
                params["workplaceType"] = "remote"

            try:
                resp = requests.get(self.BASE_URL, params=params, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    vagas = data.get("data", [])
                    for item in vagas:
                        modalidade = item.get("workplaceType", "")
                        if modalidade == "remote":
                            modalidade_str = "remoto"
                        elif modalidade == "hybrid":
                            modalidade_str = "hibrido"
                        else:
                            modalidade_str = "presencial"

                        vaga_dict = {
                            "id_fonte": str(item.get("id")),
                            "titulo": item.get("name", ""),
                            "empresa": item.get("careerPageName", "") or item.get("employer", {}).get("name", "Gupy Partner"),
                            "cidade": item.get("city", "") or ("Remoto" if modalidade_str == "remoto" else "Aracaju"),
                            "estado": item.get("state", "SE"),
                            "modalidade": modalidade_str,
                            "url": item.get("jobUrl", "") or f"https://portal.gupy.io/job/{item.get('id')}",
                            "descricao": item.get("description", "") or item.get("badges", {}).get("friendlyBadge", ""),
                            "horario": "",
                            "fonte": self.name
                        }
                        jobs.append(vaga_dict)
            except Exception as e:
                logger.warning(f"Erro ao buscar vagas no Gupy para '{term}' ({city or 'remoto'}): {e}")

        return jobs
