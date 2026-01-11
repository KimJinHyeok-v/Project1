# pybo/service/runpod_service.py
import os
import logging
import requests
from typing import Any, Optional

logger = logging.getLogger(__name__)
_SESSION = requests.Session()

def _get_runpod_url() -> str:
    return os.environ.get("RUNPOD_API_URL", "").strip()

def _require_runpod(url: str):
    if not url:
        return False, "RUNPOD_API_URL 환경변수가 설정되지 않았습니다."
    if not (url.startswith("http://") or url.startswith("https://")):
        return False, "RUNPOD_API_URL이 http(s)로 시작해야 합니다."
    return True, ""

def _extract_text(data: Any) -> str:
    if data is None:
        return ""

    if isinstance(data, str):
        return data.strip()

    if isinstance(data, dict):
        for k in ("text", "generated_text", "result", "content"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()

        out = data.get("output")
        if isinstance(out, str):
            return out.strip()
        if isinstance(out, dict):
            v = out.get("text") or out.get("generated_text")
            if isinstance(v, str):
                return v.strip()
        if isinstance(out, list) and out:
            first = out[0]
            if isinstance(first, str):
                return first.strip()
            if isinstance(first, dict):
                v = first.get("generated_text") or first.get("text")
                if isinstance(v, str):
                    return v.strip()

        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            c0 = choices[0] or {}
            if isinstance(c0, dict):
                t = c0.get("text")
                if isinstance(t, str) and t.strip():
                    return t.strip()
                msg = c0.get("message") or {}
                if isinstance(msg, dict):
                    ct = msg.get("content")
                    if isinstance(ct, str) and ct.strip():
                        return ct.strip()

    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, str):
            return first.strip()
        if isinstance(first, dict):
            v = first.get("generated_text") or first.get("text")
            if isinstance(v, str):
                return v.strip()

    return ""

def call_runpod(
    prompt: str,
    max_new_tokens: int = 256,
    *,
    model_key: str = "base",              # ✅ 추가: base/ckpt100/ckpt200
    temperature: Optional[float] = None,  # (선택)
    top_p: Optional[float] = None,        # (선택)
    raise_on_error: bool = False
) -> str:
    url = _get_runpod_url()
    ok, msg = _require_runpod(url)
    if not ok:
        return msg

    payload = {
        "prompt": prompt,
        "max_new_tokens": int(max_new_tokens),
        "model_key": model_key,   # ✅ RunPod로 전달
    }

    # 선택 파라미터는 있으면만 전달
    if temperature is not None:
        payload["temperature"] = float(temperature)
    if top_p is not None:
        payload["top_p"] = float(top_p)

    try:
        r = _SESSION.post(url, json=payload, timeout=(10, 120))

        if r.status_code >= 400:
            logger.error("RunPod HTTP %s | url=%s | body=%s", r.status_code, url, (r.text or "")[:2000])
            if raise_on_error:
                r.raise_for_status()

        r.raise_for_status()

        try:
            data = r.json()
        except ValueError:
            logger.error("RunPod 응답이 JSON이 아님 | body=%s", (r.text or "")[:2000])
            return "죄송합니다. RunPod 응답 형식이 올바르지 않습니다."

        text = _extract_text(data)

        if not text:
            logger.error("RunPod 응답이 비어 있음 | data=%r", data)
            return "죄송합니다. 응답이 비어 있습니다."

        return text

    except requests.RequestException as e:
        logger.exception("RunPod 호출 오류: %s", e)
        if raise_on_error:
            raise
        return "죄송합니다. RunPod LLM 서버 호출에 실패했습니다."
