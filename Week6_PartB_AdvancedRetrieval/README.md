# Week 6 — Part B: Advanced Splitting & Retrieval

## Overview
Moving beyond fixed-size chunking and brittle single-query embeddings:

### 1. `RecursiveCharacterTextSplitter`
- Unlike fixed-size chunking which cuts words or sentences in half arbitrarily at character index $N$, recursive splitting attempts to split by:
  1. `\n\n` (Paragraph boundaries)
  2. `\n` (Line breaks)
  3. `. ` (Sentence boundaries)
  4. ` ` (Word boundaries)
  5. `""` (Fallback character cut)
- Keeps semantically coherent units together.

---

### 2. `MultiQueryRetriever`
- Uses the LLM to rewrite the user query from multiple perspectives/synonyms.
- Queries the vector store for each permutation and merges/deduplicates the chunks.

### Trade-Off Analysis:
| Feature | Single Query Retriever | MultiQueryRetriever |
|---|---|---|
| **Latency** | Low (Single vector search). | Moderate (Requires 1 initial LLM generation call before search). |
| **Recall** | Moderate (May miss chunks if vocabulary differs). | **High** (Captures synonyms & alternate phrasings). |
| **Precision** | High for exact match topics. | Can occasionally pull noisy chunks on narrow queries. |
| **Cost** | 0 extra LLM calls. | 1 extra LLM prompt call per question. |

### Running the Demo
```bash
python advanced_retrieval_demo.py
```
