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
  # 일단 컬럼명에서 뒤에 _id를 제거함 (중요 :3을 :-3으로 변경)
  stem = column[:-3]

  # 컬럼명이 customer 일때, 관련 테이블명이 보통 customer이거나 그 뒤에 복수형표시가 붙는게 일반적이므로 s, es를 붙인 후보군을 2개 더 생성해서 반복
  for candidate in (stem, stem+"s",  stem+"es"):
    # 해당 후보군에서 실제 매칭되는 테이블명이 tables정보에 있으면 해당 값을 반환
    if candidate in tables:
      return candidate

  # 없으면 None 반환  
  return None


# 실제 모든 csv파일 정보를 가져와서 특정 컬럼명의 키가 주인인 테이블 명 찾는 구문
# 모든 csv파일을 반복돌며 rows데이터를 가져와서 다시 하나의 딕셔너리로 묶어주는 구문
# 먼저 모든 테이블 정보를 {파일명:{...}, 파일명: {...}, 파일명: {...}, 파일명: {...} } 형태로 담을 빈 딕셔너리 생성
tables = {}

# data폴더 안쪽의  모든 csv파일을 glob로 읽어서 반복하며 각 csv파일의 path경로를 구함
for path in DATA_DIR.glob("*.csv"):
  # 반복되는각 csv파일의 path경로를 read_csv함수에 전달해서 각 파일당, columns, rows 정보를 가져옴
  columns, rows = read_csv(path)

  # 미리 만든 빈 딕셔너리에 키값으로 path.stem으로 csv파일에서 확장자를 제외한 파일명으로 키를 등록
  # 그리고 각 키별로 columns에는 키값, rows에는 모든 행의 데이터를 저장
  tables[path.stem] = {
    "columns": columns,
    "rows":rows
  }

# 완성된 모든 csv파일의 중첩 딕셔너리 구조를 확인
# print(tables)

# 그럼 이제 모든 테이블 정보가 들어가 있는 tables에서 특정 컬럼명을 넣어서 해당 컬럼명에 해당하는 PK, FK후보가 주인인 참조당하는 테이블 명 확인
owner = owner_of("customer_id", tables)
print(owner) # customers  : 결국 customer_id가 PK인 테이블 명은 customers임


