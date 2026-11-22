import re
from typing import Dict, Any, Tuple
from storage.deduplicator import normalize_text

class ScheduleFilter:
    """
    Filtro de Horário Crítico:
    - O usuário só está em casa entre 12:30 e 14:00 (estuda na UFS Itabaiana).
    - Horário de início do estágio deve ser >= 12:30.
    - Descartar turnos da manhã ou integral (8h/dia ou 40h/sem).
    - Aceitar tarde, noite, flexível.
    - Se não houver horário explícito, NÃO descartar: marcar com alerta.
    """

    HORA_MINIMA_INICIO_MINUTOS = 12 * 60 + 30  # 12:30 = 750 minutos

    @classmethod
    def _parse_time_to_minutes(cls, time_str: str) -> int:
        """Converte strings como '08:00', '8h', '13h30', '14:00' para minutos do dia."""
        time_str = time_str.strip().lower().replace("h", ":")
        if ":" not in time_str:
            time_str += ":00"
        parts = time_str.split(":")
        try:
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 and parts[1] else 0
            return h * 60 + m
        except ValueError:
            return 0

    @classmethod
    def filter(cls, job: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Retorna (aprovada, motivo, info_horario)
        onde info_horario contém:
        {
            'inicio': str,
            'fim': str,
            'turno': str,
            'alerta': str,
            'flexivel': bool
        }
        """
        texto = f"{job.get('horario', '')} {job.get('descricao', '')} {job.get('titulo', '')}".lower()
        texto_norm = normalize_text(texto)

        info = {
            "inicio": None,
            "fim": None,
            "turno": "desconhecido",
            "alerta": "",
            "flexivel": False
        }

        # 1. Checa flexibilidade
        if any(term in texto_norm for term in ["horario flexivel", "horarios flexiveis", "a combinar", "flexibilidade de horario"]):
            info["flexivel"] = True
            info["turno"] = "flexivel"
            return True, "Horário flexível ou a combinar.", info

        # 2. Heurística para horários no formato HH(:MM)? às/as/- HH(:MM)?
        # Ex: "13:00 às 18:00", "08h as 12h", "13h - 19h", "08:00 as 14:00"
        padrao_faixa = re.search(
            r"\b(\d{1,2}(?:[h:]\d{2})?)\s*(?:as|as|ate|a|-)\s*(\d{1,2}(?:[h:]\d{2})?)\b",
            texto
        )

        if padrao_faixa:
            ini_str, fim_str = padrao_faixa.groups()
            ini_min = cls._parse_time_to_minutes(ini_str)
            fim_min = cls._parse_time_to_minutes(fim_str)
            info["inicio"] = ini_str
            info["fim"] = fim_str

            # Se início for antes de 12:30 (ex: 8h, 9h, 10h)
            if ini_min < cls.HORA_MINIMA_INICIO_MINUTOS and ini_min > 300: # acima de 05:00
                info["turno"] = "manha" if fim_min <= 840 else "integral"
                return False, f"Incompatível com horário de estudo: início às {ini_str} (exige início a partir das 12:30).", info
            else:
                info["turno"] = "tarde" if ini_min >= cls.HORA_MINIMA_INICIO_MINUTOS else "noite"
                return True, f"Horário aprovado: {ini_str} às {fim_str}.", info

        # 3. Heurística por palavras-chave de turno
        if any(m in texto_norm for m in ["turno matutino", "periodo matutino", "manha", "pela manha", "turno da manha"]):
            info["turno"] = "manha"
            return False, "Incompatível: turno matutino (manhã).", info

        if any(m in texto_norm for m in ["integral", "40h semanais", "8h diarias"]):
            info["turno"] = "integral"
            return False, "Incompatível: carga horária integral.", info

        if any(m in texto_norm for m in ["vespertino", "turno da tarde", "periodo da tarde", "tarde"]):
            info["turno"] = "tarde"
            return True, "Aprovado: turno vespertino (tarde).", info

        if any(m in texto_norm for m in ["noturno", "turno da noite", "noite"]):
            info["turno"] = "noite"
            return True, "Aprovado: turno noturno.", info

        # 4. Caso o horário não seja informado no anúncio
        info["alerta"] = "⚠️ Horário não informado — confirmar com a empresa se permite início a partir das 12:30."
        return True, "Horário não informado explicitamente (vaga mantida com alerta).", info
