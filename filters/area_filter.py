import re
from typing import Dict, Any, Tuple
from storage.deduplicator import normalize_text

class AreaFilter:
    """Valida se a vaga é genuinamente de estágio e pertence à área de Tecnologia da Informação."""

    TERMOS_ESTAGIO = [
        "estagio", "estagio", "estagiario", "estagiaria", "intern", "internship"
    ]

    TERMOS_DESCARTE_NIVEL = [
        "jovem aprendiz", "menor aprendiz", "trainee", "clt", "pj",
        "analista pleno", "analista senior", "desenvolvedor pleno",
        "desenvolvedor senior", "engenheiro pleno", "engenheiro senior",
        "gerente", "coordenador", "diretor", "especialista"
    ]

    TERMOS_TI = [
        "ti", "tecnologia", "desenvolvimento", "desenvolvedor", "software",
        "programacao", "programador", "sistemas", "computacao", "web",
        "frontend", "front end", "backend", "back end", "fullstack", "full stack",
        "mobile", "android", "ios", "react", "python", "java", "javascript",
        "c++", "c#", "php", "ruby", "golang", "sql", "dados", "data", "bi",
        "business intelligence", "qa", "qualidade de software", "testes",
        "suporte", "helpdesk", "help desk", "servicedesk", "service desk",
        "infraestrutura", "redes", "devops", "cloud", "seguranca da informacao",
        "cyber", "banco de dados", "ia", "inteligencia artificial", "automacao"
    ]

    @classmethod
    def filter(cls, job: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Retorna (True, "") se a vaga for elegível.
        Retorna (False, motivo) se for descartada.
        """
        titulo = normalize_text(job.get("titulo", ""))
        descricao = normalize_text(job.get("descricao", ""))
        texto_completo = f"{titulo} {descricao}"

        # 1. Verifica se é estágio
        eh_estagio = any(termo in titulo for termo in cls.TERMOS_ESTAGIO)
        if not eh_estagio:
            # Verifica se o tipo de contrato informado explicitamente é estágio
            tipo_contrato = normalize_text(job.get("tipo_contrato", ""))
            if "estagio" in tipo_contrato or "intern" in tipo_contrato:
                eh_estagio = True
            elif "estagio" in descricao[:200]:
                eh_estagio = True

        if not eh_estagio:
            return False, "Vaga não identificada como estágio."

        # 2. Descarte por nível incompatível no título
        for termo_proibido in cls.TERMOS_DESCARTE_NIVEL:
            if termo_proibido in titulo and "estagio" not in titulo:
                return False, f"Vaga descartada por nível incompatível: '{termo_proibido}'."

        # 3. Verifica se pertence à área de TI
        pertence_ti = any(
            re.search(r"\b" + re.escape(termo) + r"\b", texto_completo)
            for termo in cls.TERMOS_TI
        )

        if not pertence_ti:
            return False, "Vaga fora da área de Tecnologia da Informação."

        return True, "Aprovada no filtro de área e nível."
