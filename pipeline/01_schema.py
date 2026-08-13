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
  print(value)

# 해당 값이 정수인지 확인하는 함수
def looks_int(text):
  # 만약 음수 부호 "-"이 있으면 떼서 저장
  body = text[1:] if text.startswith("-") else text

  # 0~9가 아닌 글자가 섞여있으면
  if not body.isdigit():
    # 정수가 아님
    print("정수가 아님")
    return False
  # 만약에 정수일 때 앞자리가 0으로 시작하면 전화번호 (조건 : 2자리 이상일 때)
  print("전화번호")
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