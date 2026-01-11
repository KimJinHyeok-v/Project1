# pybo/service/rag_ingest_db.py
from __future__ import annotations

import os
import chromadb
from chromadb.utils import embedding_functions
from sqlalchemy import create_engine, text
import config

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PERSIST_DIR = os.path.join(BASE_DIR, "pybo", "rag_store")
COLLECTION = "db_facts"

# ✅ 여기만 네 DB에 맞게 수정
SQL = """
WITH cap AS (
  SELECT
    DISTRICT,
    COUNT(*)      AS center_count,
    SUM(CAPACITY) AS capacity_sum
  FROM CHILD_CENTER
  GROUP BY DISTRICT
)
SELECT
  f.DISTRICT,
  f.YEAR,
  f.PREDICTED_CHILD_USER      AS predicted_users,
  f.PRED_CHILD_USER_YOY_PCT   AS yoy_rate,
  cap.center_count,
  cap.capacity_sum
FROM REGION_FORECAST f
LEFT JOIN cap
  ON cap.DISTRICT = f.DISTRICT
WHERE f.YEAR BETWEEN :y1 AND :y2
ORDER BY f.DISTRICT, f.YEAR
"""


def main():
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="intfloat/multilingual-e5-small"
    )
    col = client.get_or_create_collection(name=COLLECTION, embedding_function=embed_fn)

    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

    with engine.connect() as conn:
        rows = conn.execute(text(SQL), {"y1": 2015, "y2": 2030}).fetchall()

    docs, ids, metas = [], [], []
    for r in rows:
        district = str(r[0])
        year = int(r[1])
        predicted_users = r[2]
        yoy_rate = r[3]
        center_count = r[4]
        capacity_sum = r[5]

        # ✅ e5 임베딩은 query/passage 프리픽스가 품질에 도움됨
        doc = (
            f"passage: {district} {year}년 지역아동센터 지표입니다. "
            f"예측 이용자수는 {predicted_users}명입니다. "
            f"전년 대비 증감률은 {yoy_rate}%입니다. "
            f"센터 수는 {center_count}개입니다. "
            f"총 정원은 {capacity_sum}명입니다."
        )

        docs.append(doc)
        ids.append(f"{district}::{year}")
        metas.append({"title": "DB_FACT", "org": "DB", "year": str(year), "district": district, "source": "db"})

    # ✅ add는 중복 id에서 터질 수 있으니 upsert 권장
    col.upsert(ids=ids, documents=docs, metadatas=metas)
    print(f"[OK] upserted {len(rows)} rows into {COLLECTION} (persist={PERSIST_DIR})")

if __name__ == "__main__":
    main()
