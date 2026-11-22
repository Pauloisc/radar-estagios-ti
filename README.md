# 🎯 Radar Autônomo de Estágios em TI (Aracaju & Remoto)

Sistema autônomo, agendado e baseado em IA que **busca diariamente vagas de estágio em Tecnologia da Informação**, analisa a compatibilidade técnica com o currículo de **Paulo Ítalo Santos Costa** e envia notificações detalhadas por e-mail com planos de adaptação e links diretos para candidatura, **sem nunca repetir uma vaga já notificada**.

---

## 📌 Principais Recursos

1. **Autonomia Total na Nuvem (GitHub Actions):** Roda todos os dias às **06:00 (horário de Aracaju/SE)** sem depender do computador pessoal ligado.
2. **Filtros Rigorosos e Inteligentes:**
   - **Localização:** Presencial/Híbrido estritamente em **Aracaju/SE** (descarta qualquer outra cidade ou interior). Vagas 100% remotas aceitas de todo o Brasil.
   - **Restrição de Horário (UFS Itabaiana):** O usuário só está em Aracaju a partir das 12:30/14:00. O sistema descarta turnos da manhã e período integral (40h). Mantém turnos vespertinos, noturnos, flexíveis ou sinaliza com alerta visual se o horário não for informado.
   - **Foco Estrito:** Apenas vagas de estágio na área de Tecnologia da Informação (desenvolvimento, dados, QA, suporte, DevOps, redes, segurança).
3. **Análise de Compatibilidade com Google Gemini:**
   - Score técnico (0 a 100).
   - Pontos fortes vinculados aos projetos e habilidades reais do Paulo (React, Java, Python, C, Maratona SBC, Monitoria).
   - Lacunas e plano de adaptação prático (ajustes no currículo sem inventar dados, o que estudar com materiais gratuitos e dicas de entrevista).
4. **Deduplicação de Vagas e Idempotência:**
   - Banco SQLite persistido em uma branch dedicada (`data`).
   - Normalização de títulos, empresas e URLs (remove parâmetros de rastreamento). Vagas iguais entre fontes diferentes não são duplicadas.
   - Dia sem vagas novas gera **exatamente um único e-mail** de resumo com estatísticas.
5. **Decisão sobre WhatsApp:** Conforme análise detalhada de custos e termos de serviço, o WhatsApp foi **descartado** devido ao risco de banimento de número por APIs não-oficiais ou custos de aprovação na Meta Cloud API. O **Gmail SMTP** atua como canal exclusivo e de alta fidelidade com layout HTML responsivo.

---

## 🛠️ Como Configurar e Ativar o Sistema

### Passo 1: Criar o Repositório Privado no GitHub
1. Crie um novo repositório no seu GitHub com o nome `radar-estagios-ti`.
2. **Defina a visibilidade como PRIVADA** (pois contém seu perfil e informações de contato).
3. Faça o push deste projeto para a branch principal (`main`):
   ```bash
   git init
   git add .
   git commit -m "feat: implementacao inicial do radar de estagios"
   git branch -M main
   git remote add origin https://github.com/SEU_USUARIO/radar-estagios-ti.git
   git push -u origin main
   ```

