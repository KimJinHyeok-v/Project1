from __future__ import annotations
from sqlalchemy import text

def make_data_facts(engine, district: str, year_from: int, year_to: int) -> str:
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT year, predicted_child_user, pred_child_user_yoy_pct
            FROM region_forecast
            WHERE district=:d AND year BETWEEN :y1 AND :y2
            ORDER BY year
        """), {"d": district, "y1": int(year_from), "y2": int(year_to)}).fetchall()

        supply = conn.execute(text("""
            SELECT COUNT(*) AS center_cnt, SUM(capacity) AS total_capacity
            FROM child_center
            WHERE district LIKE '%' || :d || '%'
        """), {"d": district}).fetchone()

    parts = []
    for yy, v, pct in rows:
        pct_str = "추가 확인 필요" if pct is None else f"{float(pct):.2f}%"
        parts.append(f"{yy}년 예측 이용자수 {int(v)}명 전년 대비 {pct_str}")

    if supply is not None:
        parts.append(f"센터 수 {int(supply.center_cnt)}개 총 정원 {int(supply.total_capacity or 0)}명")

    return " / ".join(parts) if parts else "추가 확인 필요"



def make_rag_snippets(retriever, query: str, k: int = 2) -> str:
    """
    핵심: 'format_rag_block'처럼 원문을 길게 넣지 말고,
    근거 요지 1~2문장만 만들어서 넣기.
    """
    docs = retriever.retrieve(query, k=k)
    if not docs:
        return "- G1: 추가 확인 필요"

    out = []
    for i, d in enumerate(docs, start=1):
        txt = (d.text or "").strip().replace("\n", " ")
        # 숫자/표 복붙을 줄이려면 길이를 빡세게
        txt = txt[:120] + ("…" if len(txt) > 120 else "")
        out.append(f"- G{i}: {txt}")
    return "\n".join(out)
