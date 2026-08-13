# github에 내 작업을 단계별로 올리는 방법
# 1. 깃허브에가서 내가 올리고 싶은 작업의 전용 저장소 URL복사 (private)
# 2. 내 작업폴더에 터미널 열고 다음 명령어 차례대로 실행
#  git init
#  git remote add origin 저장소url
# 3. 단계별로 기록을 남기고 싶을때마다 파일 저장 -> git add . -> git commit -m "커밋메세지" -> git push origin --all


# 정규표현식 검사해주는 파이썬 전용 패키지 (import re)
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
  # 만약에 정수일 때 앞자리가 0으로 시작하면 전화번호 (조건 : 2자리 이상일 때)
  return not (len(body) > 1 and body.startswith("0"))

looks_int("0")

# 소수 판별 함수
def looks_float(text):
  # float 실수반환되는지 우선 확인
  try:
    float(text)

  # 위의 모든 경우가 아니면 실수가 아닌게 확실하니 False반환
  except ValueError:
    return False

  # 점이 없으면 실수가 아닌것이므로 최종 확인용
  if "." not in text:
    return False
  
  # 위의 모든 예외사항 통과하면 얘는 무조건 실수
  return True

print(looks_float("21.32"))

# 날짜 판별 함수
def looks_date(text):
  # 정규표현식 
  # \d (숫자)
  # \d{갯수} (숫자가 저 갯수만큼 일때)
  # fullmatch(검증할 정규표현식, 검사할 문자값)
  return re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) is not None

print(looks_date("2025-03-05"))

# 타입 추론 함수 생성
def infer_type(values):
  # 전달된 값에서 빈칸을 제외한 값을 변수에 담음
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

# 모든 csv 파일을 하나씩 검사해서 컬럼명과 각 행의 값의 타입을 분석
for path in sorted(DATA_DIR.glob("*.csv")):
  columns, rows = read_csv(path)
  print(f"\n{path.stem} ({len(rows)})")

  for column in columns:
    kind = infer_type([r[column] for r in rows])

    example = next((r[column] for r in rows if r[column] != ""),"")

    print(f"{column} : {kind}")

# PK를 찾아주는 함수
def infer_pk(columns, rows):
  # _id로 끝나지 않는 필드명은 제외
  for col in columns:
    if not col.endswith("_id"):
      continue

    # value 값이 빈문자열은 제외
    values = [r[col] for r in rows]
    if "" in values:
      continue

    # value rkqtdl 중복되지 않으면 그건 PK
    if len(set(values)) == len(values):
      return col

    # 위의 조건이 모두 만족하지 않는다면 PK가 없음
    return None

  # 특정 PK에 주인 테이블 찾기
  def owner_of(colunm, tables):
    # 첫번째 인자로 들어온 PK에서 _id 제거하고 그 뒤에 s, es 붙여서
    # 두번째 인자로 들어온 테이블이름 리스트랑 매칭이 되는 이름을 찾음 (해당 PK의 주인 테이블 명)
    stem = column[:-3]
    for candidate in (stem, stem+"s",stem+"es"):
      if candidate in tables:
        return candidate

    return None

# 1. 모든 테이블별 필드, 데이터타입, PK 구하기
tables = {}
for path in sorted(DATA_DIR.glob("*.csv")):
  columns, rows = read_csv(path)
  tables[path.stem] = {
    "columns" : columns,
    "rows" : rows,
    "type" : {col : infer_type([r[col] for r in rows]) for col in columns},
    "pk" : infer_pk(columns, rows)
  }

print(tables)