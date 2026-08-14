# 정규표현식 검사해주는 파이썬 전용 패키지 
import re
import csv
from pathlib import Path

# 폴더 구조가 중첩되어 있기 때문에 루트 경로를 변수에 저장
ROOT = Path(__file__).resolve().parent.parent
# 루트경로에서 data폴더가 있는 경로를 다시 변수에 저장
DATA_DIR = ROOT / "data"

# 인자로 csv파일이 있는 패스 경로를 전달하면 각 파일의 필드명만 리스트형태로 반환하는 함수
def read_csv(path):
  with open(path, encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    return reader.fieldnames, list(reader)

# csv파일을 반복돌면서 read_csv함수 호출해서 각 파일당 필드데이터와 각 row 데이터정보를 출력
for path in sorted(DATA_DIR.glob("*.csv")):
  columns, rows = read_csv(path)

  # 각 csv파일의 첫번째의 모든 필드값 확인
  for column in columns:
    value = rows[0][column]


# 해당 값이 정수인지 확인하는 함수
def looks_int(text):
  # 만약 음수 부호 "-"이 있으면 떼서 저장
  body = text[1:] if text.startswith("-") else text

  # 0~9가 아닌 글자가 섞여있으면
  if not body.isdigit():
    # 정수가 아님   
    return False
  # 만약에 정수일때 앞자리가 0으로 시작하면 전화번호 (조건 2자리이상일떄)
  return not (len(body) > 1 and body.startswith("0"))


# 소수 판별 함수
def looks_float(text): 

  # float 실수반환되는지 우선 확인
  try:
    float(text)

  # 위의 모든 경우가 아니면 실수가 아닌게 확실하니 False반환
  except ValueError:
    return False

  # 점이 없으면 실수가 아닌것이니 최종 확인용
  if "." not in text:
      return False

  # 위의 모든 예외사항 통과하면 얘는 무조건 실수
  return True


# 날짜 판별 함수
def looks_date(text):
  # \d (숫자)
  # \d{갯수} (숫자가 저 갯수만큼 일때)
  # fullmatch(검증할 정규표현식, 검사할 문자값)
  return re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) is not None

# 타입 추론 함수 생성
def infer_type(values):
  #전달된 값에서 빈칸을 제외한 값을 변수에 담음
  seen = [v for v in values if v!=""]

  if not seen: 
    return "TEXT"

  if all(looks_int(v) for v in seen):
    return "INTEGER"

  if all(looks_float(v) for v in seen):
    return "FLOAT"

  if all(looks_date(v) for v in seen):
    return "DATE"

  return "TEXT"


# 모든 csv파일을 하나씩 검사해서 컬럼명과 각 행의 값의 타입을 분석
for path in sorted(DATA_DIR.glob("*.csv")):
  columns, rows = read_csv(path)

  for column in columns:
    kind = infer_type([r[column]  for r in rows])

    # next(조건에 맞는 값, 디폴트값) -> 조건에 맞는 값이 반복되면 하나만 출력하고 건너뜀, 조건문으로 빈 문자열 출력 그렇게 건너뛴 값을 반환
    # 반복되는 필드명을 한번만 출력하고 싶을때
    # example = next((r[column] for r in rows if r[column] != ""), "")

    # print(f" {column} : {kind}")


# PK를 찾아주는 함수
def infer_pk(columns, rows):
  # _id로 끝나지 않는 필드명은 제외
  for col in columns:
    if not col.endswith("_id"):
      continue

    # value값이 빈문자열은 제외
    values = [r[col] for r in rows]
    if "" in values: 
      continue

    # value값이 중복되지 않으면 그건 PK
    if len(set(values)) == len(values):
      return col

  # 위의 조건이 모두 만족하지 않는다면 PK가 없음
  return None

# 특정 PK의 주인 테이블 찾기
def owner_of(column, tables):
  # 첫번쨰 인자로 들어온 PK에서 _id제거하고 그 뒤에 s, es붙여서 
  # 두번째 인자로 들어온 테이블이름 리스트랑 매칭이 되는 이름을 찾음 (해당PK의 주인 테이블 명)
  stem = column[:-3]
  for candidate in (stem, stem+"s", stem+"es") :
    if candidate in tables:
      return candidate

  return None


# 1.모든 테이블별 필드, 데이터타입, PK 구하기
tables = {}
for path in sorted(DATA_DIR.glob("*.csv")):
  columns, rows = read_csv(path)
  tables[path.stem] = {
    "columns": columns,
    "rows":rows,
    "type": {col: infer_type([r[col] for r in rows]) for col in columns},
    "pk":infer_pk(columns, rows)
  }

# 2. 특정 테이블에 연결되어 있는 외래키 찾기
for name, table in tables.items(): # 표 이름과 내용을 그룹으로 꺼냄
  # 특정테이블에 복수개의 외래키가 담길수 있으므로 빈 리스트 생성
  fks = []

  # 현재 반복도는 테이블의 컬럼명 끝에 _id없으면 (PK, FK 아님)
  for col in table["columns"]:
    if not col.endswith("_id"):
      continue

    # 테이블의 PK의 주인 테이블몇 찾음
    owner= owner_of(col, tables)

    # 현재반복도는 후보 키값들 중에서 owner값이 동일하면 FK제외 (PK)
    if not owner or owner == name:
      continue

    #반복도는 테이블의 주인키와 현재 컬림의 키값이 같지 않으면
    if tables[owner]["pk"] != col:
      continue

    #fks란 빈 배열에 FK,테이블 명 저장
    fks.append((col, owner))

  table["fks"] = fks
# 지금까지 생성한 정보로 테이블 생성하는 sql구문 생성 함수
# CREATE TABLE purchases (
#   purchase_id TEXT PRIMARY KEY,
#   customer_id TEXT,
#   quantuty INTIGER,
#   FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
# )

def build_create(name, table):
  lines = []

  for col in table["columns"]:
    piece = f"    {col} {table['type'][col]}"

    if col == table["pk"]:
      piece += " PRIMARY KEY"

    lines.append(piece)

  for col, owner in table["fks"]:
    print(col)
    lines.append(f"    FOREIGN KEY ({col}) REFERENCES {owner}({col}")

  return f"CREATE TABLE {name} (\n"+ ".\n".join(lines) + "\n)"

# 현재 모든 테이블명과 테이블정보를 가져와서 자동으로 모든 테이블생성 sql문 확인
for name, table in tables.items():
  print(build_create(name, table) + ";\n")