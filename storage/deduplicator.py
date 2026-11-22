import re
import hashlib
import unicodedata
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

def normalize_text(text: str) -> str:
    """Remove acentos, caracteres especiais e converte para minúsculas."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip().lower()

def clean_url(url: str) -> str:
    """Remove parâmetros de tracking como utm_*, fbclid, gclid e fragmentos."""
    if not url:
        return ""
    parsed = urlparse(url)
    # Filtrar queries de rastreamento
    tracking_params = {
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "fbclid", "gclid", "ref", "source", "trk", "trkinfo"
    }
    filtered_queries = [
        (k, v) for k, v in parse_qsl(parsed.query)
        if k.lower() not in tracking_params
    ]
    new_query = urlencode(filtered_queries)
    # Remove fragments e normaliza
    cleaned = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/"),
        parsed.params,
        new_query,
        ""  # sem fragmento
    ))
    return cleaned

def generate_job_hash(empresa: str, titulo: str, cidade: str, modalidade: str) -> str:
    """
    Gera um hash SHA-256 estável para identificar unicamente a vaga entre fontes diferentes.
    Normaliza os campos para evitar discrepâncias por pontuação ou maiúsculas.
    """
    empresa_norm = normalize_text(empresa)
    titulo_norm = normalize_text(titulo)
    cidade_norm = normalize_text(cidade)
    modalidade_norm = normalize_text(modalidade)
    
    chave = f"{empresa_norm}|{titulo_norm}|{cidade_norm}|{modalidade_norm}"
    return hashlib.sha256(chave.encode("utf-8")).hexdigest()
