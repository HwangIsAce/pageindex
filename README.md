# PageIndex

Vectorless, reasoning-based RAG. 문서를 트리 구조로 인덱싱하고 LLM tree search로 검색합니다.

- **No Vector DB** – 구조 기반 retrieval
- **No Chunking** – 자연스러운 섹션 단위
- **Human-like** – 추론 기반 검색

---

## 설치

```bash
pip install -e .
```

`.env`에 OpenAI API 키 설정:

```
CHATGPT_API_KEY=sk-...
```

---

## 사용 방법

### CLI: 인덱싱

단일 PDF:

```bash
python run_pageindex.py --pdf_path doc.pdf
```

다중 PDF (unified TOC):

```bash
python run_pageindex.py --pdf_paths a.pdf,b.pdf
# 또는
python run_pageindex.py --input_dir ./pdfs/
```

마크다운:

```bash
python run_pageindex.py --md_path doc.md
```

### CLI: 쿼리

```bash
python query_pageindex.py --unified_toc toc.json --doc_store store.json -q "질문"
```

### API 서버

```bash
python run_api.py
# http://localhost:8000
```

Docker:

```bash
docker compose up --build
```

API 상세: [docs/API.md](docs/API.md)

---

## 프로젝트 구조

```
src/
├── api/          # HTTP API
└── pageindex/    # 인덱싱, retrieval
```

---

## Cookbooks

- [pageindex_RAG_simple.ipynb](cookbook/pageindex_RAG_simple.ipynb)
- [vision_RAG_pageindex.ipynb](cookbook/vision_RAG_pageindex.ipynb)

---

## 참고

- [PageIndex Framework](https://pageindex.ai/blog/pageindex-intro)
- [Vectify AI](https://vectify.ai)
