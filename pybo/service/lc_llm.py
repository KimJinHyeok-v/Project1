from __future__ import annotations
import os
import logging
import requests
from typing import Optional, List, Any
from langchain_core.language_models.llms import LLM

logger = logging.getLogger(__name__)

# .flaskenv 또는 환경변수에서 가져온 런포드 프록시 URL
RUNPOD_API_URL = os.environ.get("RUNPOD_API_URL", "").strip()
_SESSION = requests.Session()

def _extract_text(data: Any) -> str:
    """RunPod 응답에서 텍스트를 추출하는 방어적 로직"""
    if data is None: return ""
    if isinstance(data, str): return data.strip()
    if isinstance(data, dict):
        # 1. 일반적인 Flask API 응답 처리
        for k in ("result", "output", "text", "generated_text", "content"):
            v = data.get(k)
            if isinstance(v, str) and v.strip(): return v.strip()
        
        # 2. OpenAI 규격(choices) 처리
        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            c0 = choices[0] or {}
            if isinstance(c0, dict):
                t = c0.get("text") or (c0.get("message") or {}).get("content")
                if isinstance(t, str): return t.strip()
    return str(data)

class RunPodLLM(LLM):
    max_new_tokens: int = 1000  # 보고서 생성을 위해 토큰 제한을 늘림
    timeout: int = 120

    @property
    def _llm_type(self) -> str:
        return "runpod_http_llm"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        logger.info("[LC] RunPodLLM._call 시도 중...")

        if not RUNPOD_API_URL:
            return "에러: RUNPOD_API_URL이 설정되지 않았습니다."

        # Pod 프록시용 페이로드 (서버리스와 구조가 다를 수 있음)
        payload = {
            "prompt": prompt,
            "max_new_tokens": int(kwargs.get("max_new_tokens", self.max_new_tokens)),
            "temperature": 0.7
        }

        try:
            # 401 에러 방지를 위해 headers에서 Authorization을 제외함
            headers = {"Content-Type": "application/json"}
            
            r = _SESSION.post(RUNPOD_API_URL, json=payload, headers=headers, timeout=self.timeout)
            r.raise_for_status()

            try:
                data = r.json()
            except:
                data = r.text

            text = _extract_text(data)

            if stop and text:
                for s in stop:
                    if s in text:
                        text = text.split(s, 1)[0]

            return text or "응답 값이 비어있습니다."

        except Exception as e:
            logger.error(f"RunPod 통신 실패: {str(e)}")
            return f"통신 에러가 발생했습니다: {str(e)}"

    @property
    def _identifying_params(self) -> dict:
        return {"url": RUNPOD_API_URL}