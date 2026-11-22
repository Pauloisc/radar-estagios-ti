import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from storage.deduplicator import generate_job_hash, clean_url

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Gerenciador do banco de dados SQLite para histórico de vagas e deduplicação."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Cria as tabelas caso não existam."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Tabela de vagas notificadas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS jobs_history (
                        id TEXT PRIMARY KEY,               -- hash estável da vaga
                        fonte TEXT NOT NULL,               -- gupy, adzuna, etc.
                        id_fonte TEXT,                     -- ID nativo da fonte
                        titulo TEXT NOT NULL,
                        empresa TEXT NOT NULL,
                        cidade TEXT,
                        modalidade TEXT,
                        url TEXT NOT NULL,
                        url_canonica TEXT NOT NULL,
                        score INTEGER,
                        canal_notificacao TEXT DEFAULT 'email',
                        data_coleta TEXT NOT NULL,
                        data_notificacao TEXT NOT NULL
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_url_canonica ON jobs_history(url_canonica)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_data_notificacao ON jobs_history(data_notificacao)")

                # Tabela de controle de execuções (para idempotência diária e monitoramento)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS execution_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        data_execucao TEXT NOT NULL,
                        status TEXT NOT NULL,              -- SUCESSO, SEM_VAGAS, ERRO
                        vagas_coletadas INTEGER DEFAULT 0,
                        vagas_filtradas INTEGER DEFAULT 0,
                        vagas_notificadas INTEGER DEFAULT 0,
                        detalhes TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_runs_data ON execution_runs(data_execucao)")
                conn.commit()
        except Exception as e:
            logger.error(f"Erro ao inicializar o banco de dados em {self.db_path}: {e}")
            raise

    def is_job_notified(self, job_hash: str, canonical_url: str) -> bool:
        """Verifica se a vaga já foi notificada anteriormente (por hash ou URL canônica)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM jobs_history WHERE id = ? OR url_canonica = ? LIMIT 1",
                (job_hash, canonical_url)
            )
            return cursor.fetchone() is not None

    def register_notified_job(self, job: Dict[str, Any], channel: str = "email") -> bool:
        """Registra uma vaga como notificada com sucesso."""
        job_hash = job.get("job_hash") or generate_job_hash(
            empresa=job.get("empresa", ""),
            titulo=job.get("titulo", ""),
            cidade=job.get("cidade", ""),
            modalidade=job.get("modalidade", "")
        )
        url_canonica = clean_url(job.get("url", ""))
        agora = datetime.utcnow().isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO jobs_history (
                        id, fonte, id_fonte, titulo, empresa, cidade, modalidade,
                        url, url_canonica, score, canal_notificacao, data_coleta, data_notificacao
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_hash,
                    job.get("fonte", "desconhecida"),
                    str(job.get("id_fonte", "")),
                    job.get("titulo", ""),
                    job.get("empresa", ""),
                    job.get("cidade", ""),
                    job.get("modalidade", ""),
                    job.get("url", ""),
                    url_canonica,
                    job.get("score", 0),
                    channel,
                    job.get("data_coleta", agora),
                    agora
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Erro ao registrar vaga {job_hash} no banco: {e}")
            return False

    def was_empty_run_notified_today(self, date_str: str) -> bool:
        """Verifica se o e-mail de 'sem vagas' já foi disparado na data informada (YYYY-MM-DD)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM execution_runs WHERE data_execucao = ? AND status = 'SEM_VAGAS' LIMIT 1",
                (date_str,)
            )
            return cursor.fetchone() is not None

    def register_execution_run(self, date_str: str, status: str, collected: int, filtered: int, notified: int, details: str = ""):
        """Registra a conclusão de uma rodada de execução diária."""
        agora = datetime.utcnow().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO execution_runs (
                    data_execucao, status, vagas_coletadas, vagas_filtradas, vagas_notificadas, detalhes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (date_str, status, collected, filtered, notified, details, agora))
            conn.commit()
