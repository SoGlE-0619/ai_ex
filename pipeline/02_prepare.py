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
from transformers import AutoTokenizer
hf_logging.set_verbosity_error()
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from app.config import DB_PATH, EMBED_TOKENIZER, EMBED_MAX_TOKENS
from app.db import query

con = sqlite3.connect(DB_PATH)
con.execute("PRAGMA foreign_keys = ON")
tok = AutoTokenizer.from_pretrained(EMBED_TOKENIZER)


# ========================================
#  커스텀 함수 정의
# ========================================
def ntok(text):
   return len(tok.encode(text))

def dist(values):
   return (f"최소 {min(values)} / 중앙 {int(statistics.median(values))} / 최대 {max(values)}")


# ================================================
#  필수 조절값 (실무에선 이 수치값만 조절해서 업무 활용 가능)
# ================================================
CHUNK_SIZE = 324
CHUNK_OVERLAP = 48
PREFIX_BUDGET = 32 
RESPLIT_OVER = EMBED_MAX_TOKENS - PREFIX_BUDGET
HEADERS = [("##", "section")] 
SEPERATORS = ["\n\n", "\n", "다", "요", ".", ",", ""]



# ================================================
#  청킹할 데이터 원본을 DB 테이블엥서 꺼냄
# ================================================
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
#  2차 청킹 시작 : 1차 청킹이후 추가 청킹이 필요할때 SEPARATOR, CHUNK_SIZE 기분으로 청킹
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
    rows.append((pid, pname, section, i, part))






  """
    문자 데이터 청킹 흐름 (보통 실무에서 아래 순서로 작업 프로세스가 고착화되어 있음)

    **필수로 이해해야 되는 개념**
    1- 일단 마크다운의 제목 구분자로 해서 의미단위로 먼저 짜름 (의미단의)
    (분기-A) 1차 단계에서 모든 청킹데이터가 최대토큰수안에 들어오면 그냥 무시
    (분기-B) 1차 단계에서 따른 청킹데이터중 최대토큰을 넘어가는게 있으면 2차 청킹작업 시작

    2- 1차에서 짤린 청킹덩어리중 최대토큰이 넘어가는 덩어리는 다시 반복돌면서 이번엔 문장단위로 청킹시도 (문장단위)
    3- 2차에서 짤랐는데도 아직도 최대토큰수를 넘어가면 계속 반복돌며 청킹

    **추가적으로 알아두면 좋은 개념**
    [상품명 > 위치] 본문내용 : 이런식으로 본문앞에 구분자를 붙이는 이유 
    - LLM 한테 청킹된 데이터를 전달할때 해당 데이터의 제목과 출처를 같이 알려줘서 본문 데이터의 맥락을 파악하게 하기 위함 
  """


