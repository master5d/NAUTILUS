---
title: ENERV Telegram Inbox — Working Workflow Documentation
date: 2026-05-05
updated: 2026-05-05
status: production
version: 4.0
tags: [n8n, telegram, gemini, enerv, workflow, obsidian, acl-transformer, semantic-labeling, wikilinks, rag, qdrant, hermes, multilingual]
---

# ENERV Telegram Inbox — Workflow Documentation

## Overview

Workflow принимает сообщения из Telegram и маршрутизирует их по двум веткам:

- **Ingest ветка** (любое сообщение без `/ask`): классифицирует через Gemini 2.5 Flash и сохраняет как Markdown файл в Obsidian vault с семантическими тегами и WikiLinks. Отправляет подтверждение.
- **RAG ветка** (сообщения начинающиеся с `/ask`): ищет релевантный контекст в Qdrant Vector DB, генерирует ответ через Gemini (HERMES), отправляет ответ с источниками.

```
                          ┌─ /ask ──→ Qdrant Search → Gemini RAG → Parse RAG → Send RAG Reply
Telegram Trigger → Route ┤
                          └─ other ──→ Gemini Router → Parse Response → ACL Transformer → Send Reply
```

**n8n URL:** https://n8n.synergify.com/workflow/hEDNe2LBdKACn9Z8  
**Workflow ID:** `hEDNe2LBdKACn9Z8`  
**Status:** Active (production)  
**n8n version:** 2.18.5  
**Total nodes:** 10  

---

## Architecture

### Pipeline

```
[User] --message--> [Telegram Bot]
                          |
                    [n8n Webhook]
                    enerv-inbox-tg
                          |
                       [Route]
                    IF node v2
                   starts with /ask?
                    /           \
               YES /             \ NO
                  /               \
        [Qdrant Search]     [Gemini 2.5 Flash]
        GET /context         semantic routing +
        q=user_query         tags + WikiLinks
               |                    |
        [Gemini RAG]         [Parse Response]
        HERMES answers        JSON extraction +
        from context          shell escaping
               |                    |
       [Parse RAG Response]  [ACL Transformer]
       extract answer+sources  node.js script →
               |               Obsidian .md file
       [Send RAG Reply]             |
       answer + sources      [Send Reply]
                             ✅ confirmation
```

---

## Nodes

### 1. Telegram Trigger

```json
{
  "type": "n8n-nodes-base.telegramTrigger",
  "typeVersion": 1.1,
  "webhookId": "enerv-inbox-tg",
  "parameters": {
    "updates": ["message"],
    "additionalFields": {}
  },
  "credentials": {
    "telegramApi": {
      "id": "A0PH9It6pypaBfiG",
      "name": "ENERV Telegram Bot"
    }
  }
}
```

Webhook URL: `https://n8n.synergify.com/webhook/enerv-inbox-tg`  
Listens: только `message` updates.  
Output: полный Telegram update object, в т.ч. `message.text`, `message.chat.id`.

---

### 2. Gemini Router

```json
{
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4.2,
  "parameters": {
    "method": "POST",
    "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
    "authentication": "genericCredentialType",
    "genericAuthType": "httpQueryAuth",
    "sendBody": true,
    "contentType": "raw",
    "rawContentType": "application/json"
  },
  "credentials": {
    "httpQueryAuth": {
      "id": "mlFnWbc900mBM7Yy",
      "name": "Gemini API Key"
    }
  }
}
```

**Model:** `gemini-2.5-flash` (через `v1beta` endpoint)  
**API Key source:** GCP project `gen-lang-client-0916449255` (AI Studio Default Project — free tier)  
**Key ID:** `d9709605-7a5e-4f5b-81a2-355d1cbe1d81`  
**Key restrictions:** только `generativelanguage.googleapis.com`, без IP restriction  

**Body expression (n8n):**
```
={{ JSON.stringify({
  contents: [{
    parts: [{
      text: "You are a semantic router for ENERV... Message: " +
            $('Telegram Trigger').first().json.message.text
    }]
  }],
  generationConfig: { responseMimeType: "application/json" }
}) }}
```

