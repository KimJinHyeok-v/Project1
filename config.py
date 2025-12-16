import os

BASE_DIR = os.path.dirname(__file__)
print("BASE_DIR:", BASE_DIR)

SQLALCHEMY_DATABASE_URI = "oracle+cx_oracle://child:child1234@localhost:1521/xe"
print("SQLALCHEMY_DATABASE_URI:", SQLALCHEMY_DATABASE_URI)

SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = "dev"  # 나중에 배포 시에는 더 복잡한 값으로 바꾸기


# llama3.1 쓸거면 True, 실습모델 쓸거면 False
USE_LLAMA = False
LLAMA3_BASE_URL = "https://02ba904721eedc0afb.gradio.live"