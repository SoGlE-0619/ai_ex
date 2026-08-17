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

  # 이제 위에 최종적으로 만들어진 sql문을 통해 실제 db파일에 테이블 생성
  con.execute(combined_sql)

  # 이제 해당 디비파일에 테이블이 생성되었는지 확인
  # sqlite_master 테이블 안에 우리가 만든 커스텀 테이블이 들어가는 구조이므로 해당 테이블에서 생성된 타입이 테이블인것만 찾아서 해당 테이블명과 생성 sql문을 반환
  db_info = con.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")

  # for tb_name, tb_sql in db_info:
  #   print(tb_name)
  #   print(tb_sql)

  
# customers 테이블에서의 각 컬럼별 상세 정보 확인 (특정 테이블 하나의 컬럼 정보만 확인하기 위해 반복문 코드블록에서 빠져나옴)
print(con.execute("PRAGMA table_info(customers)").fetchall())
# 총 9개의 필드값 정보를 확인할 수 있으며 각 ()안의 정보 순서는 다음과 같음
# 각 컬럼 순서, 컬럼이름, 컬럼에 들어갈 타입, not null 유무, 디폴트값 유무, pk유무
# (0, 'customer_id', 'TEXT', 0, None, 1),
# 첫번째 필드순서인 0번째 컬럼명은 customer_id이고 text타입이며, not null이 0이므로 무조건 값이 지정되야함, 디폴트값은 None이므로 없고, pk유무는 1이므로 해당 컬럼이 PK임
  

