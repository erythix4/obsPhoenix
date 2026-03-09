"""
RAG Pipeline -- LLM Security Knowledge Base
Embeddings : ChromaDB local (onnxruntime)
LLM        : Ollama (llama3.2) ou OpenAI selon LLM_PROVIDER
"""

import logging, os
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.embeddings import Embeddings
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

logger = logging.getLogger("rag_pipeline")

# ── Embeddings locaux (onnxruntime, no API key) ──────────────────────────────

class LocalEmbeddings(Embeddings):
    def __init__(self):
        self._fn = DefaultEmbeddingFunction()
    def embed_documents(self, texts):
        return [[float(x) for x in v] for v in self._fn(texts)]
    def embed_query(self, text):
        return [float(x) for x in self._fn([text])[0]]

# ── Chargement des documents ─────────────────────────────────────────────────

def _load_docs(docs_dir: str = "/app/docs"):
    from pathlib import Path
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = []
    for p in Path(docs_dir).glob("*.txt"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        chunks.extend(splitter.create_documents([text], metadatas=[{"source": p.name}]))
    logger.info(f"{len(chunks)} chunks charges depuis {docs_dir}")
    return chunks

# ── Build pipeline ────────────────────────────────────────────────────────────

def build_pipeline(docs_dir: str = "/app/docs"):
    # Embeddings
    logger.info("Embeddings locaux (ChromaDB/onnxruntime)")
    embeddings = LocalEmbeddings()

    # Vectorstore
    docs = _load_docs(docs_dir)
    vectorstore = Chroma.from_documents(
        docs, embeddings,
        persist_directory="/app/.cache/chroma",
        collection_name="security_kb"
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # LLM
    llm_provider = os.getenv("LLM_PROVIDER", "ollama").lower()

    if llm_provider == "ollama":
        from langchain_community.llms import Ollama
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        llm = Ollama(model=model, base_url=base_url, temperature=0.1)
        logger.info(f"LLM Ollama : {model} @ {base_url}")
    else:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        logger.info("LLM OpenAI : gpt-4o-mini")

    # Prompt
    PROMPT = ChatPromptTemplate.from_template("""You are a cybersecurity expert. 
Answer based ONLY on the context provided. Be concise and precise.

Context:
{context}

Question: {question}
Answer:""")

    def fmt(docs): return "\n\n".join(d.page_content for d in docs)

    chain = (
        {"context": retriever | fmt, "question": RunnablePassthrough()}
        | PROMPT
        | llm
        | StrOutputParser()
    )

    logger.info("Pipeline RAG pret.")
    return chain
