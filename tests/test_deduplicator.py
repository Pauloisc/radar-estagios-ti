import os
import pytest
from pathlib import Path
from storage.db import DatabaseManager
from storage.deduplicator import generate_job_hash, clean_url, normalize_text

@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = tmp_path / "test_history.db"
    return DatabaseManager(db_file)

def test_clean_url_removes_tracking():
    raw_url = "https://gupy.io/job/12345?utm_source=linkedin&utm_medium=cpc&ref=tracker&valid=1"
    cleaned = clean_url(raw_url)
    assert cleaned == "https://gupy.io/job/12345?valid=1"

def test_generate_job_hash_is_stable():
    h1 = generate_job_hash("Empresa ABC", "Estágio em TI", "Aracaju", "presencial")
    h2 = generate_job_hash("  empresa abc  ", "ESTÁGIO EM TI", "aracaju ", "Presencial")
    assert h1 == h2

def test_deduplicator_prevents_duplicate_notifications(temp_db: DatabaseManager):
    job = {
        "titulo": "Estágio React",
        "empresa": "Tech SE",
        "cidade": "Aracaju",
        "modalidade": "presencial",
        "url": "https://empresa.com/vagas/10?utm_source=feed",
        "fonte": "gupy",
        "score": 85
    }

    url_clean = clean_url(job["url"])
    job_hash = generate_job_hash(job["empresa"], job["titulo"], job["cidade"], job["modalidade"])
    job["job_hash"] = job_hash

    # Antes de registrar: não deve constar como notificada
    assert not temp_db.is_job_notified(job_hash, url_clean)

    # Registra no banco
    assert temp_db.register_notified_job(job)

    # Após registrar: deve constar como já notificada
    assert temp_db.is_job_notified(job_hash, url_clean)

    # Nova tentativa da mesma vaga (mesmo com parâmetros diferentes na URL)
    url_outro_link = "https://empresa.com/vagas/10?utm_campaign=blackfriday"
    assert temp_db.is_job_notified(job_hash, clean_url(url_outro_link))

def test_empty_run_idempotency(temp_db: DatabaseManager):
    date_str = "2026-11-22"
    assert not temp_db.was_empty_run_notified_today(date_str)

    temp_db.register_execution_run(date_str, "SEM_VAGAS", 10, 10, 0)
    assert temp_db.was_empty_run_notified_today(date_str)
