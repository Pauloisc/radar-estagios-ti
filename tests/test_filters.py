import pytest
from filters.area_filter import AreaFilter
from filters.location_filter import LocationFilter
from filters.schedule_filter import ScheduleFilter

def test_area_filter_aceita_estagio_ti():
    vaga = {
        "titulo": "Estágio em Desenvolvimento de Software React",
        "descricao": "Atuação com desenvolvimento frontend utilizando React, Git e testes.",
        "tipo_contrato": "Estágio"
    }
    passou, motivo = AreaFilter.filter(vaga)
    assert passou is True

def test_area_filter_descarta_vaga_fora_ti():
    vaga = {
        "titulo": "Estágio em Administração Financeira",
        "descricao": "Controle de fluxo de caixa e notas fiscais.",
        "tipo_contrato": "Estágio"
    }
    passou, motivo = AreaFilter.filter(vaga)
    assert passou is False
    assert "fora da área" in motivo

def test_area_filter_descarta_efetivo_pleno():
    vaga = {
        "titulo": "Desenvolvedor Pleno Python",
        "descricao": "Desenvolvimento backend com Django.",
        "tipo_contrato": "CLT"
    }
    passou, motivo = AreaFilter.filter(vaga)
    assert passou is False

def test_location_filter_aceita_presencial_aracaju():
    vaga = {
        "titulo": "Estágio TI",
        "cidade": "Aracaju",
        "estado": "SE",
        "modalidade": "presencial"
    }
    passou, motivo = LocationFilter.filter(vaga)
    assert passou is True

def test_location_filter_descarta_presencial_fora_aracaju():
    vaga = {
        "titulo": "Estágio TI",
        "cidade": "São Paulo",
        "estado": "SP",
        "modalidade": "presencial"
    }
    passou, motivo = LocationFilter.filter(vaga)
    assert passou is False
    assert "fora de Aracaju/SE" in motivo

def test_location_filter_descarta_presencial_outra_cidade_sergipe():
    vaga = {
        "titulo": "Estágio Suporte",
        "cidade": "Itabaiana",
        "estado": "SE",
        "modalidade": "presencial"
    }
    passou, motivo = LocationFilter.filter(vaga)
    assert passou is False
    assert "fora de Aracaju/SE" in motivo

def test_location_filter_aceita_remoto_de_qualquer_lugar():
    vaga = {
        "titulo": "Estágio Frontend React",
        "cidade": "Florianópolis",
        "estado": "SC",
        "modalidade": "remoto"
    }
    passou, motivo = LocationFilter.filter(vaga)
    assert passou is True

def test_schedule_filter_descarta_turno_manha():
    vaga = {
        "titulo": "Estágio em Suporte",
        "descricao": "Horário de trabalho: 08:00 às 12:00 de segunda a sexta."
    }
    passou, motivo, info = ScheduleFilter.filter(vaga)
    assert passou is False
    assert "início a partir das 12:30" in motivo

def test_schedule_filter_aceita_turno_tarde():
    vaga = {
        "titulo": "Estágio em Desenvolvimento",
        "descricao": "Horário: das 13:00 às 19:00 com 30h semanais."
    }
    passou, motivo, info = ScheduleFilter.filter(vaga)
    assert passou is True
    assert info["turno"] == "tarde"

def test_schedule_filter_horario_nao_informado_mantem_com_alerta():
    vaga = {
        "titulo": "Estágio em Banco de Dados",
        "descricao": "Oportunidade para atuar com SQL e relatórios."
    }
    passou, motivo, info = ScheduleFilter.filter(vaga)
    assert passou is True
    assert "⚠️ Horário não informado" in info["alerta"]

def test_schedule_filter_aceita_horario_flexivel():
    vaga = {
        "titulo": "Estágio Python",
        "descricao": "Empresa de tecnologia com horários flexíveis e a combinar."
    }
    passou, motivo, info = ScheduleFilter.filter(vaga)
    assert passou is True
    assert info["flexivel"] is True
