"""CSV 여러 개를 분석해서 하나의 SQLite DB로 만드는 파일이다.

필요한 함수
    read_csv(path)
        CSV 한 개를 읽고 컬럼명과 전체 행을 반환 
        전달값: path = 읽을 CSV 파일의 경로
        반환값: (컬럼명 목록, 전체 행 목록)

    looks_int(text)
        문자열이 정수로 저장하기 적합한지 확인
        전달값: text = CSV에서 읽은 문자열 하나
        반환값: 정수로 저장할 수 있으면 True, 아니면 False

    looks_float(text)
        문자열이 소수로 저장하기 적합한지 확인
        전달값: text = CSV에서 읽은 문자열 하나
        반환값: 소수로 저장할 수 있으면 True, 아니면 False

    looks_date(text)
        문자열이 YYYY-MM-DD 형식의 날짜인지 확인
        전달값: text = CSV에서 읽은 문자열 하나
        반환값: YYYY-MM-DD 형식이면 True, 아니면 False

    infer_type(values)
        한 컬럼의 값들을 검사해 타입 반환
        전달값: values = 한 컬럼에 들어 있는 모든 문자열 값의 목록
        반환값: "INTEGER", "FLOAT", "DATE", "TEXT" 중 하나

    infer_pk(columns, rows)
        각 행을 유일하게 구분할 수 있는 기본키(PK) 컬럼을 찾음
        전달값: columns = 컬럼명 목록, rows = 전체 행 목록
        반환값: PK로 판단한 컬럼명, 찾지 못하면 None

    owner_of(column, tables)
        특정 FK가 가르키는 테이블명을 찾음
        전달값: column = FK 후보 컬럼명, tables = 전체 테이블 정보
        반환값: 해당 컬럼이 가리키는 테이블명, 찾지 못하면 None

    build_create(name, table)
        분석한 컬럼, 타입, PK, FK 정보로 CREATE TABLE SQL문을 생성
        전달값: name = 테이블명, table = 해당 테이블의 분석 정보
        반환값: 테이블을 생성할 CREATE TABLE SQL 문자열

    sort_by_dependency(tables)
        참조되는 부모 테이블이 먼저 만들어지도록 테이블 순서를 리스트로 반환
        전달값: tables = 전체 테이블 정보
        반환값: 부모 테이블부터 정렬된 테이블명 목록

    convert(value, kind)
        CSV의 문자열 값을 DB 컬럼 타입에 맞는 파이썬 값으로 변환
        전달값: value = CSV 문자열 값, kind = 저장할 데이터 타입
        반환값: 타입에 맞게 변환된 int, float, 문자열 또는 None


전체 실행 흐름
    1. DATA_DIR에서 모든 CSV 파일을 찾음
    2. read_csv()로 각 CSV의 컬럼과 행을 읽음
    3. infer_type()과 infer_pk()로 컬럼 타입과 PK를 구함
    4. 결과를 tables 딕셔너리에 테이블별로 모음    
    5. owner_of()로 테이블 사이의 FK 관계를 찾아 tables에 추가
    6. sort_by_dependency()로 부모 테이블부터 처리할 table_order를 생성
    7. build_create()로 CREATE TABLE SQL을 만들어 실제 테이블을 생성
    8. convert()로 CSV 값을 타입에 맞게 바꾸고 각 테이블에 INSERT
    9. FK 컬럼에 인덱스를 만들고 commit하여 DB_PATH의 SQLite 파일로 저장

결과
    여러 CSV 파일
        → 컬럼 타입, PK, FK 분석
        → 테이블 생성 및 데이터 삽입
        → DB_PATH에 하나의 SQLite DB 파일 생성
"""