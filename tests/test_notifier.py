import pytest
from unittest.mock import MagicMock
from notifiers.email_notifier import EmailNotifier
from analysis.schemas import AnaliseVagaCompleta, AnaliseCompatibilidade, PlanoAdaptacao

def test_email_notifier_formats_correctly():
    notifier = EmailNotifier("test@gmail.com", "app_pwd", "dest@gmail.com")
    # Mock do envio real SMTP para testar apenas a lógica e montagem
    notifier._send = MagicMock(return_value=True)

    job = {
        "titulo": "Estágio em TI",
        "empresa": "Tech Aracaju",
        "cidade": "Aracaju",
        "modalidade": "presencial",
        "url": "https://vaga.com.br/123"
    }

    analysis = AnaliseVagaCompleta(
        compatibilidade=AnaliseCompatibilidade(
            score=88,
            classificacao="🟢 Alta compatibilidade",
            justificativa_score="Excelente alinhamento com React e Git.",
            pontos_fortes=["React na Calculadora de Custo", "Monitoria UFS"],
            lacunas=["Docker básico"]
        ),
        plano_adaptacao=PlanoAdaptacao(
            ajustes_curriculo=["Destacar React no topo"],
            o_que_aprender=["Docker fundamentos"],
            dicas_candidatura=["Mencionar a Maratona SBC"]
        ),
        alertas=["⚠️ Horário a confirmar"],
        resumo_geral="Ótima vaga"
    )

    sucesso = notifier.send_job_notification(job, analysis)
    assert sucesso is True
    assert notifier._send.called

    # Verifica se os argumentos passados para _send contêm os elementos críticos
    call_args = notifier._send.call_args[0]
    subject = call_args[0]
    html = call_args[2]

    assert "Score 88" in subject
    assert "Tech Aracaju" in subject
    assert "https://vaga.com.br/123" in html
    assert "Calculadora de Custo" in html
