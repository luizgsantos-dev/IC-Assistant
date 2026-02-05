# IC-UFMT Smart Agent

Sistema de chat web baseado em RAG (Retrieval-Augmented Generation) para o Instituto de Computação (IC) da Universidade Federal de Mato Grosso (UFMT). O agente serve como uma "fonte unica de verdade", fornecendo respostas precisas e baseadas em documentos para questoes burocraticas e academicas.

## Objetivos Principais

- **Otimizacao Burocratica:** Automatizar respostas sobre processos de compras, solicitacoes de material e procedimentos oficiais para servidores.
- **Empoderamento do Discente:** Fornecer orientacao 24/7 sobre processos academicos como aproveitamento de materias, prazos de matricula e requisitos de graduacao.
- **Centralizacao de Informacoes:** Atuar como repositorio dinamico para historico do IC, projetos de pesquisa (ex: laboratorio FATA), e eventos passados (ex: IC-NEXUS).

## Arquitetura

```
[Interface Web] <-> [API FastAPI] <-> [Sistema RAG] <-> [Vector DB (ChromaDB)]
                                            |
                                     [Documentos/Pasta]
                                            |
                                      [LLM Provider]
```

## Funcionalidades

1. **Chat Interativo:** Interface web para fazer perguntas
2. **RAG com Zero Alucinacao:** Busca nos documentos fornecidos antes de responder, garantindo respostas baseadas apenas em fontes verificadas
3. **Upload de Documentos:** Colocar arquivos na pasta `data/` atualiza automaticamente o conhecimento
4. **Multiplos Formatos:** Suporte a PDF, TXT, MD
5. **Respostas Contextualizadas:** A IA so usa informacoes dos documentos fornecidos
6. **Multiplos Provedores de LLM:** Suporte para OpenAI, Anthropic, Ollama e Google Gemini (recomendado)

## Stack Tecnica

| Componente | Tecnologia | Funcao |
|------------|------------|--------|
| LLM Core | Gemini 1.5 Flash (recomendado) | Processamento de linguagem natural de alta velocidade com janela de contexto de 1M+ tokens |
| Camada Logica | RAG | Garante que a IA responda apenas com base em PDFs e resolucoes institucionais |
| Backend | FastAPI | API REST de alta performance |
| Vector DB | ChromaDB | Armazenamento e busca semantica de embeddings |
| Motor de Seguranca | Zero-Hallucination Guardrails | Prompt especializado para evitar alucinacoes |

---

## Guia de Instalacao Passo a Passo

### Pre-requisitos

Antes de comecar, certifique-se de ter instalado:

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)
- Git (para clonar o repositorio)

### Passo 1: Clonar o Repositorio

```bash
git clone https://github.com/luizgsantos-dev/IC-Assistant.git
cd IC-Assistant
```

### Passo 2: Criar Ambiente Virtual

O ambiente virtual isola as dependencias do projeto.

**No Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**No Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**No Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

Voce sabera que o ambiente esta ativo quando ver `(venv)` no inicio do prompt.

### Passo 3: Instalar Dependencias

```bash
cd backend
pip install -r requirements.txt
```

Isso instalara todos os pacotes necessarios: FastAPI, LangChain, ChromaDB, etc.

### Passo 4: Obter Chave de API do Gemini