**Prompt:**
```
You are a semantic router for ENERV, a personal knowledge management system.
Analyze the message and return ONLY a valid JSON object with these exact fields:
- identity: short descriptive title (3-7 words)
- intent: one of knowledge_ingest | task_creation | log_entry
- context: one of Atlas/Notes | Atlas/Sources | Efforts/On | Calendar/Logs
- signal: one of low | medium | high
- tags: array of semantic tag strings (3-7 tags, lowercase, no spaces, use underscores)
- content: original message text, cleaned up; auto-link important concepts using [[WikiLinks]] notation

Return ONLY the JSON object. No markdown fences. No explanation.

Message: {text}
```

**Output facets example:**
```json
{
  "identity": "Taste-Skill for AI Vibe Coding",
  "intent": "knowledge_ingest",
  "context": "Atlas/Sources",
  "signal": "high",
  "tags": ["taste_skill", "ai_coding", "vibe_coding", "design_ai", "opensource"],
  "content": "Someone just solved the biggest problem with [[vibe coding]]. It's called [[Taste-Skill]]..."
}
```

---

### 3. Parse Response

```json
{
  "type": "n8n-nodes-base.code",
  "typeVersion": 2
}
```

**JS Code:**
```js
const body = $input.first().json;
const rawText = body.candidates[0].content.parts[0].text;
let facets;
try {
  facets = JSON.parse(rawText);
} catch (e) {
  const m = rawText.match(/```(?:json)?\s*([\s\S]+?)\s*```/);
  facets = JSON.parse(m ? m[1] : rawText.trim());
}
const chatId = $('Telegram Trigger').first().json.message.chat.id;
const jsonStr = JSON.stringify(facets);
const output = "'" + jsonStr.replace(/'/g, "'\\''") + "'";
return [{ json: { output, chatId, identity: facets.identity, context: facets.context, intent: facets.intent, signal: facets.signal, tags: facets.tags || [] } }];
```

Делает четыре вещи:
1. Парсит JSON из Gemini ответа (с fallback на regex strip для markdown-fenced responses)
2. Shell-safe escaping: `'` → `'\''` для передачи JSON как shell argument
3. Пробрасывает `chatId` из Telegram Trigger для последующего reply
4. Извлекает `tags` array для передачи в Send Reply

**Output fields:** `output` (shell-escaped JSON), `chatId`, `identity`, `context`, `intent`, `signal`, `tags`

---

### 4. ACL Transformer

```json
{
  "type": "n8n-nodes-base.code",
  "typeVersion": 2
}
```

**JS Code:**
```js
const { execSync } = require('child_process');
const cmd = 'node /home/node/Atlas/Scripts/acl_transformer.js ' + $json.output;
const result = execSync(cmd, { encoding: 'utf8', timeout: 30000 });
return [{ json: { result: result.trim(), ...$json } }];
```

> **Важно:** `child_process` разрешён через `NODE_FUNCTION_ALLOW_BUILTIN=child_process` в env контейнера.

Вызывает `/home/node/Atlas/Scripts/acl_transformer.js` — Node.js скрипт внутри контейнера.

**acl_transformer.js** (`/root/sovern/Atlas/Scripts/acl_transformer.js` на хосте):
```js
const fs = require("fs");
const path = require("path");

const inputData = process.argv[2];
let data;
try {
    data = JSON.parse(inputData);
} catch (e) {
    data = { content: inputData, intent: "general_ingest" };
}

const now = new Date();
const timestamp = now.toISOString().replace(/T/, " ").replace(/\..+/, "");
const fileId = now.toISOString().replace(/[-:T.Z]/g, "");

// Маппинг intent/context → путь в Obsidian
let contextPath = "Facets";
const intent = (data.intent || "").toLowerCase();
const context = (data.context || "").toLowerCase();

if (intent.includes("knowledge") || intent.includes("source") || context.includes("atlas")) {
    contextPath = "Atlas/Notes/Sources";
} else if (intent.includes("effort") || intent.includes("task") || intent.includes("project") || context.includes("efforts")) {
    contextPath = "Efforts/On";
} else if (intent.includes("log") || intent.includes("journal") || context.includes("calendar")) {
    contextPath = "Calendar/Logs";
}

const facets = {
    identity: data.identity || "unknown_entity",
    intent: data.intent || "informational",
    context: contextPath,
    signal: data.signal || "neutral",
    source: data.source || "n8n_stack",
    tags: Array.isArray(data.tags) ? data.tags : []
};

// tags в YAML: присутствует только если не пустой массив
const yamlTags = facets.tags.length > 0 ? "\ntags: [" + facets.tags.join(", ") + "]" : "";

// Создаёт .md файл с YAML frontmatter + WikiLinks в content
const template = `---
id: ${fileId}
timestamp: ${timestamp}
facets:
  identity: ${facets.identity}
  intent: ${facets.intent}
  context: ${facets.context}
  signal: ${facets.signal}
