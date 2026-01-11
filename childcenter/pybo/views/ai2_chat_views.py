import math
import re
import json
import logging
import os
from flask import Blueprint, request, jsonify, session 
from sqlalchemy import create_engine, text
import config

# [RunPod 및 RAG 연동 필수 임포트]
from pybo.service.runpod_service import call_runpod
from pybo.service.rag_service import RagRetriever, format_rag_block
from pybo.service.lc_chains import build_brief_chain
from pybo.service.brief_facts_service import make_data_facts

logger = logging.getLogger(__name__)
bp = Blueprint("ai2_chat", __name__, url_prefix="/ai2")

engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

# [보고서용 RAG 초기화 - 로컬 rag_store 경로 연동]
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RAG_DIR = os.path.join(BASE_DIR, "pybo", "rag_store")
retriever_policy = RagRetriever(persist_dir=RAG_DIR, collection_name="policy_docs")
retriever_db = RagRetriever(persist_dir=RAG_DIR, collection_name="db_facts")
brief_chain = build_brief_chain()

PURPOSE_MAP = {"approval": "결재용", "budget": "예산편성", "pilot": "시범사업 설계"}

DEFAULT_N = 3
MAX_N = 10

# ===== 사용자님 원본 정규표현식 및 프롬프트 (수정 절대 없음) =====
NAME_SET_RE = re.compile(r"(내\s*이름은|나는)\s*([가-힣A-Za-z]{2,10})(이야|입니다|야)?")
NAME_ASK_RE = re.compile(r"(내\s*이름(이|은)\s*뭐(야|지)|내\s*이름\s*알아\??)")
CAPACITY_RE = re.compile(r"(\d+)\s*명?\s*(이상|넘는|넘게|인곳)")
CENTER_INFO_RE = re.compile(r"([가-힣0-9A-Za-z·\-\s]{2,30})(?:\s*센터|\s*정보|\s*어디|\s*알려|\s*번호)")

PROMPT_TMPL = """너는 지역아동센터 추천 비서다.
출력 규칙(중요): 아래 CENTER_CONTEXT에 있는 실제 센터만 사용한다. 답변은 반드시 "추천 줄"만 출력한다.
[CENTER_CONTEXT]
{center_context}
[사용자 질문] {question}
"""



INTENT_PROMPT = """너는 지역아동센터 챗봇의 '인텐트 분류기'다. 반드시 JSON만 출력한다.
[사용자 질문] {question}
"""

# ===== 오리지널 헬퍼 함수들 (전부 그대로 복구) =====
def extract_n(text: str) -> int | None:
    m = re.search(r"(\d+)\s*개", text)
    return int(m.group(1)) if m else None

def clean_answer(text: str, limit: int = 3) -> str:
    if not text: return ""
    text = text.replace("<|end_of_text|>", "").strip()
    if "### Response:" in text: text = text.split("### Response:")[-1].strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    rec = [ln for ln in lines if re.match(r"^\d+\)\s*", ln)]
    if rec: return "\n".join(rec[:limit]).strip()
    return (lines[0] if lines else "").strip()

def looks_like_template(answer: str) -> bool:
    bad = ["센터명(자치구)", "...", "2)...", "1) 센터명"]
    return any(x in (answer or "") for x in bad)

def format_centers(centers: list[dict], limit: int) -> str:
    lines = []
    for i, c in enumerate(centers[:limit], 1):
        lines.append(f"{i}) {c.get('center_name')}({c.get('district')}) - {c.get('distance_km')}km, 정원:{c.get('capacity')}, 토요일:{c.get('sat_yn')}, 전화:{c.get('phone')}")
    return "\n".join(lines).strip()

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = (math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))

def _to_float(x): return float(x) if x is not None else None

def parse_options(msg: str):
    m = msg.replace(" ", "")
    sat_yn = "Y" if "토요일" in m else None
    radius = float(mr.group(1)) if (mr := re.search(r"(\d+(?:\.\d+)?)km", m, re.IGNORECASE)) else 3.0
    min_capacity = int(mc.group(1)) if (mc := re.search(r"정원(\d+)", m)) else None
    district = md.group(1) if (md := re.search(r"([가-힣]{1,10}구)", msg)) else None
    requested_n = extract_n(msg)
    limit = requested_n if requested_n is not None else DEFAULT_N
    if re.search(r"(딱\s*하나|한\s*군데|한\s*곳|하나만|1개만)", m): limit = 1
    return {"sat_yn": sat_yn, "radius_km": radius, "min_capacity": min_capacity, "district": district, "limit": max(1, min(limit, MAX_N)), "candidate_limit": 1500}

