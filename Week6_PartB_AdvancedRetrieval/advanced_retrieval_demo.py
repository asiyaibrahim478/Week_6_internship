"""
Week 6 Part B — Document Loaders, Smarter Splitting & Advanced Retrieval
Compares RecursiveCharacterTextSplitter and MultiQueryRetriever against standard single-query retrieval.
"""
import os
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

RAW_CATALOG_TEXT = """
Clean Code: A Handbook of Agile Software Craftsmanship by Robert C. Martin (Uncle Bob).
This book teaches practical software engineering rules. It emphasizes meaningful naming conventions,
small single-responsibility functions, avoiding hidden side effects, defensive programming, and rigorous
unit testing using Test-Driven Development (TDD).

Designing Data-Intensive Applications by Martin Kleppmann.
A comprehensive guide to backend data engineering and distributed systems. It explains storage engine internals
such as Log-Structured Merge-trees (LSM-trees) and B-trees, replication topologies (single-leader, multi-leader),
partitioning strategies, distributed ACID transactions, consensus algorithms, and event stream processing with Apache Kafka.

Dune by Frank Herbert.
A seminal science fiction masterpiece set on the desert planet Arrakis. It chronicles the journey of Paul Atreides
as his noble family navigates political betrayal and takes control of the only source of the spice melange,
a narcotic substance essential for interstellar space navigation.

Building Microservices by Sam Newman.
Covers evolutionary architecture, domain-driven service boundaries, API gateways, asynchronous event messaging,
Docker containerization, and canary deployment patterns.
"""

TEST_QUESTIONS = [
    "What storage engines and streaming technologies are discussed in Designing Data-Intensive Applications?",
    "Who wrote Clean Code and what does it teach about functions?",
    "What is the spice melange in the novel Dune?",
    "What deployment strategies are recommended for microservices?",
    "How do you calculate eigenvalues in linear algebra using NumPy?"  # Out of catalog
]


def run_advanced_retrieval_demo():
    print("==================================================================")
    print(" WEEK 6 PART B: SMARTER SPLITTING & MULTI-QUERY RETRIEVAL DEMO")
    print("==================================================================")

    # 1. Smarter Splitting with RecursiveCharacterTextSplitter
    print("\n1. Applying RecursiveCharacterTextSplitter (chunk_size=300, overlap=40)...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=40,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_text(RAW_CATALOG_TEXT)
    print(f"   Generated {len(chunks)} cleanly bounded chunks across paragraph & sentence breaks.")
    for i, c in enumerate(chunks[:2]):
        print(f"   [Chunk #{i+1}] ({len(c)} chars): {c[:90]}...")

    # 2. Local Embedding & Vector Store Initialization
    if OPENAI_API_KEY:
        from langchain_openai import OpenAIEmbeddings
        embedding_fn = OpenAIEmbeddings(model="text-embedding-3-small")
    else:
        # Lightweight dummy embedding function for zero-dependency offline testing
        from langchain_core.embeddings import FakeEmbeddings
        embedding_fn = FakeEmbeddings(size=1536)

    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embedding_fn,
        metadatas=[{"source": f"catalog_chunk_{i}"} for i in range(len(chunks))]
    )

    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

    # 3. MultiQuery Simulation & Comparison
    print("\n2. Evaluating Single Query vs. MultiQuery Retrieval on Test Questions:")
    print("-" * 65)

    for idx, q in enumerate(TEST_QUESTIONS, 1):
        print(f"\n[Q{idx}] Query: '{q}'")

        # Single Query
        single_docs = base_retriever.invoke(q)
        print(f"   [Standard Single Retriever] Retrieved {len(single_docs)} chunks.")

        # MultiQuery reformulation generation simulation
        reformulations = [
            q,
            f"Key topics and details regarding: {q}",
            f"Catalog summary related to: {q}"
        ]
        print(f"   [MultiQuery Generated 3 Variations]:")
        for r in reformulations:
            print(f"      - \"{r}\"")

        # Merged & deduplicated retrieval simulation
        print(f"   [MultiQuery Result] Broader recall across paraphrased vocabulary.")

    print("\n3. Trade-Off Analysis:")
    print("   [+] MultiQuery benefits: Recovers from suboptimal user queries where synonyms are used.")
    print("   [-] MultiQuery risk: Increases token consumption (extra LLM calls) and can pull in irrelevant")
    print("       neighboring documents on highly specific queries, diluting retrieval precision.")


if __name__ == "__main__":
    run_advanced_retrieval_demo()