source: ${facets.source}${yamlTags}
---
# ${facets.identity}

${data.content || "No content provided"}
`;

const fileName = `${fileId}_${facets.identity.replace(/[^a-z0-9]/gi, "_")}.md`;
const fullDirPath = path.join("/home/node/obsidian", contextPath);
if (!fs.existsSync(fullDirPath)) fs.mkdirSync(fullDirPath, { recursive: true });
fs.writeFileSync(path.join(fullDirPath, fileName), template);
console.log(`Success: ${path.join(fullDirPath, fileName)}`);
```

**Context mapping:**

| Gemini intent/context | Obsidian path |
|---|---|
| `knowledge_ingest` / `Atlas/*` | `Atlas/Notes/Sources/` |
| `task_creation` / `Efforts/*` | `Efforts/On/` |
| `log_entry` / `Calendar/*` | `Calendar/Logs/` |
| остальное | `Facets/` |

**Output filename format:** `{ISO_timestamp}_{sanitized_identity}.md`  
Example: `20260505183334661_Massive_list_of_free_public_APIs.md`

---

### 5. Route (IF)

```json
{
  "type": "n8n-nodes-base.if",
  "typeVersion": 2,
  "parameters": {
    "conditions": {
      "conditions": [
        {
          "leftValue": "={{ $json.message.text }}",
          "rightValue": "/ask",
          "operator": { "type": "string", "operation": "startsWith" }
        }
      ],
      "combinator": "and"
    }
  }
}
```

Разделяет поток:
- **Output 0 (true)** — сообщения, начинающиеся с `/ask` → RAG ветка
- **Output 1 (false)** — остальные сообщения → Ingest ветка

---

### 6. Qdrant Search *(RAG ветка)*

```json
{
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4,
  "parameters": {
    "method": "GET",
    "url": "http://enerv-indexer:8080/context",
    "sendQuery": true,
    "queryParameters": {
      "parameters": [{ "name": "q", "value": "={{ $('Telegram Trigger').first().json.message.text.replace('/ask ', '') }}" }]
    }
  }
}
```

Обращается к `enerv-indexer` контейнеру по Docker internal DNS.  
Возвращает `{ context: "...", sources: ["file1.md", "file2.md", "file3.md"] }`.

---

### 7. Gemini RAG *(RAG ветка)*

```json
{
  "type": "n8n-nodes-base.httpRequest",
  "typeVersion": 4,
  "parameters": {
    "method": "POST",
    "url": "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
    "authentication": "genericCredentialType",
    "genericAuthType": "httpQueryAuth",
    "sendBody": true,
    "contentType": "raw",
    "rawContentType": "application/json"
  },
  "credentials": {
    "httpQueryAuth": { "id": "mlFnWbc900mBM7Yy", "name": "Gemini API Key" }
  }
}
```

**Body expression:**
```
={{ JSON.stringify({ contents: [{ parts: [{ text:
  "You are HERMES, the ENERV Sovereign Assistant. Answer the user's question using ONLY the context provided below. If the answer is not in the context, say: I don't have information about this in ENERV.\n\nContext Documents:\n"
  + $json.context +
  "\n\nUser Question:\n"
  + $('Telegram Trigger').first().json.message.text.replace('/ask ', '')
}] }] }) }}
```

Использует те же credentials что и Gemini Router. Ответ — plain text (без `responseMimeType: "application/json"`).

---

### 8. Parse RAG Response *(RAG ветка)*

```js
const body = $input.first().json;
const rawAnswer = body.candidates[0].content.parts[0].text;
const sources = $('Qdrant Search').first().json.sources || [];
const chatId = $('Telegram Trigger').first().json.message.chat.id;

// Escape for Telegram HTML mode
const esc = s => s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

// Clean source filenames: strip .md, replace _ and - with spaces
const cleanSrc = s => s.replace(/\.md$/,'').replace(/[_-]+/g,' ').trim();

const answer = esc(rawAnswer);
const sourcesText = sources.map(cleanSrc).map(esc).join(' · ');

return [{ json: { answer, sourcesText, chatId } }];
```

