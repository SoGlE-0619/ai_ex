import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

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
  # values로 들어온 컬럼값 리스트를 반복돌며 일단 값이 없으면 제외하고 리스트로 담음
  seen = [v for v in values if v != ""]

  # 혹시 값이 모두 비어있으면 무조건 "TEXT"타입 반환 (빈 문자열로 문자이기 때문)
  if not seen:
    return "TEXT"
  # 리스트에 있는 모든 값을 looks_int함수로 검사해서 모두 숫자여야지만 "INTEGER"타입 반환
  if all(looks_int(v) for v in seen):
    return "INTEGER"
  # 리스트에 있는 모든 값을 looks_float함수로 검사해서 모두 숫자여야지만 "FLOAT"타입 반환
  if all(looks_float(v) for v in seen):
    return "FLOAT"
  # 리스트에 있는 모든 값을 looks_date함수로 검사해서 모두 날짜형태여야만 "DATE"타입 반환
  if all(looks_date(v) for v in seen):
    return "DATE"
  # 그 외에 모든 경우는 "TEXT" 타입처리
  return "TEXT"

# 실제 테스트 호출
print(infer_type(["10", "20", "30"])) # 만약 컬럼값이 물건 구매 수량일경우 -> INTEGER
print(infer_type(["007", "008", "009"])) # 만약 컬럼값이 고객 고유 id값을 경우 -> TEXT
print(infer_type(["2024-03-04", "2024-04-05"])) # 만약 컬럼값이 고객이 물품을 구매한 날짜인 경우 -> DATE
