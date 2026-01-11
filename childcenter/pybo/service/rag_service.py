# pybo/service/rag_service.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List
import os
import chromadb
from chromadb.utils import embedding_functions

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_PERSIST_DIR = os.path.join(BASE_DIR, "pybo", "rag_store")


@dataclass
class RagDoc:
    doc_id: str
    title: str
    org: str
    year: str
    text: str
    distance : float | None = None

class RagRetriever:
    def __init__(self, persist_dir: str = DEFAULT_PERSIST_DIR, collection_name: str = "policy_docs"):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="intfloat/multilingual-e5-small"
        )
        self.col = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embed_fn
        )

    def retrieve(self, query: str, k: int = 6) -> List[RagDoc]:
        res = self.col.query(
            query_texts=[f"query: {query}"],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )
        docs = []
        ids = res.get("ids", [[]])[0]
        metadatas = res.get("metadatas", [[]])[0]
        documents = res.get("documents", [[]])[0]
        distances = res.get("distances", [[]])[0]

        for _id, md, doc, dist in zip(ids, metadatas, documents, distances):
            md = md or {}
            docs.append(RagDoc(
                doc_id=str(_id),
                title=str(md.get("title", "")),
                org=str(md.get("org", "")),
                year=str(md.get("year", "")),
                text=str(doc),
                distance=float(dist) if dist is not None else None
            ))
        return docs

def format_rag_block(rag_docs: List[RagDoc], max_chars_per_doc: int = 900) -> str:
    if not rag_docs:
        return "- (근거 없음) 관련 근거가 검색되지 않았습니다. 필요한 부분은 “추가 확인 필요”로 표기하세요."

    blocks = []
    for i, d in enumerate(rag_docs, start=1):
        excerpt = (d.text or "").strip()
        if len(excerpt) > max_chars_per_doc:
            excerpt = excerpt[:max_chars_per_doc]
        blocks.append(
            f"- 근거ID: G{i}\n"
            f"  문서: {d.title}\n"
            f"  발행: {d.org}, {d.year}\n"
            f"  발췌: {excerpt}"
        )
    return "\n".join(blocks)
