import csv
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
  # float()을 통해 문자열을 소수형 실수로 변경, 바꿀수 없으면 ValueError가 발생
  try:
    float(text)
  # ValueError 발생시 False 반환
  except ValueError:
    return False
  # 이후 안전을 위해 해당 실수에 "."이 있는지 추가로 확인해서 해당 조 건까지 통과하면 True반환
  return "." in text

# 실제 동작 테스트
print(looks_float("13.5")) # True
print(looks_float("13")) # False
print(looks_float(".13.5")) # False
  




