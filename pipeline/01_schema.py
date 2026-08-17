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
  # 먼저 검사할 숫자가 음수면 파이썬은 정수라고 인지를 못하기 때문에 먼저 앞의 -기호 제거
  body = text[1:] if text.startswith("-") else text
  # isdigit()은 문자열의 모든 글자가 숫자형일때 True 반환
  if not body.isdigit():
    return False
  # 위의 조건을 모두 만족했을때 숫자로 남은 글자가 1글자 이상이어야 하고 0으로 시작하지 않아야 숫자로 인정해 True반환
  # 0으로 시작하는 숫자를 정수로 인정하지 않는 이유는 보통 "001, 002같은 경우는 고객 고유 번호로 활용되므로 숫자처리하면 안되기 때문"
  return not (len(body) > 1 and body.startswith("0"))

# 실제 테스트
print(looks_int("34")) # True
print(looks_int("004")) # False





