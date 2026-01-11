from flask import Blueprint, request, jsonify, session
from pybo.service.runpod_service import call_runpod
import re

bp = Blueprint("ai_tools", __name__, url_prefix="/ai/api")

# ---- name memory regex ----
NAME_SET_RE = re.compile(r"(내\s*이름은|나는)\s*([가-힣A-Za-z]{2,20})(이야|입니다|야)?")
NAME_ASK_RE = re.compile(r"(내\s*이름(이|은)\s*뭐(야|지)|내\s*이름\s*알아\??)")

# ✅ 이모지 제거용(모듈 레벨)
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U0001F1E0-\U0001F1FF"
    "]+",
    flags=re.UNICODE
)

def _clean_llm_text(t: str) -> str:
    if not isinstance(t, str):
        return ""
    # ✅ 응답 구간만 추출
    if "### 응답:" in t:
        t = t.split("### 응답:", 1)[-1]
    # ✅ 깨진 문자 제거
    t = t.replace("\ufffd", "")
    # ✅ 이모지 제거
    t = _EMOJI_RE.sub("", t)
    return t.strip()

def _get_ai_state():
    st = session.get("ai_state")
    if not st:
        st = {"profile": {}, "history": []}
        session["ai_state"] = st
    return st

def _save_ai_state(st):
    st["history"] = (st.get("history") or [])[-12:]
    session["ai_state"] = st

def _classify_auto(text: str) -> str:
    t = text.strip().lower()
    if "번역" in t or "translate" in t:
        return "trans"
    if "개체명" in t or "ner" in t:
        return "ner"
    if "감성" in t or "긍정" in t or "부정" in t or "중립" in t or "sentiment" in t:
        return "sentiment"
    if "질문" in t or "?" in t:
        return "qa"
    return "gen"

def _build_prompt(task: str, user_text: str, profile: dict) -> str:
    name = profile.get("name")
    name_line = f"사용자의 이름은 {name}이다. 이름 질문이 나오면 이 정보를 사용해라.\n" if name else ""

    if task == "qa":
        return (
            "너는 한국어로만 답한다.\n"
            "아래 '### 응답:' 다음 줄에 답만 출력한다.\n"
            + name_line +
            f"질문: {user_text}\n"
            "### 응답:\n"
        )

    # gen (일단 gen만 강하게)
    return (
        "너는 한국어로만 답한다.\n"
        "규칙/주제/질문/답 같은 라벨을 출력하지 않는다.\n"
        "아래 '### 응답:' 다음 줄에 최종 답만 1~3문장으로 출력한다.\n"
        + name_line +
        f"입력: {user_text}\n"
        "### 응답:\n"
    )

@bp.post("/chat")
def api_chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    mode = (data.get("mode") or "auto").strip()
    model = (data.get("model") or "base").strip()

    if not message:
        return jsonify({"error": "메시지를 입력해 주세요."}), 400

    st = _get_ai_state()
    profile = st.get("profile", {})
    history = st.get("history", [])

    # 1) 이름 저장
    m = NAME_SET_RE.search(message)
    if m:
        profile["name"] = m.group(2)
        bot = f"오케이. 앞으로 {profile['name']}이라고 기억할게."
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": bot})
        st["profile"] = profile
        st["history"] = history
        _save_ai_state(st)
        return jsonify({"text": bot, "task": "memory", "model": model})

    # 2) 이름 질문
    if NAME_ASK_RE.search(message):
        name = profile.get("name")
        bot = f"너 이름은 {name}이야." if name else "아직 이름을 못 들었어. '내 이름은 ___야'라고 말해줘."
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": bot})
        st["profile"] = profile
        st["history"] = history
        _save_ai_state(st)
        return jsonify({"text": bot, "task": "memory", "model": model})

    # 3) task 결정
    task = _classify_auto(message) if mode == "auto" else mode

    # 4) prompt
    prompt = _build_prompt(task, message, profile)

    # 5) RunPod 호출 (runpod_service.py가 model_key 지원해야 함)
    result = call_runpod(prompt, model_key=model, max_new_tokens=256)

    if isinstance(result, str) and (result.startswith("죄송합니다") or result.startswith("RUNPOD_API_URL")):
        return jsonify({"error": result}), 503

    # ✅ 정리된 텍스트만 반환/저장
    clean = _clean_llm_text(result)

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": clean})
    st["profile"] = profile
    st["history"] = history
    _save_ai_state(st)

    return jsonify({"text": clean, "task": task, "model": model})
