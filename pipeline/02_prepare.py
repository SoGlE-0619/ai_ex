import sqlite3
import statistics
import sys
from pathlib import Path

# ========================================
#  우선 루트경로 지정 및 필수 메서드 import
# ========================================

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(errors="replace")

from transformers import logging as hf_logging

hf_logging.set_verbosity_error()

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from transformers import AutoTokenizer

from app.config import DB_PATH, EMBED_TOKENIZER, EMBED_MAX_TOKENS
from app.db import query

tok = AutoTokenizer.from_pretrained(EMBED_TOKENIZER)

# ========================================
#  커스텀 함수 정의
# ========================================
def ntok(text):
  return len(tok.encode(text))

def dist(values):
  return (f"최소 {min(values)} / 중앙 {int(statistics.median(values))} / 최대 {max(values)}")

# 접두어를 포함시켜 본문 생성 함수 (모델에게 전달하는 데이터의 문맥을 빠르게 파악시키기 위함)
# 세번째로 전달되는 인자값은 2차 청킹된 데이터가 1차 청킹만 완료된 본문
def with_context(pname, section, body):
  return f"[{pname} > {section}] {body}"

# [스킨로션 > 주의사항] 어쩌구 이렇게 써야됩니다.


# ================================================
#  필수 조절값 (실무에선 이 수치값만 조절해서 업무 활용 가능)
# ================================================
CHUNK_SIZE = 324
CHUNK_OVERLAP = 48 
PREFIX_BUDGET = 32 # [제품명 > 중제목]
RESPLIT_OVER = EMBED_MAX_TOKENS - PREFIX_BUDGET
HEADERS = [("##", "section")] 
SEPERATORS = ["\n\n", "\n", "다", "요", ".", ",", ""]



# ================================================
#  청킹할 데이터 원본을 DB 테이블엥서 꺼냄
# ================================================
con = sqlite3.connect(DB_PATH)
con.execute("PRAGMA foreign_keys = ON")

details = query("""
  SELECT product_details.product_id, products.name, product_details.detail
  FROM product_details JOIN products ON product_details.product_id = products.product_id
  ORDER BY product_details.product_id
""")


# ================================================
#  추출한 데이터의 토큰 갯수 알아내기
# ================================================
full_tokens = [ntok(detail) for _, _, detail in details]
over = [n for n in full_tokens if n > EMBED_MAX_TOKENS ]



# ================================================
#  1차 청킹 시작 : md파일의 제목을 기준으로 청킹
# ================================================
md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=HEADERS)
sections = []

for pid, pname, detail in details:
  for doc in md_splitter.split_text(detail):
    text = doc.page_content.strip() 
    if not text:
      continue
    sections.append((pid, pname, doc.metadata.get("section", "(머릿말)"), text))


# ==========================================================================
#  2차 청킹 시작 : 1차 청킹이후 추가 청킹이 필요할때 SEPARATOR, CHUNK_SIZE 기준으로 청킹
# ==========================================================================
resplitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
  tok, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, separators=SEPERATORS, keep_separator="end"
)

rows = [] 
n_resplit = 0

for pid, pname, section, text in sections:
  if ntok(text) > RESPLIT_OVER:
    n_resplit +=1
    parts = resplitter.split_text(text)  
  else:
    parts = [text]  

  for i, part in enumerate(parts):
    # 제품아이디, 제품명, (주의사항), 순번, 각각의 중제목에 대한 쪼개진 본문내용
    rows.append((pid, pname, section, i, part))

print(rows)

# 목적에 맞는 청킹 처리 (우리가 청킹을 하는 이유)
# 데이터 청킹을 짧게 해야할 때 vs 길게 해야할 때
# - 청킹데이터를 짜르는 이유는 : 사용자가 질문한 맥락에 맞는 자료조각을 탐색하기 위함
# - 탐색이 완료되면 제일연관도가 높은 조각들을 비교해서 그 조각이 바라보는 원문을 사용자에게 내보내면 됨
# - 선택된 위의 원문과 사용자 정보를 조합해서 LLM 전달
# - LLM 제공받은 정보를 통해서 그럴싸한 문장을 만들어내 내보내줌