import os
import sys
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any

from config.settings import settings
from storage.db import DatabaseManager
from storage.deduplicator import generate_job_hash, clean_url
from filters.area_filter import AreaFilter
from filters.location_filter import LocationFilter
from filters.schedule_filter import ScheduleFilter
from analysis.gemini_analyzer import JobAnalyzer
from notifiers.email_notifier import EmailNotifier
from sources.gupy import GupySource
from sources.remotes_aggregator import RemoteJobSource
from sources.sergipe_local import SergipeLocalSource

# Configuração de logs estruturados
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("RadarEstagios")

def parse_args():
    parser = argparse.ArgumentParser(description="Radar Autônomo de Estágios em TI para Paulo Ítalo")
    parser.add_argument("--dry-run", action="store_true", help="Executa todo o pipeline sem disparar e-mails e sem alterar o banco de histórico.")
    parser.add_argument("--test-notify", action="store_true", help="Envia um e-mail de teste para verificar as credenciais SMTP.")
    parser.add_argument("--force", action="store_true", help="Ignora a checagem de execução já realizada no dia.")
    return parser.parse_args()

def run_pipeline(dry_run: bool = False, force: bool = False):
    today_str = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"=== Iniciando execução do Radar de Estágios ({today_str}) [Dry-run: {dry_run}] ===")

    # 1. Inicializa Notificador e Storage
    notifier = EmailNotifier(
        smtp_user=settings.GMAIL_SENDER_EMAIL,
        smtp_pass=settings.GMAIL_APP_PASSWORD,
        target_email=settings.NOTIFICATION_TARGET_EMAIL
    )

    try:
        db = DatabaseManager(settings.DB_PATH)
    except Exception as e:
        msg = f"Falha crítica ao abrir/inicializar o banco SQLite: {e}"
        logger.error(msg)
        if not dry_run:
            notifier.send_error_alert(msg)
        sys.exit(1)

    # 2. Inicializa o Analisador de IA
    analyzer = JobAnalyzer(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL,
        profile=settings.profile
    )

    # 3. Coleta de Vagas de Múltiplas Fontes
    sources = [
        GupySource(),
        RemoteJobSource(),
        SergipeLocalSource()
    ]

    all_raw_jobs: List[Dict[str, Any]] = []
    sources_failed = 0

    for src in sources:
        try:
            logger.info(f"Buscando vagas na fonte: {src.name}...")
            jobs = src.fetch_jobs()
            logger.info(f"Fonte {src.name} retornou {len(jobs)} vagas potenciais.")
            all_raw_jobs.extend(jobs)
        except Exception as e:
            logger.error(f"Erro ao consultar a fonte {src.name}: {e}")
            sources_failed += 1

    if sources_failed == len(sources) and len(sources) > 0:
        err_msg = "Todas as fontes configuradas falharam na coleta. Verifique a conectividade de rede."
        logger.critical(err_msg)
        if not dry_run:
            notifier.send_error_alert(err_msg)
            db.register_execution_run(today_str, "ERRO", 0, 0, 0, err_msg)
        sys.exit(1)

    # 4. Pipeline de Filtragem e Deduplicação
    eligible_jobs = []
    filtered_count = 0

    for job in all_raw_jobs:
        # A. Deduplicação prévia
        url_canonica = clean_url(job.get("url", ""))
        job_hash = generate_job_hash(
            empresa=job.get("empresa", ""),
            titulo=job.get("titulo", ""),
            cidade=job.get("cidade", ""),
            modalidade=job.get("modalidade", "")
        )
        job["job_hash"] = job_hash
        job["url_canonica"] = url_canonica

        if db.is_job_notified(job_hash, url_canonica):
            logger.debug(f"Vaga já notificada anteriormente ignorada: {job.get('titulo')}")
            filtered_count += 1
            continue

        # B. Filtro de Área e Nível (Estágio em TI)
        passou_area, motivo_area = AreaFilter.filter(job)
        if not passou_area:
            logger.debug(f"Descarte por área: {job.get('titulo')} - {motivo_area}")
            filtered_count += 1
            continue

        # C. Filtro de Localização (Aracaju/SE ou Remoto)
        passou_loc, motivo_loc = LocationFilter.filter(job)
        if not passou_loc:
            logger.debug(f"Descarte por localização: {job.get('titulo')} - {motivo_loc}")
            filtered_count += 1
            continue

        # D. Filtro Crítico de Horário
        passou_horario, motivo_horario, info_horario = ScheduleFilter.filter(job)
        if not passou_horario:
            logger.debug(f"Descarte por horário: {job.get('titulo')} - {motivo_horario}")
            filtered_count += 1
            continue

        job["horario_alerta"] = info_horario.get("alerta", "")
        eligible_jobs.append(job)

    logger.info(f"Vagas coletadas: {len(all_raw_jobs)} | Vagas descartadas/já notificadas: {filtered_count} | Vagas elegíveis para análise: {len(eligible_jobs)}")

    # 5. Tratamento de Nenhuma Vaga Nova Encontrada
    if not eligible_jobs:
        logger.info("Nenhuma nova vaga elegível encontrada nesta rodada.")
        if not dry_run:
            if force or not db.was_empty_run_notified_today(today_str):
                stats = {"collected": len(all_raw_jobs), "filtered": filtered_count}
                notifier.send_empty_notification(today_str, stats)
                db.register_execution_run(today_str, "SEM_VAGAS", len(all_raw_jobs), filtered_count, 0)
            else:
                logger.info("Notificação diária de 'sem vagas' já enviada hoje. Ignorando reenvio.")
        return

    # 6. Análise com IA e Notificação
    analyzed_jobs = []
    for job in eligible_jobs:
        logger.info(f"Analisando compatibilidade para: {job.get('titulo')} na {job.get('empresa')}...")
        analysis = analyzer.analyze(job)
        job["analysis"] = analysis
        job["score"] = analysis.compatibilidade.score
        analyzed_jobs.append(job)

    # Ordena por score decrescente
    analyzed_jobs.sort(key=lambda x: x["score"], reverse=True)

    notified_count = 0
    for job in analyzed_jobs:
        analysis = job["analysis"]
        if dry_run:
            logger.info(f"[DRY-RUN] Notificação simulada: {job.get('titulo')} ({job.get('empresa')}) - Score: {job['score']}")
            logger.info(f"          Link: {job.get('url')}")
            logger.info(f"          Pontos Fortes: {analysis.compatibilidade.pontos_fortes}")
            notified_count += 1
        else:
            sucesso = notifier.send_job_notification(job, analysis)
            if sucesso:
                db.register_notified_job(job)
                notified_count += 1
            else:
                logger.warning(f"Falha ao enviar e-mail para a vaga: {job.get('titulo')}")

    if not dry_run:
        db.register_execution_run(
            today_str, "SUCESSO", len(all_raw_jobs), filtered_count, notified_count,
            f"Notificadas {notified_count} novas vagas com sucesso."
        )

    logger.info(f"=== Execução concluída com sucesso. {notified_count} vagas notificadas. ===")

def main():
    args = parse_args()
    if args.test_notify:
        logger.info("Disparando e-mail de teste de conectividade...")
        notifier = EmailNotifier(
            smtp_user=settings.GMAIL_SENDER_EMAIL,
            smtp_pass=settings.GMAIL_APP_PASSWORD,
            target_email=settings.NOTIFICATION_TARGET_EMAIL
        )
        ok = notifier.send_test_notification()
        if ok:
            logger.info("✅ E-mail de teste enviado com sucesso! Verifique sua caixa de entrada em " + settings.NOTIFICATION_TARGET_EMAIL)
        else:
            logger.error("❌ Falha no envio do e-mail de teste. Verifique GMAIL_SENDER_EMAIL e GMAIL_APP_PASSWORD no seu .env")
        return

    run_pipeline(dry_run=args.dry_run, force=args.force)

if __name__ == "__main__":
    main()
