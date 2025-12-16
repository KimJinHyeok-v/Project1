from flask import Blueprint, render_template, request, jsonify
from transformers import pipeline
import logging
import os
import json     
from gradio_client import Client 
from config import USE_LLAMA, LLAMA3_BASE_URL

logger = logging.getLogger(__name__)

bp = Blueprint('ai', __name__, url_prefix='/ai')
LLAMA3_CLIENT = None

# --------------------------------local 설정--------------------------------
# 1. gpt2 텍스트생성
LOCAL_TEXT_GEN = pipeline(
    'text-generation',
    model = 'skt/kogpt2-base-v2')

def generate_text_local(prompt: str) -> str:
    try:
        outputs = LOCAL_TEXT_GEN(
            prompt,
            max_length=50,    
            do_sample=True,    
            top_k=50,          
            top_p=0.95        
        )
        text = outputs[0]["generated_text"]
        if text.startswith(prompt):
            return text[len(prompt):].strip()
        return text.strip()
        
    except Exception as e:
        logger.error(f"로컬 텍스트 생성 오류: {e}")
        return f"로컬 모델 오류: {e}"

# 2. nllb 번역
NLLB_MODEL_NAME = "facebook/nllb-200-distilled-600M"

translator_ko_en = pipeline(
    "translation",
    model=NLLB_MODEL_NAME,
    src_lang="kor_Hang",
    tgt_lang="eng_Latn",
)

def translate_local_ko_en(text: str) -> str:
    try:
        result = translator_ko_en(text)
        return result[0]["translation_text"]
    except Exception as e:
        logger.error(f"로컬 번역 오류: {e}")
        return f"로컬 번역 모델 오류: {e}"


# 3. KcELECTRA 감성분석
LOCAL_SENTIMENT = pipeline(
    "text-classification",
    model="beomi/KcELECTRA-base-v2022",
)

def sentiment_local(text: str) -> str:
    try:
        result = LOCAL_SENTIMENT(text)[0]
        label = result["label"]
        score = result["score"]
        return f"{label} (score={score:.4f})"
    except Exception as e:
        logger.error(f"로컬 감성 분석 오류: {e}")
        return f"로컬 감성 분석 모델 오류: {e}"


# 4. bert-ner 개체명인식
LOCAL_NER = pipeline(
    "ner",
    model="Davlan/bert-base-multilingual-cased-ner-hrl",
    tokenizer="Davlan/bert-base-multilingual-cased-ner-hrl",
    aggregation_strategy="simple",
)

def ner_local(text: str) -> str:
    try:
        results = LOCAL_NER(text)
        lines = []
        for ent in results:
            word = ent["word"]
            ent_type = ent["entity_group"]
            score = ent["score"]
            lines.append(f"{word} ({ent_type}) - score: {score:.4f}")
        return "\n".join(lines) if lines else "인식된 개체명이 없습니다."
    except Exception as e:
        logger.error(f"로컬 NER 오류: {e}")
        return f"로컬 NER 모델 오류: {e}"


# 5. KoELECTRA KorQuAD 질의응답
LOCAL_QA = pipeline(
    "question-answering",
    model="monologg/koelectra-base-v3-finetuned-korquad",
    tokenizer="monologg/koelectra-base-v3-finetuned-korquad",
)

def qa_local(context: str, question: str) -> str:
    try:
        result = LOCAL_QA(question=question, context=context)
        return result["answer"]
    except Exception as e:
        logger.error(f"로컬 QA 오류: {e}")
        return f"로컬 QA 모델 오류: {e}"


# --------------------------------local 설정 끝--------------------------------


# llama api 로딩 너무 오래걸려서
def get_llama_client():

    global LLAMA3_CLIENT

    # 로컬 모드면 아예 시도조차 안 함
    if not USE_LLAMA:
        return None

    # 이미 만들어져 있으면 바로 재사용
    if LLAMA3_CLIENT is not None:
        return LLAMA3_CLIENT

    # 처음 사용할 때만 Gradio 서버에 연결 시도
    try:
        client = Client(LLAMA3_BASE_URL)
        LLAMA3_CLIENT = client
        logger.info('Gradio Client for Llama 3 initialized successfully.')
        return client
    except Exception as e:
        logger.error(f'Error initializing Gradio Client: {e}')
        return None




# Llama 3 API 호출 (Gradio)
def generate_text_from_llama3(user_prompt):
    client = get_llama_client()
    if client is None:
         return "죄송합니다. Gradio Client 초기화에 실패하여 Llama 3 서버에 접속할 수 없습니다."

    try:
        generated_text = client.predict(
            user_prompt,          
            384,                  # max_new_tokens=256
            api_name="/predict"
        )
        return generated_text
        
    except Exception as e:
        error_message = f"Llama 3 API 호출 중 오류 발생. (Gradio Client Error): {e}"
        logger.error(error_message)
        return "죄송합니다. Llama 3 AI 서버(Colab)에 문제가 발생했거나 응답이 지연되고 있습니다."