1. Acesse [Google AI Studio](https://aistudio.google.com/)
2. Faca login com sua conta Google
3. Clique em "Get API Key" ou "Criar chave de API"
4. Copie a chave gerada

### Passo 5: Configurar Variaveis de Ambiente

Volte para a raiz do projeto e copie o arquivo de exemplo:

```bash
cd ..
cp .env.example .env
```

Edite o arquivo `.env` com seu editor preferido:

```bash
nano .env
# ou
code .env
# ou
vim .env
```

Configure as seguintes variaveis:

```env
# Provedor de LLM (recomendado: gemini)
LLM_PROVIDER=gemini

# Sua chave de API do Google
GOOGLE_API_KEY=sua_chave_aqui_do_passo_4

# Modelo do Gemini
GEMINI_MODEL=gemini-1.5-flash

# Provedor de Embeddings (huggingface e gratuito e local)
EMBEDDING_PROVIDER=huggingface
```

### Passo 6: Adicionar Documentos

Coloque seus documentos na pasta `backend/data/`:

```bash
# Criar pasta se nao existir
mkdir -p backend/data

# Copiar seus documentos (PDFs, TXTs, MDs)
cp /caminho/para/seus/documentos/*.pdf backend/data/
```

**Tipos de documentos suportados:**
- `.pdf` - Documentos PDF
- `.txt` - Arquivos de texto
- `.md` - Arquivos Markdown

**Documentos recomendados para o IC-UFMT:**
- Resolucoes CONSEP e UFMT
- Manuais de procedimentos administrativos (SEI)
- Regulamentos academicos
- Calendario academico

### Passo 7: Iniciar o Backend

```bash
cd backend
python -m app.main
```

Ou usando uvicorn diretamente (com reload automatico):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Voce vera uma mensagem indicando que o servidor esta rodando:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Passo 8: Abrir o Frontend

**Opcao A - Abrir diretamente no navegador:**

Abra o arquivo `frontend/index.html` diretamente no navegador.

**Opcao B - Servir via servidor HTTP (recomendado):**

Em um novo terminal (mantenha o backend rodando):

```bash
cd frontend
python3 -m http.server 8080
```

Acesse `http://localhost:8080` no navegador.

### Passo 9: Testar o Sistema

1. Abra o navegador em `http://localhost:8080`
2. Digite uma pergunta no campo de texto, por exemplo:
   - "Qual e o processo para aproveitamento de materias?"
   - "Como solicito material de escritorio pelo SEI?"
3. Aguarde a resposta baseada nos documentos fornecidos

---

## Configuracoes Alternativas de LLM

### Usando OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sua_chave_openai
OPENAI_MODEL=gpt-4o-mini
```

### Usando Anthropic (Claude)

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sua_chave_anthropic
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

### Usando Ollama (Local/Gratuito)

1. Instale o Ollama: https://ollama.ai/
2. Baixe um modelo: `ollama pull llama3.2`
3. Configure:

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

---

## Estrutura do Projeto

```
IC-Assistant/
|-- backend/
|   |-- app/
|   |   |-- __init__.py
|   |   |-- main.py              # FastAPI app principal
|   |   |-- models/
|   |   |   |-- chat.py          # Modelos Pydantic
|   |   |-- services/
|   |   |   |-- rag_service.py   # Servico RAG principal com prompt IC-UFMT
|   |   |   |-- document_processor.py  # Processamento de documentos
|   |   |   |-- llm_provider.py  # Abstracao para multiplos LLMs
|   |   |-- routes/
|   |       |-- chat.py          # Endpoints de chat
|   |       |-- documents.py     # Endpoints de documentos
|   |-- data/                    # Pasta para documentos (monitorada)
|   |-- vectorstore/             # Banco vetorial (gerado automaticamente)
|   |-- requirements.txt
|-- frontend/
|   |-- index.html
|   |-- app.js
|   |-- styles.css
|-- .env.example
|-- .gitignore
|-- README.md
```

---

## API Endpoints

### POST `/chat`
Envia uma mensagem e recebe uma resposta baseada nos documentos.

**Request:**
```json
{
  "message": "Qual e o processo para aproveitamento de materias?",
  "conversation_history": null
}
```

**Response:**
```json
{
  "response": "De acordo com a Resolucao CONSEP no XX/XXXX...",
  "sources": ["regulamento_academico.pdf", "resolucao_aproveitamento.pdf"]
}
```

### GET `/documents`
Lista os documentos disponiveis na pasta de dados.

### POST `/documents/refresh`
Forca o reprocessamento de todos os documentos.

### GET `/api/health`
Verifica a saude da API.

---

## Solucao de Problemas

### Erro: "GOOGLE_API_KEY environment variable is required"
- Verifique se o arquivo `.env` existe na raiz do projeto
- Verifique se a variavel `GOOGLE_API_KEY` esta configurada corretamente
- Reinicie o servidor apos modificar o `.env`

### Erro: "No documents found to process"
- Adicione documentos (PDF, TXT, MD) na pasta `backend/data/`
- Verifique se os arquivos tem extensao suportada

### Erro de conexao no frontend
- Verifique se o backend esta rodando na porta 8000
- Verifique se a variavel `API_BASE_URL` em `frontend/app.js` esta correta

### Embeddings demorando muito
- Na primeira execucao, o modelo de embeddings sera baixado (pode demorar alguns minutos)
- Use `EMBEDDING_PROVIDER=huggingface` para embeddings gratuitos e locais

---

## Guardrails de Zero Alucinacao

O sistema implementa guardrails rigorosos para evitar alucinacoes:

1. **Prompt Especializado:** O prompt do sistema instrui a IA a responder APENAS com base no contexto fornecido.
2. **Citacao de Fontes:** Todas as respostas incluem as fontes documentais utilizadas.
3. **Resposta de Incerteza:** Quando a informacao nao esta nos documentos, o sistema responde explicitamente que nao encontrou a informacao.
4. **Formato Estruturado:** Para processos administrativos, o formato O QUE, ONDE, COMO, POR QUE garante respostas completas e verificaveis.

---

## Por Que Isso Importa

Em um ambiente universitario, "quase certo" nao e bom o suficiente para burocracia. Um erro em um prazo academico ou codigo de compras pode causar meses de atrasos. Este agente:

- **Reduz Erros Humanos:** Garante que todos sigam a versao mais recente dos regulamentos.
- **Aumenta Eficiencia:** Libera a secretaria para tarefas de alto valor em vez de responder FAQs repetitivas.
- **Promove Transparencia:** Torna as regras institucionais acessiveis e compreensiveis para toda a comunidade.

---

## Licenca

Este projeto e desenvolvido para uso institucional do IC-UFMT.
