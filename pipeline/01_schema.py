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


# 테이블 생성 sql문 호출시 먼저 생성되야 하는 테이블 순서 반환하는 함수
# 테이블은 크게 참조당하는 테이블, 참조하는 테이블이 있다
# 참조당하는 테이블이 먼저 생성되어야 이후 해당 테이블을 참조하는 테이블 생성 sql문이 실행됐을때 오류나지 않음
# 핵심은 참조당하는 테이블이 무조건 먼저 테이블 생성 sql이 실행되도록 해야함
# 참조당하는 테이블을 찾는 가장 간단한 방법은 해당 테이블 정보의 fks값이 비어있는 테이블을 찾으면 됨
def sort_by_dependency(tables):
  done = set() # set()은 중복을 허용하지 않는 값 모음(실제 값을 담기위함보다는 특정 조건에 부합되는 값이 목록에 있는지 빠르게 판별하기 위한 용도)
  order = [] # 실제 순서대로 실행되어야할 테이블명이 등록될 빈 리스트

  # 전체 테이블갯수와 orderd에 담길 테이블 갯수가 같아질떄까지 무한 반복처리
  while len(order) < len(tables):
    # 무한 반복시 모든 정보가 담기면 반복을 끊어주기위한 구분 값
    moved = False

    # 각 테이블 정보에서 테이블 이름, 테이블 정보를 추출
    for name, table in tables.items():
      # 일단 반복도는 테이블 명이 done에 담겨있는지 빠르게 확인 (순서에 테이블명이 담겨있는지 scan이 아닌 빠르게 search하기 위한 용도)
      # 만약 true면 이미 해당 테이블명(name)은 이미 순서에 등록된 값이기에 무시하고 넘어감
      if name in done:
        continue

      # 이번엔 현재 반복도는 테이블 정보의 외래키정보를 반복돌며 해당 참조 테이블명이 있는지 확인
      # 해당 all구문은 (값이 모두 참이거나, 값이 하나도 없으면 최종 True 판단됨)
      # 결국 아래 조건식은 지금 반복도는 테이블 정보에서 fks에 외래키 정보가 하나도 없을때만 참이되어 안쪽 코드블록이 실행됨
      if all(owner in done for _, owner in table["fks"]):
        # 위의 조건에서 외래키가 하나도 없는 테이블은 결국 참조당하는 테이블이므로 order 리스트에 담고
        order.append(name)
        # 다음번 루프때 빠른 판단을 위해 done에도 담아줌
        done.add(name)
        # 그리고 이번 루프에서 order에 테이블 순서를 하나 담았기 때문에 moved=True로 변경하여 아래쪽 조건이 아닌 다시 루프 처음으로 돌아가게 처리
        moved = True

    # 결국 위의 조건에서 우선적으로 참조 당하는 모든 테이블명이 order 순서에 담기고 나면 비로서 이곳의 if문이 실행됨
    if not moved:
      # done에 담겨있지 않는 테이블명은 모두 참조하는 테이블명이므로 모두 order의  뒤쪽에 테이블 명을 추가하고 종료
      order += [n for n in tables if n not in done]
      break
  
  # 이런식으로 완성된 테이블 순서 리스트를 반환
  return order


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
for name, table in tables.items():
  fks = []
  for col in table["columns"]:
    if not col.endswith("_id"):
      continue
    owner = owner_of(col, tables)
    if not owner or owner == name:
      continue  
    if tables[owner]["pk"] != col:
      continue
    fks.append((col, owner))
  table["fks"] = fks


# 3. 실제 순서되로 실행되어야할 테이블명 리스트 확인
table_order = sort_by_dependency(tables)
print(table_order)
# 결과값 ['customers', 'products', 'purchases', 'product_details'] 내부에 외래키가 없는 참조당하는 테이블이 제일 앞쪽의 순번으로 등록되어 있는 것을 확인