# IC-UFMT Smart Agent

Sistema de chat web baseado em RAG (Retrieval-Augmented Generation) para o Instituto de Computação (IC) da Universidade Federal de Mato Grosso (UFMT). O agente serve como uma "fonte única de verdade", fornecendo respostas precisas e baseadas em documentos para questões burocráticas e acadêmicas.

## 🏛️ Objetivos Principais

- **Otimização Burocrática:** Automatizar respostas sobre processos de compras, solicitações de material e procedimentos oficiais para servidores.
- **Empoderamento do Discente:** Fornecer orientação 24/7 sobre processos acadêmicos como aproveitamento de matérias, prazos de matrícula e requisitos de graduação.
- **Centralização de Informações:** Atuar como repositório dinâmico para histórico do IC, projetos de pesquisa (ex: laboratório FATA), e eventos passados (ex: IC-NEXUS).

## 🏗️ Arquitetura

```
[Interface Web] ↔ [API FastAPI] ↔ [Sistema RAG] ↔ [Vector DB (ChromaDB)]
                                          ↓
                                   [Documentos/Pasta]
                                          ↓
                                     [LLM Provider]
```

## ✨ Funcionalidades

1. **Chat Interativo:** Interface web para fazer perguntas
2. **RAG com Zero Alucinação:** Busca nos documentos fornecidos antes de responder, garantindo respostas baseadas apenas em fontes verificadas
3. **Upload de Documentos:** Colocar arquivos na pasta `data/` atualiza automaticamente o conhecimento
4. **Múltiplos Formatos:** Suporte a PDF, TXT, MD
5. **Respostas Contextualizadas:** A IA só usa informações dos documentos fornecidos
6. **Múltiplos Provedores de LLM:** Suporte para OpenAI, Anthropic, Ollama e **Google Gemini** (recomendado)

## ⚙️ Stack Técnica

| Componente | Tecnologia | Função |
|------------|------------|--------|
| LLM Core | **Gemini 1.5 Flash** (recomendado) | Processamento de linguagem natural de alta velocidade com janela de contexto de 1M+ tokens |
| Camada Lógica | RAG | Garante que a IA responda apenas com base em PDFs e resoluções institucionais |
| Backend | FastAPI | API REST de alta performance |
| Vector DB | ChromaDB | Armazenamento e busca semântica de embeddings |
| Motor de Segurança | Zero-Hallucination Guardrails | Prompt especializado para evitar alucinações |

## 🛠️ Tecnologias

- **Python 3.10+**
- **FastAPI:** API backend
- **LangChain:** Orquestração RAG
- **ChromaDB:** Banco de dados vetorial
- **OpenAI/Anthropic/Ollama/Gemini:** Provedores de LLM
- **HTML/CSS/JavaScript:** Frontend simples

## 📋 Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)
- Chave de API do provedor de LLM escolhido (Google AI Studio recomendado para Gemini)
- (Opcional) Ollama instalado localmente, se usar Ollama como provedor de LLM

## 🚀 Instalação

1. **Clone ou baixe o projeto**

2. **Crie um ambiente virtual (recomendado)**:
```bash
python -m venv venv
```

3. **Ative o ambiente virtual**:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/activate`

4. **Instale as dependências**:
```bash
cd ic-assistant/backend
pip install -r requirements.txt
```

5. **Configure as variáveis de ambiente**:
```bash
# Copie o arquivo .env.example para .env
cp .env.example .env

# Edite o arquivo .env com suas configurações
```

6. **Configure o provedor de LLM no arquivo `.env`**:
   - Escolha entre `openai`, `anthropic`, `ollama` ou `gemini`
   - Configure as chaves de API correspondentes
   - Se usar Ollama, certifique-se de que está rodando localmente

## 📝 Configuração

Edite o arquivo `.env` com suas configurações:

### Provedor de LLM

Escolha um dos seguintes:

**Google Gemini (RECOMENDADO):**
```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-1.5-flash
```

**OpenAI:**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sua_chave_aqui
OPENAI_MODEL=gpt-3.5-turbo
```

**Anthropic:**
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sua_chave_aqui
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

**Ollama (local):**
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

### Embeddings

**OpenAI (recomendado se usar OpenAI para LLM):**
```env
EMBEDDING_PROVIDER=openai
```

