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

  # 위에서 데이터를 다 넣은 뒤 외래키 컬럼에 인덱스를 생성
  # PK는 DB가 인덱스를 자동으로 만들어주지만 FK는 직접 생성해야함
  # 만약 FK 인덱스가 없다면 다음과 같은 문제가 발생
  # 100만건의 구매정보가 purchases 테이블에 있을때 해당 구매내역에서 C001 고객의 구매 내역을 찾을때 해당 외래키에 인덱스가 없으면
  # 100만건에 대한 purchases 구매내역을 풀로 스캔하게 되어 탐색 시간이 길어짐
  # 또한 PRAGMA foreign_keys = ON으로 외래키 연결 자동 검사를 진행하고 있기 때문에 부모행을 지우거나 수정할때 외래키연결 검사 시간도 증가하게 됨
  # 하지만 외래키 컬럼에 인덱스를 지정하면 전체 구매내역에서 특정 고객의 구매상품만 검색할때 전체 구매내역을 풀 스캔이 아니라 인덱스가 있는 데이터만 빠르게 검색 가능
  # 물론 만능은 아닌게 외래키 인덱스 지정시 데이터 저장할땐 시간이 더 많이 소요되지만
  # 웹에서는 일반적으로 저장보다 탐색의 빈도가 압도적으로 많으므로 외래키 인덱싱은 걸어두는 쪽이 이득
  for col, _owner in table["fks"]:
    # SQLite에서 인덱스 이름은 테이블 단위가 아니라 DB전체에서 고유해야함
    # 따라서 아래와 같이 각 테이블명, 컬럼명을 조합해서 인덱스 생성
    # INSERT를 다 마친뒤에 인덱스를 만드는 이유는 행마다 매번 인덱스를 갱신하는 것보다
    # 데이터를 다 넣은 상태에서 인덱스를 한번에 만드는 쪽이 더 빠르기 때문
    con.execute(f"CREATE INDEX idx_{name}_{col} ON {name}({col})")

con.commit()

# 그럼 이제 commit문 이후에 (트랜젝션이 완료된 이후에) 실제 FK컬럼에 index가 생성됐는지 확인
for row in con.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index'"):
  print(row)

# 결과화면 : name(각 index이름, 해당 테이블, FK연결을 위한 sql문)
# ('sqlite_autoindex_customers_1', 'customers', None) :FK가 없으므로 PK값이 등록되어 있고 PK는 sqlite가 자동 인덱스 처리, FK연결 aql문이 없으므로 None
# ('sqlite_autoindex_products_1', 'products', None)
# ('sqlite_autoindex_purchases_1', 'purchases', None)
# ('idx_purchases_customer_id', 'purchases', 'CREATE INDEX idx_purchases_customer_id ON purchases(customer_id)')
# ('idx_purchases_product_id', 'purchases', 'CREATE INDEX idx_purchases_product_id ON purchases(product_id)')
# ('sqlite_autoindex_product_details_1', 'product_details', None)
# ('idx_product_details_product_id', 'product_details', 'CREATE INDEX idx_product_details_product_id ON product_details(product_id)')
# 예시로 마지막 정보에는 idx_{name}_{col} 형태로 우리가 직접 지정한 FK index확인 가능

con.close()
