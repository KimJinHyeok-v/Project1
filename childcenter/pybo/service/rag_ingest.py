# pybo/service/rag_ingest.py
import os, glob
import chromadb
from chromadb.utils import embedding_functions

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PERSIST_DIR = os.path.join(BASE_DIR, "pybo", "rag_store")
DOC_DIR = os.path.join(BASE_DIR, "pybo", "rag_docs")


def chunk_text(text: str, chunk_size=900, overlap=150):
    text = text.replace("\r\n", "\n").strip()
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end]
        chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks

def main():
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="intfloat/multilingual-e5-small"
    )
    col = client.get_or_create_collection(name=COLLECTION, embedding_function=embed_fn)

    paths = sorted(glob.glob(os.path.join(DOC_DIR, "*.txt")))
    if not paths:
        raise RuntimeError(f"No .txt files found in {DOC_DIR}/")

    total = 0
    for path in paths:
        filename = os.path.basename(path)
        # 파일명 규칙: 2024_서울시_지역아동센터_운영지침.txt 같은 식으로 추천
        # metadata는 최소한 title/org/year 정도만 넣어도 됨
        meta = {
            "title": filename,
            "org": "unknown",
            "year": "unknown",
        }

        with open(path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = chunk_text(text, chunk_size=900, overlap=150)
        ids = [f"{filename}::p{i}" for i in range(len(chunks))]
        metas = [meta for _ in chunks]

        col.add(ids=ids, documents=chunks, metadatas=metas)
        total += len(chunks)
        print(f"[OK] {filename} -> {len(chunks)} chunks")

    print(f"Done. Total chunks added: {total}")

if __name__ == "__main__":
    main()
