import csv
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import DATA_DIR, DB_PATH

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
def sort_by_dependency(tables):
  done = set() 
  order = [] 
  while len(order) < len(tables):
    moved = False
    for name, table in tables.items():
      if name in done:
        continue
      if all(owner in done for _, owner in table["fks"]):  
        order.append(name)   
        done.add(name)
        moved = True
    if not moved:  
      order += [n for n in tables if n not in done]
      break
  return order


# 지금까지 생성한 csv정보로 실제 테이블 생성 SQL문 반환 함수
def build_create(name, table):
  lines = []

  for col in table["columns"]:
    piece = f"    {col} {table['type'][col]}"
    if col == table["pk"]:
      piece += " PRIMARY KEY"
    lines.append(piece)

  for col, owner in table["fks"]:
    lines.append(f"    FOREIGN KEY ({col}) REFERENCES {owner}({col})")

  return f"CREATE TABLE {name} (\n" + ",\n".join(lines) + "\n)"


# 실제 생성된 테이블에 데이터 저장할때 각 컬럼별 자료형에 맞게 문자열의 데이터 타입을 변환하는 함수
def convert(value, kind):
  if value == "":
    return None
  if kind == "INTEGER":
    return int(value)
  if kind == "FLOAT":
    return float(value)
  return value


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


# 4. DB접속 및 테이블이 생성될 DB파일 만들기
db_file = Path(DB_PATH)

if db_file.exists():
  db_file.unlink()

con = sqlite3.connect(db_file)
con.execute("PRAGMA foreign_keys = ON")


# 5. 이전에 만든 테이블 생성 순서 리스트 반복 돌며 SQL문 자동 생성후 테이블 데이터 저장
for name in table_order:
  table = tables[name]

  combined_sql = build_create(name, table)
  con.execute(combined_sql)

  columns = table["columns"]
  placeholders = ", ".join("?" for _ in columns)

  values = [
    tuple(convert(row[col], table["type"][col]) for col in columns) 
    for row in table["rows"] 
  ]

  con.executemany(
    f"INSERT INTO {name} ({', '.join(columns)}) VALUES ({placeholders})", 
    values, 
  )

con.commit()

# 이제 실제 테이블에 데이터가 잘 들어갔는지 확인
# customers테이블의 데이터행의 모든 카운트 갯수를 가지고옴 이때 튜플의 첫번째 값에 담겨있는 갯수만 저장
customers_count = con.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
print(customers_count) # 300개 출력

# 그럼 이번엔 customers 테이블의 첫번째 행의 데이터만 확인
customers_row1 = con.execute("SELECT * FROM customers LIMIT 1").fetchone()
print(customers_row1) #('C001', '박은수', 'F', 53, '건성', '010-4786-2358', 'eunsu45@example.com', '성남', '2025-06-25')

# 이렇게 실제로 DB에 테이블이 생성되고 데이터가 잘 들어간 것을 확인할 수 있음
# 하지만 단지 데이터 확인을 위해서 해당 파이프라인 폴더 안쪽의 파일을 실행하면 CSV정보확인 -> 타입 추론 -> SQL문 생성 -> DB 파일생성 -> 테이블 생성 -> 테이터 저장
# 의 모든 작업단계가 매번 실행되므로 상당히 비효율적 그래서 다다음번 강의에서 해당 파이프라인의 초기 세팅을 매번 다시 실행하지 않으면서 데이터만 빠르게 확인하는 전용 파일 생성 예정

con.close()