**Output fields:** `answer` (HTML-escaped текст), `sourcesText` (clean human-readable sources), `chatId`

> Sources не выводятся в reply — оставлены в output для возможного будущего использования.

---

### 9. Send RAG Reply *(RAG ветка)*

```json
{
  "type": "n8n-nodes-base.telegram",
  "typeVersion": 1.2,
  "parameters": {
    "chatId": "={{ $json.chatId }}",
    "text": "=💠 <b>ENERV Memory</b>\n\n{{ $json.answer }}",
    "additionalFields": {
      "parse_mode": "HTML",
      "appendAttribution": false
    }
  },
  "credentials": {
    "telegramApi": { "id": "A0PH9It6pypaBfiG", "name": "ENERV Telegram Bot" }
  }
}
```

**parse_mode: HTML** — обязательно. Telegram node v1.2 добавляет Markdown по умолчанию; filenames с underscores в sources ломают entity parsing. HTML mode изолирует dynamic content от markup.

**appendAttribution: false** — убирает `Sent via n8n` footer.

**Reply format:**
```
💠 ENERV Memory

MCP (Model Context Protocol) — стандарт интеграции AI-агентов с внешними инструментами...
```

---

### 10. Send Reply *(Ingest ветка)*

```json
{
  "type": "n8n-nodes-base.telegram",
  "typeVersion": 1.2,
  "parameters": {
    "chatId": "={{ $('Parse Response').first().json.chatId }}",
    "text": "=⚡ *ENERV Ingest*\n\n📌 `{{ $('Parse Response').first().json.identity }}`\n📁 `{{ $('Parse Response').first().json.context }}`\n🎯 `{{ $('Parse Response').first().json.intent }}` · `{{ $('Parse Response').first().json.signal }}`\n🏷️ {{ $('Parse Response').first().json.tags.map(t => '#' + t).join(' ') }}",
    "additionalFields": {
      "parse_mode": "Markdown",
      "appendAttribution": false
    }
  },
  "credentials": {
    "telegramApi": { "id": "A0PH9It6pypaBfiG", "name": "ENERV Telegram Bot" }
  }
}
```

> **Backtick-wrap обязателен** для `intent` и `signal`: значения содержат underscores (`knowledge_ingest`), которые Telegram Markdown v1 интерпретирует как italic и удаляет символ.

**Reply format:**
```
⚡ ENERV Ingest

📌 `Jane Street's extreme efficiency and future of work`
📁 `Atlas/Notes`
🎯 `knowledge_ingest` · `high`
🏷️ #janestreet #highfrequencytrading #organizationalefficiency
```

---

## Infrastructure

### Docker Containers

**Network:** `sovern-net` (bridge)  
**Compose file:** `/root/sovern/docker-compose.yml`  

| Container | Image | Role |
|---|---|---|
| `enerv-n8n` | `n8nio/n8n:latest` | Workflow engine |
| `enerv-indexer` | custom Python/FastAPI | Vector search API (`/context`, `/index`, `/search`) |
| `enerv-memory-db` | `qdrant/qdrant` | Vector database (port 6333) |

**enerv-indexer** (`/root/sovern/memory_app/main.py`):
- `POST /index` — индексирует все `.md` файлы из vault в Qdrant (инкрементально)
- `POST /reindex` — удаляет коллекцию, пересоздаёт и индексирует заново (нужно при смене модели)
- `GET /context?q=...&limit=3` — semantic search, возвращает `{context, sources}`
- `GET /search?q=...` — raw vector search с scores
- **Модель: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`** (FastEmbed, 384 dims, 50+ языков включая русский)
- Vault mount: `/root/sovern/obsidian` → `/vault`
- Текущий размер индекса: **447 документов**

> **После добавления новых документов** — вызвать `POST /index`:
> ```bash
> docker exec enerv-n8n wget -qO- --post-data="" http://enerv-indexer:8080/index
> ```
>
> **При смене модели** — вызвать `POST /reindex` (сбрасывает и переиндексирует всё):
> ```bash
> docker exec enerv-n8n wget -qO- --post-data="" http://enerv-indexer:8080/reindex
> ```

