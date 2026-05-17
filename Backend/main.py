from fastapi import FastAPI, Request
from elasticsearch import Elasticsearch
from fastapi.middleware.cors import CORSMiddleware

from index_files import build_index

app = FastAPI()
es = Elasticsearch("http://localhost:9200")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HOME
@app.get("/")
def home():
    return {"message": "Mini Search Engine Running"}


# QUERY BUILDER
def build_query(q: str):

    q = q.strip()

    if " NOT " not in q and "(" not in q:
        return {
            "query_string": {
                "query": q,
                "fields": ["content", "filename"],
                "default_operator": "AND"
            }
        }

    if " NOT " in q:
        inc, exc = q.split(" NOT ", 1)
        return {
            "bool": {
                "must": {
                    "query_string": {
                        "query": inc,
                        "fields": ["content", "filename"]
                    }
                },
                "must_not": {
                    "query_string": {
                        "query": exc,
                        "fields": ["content", "filename"]
                    }
                }
            }
        }

    return {
        "query_string": {
            "query": q,
            "fields": ["content", "filename"],
            "default_operator": "AND"
        }
    }

# BUILD INDEX API
@app.post("/build-index")
async def build_index_api(request: Request):

    data = await request.json()
    selected = data.get("selected_types", [])

    count = build_index(selected)

    return {"indexed_files": count}


# SEARCH
@app.get("/search")
def search(q: str, page: int = 1, types: str = None,
           start_date: str = None, end_date: str = None):

    size = 5

    # Pagination
    body = {
        "from": (page - 1) * size,
        "size": size,
        "query": {
            "bool": {
                "must": build_query(q),
                "filter": []
            }
        },
        "highlight": {
            "pre_tags": ["<em>"],
            "post_tags": ["</em>"],
            "fields": {
                "content": {}
            }
        }
    }

    if types:
        body["query"]["bool"]["filter"].append({
            "terms": {"filetype": types.split(",")}
        })

    if start_date and end_date:
        body["query"]["bool"]["filter"].append({
            "range": {
                "modified": {"gte": start_date, "lte": end_date}
            }
        })

    res = es.search(index="files", body=body)

    total = res["hits"]["total"]["value"]
    results = []

    for h in res["hits"]["hits"]:
        src = h["_source"]

        snippet = " ... ".join(
            h.get("highlight", {}).get("content", [src["content"][:200]])
        )

        results.append({
            "filename": src["filename"],
            "filetype": src["filetype"],
            "modified": src["modified"],
            "score":    h["_score"],
            "snippet":  snippet
        })

    # SUGGESTION
    suggestion = None

    if not results and q.strip():
        sug = es.search(
            index="files",
            body={
                "suggest": {
                    "did_you_mean": {
                        "text": q,
                        "term": {
                            "field": "content",
                            "suggest_mode": "missing"
                        }
                    }
                }
            }
        )
        try:
            opts = sug["suggest"]["did_you_mean"][0]["options"]
            if opts:
                suggestion = opts[0]["text"]
        except:
            suggestion = None

    return {
        "results":    results,
        "total":      total,
        "page":       page,
        "suggestion": suggestion
    }



# STATS
@app.get("/stats")
def stats():

    if not es.indices.exists(index="files"):
        return {"total": 0, "by_type": [], "top_terms": []}

    count = es.count(index="files")["count"]

    agg = es.search(
        index="files",
        size=0,
        aggs={
            "by_type": {
                "terms": {
                    "field": "filetype",
                    "size": 20
                }
            },
            "top_terms": {
                "terms": {
                    "field": "content_keyword",
                    "size": 10
                }
            }
        }
    )

    return {
        "total": count,

        "by_type": [
            {
                "type":  b["key"],
                "count": b["doc_count"]
            }
            for b in agg["aggregations"]["by_type"]["buckets"]
        ],

        "top_terms": [
            {
                "term":  b["key"],
                "count": b["doc_count"]
            }
            for b in agg["aggregations"]["top_terms"]["buckets"]
        ]
    }


