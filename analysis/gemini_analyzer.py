import json
import logging
from typing import Dict, Any, Optional
from analysis.schemas import AnaliseVagaCompleta, AnaliseCompatibilidade, PlanoAdaptacao

logger = logging.getLogger(__name__)

class JobAnalyzer:
    """
    Análise de vagas utilizando Google Gemini com fallback heurístico
    caso a chave não esteja configurada ou haja instabilidade.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash", profile: Dict[str, Any] = None):
        self.api_key = api_key
        self.model_name = model_name
        self.profile = profile or {}
        self.client = None

        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config={"response_mime_type": "application/json"}
                )
            except Exception as e:
                logger.warning(f"Não foi possível inicializar o cliente Google Generative AI: {e}")

    def analyze(self, job: Dict[str, Any]) -> AnaliseVagaCompleta:
        """Executa a análise de compatibilidade e gera o plano de adaptação."""
        if self.client:
            try:
                return self._analyze_with_gemini(job)
            except Exception as e:
                logger.error(f"Erro ao analisar vaga com Gemini: {e}. Acionando analisador de contingência.")

        return self._analyze_heuristic_fallback(job)

    def _build_prompt(self, job: Dict[str, Any]) -> str:
        prompt = f"""
Você é um especialista em recrutamento em Tecnologia e orientação de carreira para estudantes universitários.
Analise a vaga de estágio abaixo com base no currículo real do candidato.

# PERFIL DO CANDIDATO:
{json.dumps(self.profile, ensure_ascii=False, indent=2)}

# DADOS DA VAGA:
- Título: {job.get('titulo')}
- Empresa: {job.get('empresa')}
- Localidade: {job.get('cidade')} / {job.get('estado')} (Modalidade: {job.get('modalidade')})
- Horário Informado: {job.get('horario', 'Não informado')}
- Descrição Completa e Requisitos:
{job.get('descricao', '')}

# INSTRUÇÕES CRÍTICAS:
1. Calcule um score de 0 a 100 com honestidade técnica.
2. Identifique pontos fortes citando projetos e tecnologias específicas do Paulo (ex.: React, Java, C/Grafos, Monitoria, Lectria).
3. Aponte lacunas reais.
4. No plano de adaptação, NÃO invente experiências. Recomende como evidenciar o que ele já sabe e liste o que aprender com sugestões de materiais gratuitos de qualidade.
5. Se o horário for ambíguo ou não informado, inclua o alerta apropriado.
6. A saída DEVE ser estritamente em JSON compatível com o schema:
{{
  "compatibilidade": {{
    "score": 85,
    "classificacao": "🟢 Alta compatibilidade",
    "justificativa_score": "...",
    "pontos_fortes": ["..."],
    "lacunas": ["..."]
  }},
  "plano_adaptacao": {{
    "ajustes_curriculo": ["..."],
    "o_que_aprender": ["..."],
    "dicas_candidatura": ["..."]
  }},
  "alertas": ["..."],
  "resumo_geral": "..."
}}
"""
        return prompt

    def _analyze_with_gemini(self, job: Dict[str, Any]) -> AnaliseVagaCompleta:
        prompt = self._build_prompt(job)
        response = self.client.generate_content(prompt)
        data = json.loads(response.text)
        return AnaliseVagaCompleta.model_validate(data)

    def _analyze_heuristic_fallback(self, job: Dict[str, Any]) -> AnaliseVagaCompleta:
        """Gera análise determinística consistente caso a API de IA não esteja acessível."""
        titulo = job.get("titulo", "").lower()
        desc = job.get("descricao", "").lower()
        texto = f"{titulo} {desc}"

        score = 50
        pontos_fortes = []
        lacunas = []

        # Regras de afinidade técnica com o perfil do Paulo
        tags_paulo = {
            "react": ("React", "Experiência com React na Calculadora Portal da Fenda WEB"),
            "javascript": ("JavaScript", "Domínio de JS moderno e desenvolvimento web"),
            "python": ("Python", "Uso de Python e IA no Projeto Lectria"),
            "java": ("Java", "Projeto Portal da Fenda e fundamentos sólidos de POO"),
            "c": ("Linguagem C", "Conhecimento avançado em C e estruturas de dados na Maratona SBC"),
            "sql": ("SQL/Banco de Dados", "Bancos relacionais e modelagem"),
            "git": ("Git/GitHub", "Controle de versão e gestão com GitHub Projects")
        }

        for tag, (nome_tec, detalhe) in tags_paulo.items():
            if tag in texto:
                score += 8
                pontos_fortes.append(f"{nome_tec}: {detalhe}")

        if "estágio" in titulo:
            score += 10

        score = min(score, 95)
        if score >= 75:
            classificacao = "🟢 Alta compatibilidade"
        elif score >= 50:
            classificacao = "🟡 Média compatibilidade"
        else:
            classificacao = "🔴 Baixa compatibilidade"

        if not pontos_fortes:
            pontos_fortes.append("Formação em curso em Sistemas de Informação na UFS com base sólida em algoritmos e lógica.")
            lacunas.append("Tecnologias específicas do anúncio que não constam diretamente no currículo principal.")

        alertas = []
        if job.get("horario_alerta"):
            alertas.append(job.get("horario_alerta"))

        return AnaliseVagaCompleta(
            compatibilidade=AnaliseCompatibilidade(
                score=score,
                classificacao=classificacao,
                justificativa_score=f"Score calculado com base na presença de requisitos alinhados ao seu perfil acadêmico e projetos.",
                pontos_fortes=pontos_fortes,
                lacunas=lacunas
            ),
            plano_adaptacao=PlanoAdaptacao(
                ajustes_curriculo=[
                    "Destaque no topo do currículo os projetos práticos que utilizam as tecnologias exigidas na vaga.",
                    "Enfatize a monitoria em Programação 1 na UFS como diferencial de comunicação e resolução de problemas."
                ],
                o_que_aprender=[
                    "Revisar a documentação oficial das ferramentas exigidas na vaga.",
                    "Construir uma pequena prova de conceito (PoC) aplicando os requisitos específicos do anúncio."
                ],
                dicas_candidatura=[
                    "Na apresentação, cite a sua participação na Maratona de Programação e a facilidade em aprender novas stacks sob demanda."
                ]
            ),
            alertas=alertas,
            resumo_geral=f"Oportunidade de estágio em {job.get('empresa')} com foco em desenvolvimento e tecnologia."
        )