def textgen_unified(user_input: str) -> str:
    # Llama용 프롬프트
    llama_prompt = (
        "당신은 지역아동센터 정책 기획자입니다. "
        "다음 주제에 대한 정책 제안서 또는 알림장 초안을 상세하고 친절한 문체로 작성해주세요: "
        f"{user_input}"
    )

    if USE_LLAMA:
        return generate_text_from_llama3(llama_prompt)
    else:
        # 로컬에선 그냥 사용자 입력을 바로 KoGPT2에 넣음
        return generate_text_local(user_input)

#---------------------------------------------
# 텍스트생성
@bp.route("/api/generate-text", methods=["POST"])
def api_generate_text():
    data = request.json
    input_text = data.get("inputText", "").strip()

    if not input_text:
        return jsonify({"error": "생성할 주제를 입력해 주세요."}), 400

    result = textgen_unified(input_text)

    if result.startswith("죄송합니다"):
        return jsonify({"error": result}), 503

    return jsonify({"result": result})

#---------------------------------------------
# 번역기 API

def translate_unified_ko_en(text: str) -> str:
    if USE_LLAMA:
        prompt = (
            "당신은 전문 번역가입니다. 제공된 한국어 텍스트를 문맥에 맞게 정확한 영어로 번역하고, "
            "번역 결과 외의 다른 설명은 일절 포함하지 마세요. "
            f"한국어 텍스트: {text}"
        )
        return generate_text_from_llama3(prompt)
    else:
        return translate_local_ko_en(text)


@bp.route("/api/translate-text", methods=["POST"])
def api_translate_text():
    data = request.json
    input_text = data.get("inputText", "").strip()

    if not input_text:
        return jsonify({"error": "번역할 텍스트를 입력해 주세요."}), 400

    result = translate_unified_ko_en(input_text)

    if result.startswith("죄송합니다"):
        return jsonify({"error": result}), 503

    return jsonify({"result": result})


# ---------------------------------------------
# 개체명 인식 
def ner_unified(text: str) -> str:
    if USE_LLAMA:
        prompt = (
            "당신은 전문 개체명 인식 시스템입니다. 다음 한국어 텍스트에서 '사람', '장소', '날짜', '기관'에 해당하는 모든 개체명을 추출하고, "
            "각 개체명과 그 유형을 '개체명: 유형, 개체명: 유형, ...' 형식으로만 나열하세요. 다른 설명은 일절 포함하지 마세요. "
            f"텍스트: {text}"
        )
        return generate_text_from_llama3(prompt)
    else:
        return ner_local(text)


@bp.route("/api/ner", methods=["POST"])
def api_ner():
    data = request.json
    input_text = data.get("inputText", "").strip()

    if not input_text:
        return jsonify({"error": "개체명 인식할 텍스트를 입력해 주세요."}), 400

    result = ner_unified(input_text)

    if result.startswith("죄송합니다"):
        return jsonify({"error": result}), 503

    return jsonify({"result": result})

# ---------------------------------------------
# 질의응답 
def qa_unified(context: str, question: str) -> str:
    if USE_LLAMA:
        prompt = (
            "당신은 배경 텍스트 기반 질의응답 전문가입니다. 아래 제공된 [배경 텍스트]를 참고하여 [질문]에 대한 답을 정확하게 한 문장으로 제시하세요. "
            "답변 외의 불필요한 서론/결론/설명은 포함하지 마세요. "
            f"[배경 텍스트]: {context}\n[질문]: {question}"
        )
        return generate_text_from_llama3(prompt)
    else:
        return qa_local(context, question)


@bp.route("/api/qa", methods=["POST"])
def api_qa():
    data = request.json
    context = data.get("context", "").strip()
    question = data.get("question", "").strip()

    if not context or not question:
        return jsonify({"error": "질문과 배경 텍스트를 모두 입력해 주세요."}), 400

    result = qa_unified(context, question)

    if result.startswith("죄송합니다"):
        return jsonify({"error": result}), 503

    return jsonify({"result": result})

# ---------------------------------------------
# 감성분석
def sentiment_unified(text: str) -> str:
    if USE_LLAMA:
        prompt = (
            "당신은 감성분석 전문가입니다. 다음 텍스트가 '긍정', '부정', '중립' 중 어떤 감성인지 판단하여 "
            "해당 감성만 한 단어로 출력하세요. "
            f"텍스트: {text}"
        )
        return generate_text_from_llama3(prompt)
    else:
        return sentiment_local(text)


@bp.route("/api/sentiment", methods=["POST"])
def api_sentiment():
    data = request.json
    input_text = data.get("inputText", "").strip()

    if not input_text:
        return jsonify({"error": "감성 분석할 텍스트를 입력해 주세요."}), 400

    result = sentiment_unified(input_text)

    if result.startswith("죄송합니다"):
        return jsonify({"error": result}), 503

    return jsonify({"result": result.strip()})