def fetch_nearby(lat, lon, radius_km, district=None, sat_yn=None, min_capacity=None, candidate_limit=1500, limit=3, order="near"):
    where = ["LAT IS NOT NULL", "LON IS NOT NULL"]
    params = {"candidate_limit": candidate_limit}
    if district: where.append("DISTRICT = :district"); params["district"] = district
    if sat_yn in ("Y", "N"): where.append("SAT_YN = :sat_yn"); params["sat_yn"] = sat_yn
    if min_capacity is not None: where.append("CAPACITY >= :min_capacity"); params["min_capacity"] = int(min_capacity)
    lat_delta, lon_delta = radius_km / 111.0, radius_km / (111.0 * max(0.2, math.cos(math.radians(lat))))
    where.append("LAT BETWEEN :lat_min AND :lat_max"); where.append("LON BETWEEN :lon_min AND :lon_max")
    params.update({"lat_min": lat - lat_delta, "lat_max": lat + lat_delta, "lon_min": lon - lon_delta, "lon_max": lon + lon_delta})
    sql = text(f"SELECT CENTER_ID AS center_id, DISTRICT AS district, CENTER_NAME AS center_name, ADDRESS AS address, PHONE AS phone, CAPACITY AS capacity, LAT AS lat, LON AS lon, SAT_YN AS sat_yn, FEE AS fee FROM CHILD_CENTER WHERE {' AND '.join(where)} AND ROWNUM <= :candidate_limit")
    with engine.connect() as conn: rows = conn.execute(sql, params).mappings().all()
    scored = []
    for r in rows:
        rlat, rlon = _to_float(r.get("lat")), _to_float(r.get("lon"))
        if rlat is None or rlon is None: continue
        d = haversine_km(lat, lon, rlat, rlon)
        if d <= radius_km: rr = dict(r); rr["distance_km"] = round(d, 3); scored.append(rr)
    scored.sort(key=lambda x: x["distance_km"])
    if order == "far": scored.reverse()
    return scored[:limit]

def find_centers_by_name(name: str, limit: int = 5) -> list[dict]:
    clean_name = name.replace(" ", "").replace("센터", "")
    sql = text("SELECT CENTER_ID AS center_id, DISTRICT AS district, CENTER_NAME AS center_name, ADDRESS AS address, PHONE AS phone, CAPACITY AS capacity, LAT AS lat, LON AS lon, SAT_YN AS sat_yn, FEE AS fee FROM CHILD_CENTER WHERE (REPLACE(CENTER_NAME, ' ', '') LIKE :q1 OR CENTER_NAME LIKE :q2) AND ROWNUM <= :limit")
    with engine.connect() as conn: rows = conn.execute(sql, {"q1": f"%{clean_name}%", "q2": f"%{name}%", "limit": limit}).mappings().all()
    return [dict(r) for r in rows]

def extract_json_obj(raw: str) -> dict | None:
    try:
        raw = raw.replace("<|end_of_text|>", "").strip()
        lb, rb = raw.find("{"), raw.rfind("}")
        return json.loads(raw[lb:rb + 1]) if lb != -1 else None
    except: return None

def classify_intent_llm(msg: str) -> tuple[str, dict]:
    s_clean = msg.replace(" ", "").lower()
    if any(k in s_clean for k in ["가까", "근처", "추천", "어디있어", "센터알려"]): return "RECO_NEAR", {}
    if any(k in s_clean for k in ["전화", "번호"]): return "PHONE", {}
    if any(k in s_clean for k in ["주소", "위치", "지도"]): return "ADDRESS", {}
    try:
        raw = call_runpod(INTENT_PROMPT.format(question=msg), max_new_tokens=100)
        obj = extract_json_obj(raw)
        return (obj.get("intent"), obj.get("slots")) if obj else ("NOISE", {})
    except: return ("NOISE", {})

