from typing import Dict, Any, Tuple
from storage.deduplicator import normalize_text

class LocationFilter:
    """
    Filtro de Localização e Modalidade:
    - Presencial ou Híbrido: SOMENTE em Aracaju/SE. (Descartar qualquer outra cidade de SE ou do Brasil).
    - Remoto / Home Office: Permitido de qualquer localidade do Brasil.
    """

    CIDADES_PERMITIDAS = ["aracaju"]
    ESTADO_PERMITIDO = "se"

    @classmethod
    def filter(cls, job: Dict[str, Any]) -> Tuple[bool, str]:
        modalidade = normalize_text(job.get("modalidade", ""))
        cidade = normalize_text(job.get("cidade", ""))
        estado = normalize_text(job.get("estado", ""))
        titulo = normalize_text(job.get("titulo", ""))
        descricao = normalize_text(job.get("descricao", ""))

        # 1. Verifica se a vaga é 100% remota
        eh_remoto = (
            "remoto" in modalidade or "home office" in modalidade or "teletrabalho" in modalidade
            or "remoto" in cidade or "remoto" in titulo
            or "100% remoto" in descricao or "trabalho remoto" in descricao
        )

        # Se for explicitamente híbrido, NÃO é 100% remoto
        eh_hibrido = "hibrid" in modalidade or "hibrid" in descricao[:300]

        if eh_remoto and not eh_hibrido:
            return True, "Vaga remota aceita de qualquer localidade."

        # 2. Vaga Presencial ou Híbrida: Obrigatoriamente Aracaju/SE
        eh_aracaju = (
            any(c in cidade for c in cls.CIDADES_PERMITIDAS)
            or "aracaju" in titulo
            or "aracaju" in descricao[:300]
        )

        if not eh_aracaju:
            return False, f"Vaga presencial/híbrida fora de Aracaju/SE (Local detectado: '{cidade}/{estado}')."

        return True, "Vaga presencial/híbrida confirmada em Aracaju/SE."
