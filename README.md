# IC-UFMT Smart Agent

Assistente inteligente baseado em RAG (Retrieval-Augmented Generation) para o Instituto de Computacao da Universidade Federal de Mato Grosso. O sistema responde perguntas sobre processos academicos, administrativos e informacoes institucionais usando apenas o conteudo dos documentos fornecidos.

## Funcionalidades

- **Chat com streaming**: Respostas em tempo real token-a-token via SSE
- **Multiplos provedores de LLM**: OpenAI, Anthropic, Google Gemini e Ollama
- **Auto-deteccao de provedor**: Detecta automaticamente qual LLM usar baseado nas chaves configuradas
- **Historico de conversa**: Mantem contexto entre mensagens
- **Interface moderna**: Design inspirado no ChatGPT
- **Zero alucinacao**: Responde apenas com base nos documentos fornecidos
- **Prompt em portugues**: Otimizado para o contexto do IC-UFMT

## Arquitetura

```
[Frontend - Chat UI]
        |
        | HTTP / SSE
        v
[FastAPI Backend]
        |
        +-- Config Manager (auto-detect LLM)
        |
        +-- RAG Service
        |       |
        |       +-- LLM Provider (OpenAI/Anthropic/Gemini/Ollama)
        |       |
        |       +-- ChromaDB (Vector Store)
        |
        +-- Document Processor
                |
                +-- PDF/TXT/MD files
```

## Inicio Rapido

### 1. Clone o repositorio

```bash
git clone https://github.com/luizgsantos-dev/IC-Assistant.git
cd IC-Assistant
```

### 2. Crie o ambiente virtual

```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instale as dependencias

```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure o ambiente

```bash
cd ..
cp .env.example .env
```

Edite o arquivo `.env` e configure pelo menos uma chave de API:

```env
# Escolha um dos provedores:

# Google Gemini (recomendado - rapido e economico)
GOOGLE_API_KEY=sua_chave_aqui

# Ou OpenAI
OPENAI_API_KEY=sk-...

# Ou Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Ou Ollama (local, gratuito)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### 5. Adicione documentos

Coloque seus documentos (PDF, TXT, MD) na pasta `backend/data/`:

```bash
cp /seus/documentos/*.pdf backend/data/
```

### 6. Inicie o servidor

```bash
cd backend
python -m app.main
```

O servidor estara disponivel em `http://localhost:8000`

### 7. Abra o frontend

Abra `frontend/index.html` no navegador, ou sirva com um servidor HTTP:

```bash
cd frontend
python -m http.server 8080
```

Acesse `http://localhost:8080`

## Provedores de LLM

### Auto-deteccao

O sistema detecta automaticamente qual provedor usar baseado nas chaves de API configuradas.

**Ordem de prioridade**: OpenAI > Anthropic > Gemini > Ollama

### Forcando um provedor

Defina `LLM_PROVIDER` no `.env`:

```env
LLM_PROVIDER=gemini
```

### Configuracoes por provedor

| Provedor | Variaveis | Modelos recomendados |
|----------|-----------|---------------------|
| OpenAI | `OPENAI_API_KEY`, `OPENAI_MODEL` | gpt-4o-mini, gpt-4o |
| Anthropic | `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` | claude-3-5-sonnet-20241022 |
| Gemini | `GOOGLE_API_KEY`, `GEMINI_MODEL` | gemini-1.5-flash, gemini-1.5-pro |
| Ollama | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` | llama3.2, mistral, phi3 |

## API Endpoints

### Chat

**POST /chat** - Resposta sincrona
```json
{
    "message": "Como funciona o aproveitamento de materias?",
    "conversation_history": [
        {"role": "user", "content": "Ola"},
        {"role": "assistant", "content": "Ola! Como posso ajudar?"}
    ]
}
```

**POST /chat/stream** - Streaming via SSE
- Mesma estrutura de request
- Retorna eventos: `sources`, `token`, `done`, `error`

### Documentos

**GET /documents** - Lista documentos carregados

**POST /documents/refresh** - Reprocessa documentos

**GET /documents/info** - Informacoes do provedor

### Health

**GET /api/health** - Status do sistema

## Estrutura do Projeto

```
IC-Assistant/
├── backend/
│   ├── app/
│   │   ├── config.py           # Config + auto-detect
│   │   ├── main.py             # FastAPI + DI
│   │   ├── models/
│   │   │   └── chat.py         # Modelos Pydantic
│   │   ├── routes/
│   │   │   ├── chat.py         # /chat + /chat/stream
│   │   │   └── documents.py    # /documents
│   │   └── services/
│   │       ├── llm_provider.py # Factory LLM + streaming
│   │       ├── rag_service.py  # RAG + historico
│   │       └── document_processor.py
│   ├── data/                   # Seus documentos aqui
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js                  # SSE + markdown
├── .env.example
└── README.md
```

## Tecnologias

- **Backend**: FastAPI, LangChain 0.3.x, ChromaDB 0.6.x
- **LLM**: OpenAI, Anthropic, Google Gemini, Ollama
- **Embeddings**: HuggingFace sentence-transformers
- **Frontend**: HTML/CSS/JS, marked.js, SSE
- **Documentos**: pypdf, watchdog

## Desenvolvimento

### Primeira execucao

Na primeira execucao, o modelo de embeddings sera baixado (~90MB). Isso pode demorar alguns minutos.

### Atualizando documentos

Os documentos sao monitorados automaticamente. Adicione/remova arquivos em `backend/data/` e o sistema atualizara o indice.

Voce tambem pode forcar uma atualizacao via API ou pelo botao no frontend.

### Logs

O sistema loga informacoes uteis no console, incluindo:
- Provedor de LLM detectado
- Documentos processados
- Erros de query

## Troubleshooting

### "No LLM provider available"
Configure pelo menos uma chave de API no arquivo `.env`.

### "OPENAI_API_KEY is required"
Voce definiu `LLM_PROVIDER=openai` mas nao configurou a chave. Configure a chave ou remova `LLM_PROVIDER` para auto-detectar.

### Embeddings demorando muito
Na primeira execucao, o modelo HuggingFace sera baixado. Aguarde o download completar.

### Frontend nao conecta
Verifique se o backend esta rodando em `http://localhost:8000`. Se estiver em outra porta, edite `API_BASE_URL` em `frontend/app.js`.

## Licenca

Desenvolvido para uso institucional do IC-UFMT.
