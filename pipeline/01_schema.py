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
# 아래와 같은 각 테이블명 SQL문을 자동으로 생성하는 함수 제작
# 아래 SQL문 구조를 보면 크게 4단계로 구분됨 (CREATE 구문, PRIMARY KEY가 지정된 줄, FK지정된 줄, 그외 나머지 구문 )
# build_create("purchases", tables["purchases"])의 결과 예시
# CREATE TABLE purchases (
#     purchase_id TEXT PRIMARY KEY,
#     customer_id TEXT,
#     product_id TEXT,
#     purchased_at DATE,
#     quantity INTEGER,
#     rating INTEGER,
#     review TEXT,
#     is_holdout INTEGER,
#     FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
#     FOREIGN KEY (product_id) REFERENCES products(product_id)
# )
def build_create(name, table):
  # 첫번쨰 인자로 테이블명, 두번째 인자로 테이블 정보가 전달됨
  # 각 sql문 줄의 구문이 담길 빈 리스트 생성
  lines = []

  for col in table["columns"]:
    # 아래 구문은 PK, FK가 없는 일반 필드 생성하는 구문 앞쪽에 빈칸을 일부러 4칸 띄어서 위의 구조를 맞춤
    piece = f"    {col} {table['type'][col]}"

    # 만약 현재 반복도는 컬럼이 PK로 지정되어 있으면 해당 필드명 뒤에 PRIMARY KEY 문자값 더해서 이어붙임
    if col == table["pk"]:
      piece += " PRIMARY KEY"

    # 여기까지 하면 외래키 지정하는 필드를 제외하곤 모든 필드 생성 sql문이 list형태로 담기게됨
    lines.append(piece)

  # 이젠 나머지 외래키 연결하는 구문 생성
  for col, owner in table["fks"]:
    # 해당 컬럼에 외래키가 있으면 외래키 갯수만큼 반복돌며 해당 외래키명과 참조하는 테이블 명을 sql문에 추가
    lines.append(f"    FOREIGN KEY ({col}) REFERENCES {owner}({col})")

  # 최종적으로 f-string으로 제일 첫줄인 CREATE TABLE 테이블명 문구를 생성
  # 이어서 lines 리스트에 모아놓은 각 필드 생성 sql문을 ,줄바꿈하면서 이어붙임
  # 마지막으로 줄바꿈하고 괄호를 붙여주면 하나의 테이블 SQL문 완성됨
  return f"CREATE TABLE {name} (\n" + ",\n".join(lines) + "\n)"


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


# 5. 이전에 만든 테이블 생성 순서 리스트 반복 돌며 SQL문 자동 생성
for name in table_order:
  table = tables[name]

  combined_sql = build_create(name, table)

  print(combined_sql)
