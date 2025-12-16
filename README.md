# Agentic AI를 활용한 지역아동센터 수요 예측 서비스

서울시 **자치구별 사회·인구·복지 지표**를 기반으로  
**XGBoost 회귀 모델**로 지역아동센터 이용자 수(2015~2030)를 예측하고,  
예측 결과를 **Flask + Oracle DB + 웹 UI**로 제공하는 서비스입니다.

> 현재 저장소는 **1차 프로젝트 결과물**로,  
> 데이터 전처리 → 모델 학습 → DB 적재 → 대시보드/예측 UI 연동까지 완료된 상태입니다.  
> 2차 프로젝트에서 Agentic AI / LLM 기반 지원 기능을 추가할 예정입니다.

---

## 1. 프로젝트 구조

## 프로젝트 구조

```text
childcenter/
 ├── data/
 │    ├── master_2015_2022.csv                # 실제 관측 데이터 (2015~2022)
 │    ├── predicted_child_user_2023_2030.csv  # XGBoost 예측값 (2023~2030)
 │    ├── GRDP_15~22.csv                      # GRDP 지표
 │    ├── 기초생활수급자_12~24.csv
 │    ├── 다문화가구_15~23.csv
 │    ├── 등록인구(연령별_동별)_14~24.xlsx
 │    ├── 시도_시군구_월별_이혼_11~24.xlsx
 │    ├── 아동복지시설_06~24.csv
 │    ├── 저소득_한부모가족_15~23.csv
 │    └── 학생_1만명당_사설학원수_10~24.csv
 │
 ├── docs/
 │    ├── 요구사항 정의서.xlsx
 │    ├── 요구사항분석서.docx
 │    ├── 화면설계서.pptx
 │    ├── 머신러닝 결과 보고서.docx
 │    ├── 개발스케줄,업무분장.xlsx
 │    ├── SequenceDiagram.png
 │    └── UsecaseDiagram.png
 │
 ├── pybo/
 │    ├── ml/
 │    │    ├── model_xgb.pkl        # 학습 완료된 XGBoost 모델
 │    │    ├── predictor.py         # /predict API에서 사용하는 예측 함수
 │    │    ├── future_predict.py    # 2023~2030 예측 CSV 생성 스크립트
 │    │    └── future_predict_backup.py
 │    │
 │    ├── static/
 │    │    ├── css/
 │    │    │    ├── dashboard.css
 │    │    │    ├── home.css
 │    │    │    ├── predict.css
 │    │    │    └── ai.css (예정)
 │    │    ├── style.css            # 전체 공통 스타일
 │    │    ├── bootstrap-icons.css  # 아이콘 폰트 스타일
 │    │    ├── fonts/
 │    │    │    ├── bootstrap-icons.woff
 │    │    │    └── bootstrap-icons.woff2
 │    │    └── images/
 │    │         ├── hero-introduce.jpg
 │    │         ├── hero-dashboard.jpg
 │    │         ├── hero-predict.png
 │    │         ├── hero-qna.jpg
 │    │         ├── ai-hero.jfif
 │    │         └── ...              # 메인/대시보드/AI/Q&A 관련 이미지
 │    │
 │    ├── templates/
 │    │    ├── base.html             # 공통 레이아웃(헤더/푸터/네비게이션)
 │    │    ├── main/
 │    │    │    ├── home.html        # 메인 홈 화면
 │    │    │    ├── introduce.html   # 프로젝트 소개 페이지
 │    │    │    ├── predict.html     # 예측 결과 + 서울 지도 시각화
 │    │    │    ├── dashboard.html   # 통계 대시보드(연도/자치구별 지표 시각화)
 │    │    │    └── ai.html          # 생성형 AI 서비스(추후 구현)
 │    │    ├── question/
 │    │    │    ├── qna.html         # Q&A 메인 화면
 │    │    │    ├── question_list.html
 │    │    │    ├── question_detail.html
 │    │    │    └── question_form.html
 │    │    ├── auth/
 │    │    │    ├── login.html
 │    │    │    ├── signup.html
 │    │    │    ├── find_id.html
 │    │    │    ├── reset_password_verify.html
 │    │    │    └── reset_password_change.html
 │    │    ├── policy/
 │    │    │    ├── privacy.html     # 개인정보처리방침
 │    │    │    └── terms.html       # 이용약관
 │    │    └── partials/
 │    │         ├── intro_content.html
 │    │         ├── seoul_map.svg
 │    │         └── seoul_map1.svg
 │    │
 │    ├── views/
 │    │    ├── main_views.py         # 홈/소개/대시보드/예측/AI 라우팅
 │    │    ├── predict_views.py      # /predict 관련 API 및 페이지
 │    │    ├── data_views.py         # /data/* 통계용 API
 │    │    ├── ai_views.py           # 생성형 AI 관련 라우팅(예정)
 │    │    ├── question_views.py     # Q&A 리스트/상세/등록
 │    │    ├── answer_views.py       # Q&A 답변 등록/수정/삭제
 │    │    └── auth_views.py         # 로그인/회원가입/비밀번호 찾기
 │    │
 │    ├── service/
 │    │    ├── auth_service.py       # 인증/회원 관련 서비스 로직
 │    │    ├── data_service.py       # 통계/예측 데이터 조회 서비스
 │    │    ├── qna_service.py        # Q&A 도메인 서비스
 │    │    ├── question_repository.py
 │    │    ├── region_repository.py
 │    │    └── user_repository.py
 │    │
 │    ├── models.py                  # SQLAlchemy 모델 정의
 │    └── __init__.py                # create_app() Flask App Factory
 │
 ├── migrations/                     # Flask-Migrate(Alembic) 마이그레이션 파일
 │    └── versions/                  # 스키마 변경 이력
 │
 ├── insert_region_data.py           # 2015~2022 데이터 Oracle DB 삽입
 ├── insert_future_region_data.py    # 2023~2030 예측 데이터 DB 삽입
 ├── train_model.py                  # 모델 학습 및 model_xgb.pkl 저장
 ├── check_db.py                     # DB 상태/레코드 수 점검용 유틸
 ├── EDA.ipynb                       # 탐색적 데이터 분석 노트
 ├── preprocessing.ipynb             # 전처리 실험 노트
 ├── models.ipynb                    # 모델링 실험 노트
 │
 ├── .flaskenv                       # Flask 환경 변수 설정 (FLASK_APP 등)
 ├── .gitignore                      # Git 제외 파일 설정
 ├── requirements.txt                # Python 패키지 의존성 리스트
 ├── config.py                       # Flask / SQLAlchemy / Oracle 설정
 └── README.md                       # (현재 문서)

2. 개발환경 세팅
2-1. 가상환경 생성
# (Windows 기준)
python -m venv venv
venv\Scripts\activate

2-2. 패키지 설치
pip install -r requirements.txt

2-3. Oracle XE 준비

서비스명: xe

유저: child

비밀번호: child1234

config.py / .flaskenv 에서 SQLALCHEMY_DATABASE_URI가 다음과 같이 설정되어야 합니다.

oracle+cx_oracle://child:child1234@localhost:1521/xe

3. 데이터 & DB 초기 세팅
3-1. 실제 데이터 삽입 (2015~2022)
python insert_region_data.py

3-2. 미래 예측 CSV 생성 (2023~2030)
python pybo/ml/future_predict.py


master_2015_2022.csv를 기반으로 XGBoost 모델을 사용하여
predicted_child_user_2023_2030.csv를 생성합니다.

3-3. 미래 예측 데이터 DB 삽입
python insert_future_region_data.py


CSV에 있는 2023~2030 자치구별 예측값을 Oracle DB에 적재합니다.

이후 웹 대시보드/예측 페이지는 DB에서 직접 조회해서 사용합니다.

4. 모델 재학습 (선택)

새로운 데이터나 피처를 추가한 뒤 모델을 다시 학습하려면:

python train_model.py


학습 완료 후 모델은 자동으로 pybo/ml/model_xgb.pkl로 저장됩니다.

predictor.py에서 이 파일을 로드하여 /predict API에서 사용합니다.

5. Flask 서버 실행

.flaskenv 덕분에 FLASK_APP 등은 자동 설정됩니다.

flask run

주요 URL

메인 페이지 / 소개 / 대시보드 / 예측

http://127.0.0.1:5000/

테스트용 데이터 API

http://127.0.0.1:5000/data/test

예측 API

POST http://127.0.0.1:5000/predict

6. 예측 API 명세 (Frontend 용)
✔ 엔드포인트
POST /predict
Content-Type: application/json

요청(JSON)
{
  "single_parent": 1500,
  "basic_beneficiaries": 8000,
  "multicultural_hh": 2000,
  "academy_cnt": 120.5,
  "grdp": 18000000
}


각 필드는 다음을 의미합니다.

single_parent : 자치구별 한부모 가구 수

basic_beneficiaries : 기초생활수급자 수

multicultural_hh : 다문화 가구 수

academy_cnt : 사설 학원 수

grdp : 지역 총소득(또는 1인당 GRDP 기반 지표)

응답(JSON)
{
  "success": true,
  "prediction": 1234.56
}


prediction : 입력 피처를 기반으로 예측된 지역아동센터 이용자 수

7. 유틸 스크립트
데이터베이스 상태 점검
python check_db.py


DB 연결 상태, 주요 테이블 레코드 수 등을 확인하는 용도입니다.

8. 향후 계획 (2차 프로젝트)

Agentic AI / LLM 연동