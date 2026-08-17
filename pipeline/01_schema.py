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
# infer_pk(colums, rows) -> 해당 데이터에서의 PK값 반환
# columns = ["customer_id", "name", "gender", ...]
# rows = [{"customer_id": "C001", "name": "박은수", ...}, ...]
def infer_pk(columns, rows):
  # 첫번째 인자로 전달된 모든 컬렴값을 반복돌며 _id로 끝나지 않는다면 무시하고 넘어감
  # _id가 없으면 PK, FK 둘다 아니므로
  for col in columns:
    if not col.endswith("_id"):
      continue
    # 결국 _id로 끝나는 컬럼명에 해당 하는 모든 값을 values에 리스트 형태로 담음
    values = [r[col] for r in rows]

    # 만약 values에 빈문자열이 하나라도 있으면 무조건 다음 컬럼으로 넘어감
    if "" in values:
      continue
    # 마지막으로 특정 컬럼값에 중복을 제거한 리스트 갯수와 전체 리스트 갯수를 비교해서 같으면
    # 그 값에는 공통의 _id의 값이 없으므로 FK가 아닌 PK이고 해당 컬럼명을 반환한다 
    if len(set(values)) == len(values):
      return col
  # 만약 위의 조건에 걸러지는게 하나도 없으면 결국 PK가 없는 것이므로 None반환
  return None


# 실제 infer_pk를 통해 CSV파일의 PK알아내기
# 준비물 해당 함수에 들어갈 columns, rows 데이터 필요 (read_csv 함수 활용)

# 먼저 인자로 전달할 colums, rows 데이터 추출
columns, rows = read_csv(DATA_DIR / "customers.csv")

print(columns) # 리스트 형태로 컬럼값 확인
print(rows[0]) # rows 데이터 행이 많으므로 첫번째 행만 확인

# 이제 실해 해당 정보 2개를 인자로 전달해서 PK찾기
pk_name = infer_pk(columns, rows)
print(pk_name) # 결국 customers.csv파일 데이터에서의 PK명은 customer_id인것을 확인 가능




