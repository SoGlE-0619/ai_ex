import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import DATA_DIR

# csv 파일정보 반환 함수
def read_csv(path):
  with open(path, encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    return reader.fieldnames, list(reader)  
  
  
# 문자열을 정수로 저장해도 되는지 판단 함수
def looks_int(text):
  body = text[1:] if text.startswith("-") else text  
  if not body.isdigit():
    return False
  return not (len(body) > 1 and body.startswith("0"))


# 문자열을 실수로 저장해도 되는지 판단 함수
def looks_float(text):
  try:
    float(text)
  except ValueError:
    return False
  return "." in text


# 문자열이 YYYY-MM-DD 모양인지 판단 함수
def looks_date(text):
  return re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) is not None


# 한 컬럼의 값들을 보고 알맞은 DB 타입 반환 함수
def infer_type(values):
  seen = [v for v in values if v != ""]

  if not seen:
    return "TEXT"
  if all(looks_int(v) for v in seen):
    return "INTEGER"
  if all(looks_float(v) for v in seen):
    return "FLOAT"
  if all(looks_date(v) for v in seen):
    return "DATE"
  return "TEXT"


# 컬럼명과, 데이터를 전달해 PK를 찾는 함수
def infer_pk(columns, rows):
  for col in columns:
    if not col.endswith("_id"):
      continue
    values = [r[col] for r in rows]

    if "" in values:
      continue
    if len(set(values)) == len(values):
      return col
  return None


# FK 후보 컬럼명의 주인으로 예상되는 테이블을 찾는 함수
# 특정 컬럼에 매칭되는 참조 대상 테이블이 있는지 찾아서 해당 컬럼이 실제 FK인지 판단하기 위해 필요
def owner_of(column, tables):
  # column : "customer_id", 첫번째 인자엔 FK인지 검사하고 싶은 컬럼명이 들어옴
  # tables : {"customsers":{...}, "products: {...}"}, 두번째 인자엔 모든 csv파일 정보값이 들어옴
  # 일단 컬럼명에서 뒤에 _id를 제거함
  stem = column[:3]

  # 컬럼명이 customer 일때, 관련 테이블명이 보통 customer이거나 그 뒤에 복수형표시가 붙는게 일반적이므로 s, es를 붙인 후보군을 2개 더 생성해서 반복
  for candidate in (stem, stem+"s",  stem+"es"):
    # 해당 후보군에서 실제 매칭되는 테이블명이 tables정보에 있으면 해당 값을 반환
    if candidate in tables:
      return candidate

  # 없으면 None 반환  
  return None




