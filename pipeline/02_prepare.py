import sqlite3
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 터미널이 출력하지 못하는 이모지나 특수문자같은걸 만났을때 대체 문자로 변경처리해서 에러를 방지
sys.stdout.reconfigure(errors="replace")

# transformers 실행시 발생하는 경고메시지등을 관리는 로깅처리 모듈
from transformers import logging as hf_logging

# 청킹하는 문자가 최대토큰갯수를 넘어설때 지저분하게 발생하는 에러 권고사항을 꺼줌
# 중요한 에러 문구는 그대로 출력 처리
hf_logging.set_verbosity_error()

from transformers import AutoTokenizer

from app.config import DB_PATH, EMBED_TOKENIZER

con = sqlite3.connect(DB_PATH)
con.execute("PRAGMA foreign_keys = ON")

tok = AutoTokenizer.from_pretrained(EMBED_TOKENIZER)

# 텍스트를 인자로 전달받아서 모델이 이해하는 토큰으로 나누고 토큰의 갯수를 반환하는 함수
def ntok(text):
   return len(tok.encode(text))

# 여러개의 문장을 토큰화 했을때 최소, 중간, 최대 토큰갯수를 파악하는 함수
def dist(values):
   return (f"최소 {min(values)} / 중앙 {int(statistics.median(values))} / 최대 {max(values)}")

if __name__ == "__main__":
  details = [
    "짧은 상품 설명",
    "조금 더 긴 상품 설명입니다",
    "아주 길고 자세한 상품 설명입니다...",
    "간단한 설명",
    "보통 길이의 상품 설명입니다"
  ]

  token_counts = [ntok(detail) for detail in details]
  print(token_counts) # [5, 8, 10, 4, 8]
  print(dist(token_counts)) # 최소 4 / 중앙 8 / 최대 10
