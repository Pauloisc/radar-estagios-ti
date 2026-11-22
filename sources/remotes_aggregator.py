import logging
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from sources.base import BaseSource

logger = logging.getLogger(__name__)

class RemoteJobSource(BaseSource):
    """
    Coleta vagas de TI 100% remotas através de feeds públicos e agregadores de vagas remotas.
    """

    name = "remotes_aggregator"

    # Feeds RSS conhecidos de vagas remotas de tecnologia
    RSS_FEEDS = [
        "https://remotar.com.br/feed",
        "https://weworkremotely.com/categories/remote-programming-jobs.rss"
    ]

    def fetch_jobs(self) -> List[Dict[str, Any]]:
        jobs = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EstagiosRadarBot/1.0"
        }

        for feed_url in self.RSS_FEEDS:
            try:
                resp = requests.get(feed_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    channel = root.find("channel")
                    if channel is None:
                        continue

                    for item in channel.findall("item"):
                        title = item.findtext("title", "")
                        link = item.findtext("link", "")
                        description = item.findtext("description", "")

                        # Pré-filtro simples para otimizar antes do filtro formal
                        title_lower = title.lower()
                        if any(k in title_lower for k in ["estagio", "estágio", "intern"]):
                            jobs.append({
                                "id_fonte": link,
                                "titulo": title,
                                "empresa": "Portal Remoto",
                                "cidade": "Remoto",
                                "estado": "BR",
                                "modalidade": "remoto",
                                "url": link,
                                "descricao": description,
                                "horario": "",
                                "fonte": self.name
                            })
            except Exception as e:
                logger.warning(f"Erro ao consultar feed remoto {feed_url}: {e}")

        return jobs
