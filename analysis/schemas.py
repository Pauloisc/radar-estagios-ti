from typing import List, Optional
from pydantic import BaseModel, Field

class AnaliseCompatibilidade(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Score de 0 a 100 de compatibilidade com o perfil")
    classificacao: str = Field(..., description="🟢 Alta compatibilidade, 🟡 Média compatibilidade ou 🔴 Baixa compatibilidade")
    justificativa_score: str = Field(..., description="Justificativa concisa da pontuação atribuída")
    pontos_fortes: List[str] = Field(default_factory=list, description="Habilidades e projetos do Paulo que combinam com a vaga")
    lacunas: List[str] = Field(default_factory=list, description="Requisitos solicitados que o usuário ainda não demonstra")

class PlanoAdaptacao(BaseModel):
    ajustes_curriculo: List[str] = Field(default_factory=list, description="Ajustes reais no currículo (sem inventar experiências)")
    o_que_aprender: List[str] = Field(default_factory=list, description="Tecnologias ausentes com cursos/materiais gratuitos recomendados")
    dicas_candidatura: List[str] = Field(default_factory=list, description="Estratégia para carta de apresentação e entrevista")

class AnaliseVagaCompleta(BaseModel):
    compatibilidade: AnaliseCompatibilidade
    plano_adaptacao: PlanoAdaptacao
    alertas: List[str] = Field(default_factory=list, description="Avisos sobre horários, prazos ou dados ausentes")
    resumo_geral: str = Field(..., description="Visão geral objetiva da oportunidade para o candidato")