# ===== 메인 채팅 로직 (원본 유지) =====
@bp.post("/chat")
def ai2_chat():
    data = request.get_json(silent=True) or {}
    msg, lat, lon = (data.get("message") or "").strip(), data.get("lat"), data.get("lon")
    if not msg: return jsonify({"error": "No msg"}), 400

    if m_set := NAME_SET_RE.search(msg):
        session['user_name'] = m_set.group(2)
        return jsonify({"text": f"반가워요, {m_set.group(2)}님! 이름을 기억해둘게요.", "centers": []})
    if NAME_ASK_RE.search(msg):
        saved = session.get('user_name')
        return jsonify({"text": f"사용자님 성함은 {saved}입니다. 잊지 않고 있어요!" if saved else "아직 성함을 모르겠어요.", "centers": []})

    if any(k in msg.lower() for k in ["vs", "비교", "대비", "랑"]):
        parts = re.split(r"vs|랑|와|과|비교", msg.replace(" ", ""))
        if len(parts) >= 2:
            a_list, b_list = find_centers_by_name(parts[0], limit=1), find_centers_by_name(parts[1], limit=1)
            if a_list and b_list:
                a, b = a_list[0], b_list[0]
                res = f"비교 결과:\n- {a['center_name']} : {a['district']}, 정원 {a['capacity']}명\n- {b['center_name']} : {b['district']}, 정원 {b['capacity']}명"
                return jsonify({"text": res, "centers": [a, b]})

    if info_m := CENTER_INFO_RE.search(msg):
        c_name = info_m.group(1).strip()
        rows = find_centers_by_name(c_name, limit=1)
        if rows:
            c = rows[0]
            dist_str = f"\n- 거리: {round(haversine_km(lat, lon, c['lat'], c['lon']), 3)}km" if lat and c['lat'] else ""
            return jsonify({"text": f"[{c['center_name']}] 정보:\n- 자치구: {c['district']}{dist_str}\n- 주소: {c['address']}\n- 전화: {c['phone']}\n- 정원: {c['capacity']}명", "centers": rows})

    intent, slots = classify_intent_llm(msg)
    u_lat, u_lon = _to_float(lat), _to_float(lon)
    is_center = any(k in msg for k in ["센터", "추천", "가까", "번호", "주소", "정원", "곳"])

    if (intent in ("NOISE", "OUT_OF_DOMAIN") and not is_center) or any(k in msg for k in ["안녕", "반가워", "하이"]):
        try:
            raw = call_runpod(f"너는 친절한 AI 비서야. 한국어로 짧게 답해줘. 질문: {msg}\n### 응답:", max_new_tokens=100)
            ans = clean_answer(raw)
            return jsonify({"text": ans if ans and "RunPod" not in ans else "반가워요! 무엇을 도와드릴까요?", "centers": []})
        except: return jsonify({"text": "안녕하세요! 어떤 도움이 필요하신가요?", "centers": []})

    if (intent in ("RECO_NEAR", "RECO_FAR") or is_center) and u_lat:
        opt = parse_options(msg)
        min_cap = int(m.group(1)) if (m := CAPACITY_RE.search(msg)) else opt["min_capacity"]
        centers = fetch_nearby(u_lat, u_lon, radius_km=opt["radius_km"], min_capacity=min_cap, limit=opt['limit'], order="far" if intent == "RECO_FAR" else "near")
        if centers:
            db_ans = format_centers(centers, opt["limit"])
            try:
                ctx = "\n".join([f"- {c['center_name']} | {c.get('distance_km')}km" for c in centers])
                raw = call_runpod(PROMPT_TMPL.format(center_context=ctx, question=msg, limit=opt["limit"]), max_new_tokens=160)
                ans = clean_answer(raw, limit=opt["limit"])
                return jsonify({"text": ans if ans and "RunPod" not in ans else db_ans, "centers": centers})
            except: return jsonify({"text": db_ans, "centers": centers})

    return jsonify({"text": "지역아동센터 추천이나 정보를 도와드릴 수 있어요!", "centers": []})

# ===== [보고서 전용 라우트] - 채팅 로직에 영향을 주지 않는 독립 블록 =====
@bp.post("/b2b/report/generate")
def b2b_report_generate():
    data = request.get_json(silent=True) or {}
    district, yf, yt = (data.get("district") or "").strip(), data.get("year_from"), data.get("year_to")
    if not district or not yf or not yt: return jsonify({"report": "필수값이 누락되었습니다."}), 400
    try:
        # 1) DB 팩트 생성
        data_facts = make_data_facts(engine, district, int(yf), int(yt))
        # 2) RAG 검색 연동
        policy_docs = retriever_policy.retrieve(f"{district} 지원 운영", k=2)
        db_docs = retriever_db.retrieve(f"{district} 이용자수", k=3)
        rag_snippets = format_rag_block(db_docs + policy_docs, 900)
        # 3) LangChain 기반 보고서 생성
        report_text = brief_chain.invoke({"topic": "운영 개선 보고서", "district": district, "year_from": int(yf), "year_to": int(yt), "purpose": "결재용", "extra_block": "", "data_facts": data_facts, "rag_snippets": rag_snippets})
        return jsonify({"report": report_text})
    except Exception as e:
        logger.exception(e)
        return jsonify({"report": "현재 서버 연결이 원활하지 않아 보고서를 생성할 수 없습니다. 서버 상태를 확인해주세요."}), 500