### Passo 2: Gerar a Senha de App do Gmail (Gmail SMTP)
O envio de e-mails usa o servidor SMTP seguro do Google:
1. Acesse sua Conta Google em [myaccount.google.com/security](https://myaccount.google.com/security).
2. Ative a **Verificação em duas etapas** (caso ainda não esteja ativada).
3. Na barra de busca superior da sua Conta Google, pesquise por **"Senhas de app"** (ou acesse a seção de Segurança > Verificação em duas etapas > Senhas de app).
4. Crie uma nova senha de app com o nome `Radar Estagios`.
5. O Google gerará um código de 16 letras (ex: `abcd efgh ijkl mnop`). **Copie e guarde essa chave**.

### Passo 3: Obter a Chave Gratuita da API do Google Gemini
1. Acesse o **Google AI Studio** em [aistudio.google.com](https://aistudio.google.com/).
2. Faça login com sua conta Google e clique em **"Get API key"**.
3. Crie uma nova chave gratuita e copie o token gerado.

### Passo 4: Cadastrar os Segredos no GitHub Actions
No seu repositório privado no GitHub:
1. Vá em **Settings** > **Secrets and variables** > **Actions**.
2. Clique em **New repository secret** e adicione:

| Nome do Secret | Valor |
|---|---|
| `GMAIL_SENDER_EMAIL` | Seu e-mail do Gmail que fará o envio |
| `GMAIL_APP_PASSWORD` | A Senha de App de 16 caracteres gerada no Passo 2 |
| `GEMINI_API_KEY` | A chave de API do Gemini gerada no Passo 3 |
| `NOTIFICATION_TARGET_EMAIL` | `pauloitalo061@gmail.com` |

3. Conceda permissão de escrita para o workflow salvar o histórico:
   - Vá em **Settings** > **Actions** > **General**.
   - Na seção **Workflow permissions**, selecione **"Read and write permissions"** e salve.

---

## 🚀 Execução Manual e Monitoramento

### Como disparar uma busca agora mesmo pelo GitHub:
1. Acesse o repositório no GitHub.
2. Clique na aba **Actions**.
3. No menu à esquerda, selecione **"Radar Diario de Estagios em TI"**.
4. Clique no botão **Run workflow** > Selecione a branch `main` e confirme.
5. O workflow iniciará imediatamente e você receberá as notificações no seu e-mail.

### Execução Local (Opcional):
Caso queira testar na sua máquina:
1. Crie um arquivo `.env` com base no `.env.example`.
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Teste o envio de e-mail:
   ```bash
   python main.py --test-notify
   ```
4. Simule uma execução completa sem enviar e-mails:
   ```bash
   python main.py --dry-run
   ```

---

## 📂 Estrutura de Arquivos

```
├── .github/workflows/daily.yml   # Workflow agendado (06:00 UTC-3)
├── config/
│   ├── profile.yaml              # Currículo estruturado do Paulo Ítalo
│   ├── config.yaml               # Parâmetros de busca, filtros e horários
│   └── settings.py               # Carregador de configurações
├── filters/
│   ├── area_filter.py            # Validação de estágio em TI
│   ├── location_filter.py        # Aracaju/SE ou Remoto Brasil
│   └── schedule_filter.py        # Validação do horário vespertino/noturno
├── analysis/
│   ├── gemini_analyzer.py        # Analisador de IA (Google Gemini)
│   └── schemas.py                # Validação estruturada da resposta
├── sources/
│   ├── base.py                   # Classe abstrata para novas fontes
│   ├── gupy.py                   # Busca de vagas públicas do Gupy
│   ├── remotes_aggregator.py     # Vagas remotas em TI
│   └── sergipe_local.py          # Monitor de oportunidades locais
├── storage/
│   ├── db.py                     # SQLite de histórico e idempotência
│   └── deduplicator.py           # Hash de desduplicação e limpeza de URLs
├── notifiers/
│   └── email_notifier.py         # Envio de e-mails em HTML via Gmail
├── tests/                        # Testes unitários com pytest
├── main.py                       # CLI e orquestrador
└── requirements.txt
```

---

## 🛡️ Resiliência e Consumo de Recursos
- **Estimativa de Minutos GitHub Actions:** Cada execução dura em média de 1 a 2 minutos. Com 30 dias no mês, o consumo gira em torno de 30 a 60 minutos mensais (muito abaixo do limite gratuito de 2.000 minutos do GitHub para contas gratuitas).
- **Branch `data`:** Mantém o histórico sem poluir o histórico de commits do código principal e previne que o GitHub pause workflows agendados por inatividade.
