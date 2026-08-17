# config.py에 등록한 경로 변수를 쓸 수 있게 설정하고 경로 변수 가져옴
# 모듈 검색 경로를 손보기 위해 가져옴
import sys
from pathlib import Path

# 해당 파일경로로부터 두단계 위인 루트 경로의 절대 경로를 가져와서 str()로 강제 문자화
# 그렇게 지정한 루트 경로를 insert(0, 경로)를 실행해 시스템에서 루트경로에서 필요한 모듈을 제일 먼저 실행하도록 강제
# 이 코드가 실행되어야 아래쪽에 DATA_DIR 경로 변수를 사용할 수 있음
# 같은 이유로 아래 코드에 ROOT 변수값을 사용 못함
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import DATA_DIR