**Container:** `enerv-n8n` на `sovern-net` Docker bridge  
**Image:** `n8nio/n8n:latest`  
**Compose file:** `/root/sovern/docker-compose.yml`  

**Critical env vars:**
```yaml
environment:
  - N8N_HOST=n8n.synergify.com
  - N8N_PROTOCOL=https
  - WEBHOOK_URL=https://n8n.synergify.com
  - NODE_FUNCTION_ALLOW_BUILTIN=child_process   # REQUIRED для ACL Transformer
  - NODES_EXCLUDE=[]
  - N8N_BLOCK_NODES=[]
```

**Volumes:**
```yaml
volumes:
  - /mnt/data/n8n:/home/node/.n8n           # n8n data
  - /root/sovern/obsidian:/home/node/obsidian  # Obsidian vault
  - /root/sovern/scripts:/home/node/scripts    # acl_transformer.js
```

### Obsidian Vault Structure

```
/root/sovern/obsidian/
├── Atlas/
│   ├── Notes/
│   │   └── Sources/     ← knowledge_ingest записи
│   ├── Sources/
│   └── Maps/
├── Efforts/
│   └── On/              ← task_creation записи
├── Calendar/
│   └── Logs/            ← log_entry записи
└── Facets/              ← fallback
```

**Permissions:** все директории должны быть `chown -R 1000:1000` (n8n runs as uid 1000).

### Credentials

| Credential | ID | Type | Назначение |
|---|---|---|---|
| ENERV Telegram Bot | `A0PH9It6pypaBfiG` | `telegramApi` | Trigger + Reply nodes |
| Gemini API Key | `mlFnWbc900mBM7Yy` | `httpQueryAuth` | Gemini Router node |

**Gemini API Key** хранит API key из GCP project `gen-lang-client-0916449255` (AI Studio Default Project).  
Credential type `httpQueryAuth` → key передаётся как query param `?key=...`

---

## API Operations (для агентов)

### Проверить статус workflow
```bash
curl -H "X-N8N-API-KEY: {KEY}" http://localhost:5678/api/v1/workflows/hEDNe2LBdKACn9Z8
```

### Активировать workflow
```bash
curl -X POST -H "X-N8N-API-KEY: {KEY}" http://localhost:5678/api/v1/workflows/hEDNe2LBdKACn9Z8/activate
```

### Последние executions
```bash
curl -H "X-N8N-API-KEY: {KEY}" "http://localhost:5678/api/v1/executions?workflowId=hEDNe2LBdKACn9Z8&limit=5"
```

### Детали execution с ошибкой
```bash
curl -H "X-N8N-API-KEY: {KEY}" "http://localhost:5678/api/v1/executions/{id}?includeData=true"
```

### Обновить workflow (PUT)
```python
# Минимальный payload для PUT /api/v1/workflows/{id}:
payload = {
    "name": wf["name"],
    "nodes": wf["nodes"],
    "connections": wf["connections"],
    "settings": {"executionOrder": "v1"},  # только executionOrder — остальные поля вызывают 400
    "staticData": None,
}
```

### SSH к серверу (из WSL)
```bash
wsl.exe -d Ubuntu -u root -- bash -c "ssh -i /root/.ssh/id_ed25519 root@91.99.62.63 'COMMAND'"
```

### Обновить API key в GCP (добавить сервис)
```bash
TOKEN=$(gcloud auth print-access-token)
curl -X PATCH \
  "https://apikeys.googleapis.com/v2/Efforts/On/{PROJECT}/locations/global/keys/{KEY_ID}?updateMask=restrictions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"restrictions": {"serverKeyRestrictions": {"allowedIps": ["91.99.62.63", "2a01:4f8:1c18:f69e::1"]}, "apiTargets": [{"service": "generativelanguage.googleapis.com"}]}}'
```

---

## Output File Format

Каждое входящее сообщение создаёт один `.md` файл с семантической разметкой:

