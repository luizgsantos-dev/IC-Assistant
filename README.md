# Assistente IA para IC

Sistema de chat web baseado em RAG (Retrieval-Augmented Generation) que permite ao usuário alimentar documentos e a IA responder perguntas sobre processos burocráticos, aproveitamento de matérias, projetos de pesquisa, eventos e calendário acadêmico do IC, usando apenas as informações fornecidas.

## 🏗️ Arquitetura

```
[Interface Web] ↔ [API FastAPI] ↔ [Sistema RAG] ↔ [Vector DB (ChromaDB)]
                                         ↓
                                  [Documentos/Pasta]
                                         ↓
                                    [LLM Provider]
```

## ✨ Funcionalidades

1. **Chat Interativo**: Interface web para fazer perguntas
2. **RAG**: Busca nos documentos fornecidos antes de responder
3. **Upload de Documentos**: Colocar arquivos na pasta `data/` atualiza automaticamente o conhecimento
4. **Múltiplos Formatos**: Suporte a PDF, TXT, MD
5. **Respostas Contextualizadas**: A IA só usa informações dos documentos fornecidos
6. **Múltiplos Provedores de LLM**: Suporte para OpenAI, Anthropic e Ollama

## 🛠️ Tecnologias

- **Python 3.10+**
- **FastAPI**: API backend
- **LangChain**: Orquestração RAG
- **ChromaDB**: Banco de dados vetorial
- **OpenAI/Anthropic/Ollama**: Provedores de LLM
- **HTML/CSS/JavaScript**: Frontend simples

## 📋 Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)
- (Opcional) Ollama instalado localmente, se usar Ollama como provedor de LLM

## 🚀 Instalação

1. **Clone ou baixe o projeto**

2. **Crie um ambiente virtual (recomendado)**:
```bash
python -m venv venv
```

3. **Ative o ambiente virtual**:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

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
   - Escolha entre `openai`, `anthropic` ou `ollama`
   - Configure as chaves de API correspondentes
   - Se usar Ollama, certifique-se de que está rodando localmente

## 📝 Configuração

Edite o arquivo `.env` com suas configurações:

### Provedor de LLM

Escolha um dos seguintes:

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
│   │   │   ├── rag_service.py   # Serviço RAG principal
│   │   │   ├── document_processor.py  # Processamento de documentos
│   │   │   └── llm_provider.py  # Abstração para múltiplos LLMs
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
  "response": "Baseado nos documentos fornecidos...",
  "sources": ["documento1.pdf", "documento2.txt"]
}
```

### GET `/documents`
Lista todos os documentos na pasta `data/`.

### POST `/documents/refresh`
Força a reprocessamento de todos os documentos e atualização do vectorstore.

## 🔍 Troubleshooting

### Erro: "OPENAI_API_KEY environment variable is required"
- Certifique-se de ter configurado o arquivo `.env` com suas chaves de API
- Verifique se o arquivo `.env` está na raiz do projeto `ic-assistant/`

### Erro: "Vectorstore not initialized"
- Certifique-se de que a pasta `backend/data/` existe e contém documentos
- Tente executar `/documents/refresh` para reprocessar os documentos

### Frontend não conecta com o backend
- Verifique se o backend está rodando
- Verifique se a URL no `frontend/app.js` corresponde à porta do backend
- Verifique as configurações de CORS (por padrão está permitindo todas as origens)

### Ollama não funciona
- Certifique-se de que o Ollama está instalado e rodando
- Verifique se o modelo especificado em `OLLAMA_MODEL` está disponível
- Teste acessando `http://localhost:11434` no navegador

## 📚 Próximos Passos

1. Adicionar mais formatos de arquivo (DOCX, etc.)
2. Implementar autenticação
3. Adicionar histórico de conversação persistente
4. Melhorar a interface do frontend
5. Adicionar métricas e monitoramento

## 📄 Licença

Este projeto é fornecido como está, para uso educacional e de pesquisa.
