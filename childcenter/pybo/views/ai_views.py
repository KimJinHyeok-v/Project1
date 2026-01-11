import logging
from flask import Blueprint, render_template, request, jsonify, redirect, url_for

from pybo.service.runpod_service import call_runpod

logger = logging.getLogger(__name__)
bp = Blueprint("ai1", __name__, url_prefix="/ai")


@bp.get("/")
def ai_page():
    return render_template("main/ai.html")


# pybo/views/ai_views.py

@bp.post("/chat")
def ai_chat():
    data = request.get_json(silent=True) or {}
    user_msg = (data.get("message") or "").strip()
    model_type = data.get("model_type")  # 프론트에서 보낸 base, cp50, cp100
    lat = data.get("lat")
    lon = data.get("lon")

    if not user_msg:
        return jsonify({"error": "메시지가 비어있습니다."}), 400

    # 1️⃣ 인텐트 분류 (ai2의 엔진 활용)
    intent, slots = classify_intent_llm(user_msg)

    # 2️⃣ 추천 로직 (RECO_NEAR / RECO_FAR)
    if intent in ("RECO_NEAR", "RECO_FAR"):
        opt = parse_options(user_msg)
        # 위치 정보가 있을 때만 DB 조회
        centers = []
        if lat and lon:
            centers = fetch_nearby(float(lat), float(lon), radius_km=opt["radius_km"], order="near" if intent == "RECO_NEAR" else "far")
        
        # 모델별 답변 생성 (call_runpod 호출 시 model_type 전달)
        prompt = PROMPT_TMPL.format(center_context=format_centers(centers, opt['limit']), question=user_msg, limit=opt['limit'])
        text_out = call_runpod(prompt, model_type=model_type) # 모델 타입에 따라 어댑터 변경
        
        return jsonify({"text": clean_answer(text_out), "centers": centers})

    # 3️⃣ 정보 조회 로직 (PHONE, ADDRESS, FEE 등)
    elif intent in ("PHONE", "ADDRESS", "FEE", "CAP_SUM"):
        # DB에서 센터 정보 찾기 로직 수행
        center_name = slots.get("center_name") or ""
        rows = find_centers_by_name(center_name)
        # ... (ai2_chat_views.py의 포맷팅 로직 그대로 수행) ...
        return jsonify({"text": formatted_result, "centers": rows})

    # 4️⃣ 그 외 일반 대화
    else:
        text_out = call_runpod(user_msg, model_type=model_type)
        return jsonify({"text": text_out})

@bp.get("/v2")
def ai_v2_redirect():
    return redirect(url_for("ai2.ai2_page"))
