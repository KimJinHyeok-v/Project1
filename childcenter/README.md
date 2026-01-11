### 지역아동센터 수요 예측

사회적 변화에 따른 다양한 가정 형태의 증가와 돌봄 공백 문제를 해결하기 위해, 공공 데이터를 기반으로 서울시 자치구별 센터 수요를 정밀하게 예측하고, 데이터 기반의 효율적인 센터 운영 정보를 제공합니다.

---

### 주요 기능

**대시보드 기능**
  ✅2015년부터 2022년까지의 서울시 자치구별 지역아동센터 이용 현황 제공

**머신러닝 예측**
  ✅XGBoost 모델을 활용하여 2023년부터 2030년까지의 자치구별 센터 이용자 수 예측
  ✅다차원 피처(Feature) 분석을 통해 도출된 예측 결과를 그래프 및 데이터 테이블로 직관적 제공

**생성형 AI 챗봇**
  ✅지역아동센터 운영 지침 및 관련 정보를 실시간으로 제공하는 AI 챗봇
    (RAG와 LangChain을 통해 단순 답변을 넘어선 컨텍스트 기반의 정교한 응답 구현 예정)

---

### flask 구조

childcenter
├─ data/                     # 전처리 및 분석용 데이터셋 (.csv, .xlsx)
├─ docs/                     # 프로젝트 기획서 및 설계 문서
├─ migrations/               # 데이터베이스 마이그레이션 이력
├─ pybo/                     # 애플리케이션 메인 패키지
│  ├─ ml/                    # ML 모델 및 예측 로직 (XGBoost)
│  │  ├─ model_xgb.pkl       # 학습된 예측 모델
│  │  └─ predictor.py        # 예측 실행 모듈
│  ├─ service/               # 비즈니스 로직 (Auth, RAG, Data Service)
│  ├─ static/                # 정적 파일 (CSS, JS, Images)
│  ├─ templates/               # HTML 템플릿 (JinJa2)
│  ├─ views/                  # Flask 블루프린트 (Controller)
│  └─ models.py              # SQLAlchemy DB 모델 정의
├─ EDA.ipynb                 # 데이터 탐색 및 시각화 노트북
├─ preprocessing.ipynb       # 데이터 전처리 파이프라인
├─ models.ipynb              # ML 모델 학습 및 검증 노트북
├─ config.py                 # 앱 환경 설정
├─ requirements.txt          # 의존성 패키지 목록
├─ train_model.py            # 모델 재학습 스크립트
└─ wsgi.py                   # 웹 서버 진입점

---

### 개발 현황
  [x] Data Engineering: 공공데이터(서울시, 통계청) 수집 및 데이터 파이프라인 전처리 완료

  [x] Model Training: XGBoost 기반의 수요 예측 모델 1차 학습 및 검증 완료

  [x] Backend Core: 데이터베이스 기반 챗봇 엔진 프로토타입 구현

  [x] System Architecture: Flask 프레임워크 기반 웹 서비스 기본 아키텍처 설계 완료

  [ ] AI Optimization: RAG 및 LangChain 고도화를 통한 고정밀 답변 엔진 업데이트

  [ ] Next Generation AI: MCP기반의 AI Agentic 시스템 전환 및 자동화 워크플로우 구현

---

### Data Sources (데이터 출처)
  ✅ 서울시 열린데이터 광장
  ✅ KOSIS 국가통계포털