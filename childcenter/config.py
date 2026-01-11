import os

# 현재 config.py 파일이 있는 폴더 경로 (필요시 사용)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# SQLAlchemy 설정 (Oracle 접속 정보)
# 형식: oracle+cx_oracle://아이디:비밀번호@호스트:포트/서비스이름
SQLALCHEMY_DATABASE_URI = "oracle+cx_oracle://child:child1234@localhost:1521/xe"

# 수정 사항 추적 기능 비활성화 (메모리 절약)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 비밀키 설정
SECRET_KEY = "dev"

# (선택 사항) 한글 깨짐 방지 및 오라클 인코딩 설정
os.environ["NLS_LANG"] = ".UTF8"
RUNPOD_API_URL = "https://api.runpod.ai/v2/abc060ckiu6poc/runsync"
RUNPOD_API_KEY = "rpa_61UJPQHP165EQ3O9CTK36QJJTG362AJZJ40Q6LT91qd7z9"
