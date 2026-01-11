# pybo/views/ai2_views.py
import os
import logging
from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import create_engine
import config

from pybo.service.rag_service import RagRetriever, format_rag_block
from pybo.service.lc_chains import build_brief_chain
from pybo.service.brief_facts_service import make_data_facts  # make_rag_snippets는 이제 안 써도 됨
from pybo.service.runpod_service import call_runpod  # refine에서 쓰고 있으니 import 필요


logger = logging.getLogger(__name__)
bp = Blueprint("ai2", __name__, url_prefix="/ai2")

engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAG_DIR = os.path.join(BASE_DIR, "pybo", "rag_store")

retriever_policy = RagRetriever(persist_dir=RAG_DIR, collection_name="policy_docs")
retriever_db = RagRetriever(persist_dir=RAG_DIR, collection_name="db_facts")
brief_chain = build_brief_chain()


PURPOSE_MAP = {
    "approval": "결재용",
    "budget": "예산편성",
    "pilot": "시범사업 설계",
}

@bp.get("/")
def ai2_page():
    return render_template("main/ai2.html")

@bp.post("/b2b/report/generate")
def b2b_report_generate():
    data = request.get_json(silent=True) or {}
    district = (data.get("district") or "").strip()
    year_from = data.get("year_from")
    year_to = data.get("year_to")
    report_type = (data.get("report_type") or "").strip()
    extra = (data.get("extra") or "").strip()

    if not district or not year_from or not year_to or not report_type:
        return jsonify({"error": "필수 입력값이 부족합니다."}), 400

    purpose = PURPOSE_MAP.get(report_type, report_type)
    extra_block = f"추가 요구사항: {extra}" if extra else ""

    # 1) DB → DATA_FACTS (정확한 수치 출력용)
    data_facts = make_data_facts(engine, district, int(year_from), int(year_to))

    # 2) RAG (정책 근거 + DB 근거 함께)
    policy_query = f"{district} 지역아동센터 지원 기준 운영 원칙 산정 예외 {purpose}"
    db_query = f"{district} {year_from}~{year_to} 예측 이용자수 전년 대비 증감률 센터 수 총 정원"

    try:
        policy_docs = retriever_policy.retrieve(policy_query, k=2)
        db_docs = retriever_db.retrieve(db_query, k=4)
        rag_snippets = format_rag_block(db_docs + policy_docs, max_chars_per_doc=900)
    except Exception:
        logger.exception("RAG retrieve failed")
        rag_snippets = "- (근거 없음) 관련 근거가 검색되지 않았습니다."

    # 3) LangChain invoke
    try:
        text = brief_chain.invoke({
            "topic": "지역아동센터 운영 개선 및 접근성·정원 불균형 완화",
            "district": district,
            "year_from": int(year_from),
            "year_to": int(year_to),
            "purpose": purpose,
            "extra_block": extra_block,
            "data_facts": data_facts,
            "rag_snippets": rag_snippets,
        })
        return jsonify({"report": text})
    except Exception:
        logger.exception("보고서 생성 실패")
        return jsonify({"error": "보고서 생성 실패"}), 500




@bp.post("/b2b/report/refine")
def b2b_report_refine():
    data = request.get_json(silent=True) or {}
    report = (data.get("report") or "").strip()
    instruction = (data.get("instruction") or "").strip()

    if not report or not instruction:
        return jsonify({"error": "report/instruction이 비었습니다."}), 400

    prompt = f"""너는 정책보고서 편집자다. (한국어, 공문체 유지)
아래 [기존 보고서]를 [수정 요청]에 맞게 '전체 문서'를 다시 써라.
- 허위 수치 생성 금지: 수치 필요 시 '근거 필요' 표기

[수정 요청]
{instruction}

[기존 보고서]
{report}
"""

    try:
        text = call_runpod(prompt, max_new_tokens=1400)
        return jsonify({"report": text})
    except Exception as e:
        logger.exception(e)
        return jsonify({"error": "보고서 수정 실패"}), 500

