import os
import json
import pandas as pd
from datetime import datetime
from PyPDF2 import PdfReader
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")

FOLDER = "../dataset"

ALLOWED_TYPES = ["txt", "pdf", "csv", "json", "xlsx"]


# =========================
# EXTRACT TEXT
# =========================
def extract(file_path):

    ext = file_path.split(".")[-1].lower()

    try:

        if ext == "txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        elif ext == "pdf":
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"
            return text

        elif ext == "csv":
            df = pd.read_csv(file_path)
            return df.astype(str).to_string()

        elif ext == "xlsx":
            df = pd.read_excel(file_path)
            return df.astype(str).to_string()

        elif ext == "json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return json.dumps(data, ensure_ascii=False)

        return ""

    except Exception as e:
        print("ERROR:", file_path, e)
        return ""


# =========================
# BUILD INDEX
# =========================
def build_index(selected_types=None):

    # =========================
    # CREATE INDEX WITH MAPPING
    # =========================
    if es.indices.exists(index="files"):
        es.indices.delete(index="files")

    es.indices.create(
        index="files",
        body={
            "mappings": {
                "properties": {
                    "filename":        {"type": "text"},
                    "content":         {"type": "text"},
                    "filetype":        {"type": "keyword"},
                    "modified":        {"type": "date"},
                    "content_tokens":  {"type": "keyword"},
                    "content_keyword": {"type": "keyword"}
                }
            }
        }
    )

    indexed_count = 0

    for file in os.listdir(FOLDER):

        path = os.path.join(FOLDER, file)

        if not os.path.isfile(path):
            continue

        ext = file.split(".")[-1].lower()

        if selected_types and ext not in selected_types:
            continue

        text = extract(path)
        if not text.strip():
            continue

        doc = {
            "filename":        file,
            "content":         text,
            "content_tokens":  text.lower().split(),
            "content_keyword": text.lower().split()[:50],
            "filetype":        ext,
            "modified":        datetime.fromtimestamp(
                                   os.path.getmtime(path)
                               ).strftime("%Y-%m-%d")
        }

        es.index(index="files", document=doc)

        indexed_count += 1
        print("INDEXED:", file)

    print("DONE")
    return indexed_count


if __name__ == "__main__":
    build_index()