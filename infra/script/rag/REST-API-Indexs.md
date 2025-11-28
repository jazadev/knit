### Command-line rag-index-1 RAG

```bash
curl -X POST "$SEARCH_ENDPOINT/indexers/$IDX_HISTORIC/run?api-version=$API_VERSION" -H "api-key: $SEARCH_ADMIN_KEY" -H "Content-Length: 0"

curl -X POST "$SEARCH_ENDPOINT/indexers/$IDX_HISTORIC/reset?api-version=$API_VERSION" -H "api-key: $SEARCH_ADMIN_KEY" -H "Content-Length: 0"

curl -X GET "$SEARCH_ENDPOINT/indexers/$IDX_HISTORIC/status?api-version=$API_VERSION" -H "api-key: $SEARCH_ADMIN_KEY" >> log01.txt

```

---

### Command-line rag-index-2 RAG

```bash
curl -X POST "$SEARCH_ENDPOINT/indexers/$IDX_CURRENT/run?api-version=$API_VERSION" -H "api-key: $SEARCH_ADMIN_KEY" -H "Content-Length: 0"

curl -X POST "$SEARCH_ENDPOINT/indexers/$IDX_CURRENT/reset?api-version=$API_VERSION" -H "api-key: $SEARCH_ADMIN_KEY" -H "Content-Length: 0"

curl -X GET "$SEARCH_ENDPOINT/indexers/$IDX_CURRENT/status?api-version=$API_VERSION" -H "api-key: $SEARCH_ADMIN_KEY" >> log01.txt

```