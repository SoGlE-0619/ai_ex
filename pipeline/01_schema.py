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


# 1. 모든 테이블별 필드, 데이터타입, PK구하는 실행
# 이제부터 모든 csv파일을 반복 돌면서 각 csv파일로부터 컬럼명, 각 데이터를 read_csv함수로 추출
# 이후 추출한 데이터를 다시 tables라는 변수에 중첩 딕셔너리 형태로 저장
# 각 딕셔너리에는 csv파일별로 (컬럼명, 모든 데이터 행, 각 컬럼별 타입명, 해당 테이블의 PK 정보)를 담을 예정

# 먼저 데이터가 담길 빈 딕셔너리 생성
tables = {}

# data폴더 안쪽의 모든 csv파일을 glob로 찾아서 반복돌며 파일 순서대로 정렬해서 각 파일 경로를 전달
for path in sorted(DATA_DIR.glob("*.csv")):
  # 전달받은 path값을 인자로 전달해 read_csv함수를 호출해 컬럼명, 데이터 정보를 변수에 담음
  columns, rows = read_csv(path)

  tables[path.stem] = {
    "columns": columns, # 각 csv파일의 모든 컬럼명을 리스트로 담음
    "rows": rows, # 모든 데이터행을 딕셔너리가 포함된 리스트 형태로 담음
    "type": {col: infer_type([r[col] for r in rows]) for col in columns}, # 모든 컬럼값을 infer_type함수로 추론해 지정될 타입명 정보 담음
    "pk": infer_pk(columns, rows) # infer_pk함수를 이용해 해당 테이블 정보에서의 PK값 구해서 담음
  }

# print(tables) # 합쳐진 모든 테이블 정보 확인
# print(tables["customers"]) # 그중에서 customers 테이블 정보만 확인
print(tables["customers"]["columns"]) # customers 테이블에서 컬럼명만 확인
print(tables["customers"]["rows"][0]) # customers 테이블에서 첫번째 row행 데이터만 확인
print(tables["customers"]["type"]) # customers 테이블에서 각 컬럼에 담길 데이터타입을 문자열로 확인
print(tables["customers"]["pk"]) # customers 테이블에서의 PK값 확인