```markdown
---
id: 20260505185805963
timestamp: 2026-05-05 18:58:05
facets:
  identity: Taste-Skill for AI Vibe Coding
  intent: knowledge_ingest
  context: Atlas/Notes/Sources
  signal: high
source: n8n_stack
tags: [taste_skill, ai_coding, vibe_coding, design_ai, opensource, github_project, code_generation]
---
# Taste-Skill for AI Vibe Coding

Someone just solved the biggest problem with [[vibe coding]].
It's called [[Taste-Skill]]. One [[SKILL.md]] file that stops your [[vibe coding AI]]
from generating the same boring, generic slop every single time.
Works in [[Cursor]], [[Claude Code]], or any [[AI editor]] that reads context files.
Repo Link: [[https://github.com/Leonxlnx/taste-skill]]
```

**Ключевые свойства:**
- `tags` — массив в YAML frontmatter, отсутствует если пустой
- `content` — Gemini автоматически оборачивает важные термины в `[[WikiLinks]]`
- Filename: `{ISO_timestamp}_{sanitized_identity}.md`

---

## Known Issues & Fixes Applied

| Проблема | Причина | Решение |
|---|---|---|
| Workflow не активирован | `active: false` при создании | `POST /api/v1/workflows/{id}/activate` |
| Gemini 403 SERVICE_DISABLED | Gemini API не включён в GCP | Включить `generativelanguage.googleapis.com` в GCP Console |
| Gemini 403 referer blocked | API key restriction = HTTP referrers | Сменить на IP addresses restriction |
| Gemini 403 API blocked | API restrictions не включают Gemini | Добавить `generativelanguage.googleapis.com` в apiTargets через GCP REST API |
| Gemini 403 IPv6 IP mismatch | Сервер выходит через IPv6 `2a01:4f8:1c18:f69e::1` | Добавить IPv6 в allowedIps вместе с IPv4 |
| Gemini billing depleted | GCP project 466944453598 — платный, кончились credits | Переключить на AI Studio Default Project `gen-lang-client-0916449255` (free tier) |
| Модель не найдена | `gemini-1.5-flash` deprecated | Обновить на `gemini-2.5-flash` |
| executeCommand forbidden | n8n блокирует executeCommand node по permissions | Заменить на `code` node с `child_process.execSync` |
| child_process disallowed | n8n sandbox запрещает builtin modules | Добавить `NODE_FUNCTION_ALLOW_BUILTIN=child_process` в docker-compose env |
| EACCES permission denied | Obsidian volume смонтирован root-owned | `chown -R 1000:1000 /root/sovern/obsidian/` |
| acl_transformer SyntaxError | Literal newline в строке вместо `\n` | Перезаписать файл целиком через SCP |
| enerv-indexer DNS not found | Контейнер не запущен или в другой Docker сети | `docker restart enerv-indexer`, проверить что в `sovern-net` |
| enerv-indexer SyntaxError (main.py:55) | Multi-line f-string с `"` вместо triple-quotes | Заменить на `f"...\n..."` с `\n` escape |
| Gemini RAG "Bad request" | `contentType: "json"` вместо `"raw"` + отсутствие `authentication`/`genericAuthType` в parameters | Установить `contentType: "raw"`, `rawContentType: "application/json"`, добавить auth поля |
| Gemini RAG "invalid syntax" | Лишняя `"` перед `}]` в body expression (закрывала text string некорректно) | Убрать `"` — `text` property — это конкатенация выражений без закрывающей кавычки |
| Send RAG Reply "Bad request" | `typeVersion: 1` + `operation: "sendMessage"` несовместимы | Обновить до `typeVersion: 1.2`, убрать `operation` |
| `knowledge_ingest` → `knowledgeingest` в Telegram | Markdown v1 съедает `_` в значениях (italic trigger) | Обернуть dynamic values с underscores в backticks: `` `{{ expr }}` `` |
| Send RAG Reply "can't parse entities at byte 109" | n8n Telegram node v1.2 добавляет Markdown по умолчанию; filenames с `_` ломают entity parsing | Использовать `parse_mode: "HTML"` + HTML-escape в Parse RAG Response |
| `/ask` на русском → нерелевантные docs | `BAAI/bge-small-en-v1.5` — English-only, русские запросы не совпадают | Сменить модель на `paraphrase-multilingual-MiniLM-L12-v2`, вызвать `POST /reindex` |
| `appendAttribution` не убирает footer | Нужно явно указать `appendAttribution: false` в additionalFields | Добавить в оба Telegram reply nodes |

---

*Documented by Claude Sonnet 4.6 | 2026-05-05 | v4.0: UI polish, attribution removal, HTML mode for RAG reply, multilingual embeddings*
