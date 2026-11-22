import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class EmailNotifier:
    """Responsável pela formatação e envio de e-mails via Gmail SMTP."""

    def __init__(self, smtp_user: str, smtp_pass: str, target_email: str):
        self.smtp_user = smtp_user
        self.smtp_pass = smtp_pass
        self.target_email = target_email
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587

    def _send(self, subject: str, text_content: str, html_content: str) -> bool:
        """Envia mensagem MIME multipart (texto e HTML)."""
        if not self.smtp_user or not self.smtp_pass:
            logger.error("Credenciais de e-mail (GMAIL_SENDER_EMAIL ou GMAIL_APP_PASSWORD) não configuradas.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Radar de Estágios TI <{self.smtp_user}>"
        msg["To"] = self.target_email

        part_text = MIMEText(text_content, "plain", "utf-8")
        part_html = MIMEText(html_content, "html", "utf-8")

        msg.attach(part_text)
        msg.attach(part_html)

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.sendmail(self.smtp_user, [self.target_email], msg.as_string())
            logger.info(f"E-mail enviado com sucesso para {self.target_email}: '{subject}'")
            return True
        except Exception as e:
            logger.error(f"Falha ao enviar e-mail: {e}")
            return False

    def send_test_notification(self) -> bool:
        """Envia um e-mail de teste de conectividade."""
        subject = "🧪 [Teste de Conectividade] Radar de Estágios TI"
        text = "Este é um e-mail de teste para validar suas credenciais SMTP do Gmail e canal de notificações."
        html = """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h2 style="color: #2b6cb0;">🧪 Teste de Conexão Bem-Sucedido!</h2>
            <p>Olá, Paulo Ítalo!</p>
            <p>Suas credenciais do Gmail SMTP foram validadas com sucesso. O sistema está pronto para enviar notificações diárias de vagas de estágio em TI.</p>
            <p style="font-size: 12px; color: #718096;">Radar de Estágios TI • Aracaju/SE</p>
        </div>
        """
        return self._send(subject, text, html)

    def send_job_notification(self, job: Dict[str, Any], analysis: Any) -> bool:
        """Envia a notificação detalhada de uma vaga nova aprovada."""
        comp = analysis.compatibilidade
        plano = analysis.plano_adaptacao

        score = comp.score
        icone = "🟢" if score >= 75 else ("🟡" if score >= 50 else "🔴")
        titulo_vaga = job.get("titulo", "Estágio em TI")
        empresa = job.get("empresa", "Empresa")
        cidade = job.get("cidade", "Aracaju")
        modalidade = job.get("modalidade", "Presencial").capitalize()

        subject = f"{icone} [Estágio TI] {titulo_vaga} — {empresa} ({cidade}, {modalidade}) — Score {score}"

        # Versão Texto Simples (Fallback)
        text_lines = [
            f"VAGA DE ESTÁGIO: {titulo_vaga}",
            f"Empresa: {empresa}",
            f"Local: {cidade} ({modalidade})",
            f"Score de Compatibilidade: {score}/100 ({comp.classificacao})",
            f"Link de Candidatura: {job.get('url')}",
            "",
            "ANÁLISE:",
            comp.justificativa_score,
            "",
            "PONTOS FORTES NO SEU PERFIL:",
            "\n".join(f"- {p}" for p in comp.pontos_fortes),
            "",
            "LACUNAS / OPORTUNIDADES:",
            "\n".join(f"- {l}" for l in comp.lacunas),
            "",
            "PLANO DE ADAPTAÇÃO DO CURRÍCULO:",
            "\n".join(f"- {a}" for a in plano.ajustes_curriculo),
            "",
            "O QUE APRENDER:",
            "\n".join(f"- {o}" for o in plano.o_que_aprender),
            "",
            "DICA PARA A CANDIDATURA:",
            "\n".join(f"- {d}" for d in plano.dicas_candidatura)
        ]
        text_content = "\n".join(text_lines)

        # Montagem dos alertas em HTML
        alertas_html = ""
        for alerta in analysis.alertas:
            alertas_html += f"""
            <div style="background-color: #fffaf0; border-left: 4px solid #dd6b20; padding: 10px; margin: 10px 0; font-size: 14px; color: #7b341e;">
                {alerta}
            </div>
            """

        pontos_fortes_html = "".join([f"<li>{p}</li>" for p in comp.pontos_fortes])
        lacunas_html = "".join([f"<li>{l}</li>" for l in comp.lacunas])
        ajustes_html = "".join([f"<li>{a}</li>" for a in plano.ajustes_curriculo])
        aprender_html = "".join([f"<li>{o}</li>" for o in plano.o_que_aprender])
        dicas_html = "".join([f"<li>{d}</li>" for d in plano.dicas_candidatura])

        cor_score = "#38a169" if score >= 75 else ("#d69e2e" if score >= 50 else "#e53e3e")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f7fafc; padding: 20px; margin: 0;">
            <div style="max-width: 650px; margin: auto; background-color: #ffffff; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow: hidden; border: 1px solid #e2e8f0;">
                
                <!-- Cabeçalho -->
                <div style="background-color: #1a202c; padding: 25px 20px; color: white;">
                    <span style="background-color: {cor_score}; color: white; padding: 4px 10px; border-radius: 20px; font-size: 13px; font-weight: bold; text-transform: uppercase;">
                        Score {score} • {comp.classificacao}
                    </span>
                    <h1 style="margin: 15px 0 5px 0; font-size: 22px; color: #ffffff;">{titulo_vaga}</h1>
                    <p style="margin: 0; color: #a0aec0; font-size: 15px;">{empresa} • 📍 {cidade} ({modalidade})</p>
                </div>

                <div style="padding: 25px;">
                    {alertas_html}

                    <!-- Botão Candidatar-se -->
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="{job.get('url')}" target="_blank" style="display: inline-block; background-color: #3182ce; color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">
                            🚀 Candidatar-se Agora no Site Oficial
                        </a>
                    </div>

                    <!-- Resumo -->
                    <div style="background-color: #edf2f7; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
                        <h3 style="margin-top: 0; font-size: 16px; color: #2d3748;">Visão Geral</h3>
                        <p style="margin-bottom: 0; font-size: 14px; color: #4a5568;">{comp.justificativa_score}</p>
                    </div>

                    <!-- Pontos Fortes e Lacunas -->
                    <div style="display: flex; flex-direction: column; gap: 15px; margin-bottom: 20px;">
                        <div style="background-color: #f0fff4; border: 1px solid #c6f6d5; border-radius: 6px; padding: 15px;">
                            <h4 style="margin-top: 0; color: #22543d; font-size: 15px;">🌟 Pontos Fortes no seu Perfil:</h4>
                            <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #276749;">
                                {pontos_fortes_html}
                            </ul>
                        </div>

                        <div style="background-color: #fffaf0; border: 1px solid #feebc8; border-radius: 6px; padding: 15px;">
                            <h4 style="margin-top: 0; color: #744210; font-size: 15px;">🎯 Lacunas e Pontos a Desenvolver:</h4>
                            <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #7b341e;">
                                {lacunas_html}
                            </ul>
                        </div>
                    </div>

                    <!-- Plano de Adaptação -->
                    <div style="border-top: 2px solid #edf2f7; padding-top: 20px; margin-bottom: 20px;">
                        <h3 style="font-size: 17px; color: #2d3748; margin-top: 0;">📋 Plano de Adaptação Recomendado</h3>

                        <h5 style="color: #4a5568; margin-bottom: 5px; font-size: 14px;">Ajustes Sugeridos no Currículo:</h5>
                        <ul style="padding-left: 20px; font-size: 13px; color: #4a5568;">{ajustes_html}</ul>

                        <h5 style="color: #4a5568; margin-bottom: 5px; font-size: 14px;">O que Estudar (Recursos Recomendados):</h5>
                        <ul style="padding-left: 20px; font-size: 13px; color: #4a5568;">{aprender_html}</ul>

                        <h5 style="color: #4a5568; margin-bottom: 5px; font-size: 14px;">Dica para a Entrevista / Carta:</h5>
                        <ul style="padding-left: 20px; font-size: 13px; color: #4a5568;">{dicas_html}</ul>
                    </div>

                    <!-- Rodapé com Link Direto -->
                    <div style="text-align: center; border-top: 1px solid #e2e8f0; padding-top: 15px;">
                        <p style="font-size: 12px; color: #a0aec0;">
                            Link da vaga: <a href="{job.get('url')}" style="color: #3182ce;">{job.get('url')}</a><br>
                            Radar de Estágios TI • Gerado de forma autônoma para Paulo Ítalo
                        </p>
                    </div>

                </div>
            </div>
        </body>
        </html>
        """
        return self._send(subject, text_content, html_content)

    def send_empty_notification(self, date_str: str, stats: Dict[str, int]) -> bool:
        """Envia um único e-mail diário avisando que nenhuma vaga nova foi encontrada."""
        subject = f"ℹ️ [Radar Estágios TI] Nenhuma nova vaga de estágio encontrada hoje ({date_str})"
        text = f"Relatório diário de {date_str}:\nNenhuma nova vaga de estágio em TI passou nos filtros.\nVagas coletadas: {stats.get('collected', 0)}.\nVagas descartadas: {stats.get('filtered', 0)}."
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
            <h3 style="color: #4a5568;">ℹ️ Nenhuma nova vaga encontrada hoje ({date_str})</h3>
            <p>Olá, Paulo Ítalo!</p>
            <p>O monitoramento de vagas de estágio em TI foi executado hoje e nenhuma nova oportunidade elegível foi identificada.</p>
            <div style="background-color: #f7fafc; padding: 15px; border-radius: 6px; font-size: 14px; color: #4a5568;">
                <strong>Estatísticas da Execução:</strong><br>
                - Total de oportunidades varridas nas fontes: {stats.get('collected', 0)}<br>
                - Vagas que não atenderam aos critérios (localização fora de Aracaju, turno matutino ou fora de TI): {stats.get('filtered', 0)}<br>
                - Novas vagas notificadas: 0
            </div>
            <p style="font-size: 12px; color: #a0aec0; margin-top: 20px;">
                O sistema continuará monitorando diariamente às 06:00 (horário de Aracaju).
            </p>
        </div>
        """
        return self._send(subject, text, html)

    def send_error_alert(self, error_message: str) -> bool:
        """Envia alerta de emergência caso haja quebra total de fontes ou falha no banco de dados."""
        subject = "🚨 [Alerta Crítico] Falha na Execução do Radar de Estágios TI"
        text = f"Ocorreu uma falha crítica na execução do radar:\n\n{error_message}"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #feb2b2; border-radius: 8px; background-color: #fff5f5;">
            <h3 style="color: #c53030;">🚨 Alerta de Falha Crítica na Execução</h3>
            <p>O Radar de Estágios TI encontrou um erro impeditivo durante a execução diária:</p>
            <pre style="background-color: #edf2f7; padding: 10px; border-radius: 4px; font-size: 12px; overflow-x: auto;">{error_message}</pre>
            <p style="font-size: 13px; color: #4a5568;">
                Verifique a aba 'Actions' no seu repositório do GitHub para visualizar os logs completos.
            </p>
        </div>
        """
        return self._send(subject, text, html)
