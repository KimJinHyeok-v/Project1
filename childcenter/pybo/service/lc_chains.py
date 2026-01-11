from __future__ import annotations
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pybo.service.lc_llm import RunPodLLM

BRIEF_PROMPT = PromptTemplate.from_template(
"""너는 지방정부 정책브리프를 쓰는 분석관입니다.

규칙
- 출력은 아래 [출력 형식] 그대로만 작성합니다.
- 출력에는 DATA_FACTS, EVIDENCE 원문을 그대로 복사하지 않습니다.
- 모든 문장은 반드시 "입니다."로 끝납니다.
- 과장 없이 간결하게 작성합니다.
- 불릿, 번호, 하이픈, 슬래시를 사용하지 않습니다.
- 숫자는 DATA_FACTS에 있는 값만 사용합니다. 없으면 "추가 확인 필요입니다."라고만 씁니다.
- 추가 요구사항/없음” 같은 입력 문구는 출력 금지(CONTEXT에 있어도 무시)
- 총 정원, 센터 수, 예측 이용자수”가 있으면 이용률(예측 이용자수 ÷ 총 정원)을 계산해 ‘여유/부족’ 판단 후 제안 2개를 고른다. (숫자는 DB 숫자만 사용)
- 문장 종결을 “~입니다.”로 강제하고, 출력 형식을 [데이터요약][진단][제안] 3블록으로 고정한다.

CONTEXT
{district} {year_from}~{year_to} {purpose} {extra_block}

DATA_FACTS
{data_facts}

EVIDENCE
{rag_snippets}
END_CONTEXT

[출력 형식]
[기초정보]
(2문장 이내)

[핵심지표]
(2~3문장 이내, 숫자 최소 2개 포함)

[진단 및 제안]
(2~3문장 이내, 증감률과 정원 대비 수요를 근거로 진단 1문장과 제안 1~2문장 작성)
""")

def build_brief_chain():
    llm = RunPodLLM(max_new_tokens=260)
    return BRIEF_PROMPT | llm | StrOutputParser()
