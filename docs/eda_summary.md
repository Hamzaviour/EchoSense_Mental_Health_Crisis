# MentalChat16K — EDA Summary

Dataset: [ShenLab/MentalChat16K](https://huggingface.co/datasets/ShenLab/MentalChat16K)

## Planned analyses (run during ingest)

| Metric | Description |
|--------|-------------|
| Conversation length | Token/word distribution per row |
| Emotional categories | Tag frequency if present in metadata |
| Topics | Keyword clustering on instructions |
| Counselor responses | Length vs patient utterances |
| Patient intent types | Instruction field categorization |

## Cleaning rules

- Remove duplicates (MD5 hash)
- Drop entries under 50 characters
- Normalize whitespace

## Chunking

- Size: 500 tokens
- Overlap: 100 tokens
- Embedding: `BAAI/bge-large-en-v1.5` or `all-MiniLM-L6-v2`
- Store in ChromaDB collection `mental_health_knowledge`

## Ingestion results (latest run)

| Metric | Value |
|--------|-------|
| Rows processed | 200 |
| Conversations after cleaning | 197 |
| Chunks generated | 301 |
| ChromaDB collection | `mental_health_knowledge` |
| Embedding mode | `simple` (offline; use `hf-api` when HF network available) |

Run: `python backend/scripts/ingest_mentalchat16k.py --limit 200 --model simple`
