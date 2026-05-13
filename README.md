# 🔍 Mini Search Engine

A local file search engine built with **FastAPI** + **Elasticsearch** + **HTML/JS frontend**.  
It indexes files from a local folder and lets you search through them using Boolean, Phrase, Fuzzy, and Wildcard queries — with filters, highlights, paging, and stats.

---

## 📌 Features

| Feature | Status |
|---|---|
| Index TXT, PDF, CSV, JSON, XLSX files | ✅ |
| Pick file types before indexing | ✅ |
| Boolean search: AND, OR, NOT | ✅ |
| Phrase search: `"information retrieval"` | ✅ |
| Fuzzy search: `retrival~` | ✅ |
| Wildcard search: `inform*`, `?earch` | ✅ |
| Filter by file type at search time | ✅ |
| Filter by modification date range | ✅ |
| Highlighted snippets in results | ✅ |
| "Did you mean?" on zero results | ✅ |
| Paging — 5 results per page | ✅ |
| Stats: total docs, by type, top 10 terms | ✅ |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python) |
| Search Engine | Elasticsearch 8.x |
| File Parsing | PyPDF2, pandas, openpyxl |
| Frontend | HTML + JavaScript (Vanilla) |
| Server | Uvicorn |

---

## 📁 Project Structure

```
mini-search-engine/
├── Backend/
│   ├── main.py            # FastAPI app — all API routes
│   └── index_files.py     # File parser + Elasticsearch indexer
├── Frontend/
│   └── index.html         # Web UI
├── dataset/               # Put your files here to be indexed
└── README.md
```

---

## ✅ Requirements

- Python 3.9+
- Elasticsearch 8.x
- Docker (recommended for running Elasticsearch)

---

## 📦 Installation

### 1. Clone the repo

```bash
git clone https://github.com/your-username/mini-search-engine.git
cd mini-search-engine
```

### 2. Install Python dependencies

```bash
pip install fastapi uvicorn elasticsearch pandas PyPDF2 openpyxl
```

### 3. Add your files

Put the files you want to search inside the `dataset/` folder:

```
dataset/
├── report.pdf
├── notes.txt
├── data.csv
├── config.json
└── sheet.xlsx
```

---

## 🚀 Running the Project

### Step 1 — Start Elasticsearch

Using Docker (easiest):

```bash
docker run -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.11.0
```

Or download and run manually from: https://www.elastic.co/downloads/elasticsearch

Verify it's running:
```
http://localhost:9200
```

### Step 2 — Start the Backend

```bash
cd Backend
python -m uvicorn main:app --reload
```

API will be available at: `http://127.0.0.1:8000`

### Step 3 — Open the Frontend

Open `Frontend/index.html` with **Live Server** (VS Code extension) or any local server:

```
http://127.0.0.1:5500
```

---

## 🖥️ How to Use

### 1. Build the Index

- Check the file types you want to index (PDF, TXT, CSV, JSON, XLSX)
- Click **Build Index**
- You'll see a summary: how many files were indexed

### 2. Search

Type your query in the search box. Supported syntax:

| Syntax | Example | Description |
|---|---|---|
| Simple keyword | `invoice` | Finds files containing "invoice" |
| AND (default) | `search engine` | Both words must appear |
| OR | `search OR data` | Either word can appear |
| NOT | `report NOT draft` | Include "report", exclude "draft" |
| Phrase | `"information retrieval"` | Exact phrase match |
| Fuzzy | `retrival~` | Tolerates typos |
| Fuzzy (degree) | `retrival~2` | Allows up to 2 character edits |
| Wildcard `*` | `inform*` | Matches: information, informative, … |
| Wildcard `?` | `?earch` | Matches: search, pearch, … |
| Grouping | `(java OR python) AND database` | Combined logic |

### 3. Filters (Optional)

- **File type filter** — check which types to search in at search time
- **Date range filter** — set "Modified from" and "to" dates to filter by file modification date

### 4. Results

Each result shows:
- Filename
- File type
- Modification date
- Relevance score
- Highlighted snippet (matched words are highlighted in yellow)

### 5. Paging

- 5 results per page
- Use **Prev** / **Next** buttons to navigate
- Buttons are disabled when there is no previous/next page

### 6. Did You Mean?

If your search returns no results, the engine suggests a corrected query automatically.

### 7. Stats

Hit the `/stats` endpoint to see index statistics:

```
http://127.0.0.1:8000/stats
```

Returns:
- Total indexed documents
- Count per file type
- Top 10 most frequent terms

---

## 📡 API Reference

### `GET /`
Health check.
```json
{ "message": "Mini Search Engine Running 🚀" }
```

---

### `POST /build-index`
Index files from the `dataset/` folder.

**Request:**
```json
{ "selected_types": ["pdf", "txt", "csv"] }
```
> Send `[]` to index all supported types.

**Response:**
```json
{ "indexed_files": 12 }
```

---

### `GET /search`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `q` | string | ✅ | Search query |
| `page` | int | ❌ | Page number (default: 1) |
| `types` | string | ❌ | Comma-separated types e.g. `pdf,txt` |
| `start_date` | string | ❌ | e.g. `2024-01-01` |
| `end_date` | string | ❌ | e.g. `2024-12-31` |

**Examples:**
```
GET /search?q=invoice
GET /search?q=report NOT draft&types=pdf
GET /search?q="information retrieval"
GET /search?q=retrival~&page=2
GET /search?q=data&start_date=2024-01-01&end_date=2024-12-31
```

**Response:**
```json
{
  "results": [
    {
      "filename": "report.pdf",
      "filetype": "pdf",
      "modified": "2024-05-10",
      "score": 3.14,
      "snippet": "...quarterly <em>sales</em> report..."
    }
  ],
  "total": 25,
  "page": 1,
  "suggestion": null
}
```

---

### `GET /stats`

**Response:**
```json
{
  "total": 42,
  "by_type": [
    { "key": "pdf", "count": 20 },
    { "key": "txt", "count": 15 }
  ],
  "top_terms": [
    { "term": "invoice", "count": 8 },
    { "term": "report", "count": 6 }
  ]
}
```

---

## 📝 Design Decisions

### JSON / CSV / Excel — What counts as the document?

- **JSON**: The entire file is treated as one document (serialized as a string).
- **CSV**: The entire file is treated as one document (converted to string using pandas).
- **Excel (.xlsx)**: The entire sheet is treated as one document (converted to string using pandas).

This approach keeps indexing simple and ensures all content is searchable without creating thousands of micro-documents per file.

---

## ⚠️ Common Issues

**Elasticsearch not running:**
```
ConnectionError: http://localhost:9200
```
→ Start Elasticsearch first before running the backend.

**500 error on `/stats`:**
→ The index does not exist yet. Click **Build Index** first.

**No results returned:**
→ Make sure files exist in `dataset/` and you clicked **Build Index**.

**Next button not disabling at last page:**
→ Make sure `pageSize` in the frontend matches the backend `size = 5`.

---

## 🔌 Ports Summary

| Service | URL | Port |
|---|---|---|
| FastAPI Backend | http://127.0.0.1:8000 | 8000 |
| Frontend (Live Server) | http://127.0.0.1:5500 | 5500 |
| Elasticsearch | http://localhost:9200 | 9200 |
