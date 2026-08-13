import csv
from pathlib import Path

# 폴더 구조가 중첩되어 있기 때문에 루트 경로를 변수에 저장
ROOT = Path(__file__).parent.parent
# 루트경로에서 data폴더가 있는 경로를 다시 변수에 저장
DATA_DIR = ROOT / "data"

# 인자로 csv파일이 있는 패스 경로를 전달하면 각 파일의 필드명만 리스트형태로 반환하는 함수
def read_csv(path):
  with open(path, encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    return reader.fieldnames, list(reader)

# csv파일을 반복돌면서 read_csv함수 호출해서 각 파일당 필드데이터와 각 row 데이터정보를 출력
for path in sorted(DATA_DIR.glob("*.csv")):
  colums, rows = read_csv(path)
  print(f"\n{path.name} - {len(rows)}행 - {len(colums)}열")