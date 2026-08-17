import csv
import re # 정규식 검사를 위한 파이썬 내장 모듈 import
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
  # 상단에 import한 re 정규식 모듈의 내장 메서드인 fullmatch 호출
  # fullmatch(정규표현식 검사, 검사할 문자열) -> True, False 반환
  # r"정규표현식 시작" \d{갯수} \d -시작 문자열이 숫자인지 판단 이후 중괄호의 갯수만큼 반복되는지 확인 이후 "-"이 있는지 확인
  # 결국 무조건 숫자4개-숫자2개-숫자2개 이런식이면 True반환, 그렇지 않으면 None으로 처리해서 False반환
  return re.fullmatch(r"\d{4}-\d{2}-\d{2}", text) is not None

# 테스트 호출
print(looks_date("2025-02-04")) # True
print(looks_date("2024-1-4")) # False
