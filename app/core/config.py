"""설정 ― 프로그램 전체가 함께 쓰는 값을 여기 모은다.

지금은 경로와 2일차에 더한 모델 이름뿐이다. 수업이 진행되면서 여기가 늘어난다 ―
    3일차  벡터 차원 · 소수점 자리
    4일차  LLM 주소와 모델 이름
    6일차  로컬/상용 스위치

다른 파일은 전부 이렇게 쓴다 ─
    from app.core.config import DATA_DIR, DB_PATH
"""

from pathlib import Path

# 🔴 오늘 고친 줄 ― 이 파일이 app/core/ 로 한 칸 더 들어갔다.
#    .parent 는 한 번에 한 칸씩 올라간다. 그래서 뿌리까지 세 단계다
#        .parent         app/core
#        .parent.parent  app
#        세 번째          cosmetic-admin  ← 여기가 뿌리
ROOT = Path(__file__).resolve().parent.parent.parent

DATA_DIR = ROOT / "data"
DB_PATH = str(ROOT / "cosmetic.db")

# ─────────────────────────────────────────────────────────────
# 2일차 ― 글을 자를 때 쓰는 값
# ─────────────────────────────────────────────────────────────

EMBED_TOKENIZER = "intfloat/multilingual-e5-small"
EMBED_MAX_TOKENS = 512
EMBED_MODEL = "intfloat/multilingual-e5-small"

# 🔴 오늘 더한 줄 ― sqlite3 는 파일이 없으면 조용히 새로 만든다.
#    그래서 경로가 틀려도 오류가 안 난다. 죽이지는 않고 경로만 눈에 보이게 한다
if not Path(DB_PATH).exists():
    print(f"알림: DB 가 아직 없다 -> {DB_PATH}")

# 이 모델이 한 문장을 몇 개의 실수로 바꾸는가. 표를 만들 때와 점검할 때 쓴다
EMBED_DIM = 384

# 벡터를 문자로 적을 때 소수점 몇 자리까지 쓸까.
# 자릿수를 그대로 두면 파일이 두 배가 된다. 얼마나 손해인지는 5교시에 직접 잰다
EMBED_DECIMALS = 6