**HuggingFace (gratuito, requer download do modelo):**
```env
EMBEDDING_PROVIDER=huggingface
HUGGINGFACE_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## 🎯 Uso

### 1. Adicionar Documentos

Coloque seus documentos (PDF, TXT, MD) na pasta `backend/data/`. O sistema irá:
- Processar automaticamente os documentos
- Criar embeddings e armazenar no ChromaDB
- Monitorar a pasta para atualizações automáticas

**Documentos recomendados para o IC-UFMT:**
- Resoluções CONSEP e UFMT
- Manuais de procedimentos administrativos (SEI)
- Regulamentos acadêmicos
- Calendário acadêmico
- Documentação de projetos de pesquisa

### 2. Iniciar o Backend

```bash
cd ic-assistant/backend
python -m app.main
```

Ou usando uvicorn diretamente:
```bash
cd ic-assistant/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

O servidor estará disponível em `http://localhost:8000`

### 3. Abrir o Frontend

Abra o arquivo `frontend/index.html` no seu navegador ou sirva via um servidor HTTP simples:

```bash
# Python 3
cd ic-assistant/frontend
python -m http.server 8080
```

Acesse `http://localhost:8080` no navegador.

**Nota**: Se o backend estiver em uma porta diferente, edite a variável `API_BASE_URL` no arquivo `frontend/app.js`.

### 4. Fazer Perguntas

Use a interface web para fazer perguntas sobre os documentos fornecidos. O sistema irá:
- Buscar informações relevantes nos documentos
- Gerar uma resposta baseada apenas no contexto encontrado
- Mostrar as fontes utilizadas

**Exemplos de perguntas:**
- "Qual é o processo para aproveitamento de matérias?"
- "Como solicito material de escritório pelo SEI?"
- "Quais são os requisitos para graduação?"
- "Qual é a resolução que rege o processo de compras?"

## 📁 Estrutura do Projeto

```
ic-assistant/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app principal
│   │   ├── models/
│   │   │   └── chat.py          # Modelos Pydantic
│   │   ├── services/
│   │   │   ├── rag_service.py   # Serviço RAG principal com prompt IC-UFMT
│   │   │   ├── document_processor.py  # Processamento de documentos
│   │   │   └── llm_provider.py  # Abstração para múltiplos LLMs (inclui Gemini)
│   │   └── routes/
│   │       ├── chat.py          # Endpoints de chat
│   │       └── documents.py     # Endpoints de documentos
│   ├── data/                    # Pasta para documentos (monitorada)
│   ├── vectorstore/             # Banco vetorial (gerado automaticamente)
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── .env.example
└── README.md
```

## 🔧 API Endpoints

### POST `/chat`
Envia uma mensagem e recebe uma resposta baseada nos documentos.

**Request:**
```json
{
  "message": "Qual é o processo para aproveitamento de matérias?",
  "conversation_history": null
}
```

**Response:**
```json
{
  "response": "De acordo com a Resolução CONSEP nº XX/XXXX...",
  "sources": ["regulamento_academico.pdf", "resolucao_aproveitamento.pdf"]
}
```

### GET `/documents`
Lista os documentos disponíveis na pasta de dados.

**Response:**
```json
{
  "documents": [
    {"filename": "regulamento_academico.pdf", "file_type": ".pdf", "processed": true},
    {"filename": "calendario_2024.txt", "file_type": ".txt", "processed": true}
  ]
}
```

### POST `/documents/refresh`
Força o reprocessamento de todos os documentos.

**Response:**
```json
{
  "status": "success",
  "message": "Documents processed and vectorstore updated"
}
```

### GET `/api/health`
Verifica a saúde da API.

**Response:**
```json
{
  "status": "healthy"
}
```

## 🔒 Guardrails de Zero Alucinação

O sistema implementa guardrails rigorosos para evitar alucinações:

1. **Prompt Especializado:** O prompt do sistema instrui a IA a responder APENAS com base no contexto fornecido.
2. **Citação de Fontes:** Todas as respostas incluem as fontes documentais utilizadas.
3. **Resposta de Incerteza:** Quando a informação não está nos documentos, o sistema responde explicitamente que não encontrou a informação.
4. **Formato Estruturado:** Para processos administrativos, o formato O QUÊ, ONDE, COMO, POR QUÊ garante respostas completas e verificáveis.

## 🚀 Por Que Isso Importa

Em um ambiente universitário, "quase certo" não é bom o suficiente para burocracia. Um erro em um prazo acadêmico ou código de compras pode causar meses de atrasos. Este agente:

- **Reduz Erros Humanos:** Garante que todos sigam a versão mais recente dos regulamentos.
- **Aumenta Eficiência:** Libera a secretaria para tarefas de alto valor em vez de responder FAQs repetitivas.
- **Promove Transparência:** Torna as regras institucionais acessíveis e compreensíveis para toda a comunidade.

## 📄 Licença

Este projeto é desenvolvido para uso institucional do IC-UFMT.
