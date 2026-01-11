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
```
childcenter
├─ .dockerignore
├─ .flaskenv
├─ app.db
├─ check_db.py
├─ childcenter.zip
├─ Clean_ML_Report.png
├─ config.py
├─ data
│  ├─ child_centers_clean.json
│  ├─ GRDP_15~22.csv
│  ├─ master_2015_2022.csv
│  ├─ predicted_child_user_2023_2030.csv
│  ├─ 기초생활수급자_12~24.csv
│  ├─ 네트워크 - 바로 가기.lnk
│  ├─ 다문화가구_15~23.csv
│  ├─ 등록인구(연령별_동별)_14~24.xlsx
│  ├─ 시도_시군구_월별_이혼_11~24.xlsx
│  ├─ 아동복지시설_06~24.csv
│  ├─ 저소득_한부모가족_15~23.csv
│  ├─ 지역아동센터_자치구별_데이터.xlsx
│  ├─ 출생아수_06~24.csv
│  └─ 학생_1만명당_사설학원수_10~24.csv
├─ docker-compose.yml
├─ dockerfile
├─ Dockerfile.runtime
├─ Dockerfile.worker
├─ docs
│  ├─ README.md
│  ├─ requirement.txt
│  ├─ SequenceDiagram.png
│  ├─ UsecaseDiagram.png
│  ├─ 개발스케줄,업무분장.xlsx
│  ├─ 머신러닝 결과 보고서.docx
│  ├─ 요구사항 정의서.xlsx
│  ├─ 요구사항분석서.docx
│  └─ 화면설계서.pptx
├─ EDA.ipynb
├─ Final_ML_Project_Report.png
├─ final_model_performance_report.png
├─ final_professional_report.png
├─ final_project_report.png
├─ folder_structure.txt
├─ handler.py
├─ insert_future_region_data.py
├─ insert_region_data.py
├─ instance
│  ├─ app.db
│  └─ local_dev.db
├─ load_child_centers.py
├─ migrations
│  ├─ alembic.ini
│  ├─ env.py
│  ├─ README
│  ├─ script.py.mako
│  └─ versions
│     ├─ 995318d08496_initial_tables.py
│     └─ fee148399c62_add_users_and_qna_tables.py
├─ models.ipynb
├─ model_comparison_final.png
├─ predicted_child_user_2023_2030_cagr.csv
├─ preprocessing.ipynb
├─ pybo
│  ├─ forms.py
│  ├─ ml
│  │  ├─ future_predict.py
│  │  ├─ future_predict_backup.py
│  │  ├─ model_xgb.pkl
│  │  ├─ predictor.py
│  │  └─ python
│  ├─ models.py
│  ├─ rag_docs
│  │  └─ 지역아동센터 지원 사업안내(정제본).txt
│  ├─ rag_store
│  │  ├─ 84cfeb60-01b8-4dcf-8360-32f2f8c75bf6
│  │  │  ├─ data_level0.bin
│  │  │  ├─ header.bin
│  │  │  ├─ length.bin
│  │  │  └─ link_lists.bin
│  │  ├─ bde767b0-add2-4f07-a5d9-5aa020c43f38
│  │  │  ├─ data_level0.bin
│  │  │  ├─ header.bin
│  │  │  ├─ length.bin
│  │  │  └─ link_lists.bin
│  │  └─ chroma.sqlite3
│  ├─ service
│  │  ├─ auth_service.py
│  │  ├─ brief_facts_service.py
│  │  ├─ data_service.py
│  │  ├─ lc_chains.py
│  │  ├─ lc_llm.py
│  │  ├─ qna_service.py
│  │  ├─ question_repository.py
│  │  ├─ rag_ingest.py
│  │  ├─ rag_ingest_db.py
│  │  ├─ rag_service.py
│  │  ├─ region_repository.py
│  │  ├─ runpod_service.py
│  │  ├─ user_repository.py
│  │  └─ __init__.py
│  ├─ static
│  │  ├─ bootstrap-4.6.2-dist.zip
│  │  ├─ bootstrap-icons.css
│  │  ├─ bootstrap.bundle.js
│  │  ├─ bootstrap.bundle.js.map
│  │  ├─ bootstrap.bundle.min.js
│  │  ├─ bootstrap.bundle.min.js.map
│  │  ├─ bootstrap.min.css
│  │  ├─ bootstrap.min.js
│  │  ├─ css
│  │  │  ├─ ai.css
│  │  │  ├─ ai2.css
│  │  │  ├─ base.css
│  │  │  ├─ dashboard.css
│  │  │  ├─ home.css
│  │  │  ├─ predict.css
│  │  │  └─ theme.css
│  │  ├─ fonts
│  │  │  ├─ bootstrap-icons.woff
│  │  │  └─ bootstrap-icons.woff2
│  │  ├─ images
│  │  │  ├─ ai-hero.png
│  │  │  ├─ bigdata.jpg
│  │  │  ├─ carousel1.jpg
│  │  │  ├─ carousel1_1.jpg
│  │  │  ├─ carousel2.jpg
│  │  │  ├─ carousel2_1.jpg
│  │  │  ├─ carousel3.jpg
│  │  │  ├─ find_image
│  │  │  │  ├─ 27Qpq7pqCRfVf9Grzbgv9n-840-80.jpg.webp
│  │  │  │  ├─ 61d3ad52a9f76fcc29b4cfb81e0f21ad.jpg
│  │  │  │  ├─ ai-generated-8005084_1920.png
│  │  │  │  ├─ ai-pennwest-2024.jpg
│  │  │  │  ├─ Arte delle Equazioni Scientifiche Fantastiche di….jfif
│  │  │  │  ├─ Artificial intelligence may be the most intricate….jfif
│  │  │  │  ├─ deng-xiang--WXQm_NTK0U-unsplash.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_01.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_02.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_03.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_04.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_05.png
│  │  │  │  ├─ KakaoTalk_20251124_125842479_06.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_07.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_08.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_09.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_10.jpg
│  │  │  │  ├─ luke-chesser-JKUTrJ4vK00-unsplash.jpg
│  │  │  │  ├─ pexels-rdne-7947663.jpg
│  │  │  │  ├─ Skærmbillede-2017-09-04-kl.-16.00.22.png
│  │  │  │  ├─ vecteezy_digital-business-image-with-graphs-and-diagrams-over-blue_25500634.jpg
│  │  │  │  ├─ What the world will be like in 30 years, according….jfif
│  │  │  │  └─ 🧠 Next-gen technology analyzes writing style DNA….jfif
│  │  │  ├─ hero-introduce.jpg
│  │  │  ├─ hero-predict.png
│  │  │  ├─ hero-qna.jpg
│  │  │  ├─ logo-black.png
│  │  │  ├─ logo.png
│  │  │  ├─ logo2.png
│  │  │  ├─ logo3.png
│  │  │  ├─ logo4.png
│  │  │  ├─ logo5.png
│  │  │  ├─ logo_cropped.png
│  │  │  ├─ privacy-hero.jpg
│  │  │  ├─ section2_1.jpg
│  │  │  ├─ section2_2.jpg
│  │  │  ├─ section3_qna.jpg
│  │  │  └─ terms-hero.webp
│  │  ├─ jquery-3.7.1.min.js
│  │  ├─ js
│  │  │  ├─ ai2.js
│  │  │  ├─ Chart-bar.html
│  │  │  ├─ Chart-line.html
│  │  │  ├─ Chart-pie.html
│  │  │  ├─ dashboard.js
│  │  │  ├─ Multi-line.html
│  │  │  └─ predict.js
│  │  └─ style.css
│  ├─ templates
│  │  ├─ ai
│  │  ├─ auth
│  │  │  ├─ find_id.html
│  │  │  ├─ login.html
│  │  │  ├─ logout.html
│  │  │  ├─ reset_password_change.html
│  │  │  ├─ reset_password_verify.html
│  │  │  └─ signup.html
│  │  ├─ base.html
│  │  ├─ form_errors.html
│  │  ├─ main
│  │  │  ├─ ai.html
│  │  │  ├─ ai2.html
│  │  │  ├─ dashboard.html
│  │  │  ├─ home.html
│  │  │  ├─ introduce.html
│  │  │  └─ predict.html
│  │  ├─ partials
│  │  │  ├─ intro_content.html
│  │  │  ├─ seoul_map.svg
│  │  │  └─ seoul_map1.svg
│  │  ├─ policy
│  │  │  ├─ privacy.html
│  │  │  └─ terms.html
│  │  └─ question
│  │     ├─ qna.html
│  │     ├─ question_detail.html
│  │     ├─ question_form.html
│  │     └─ question_list.html
│  ├─ views
│  │  ├─ ai2_chat_views.py
│  │  ├─ ai2_hub.views.py
│  │  ├─ ai2_views.py
│  │  ├─ ai_tools_views.py
│  │  ├─ ai_views.py
│  │  ├─ answer_views.py
│  │  ├─ auth_views.py
│  │  ├─ center_api_views.py
│  │  ├─ data_views.py
│  │  ├─ main_views.py
│  │  ├─ predict_views.py
│  │  └─ question_views.py
│  └─ __init__.py
├─ rag_docs
│  └─ rag_store
│     └─ chroma.sqlite3
├─ rag_store
│  └─ chroma.sqlite3
├─ README.md
├─ requirements.txt
├─ requirements_serverless.txt
├─ train_model.py
├─ wsgi.py
└─ xgb_performance_report.png

```
```
childcenter
├─ .dockerignore
├─ .flaskenv
├─ app.db
├─ check_db.py
├─ childcenter.zip
├─ Clean_ML_Report.png
├─ config.py
├─ data
│  ├─ child_centers_clean.json
│  ├─ GRDP_15~22.csv
│  ├─ master_2015_2022.csv
│  ├─ predicted_child_user_2023_2030.csv
│  ├─ 기초생활수급자_12~24.csv
│  ├─ 네트워크 - 바로 가기.lnk
│  ├─ 다문화가구_15~23.csv
│  ├─ 등록인구(연령별_동별)_14~24.xlsx
│  ├─ 시도_시군구_월별_이혼_11~24.xlsx
│  ├─ 아동복지시설_06~24.csv
│  ├─ 저소득_한부모가족_15~23.csv
│  ├─ 지역아동센터_자치구별_데이터.xlsx
│  ├─ 출생아수_06~24.csv
│  └─ 학생_1만명당_사설학원수_10~24.csv
├─ docker-compose.yml
├─ dockerfile
├─ Dockerfile.runtime
├─ Dockerfile.worker
├─ docs
│  ├─ README.md
│  ├─ requirement.txt
│  ├─ SequenceDiagram.png
│  ├─ UsecaseDiagram.png
│  ├─ 개발스케줄,업무분장.xlsx
│  ├─ 머신러닝 결과 보고서.docx
│  ├─ 요구사항 정의서.xlsx
│  ├─ 요구사항분석서.docx
│  └─ 화면설계서.pptx
├─ EDA.ipynb
├─ Final_ML_Project_Report.png
├─ final_model_performance_report.png
├─ final_professional_report.png
├─ final_project_report.png
├─ folder_structure.txt
├─ handler.py
├─ insert_future_region_data.py
├─ insert_region_data.py
├─ instance
│  ├─ app.db
│  └─ local_dev.db
├─ load_child_centers.py
├─ migrations
│  ├─ alembic.ini
│  ├─ env.py
│  ├─ README
│  ├─ script.py.mako
│  └─ versions
│     ├─ 995318d08496_initial_tables.py
│     └─ fee148399c62_add_users_and_qna_tables.py
├─ models.ipynb
├─ model_comparison_final.png
├─ predicted_child_user_2023_2030_cagr.csv
├─ preprocessing.ipynb
├─ pybo
│  ├─ forms.py
│  ├─ ml
│  │  ├─ future_predict.py
│  │  ├─ future_predict_backup.py
│  │  ├─ model_xgb.pkl
│  │  ├─ predictor.py
│  │  └─ python
│  ├─ models.py
│  ├─ rag_docs
│  │  └─ 지역아동센터 지원 사업안내(정제본).txt
│  ├─ rag_store
│  │  ├─ 84cfeb60-01b8-4dcf-8360-32f2f8c75bf6
│  │  │  ├─ data_level0.bin
│  │  │  ├─ header.bin
│  │  │  ├─ length.bin
│  │  │  └─ link_lists.bin
│  │  ├─ bde767b0-add2-4f07-a5d9-5aa020c43f38
│  │  │  ├─ data_level0.bin
│  │  │  ├─ header.bin
│  │  │  ├─ length.bin
│  │  │  └─ link_lists.bin
│  │  └─ chroma.sqlite3
│  ├─ service
│  │  ├─ auth_service.py
│  │  ├─ brief_facts_service.py
│  │  ├─ data_service.py
│  │  ├─ lc_chains.py
│  │  ├─ lc_llm.py
│  │  ├─ qna_service.py
│  │  ├─ question_repository.py
│  │  ├─ rag_ingest.py
│  │  ├─ rag_ingest_db.py
│  │  ├─ rag_service.py
│  │  ├─ region_repository.py
│  │  ├─ runpod_service.py
│  │  ├─ user_repository.py
│  │  └─ __init__.py
│  ├─ static
│  │  ├─ bootstrap-4.6.2-dist.zip
│  │  ├─ bootstrap-icons.css
│  │  ├─ bootstrap.bundle.js
│  │  ├─ bootstrap.bundle.js.map
│  │  ├─ bootstrap.bundle.min.js
│  │  ├─ bootstrap.bundle.min.js.map
│  │  ├─ bootstrap.min.css
│  │  ├─ bootstrap.min.js
│  │  ├─ css
│  │  │  ├─ ai.css
│  │  │  ├─ ai2.css
│  │  │  ├─ base.css
│  │  │  ├─ dashboard.css
│  │  │  ├─ home.css
│  │  │  ├─ predict.css
│  │  │  └─ theme.css
│  │  ├─ fonts
│  │  │  ├─ bootstrap-icons.woff
│  │  │  └─ bootstrap-icons.woff2
│  │  ├─ images
│  │  │  ├─ ai-hero.png
│  │  │  ├─ bigdata.jpg
│  │  │  ├─ carousel1.jpg
│  │  │  ├─ carousel1_1.jpg
│  │  │  ├─ carousel2.jpg
│  │  │  ├─ carousel2_1.jpg
│  │  │  ├─ carousel3.jpg
│  │  │  ├─ find_image
│  │  │  │  ├─ 27Qpq7pqCRfVf9Grzbgv9n-840-80.jpg.webp
│  │  │  │  ├─ 61d3ad52a9f76fcc29b4cfb81e0f21ad.jpg
│  │  │  │  ├─ ai-generated-8005084_1920.png
│  │  │  │  ├─ ai-pennwest-2024.jpg
│  │  │  │  ├─ Arte delle Equazioni Scientifiche Fantastiche di….jfif
│  │  │  │  ├─ Artificial intelligence may be the most intricate….jfif
│  │  │  │  ├─ deng-xiang--WXQm_NTK0U-unsplash.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_01.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_02.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_03.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_04.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_05.png
│  │  │  │  ├─ KakaoTalk_20251124_125842479_06.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_07.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_08.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_09.jpg
│  │  │  │  ├─ KakaoTalk_20251124_125842479_10.jpg
│  │  │  │  ├─ luke-chesser-JKUTrJ4vK00-unsplash.jpg
│  │  │  │  ├─ pexels-rdne-7947663.jpg
│  │  │  │  ├─ Skærmbillede-2017-09-04-kl.-16.00.22.png
│  │  │  │  ├─ vecteezy_digital-business-image-with-graphs-and-diagrams-over-blue_25500634.jpg
│  │  │  │  ├─ What the world will be like in 30 years, according….jfif
│  │  │  │  └─ 🧠 Next-gen technology analyzes writing style DNA….jfif
│  │  │  ├─ hero-introduce.jpg
│  │  │  ├─ hero-predict.png
│  │  │  ├─ hero-qna.jpg
│  │  │  ├─ logo-black.png
│  │  │  ├─ logo.png
│  │  │  ├─ logo2.png
│  │  │  ├─ logo3.png
│  │  │  ├─ logo4.png
│  │  │  ├─ logo5.png
│  │  │  ├─ logo_cropped.png
│  │  │  ├─ privacy-hero.jpg
│  │  │  ├─ section2_1.jpg
│  │  │  ├─ section2_2.jpg
│  │  │  ├─ section3_qna.jpg
│  │  │  └─ terms-hero.webp
│  │  ├─ jquery-3.7.1.min.js
│  │  ├─ js
│  │  │  ├─ ai2.js
│  │  │  ├─ Chart-bar.html
│  │  │  ├─ Chart-line.html
│  │  │  ├─ Chart-pie.html
│  │  │  ├─ dashboard.js
│  │  │  ├─ Multi-line.html
│  │  │  └─ predict.js
│  │  └─ style.css
│  ├─ templates
│  │  ├─ ai
│  │  ├─ auth
│  │  │  ├─ find_id.html
│  │  │  ├─ login.html
│  │  │  ├─ logout.html
│  │  │  ├─ reset_password_change.html
│  │  │  ├─ reset_password_verify.html
│  │  │  └─ signup.html
│  │  ├─ base.html
│  │  ├─ form_errors.html
│  │  ├─ main
│  │  │  ├─ ai.html
│  │  │  ├─ ai2.html
│  │  │  ├─ dashboard.html
│  │  │  ├─ home.html
│  │  │  ├─ introduce.html
│  │  │  └─ predict.html
│  │  ├─ partials
│  │  │  ├─ intro_content.html
│  │  │  ├─ seoul_map.svg
│  │  │  └─ seoul_map1.svg
│  │  ├─ policy
│  │  │  ├─ privacy.html
│  │  │  └─ terms.html
│  │  └─ question
│  │     ├─ qna.html
│  │     ├─ question_detail.html
│  │     ├─ question_form.html
│  │     └─ question_list.html
│  ├─ views
│  │  ├─ ai2_chat_views.py
│  │  ├─ ai2_hub.views.py
│  │  ├─ ai2_views.py
│  │  ├─ ai_tools_views.py
│  │  ├─ ai_views.py
│  │  ├─ answer_views.py
│  │  ├─ auth_views.py
│  │  ├─ center_api_views.py
│  │  ├─ data_views.py
│  │  ├─ main_views.py
│  │  ├─ predict_views.py
│  │  └─ question_views.py
│  └─ __init__.py
├─ rag_docs
│  └─ rag_store
│     └─ chroma.sqlite3
├─ rag_store
│  └─ chroma.sqlite3
├─ README.md
├─ requirements.txt
├─ requirements_serverless.txt
├─ train_model.py
├─ wsgi.py
└─ xgb_performance_report.png

```