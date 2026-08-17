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
def owner_of(column, tables):
  stem = column[:-3]
  for candidate in (stem, stem+"s",  stem+"es"):  
    if candidate in tables:
      return candidate
  return None


# 1. 모든 테이블별 필드, 데이터타입, PK값 정보 저장하는 실행문
tables = {}
for path in sorted(DATA_DIR.glob("*.csv")): 
  columns, rows = read_csv(path)
  tables[path.stem] = {
    "columns": columns, 
    "rows": rows, 
    "type": {col: infer_type([r[col] for r in rows]) for col in columns}, 
    "pk": infer_pk(columns, rows) 
  }


# 2. 특정 테이블에 연결되어 있는 외래키 정보 찾아 기존 tables 정보에 추가

# 먼저 위에서 각 csv파일에서 추출해 모아놓은 tables정보에서 name(테이블명), table(테이블정보)를 내부로 반복해서 전달
for name, table in tables.items():
  # 각 테이블에 리스트 형식을 외래키 정보가 담길 빈 리스트 생성
  fks = []

  # 각 테이블의 컬럼명을 하나씩 뽑아서 조건 비교 시작
  for col in table["columns"]:
    # 만약 컬럼명이 _id로 끝나지 않으면 PK, FK 둘다 아니므로 무시하고 넘어감
    if not col.endswith("_id"):
      continue
    
    # 현재 컬럼명이 가르키는 참조당하는 테이블이 있는지 확인
    owner = owner_of(col, tables)
    # 만약 참조당하는 테이블이 없거나 해당 참조테이블 명과 현재 테이블명이 같으면 그건 PK이므로 무시하고 넘어감
    if not owner or owner == name:
      continue
    
    # 참조당하는 테이블의 PK값이 현재의 col명과 동일하지 않으면 그건 FK이므로 통과 
    if tables[owner]["pk"] != col:
      continue
    
    # 위의 조건에 통과된 FK인 컬럼명과 해당 외래키가 가르키는 참조 테이블 명을 괄호로 묶어서 리스트 형태로 담음
    fks.append((col, owner))

  # 위에서 만들어진 fks 리스트 정보를 기존 테이블에 "fks"라는 추가 키를 만들어서 등록
  table["fks"] = fks

# 그럼 위에서 만들어진 fks키가 기존 테이블에 추가되고 그 안에 외래키 정보가 있는지 직접 확인

print(tables["purchases"]["fks"]) # 전체 tables정보에서 purchases테이블 정보만 찾고 다시 거기에서 fks키값의 정보를 출력
# 실행하면 아래와 같이 purchases테이블 안에는 customers 테이블을 참조하는 customer_id라는 외래키와 products 테이블을 참조하는 product_id 외래키 2개가 있음을 확인 가능
# [('customer_id', 'customers'), ('product_id', 'products')]