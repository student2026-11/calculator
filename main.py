import json
import time

# ---------------------------------------------------------
# [공통 함수] MAC 연산, 판정 및 검증 로직
# ---------------------------------------------------------
def calculate_mac(matrix_a, matrix_b):
    """두 행렬의 MAC(Multiply-Accumulate) 연산을 외부 라이브러리 없이 수행합니다."""
    size = len(matrix_a)
    score = 0.0
    for i in range(size):
        for j in range(size):
            score += matrix_a[i][j] * matrix_b[i][j]
    return score

def judge_pattern(score_a, score_b, label_a="A", label_b="B"):
    """허용오차(epsilon) 기반으로 두 점수를 비교하여 판정 결과를 반환합니다."""
    epsilon = 1e-9
    if abs(score_a - score_b) < epsilon:
        return "UNDECIDED"
    return label_a if score_a > score_b else label_b

def is_valid_matrix(matrix, expected_size):
    """행렬이 expected_size x expected_size 크기인지 검증합니다."""
    if not isinstance(matrix, list) or len(matrix) != expected_size:
        return False
    return all(isinstance(row, list) and len(row) == expected_size for row in matrix)

def get_matrix_input(size, name):
    """사용자로부터 N x N 행렬을 한 줄씩 공백 구분으로 입력받습니다."""
    print(f"\n[{name}] ({size}x{size} 행렬 입력)")
    matrix = []
    for i in range(size):
        while True:
            try:
                line = input(f"{i+1}행 (숫자 {size}개를 공백으로 구분): ").split()
                if len(line) != size:
                    print(f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요. (현재 {len(line)}개 입력됨)")
                    continue
                row = list(map(float, line))
                matrix.append(row)
                break
            except ValueError:
                print(f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요.")
    return matrix

# ---------------------------------------------------------
# [모드 1] 사용자 입력 처리 (3x3)
# ---------------------------------------------------------
def mode_user_input():
    print("\n#---------------------------------------")
    print("# [1] 필터 입력")
    print("#---------------------------------------")
    filter_a = get_matrix_input(3, "필터 A")
    filter_b = get_matrix_input(3, "필터 B")
    print("\n✓ 필터 A, B 저장 완료")

    print("\n#---------------------------------------")
    print("# [2] 패턴 입력")
    print("#---------------------------------------")
    pattern = get_matrix_input(3, "패턴")

    # 성능 측정을 위해 10회 반복 실행 (I/O 제외 순수 연산 구간)
    start_time = time.perf_counter()
    for _ in range(10):
        score_a = calculate_mac(filter_a, pattern)
        score_b = calculate_mac(filter_b, pattern)
    end_time = time.perf_counter()

    avg_time = ((end_time - start_time) / 10) * 1000  # ms 단위
    result = judge_pattern(score_a, score_b)

    print("\n#---------------------------------------")
    print("# [3] MAC 결과 및 성능 분석")
    print("#---------------------------------------")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/10회): {avg_time:.3f} ms (연산 횟수: {3 * 3})")
    if result == "UNDECIDED":
        print("판정: 판정 불가 (|A-B| < 1e-9)")
    else:
        print(f"판정: {result}")

# ---------------------------------------------------------
# [모드 2] JSON 데이터 분석 (data.json)
# ---------------------------------------------------------
def mode_json_analysis():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("에러: data.json 파일을 찾을 수 없습니다.")
        return
    except json.JSONDecodeError:
        print("에러: data.json 파일 형식이 올바르지 않습니다.")
        return

    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")
    sizes = sorted([int(k.split('_')[1]) for k in data.get('filters', {}).keys()])
    for s in sizes:
        print(f"✓ size_{s} 필터 로드 완료 (Cross, X)")

    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")
    test_results = []
    perf_stats = {s: [] for s in sizes}

    # 라벨 정규화 매핑 ('+' -> 'Cross', 'x' -> 'X')
    label_map = {"+": "Cross", "x": "X"}

    for case_id, case in data.get('patterns', {}).items():
        try:
            size = int(case_id.split('_')[1])
        except (IndexError, ValueError):
            test_results.append({
                "id": case_id,
                "prediction": "ERROR",
                "expected": "UNKNOWN",
                "is_pass": "FAIL",
                "reason": "잘못된 패턴 키 형식"
            })
            print(f"--- {case_id} ---")
            print("판정: ERROR | FAIL (사유: 잘못된 패턴 키 형식)")
            continue

        filter_key = f"size_{size}"

        # expected 값 정규화
        raw_expected = str(case.get('expected', '')).strip().lower()
        expected = label_map.get(raw_expected, case.get('expected', ''))

        # 스키마 검증 1: 해당 크기의 필터 존재 여부
        if filter_key not in data.get('filters', {}):
            test_results.append({
                "id": case_id,
                "prediction": "ERROR",
                "expected": expected,
                "is_pass": "FAIL",
                "reason": f"{filter_key} 필터 없음"
            })
            print(f"--- {case_id} ---")
            print(f"판정: ERROR | expected: {expected} | FAIL (사유: {filter_key} 필터 없음)")
            continue

        filter_cross = data['filters'][filter_key].get('cross')
        filter_x = data['filters'][filter_key].get('x')
        pattern_matrix = case.get('input')

        # 스키마 검증 2: 필터와 패턴의 크기가 N x N으로 일치하는지 검증
        if not (is_valid_matrix(filter_cross, size) and is_valid_matrix(filter_x, size) and is_valid_matrix(pattern_matrix, size)):
            test_results.append({
                "id": case_id,
                "prediction": "ERROR",
                "expected": expected,
                "is_pass": "FAIL",
                "reason": "필터 및 패턴 크기 불일치"
            })
            print(f"--- {case_id} ---")
            print(f"판정: ERROR | expected: {expected} | FAIL (사유: 필터 및 패턴 크기 불일치)")
            continue

        # 성능 측정 (10회 반복, I/O 제외)
        start = time.perf_counter()
        for _ in range(10):
            s_cross = calculate_mac(filter_cross, pattern_matrix)
            s_x = calculate_mac(filter_x, pattern_matrix)
        end = time.perf_counter()

        avg_t = ((end - start) / 10) * 1000
        perf_stats[size].append(avg_t)

        prediction = judge_pattern(s_cross, s_x, "Cross", "X")
        is_pass = "PASS" if prediction == expected else "FAIL"

        test_results.append({
            "id": case_id,
            "prediction": prediction,
            "expected": expected,
            "is_pass": is_pass,
            "reason": "동점 규칙(UNDECIDED)" if prediction == "UNDECIDED" else "예측 불일치"
        })

        print(f"--- {case_id} ---")
        print(f"Cross 점수: {s_cross:.2f}")
        print(f"X 점수: {s_x:.2f}")
        print(f"판정: {prediction} | expected: {expected} | {is_pass}")

    print("\n#---------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#---------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수'}")
    print("-" * 40)

    # 3x3 기준 연산 시간 측정 (실행 흐름 요구사항 반영)
    dummy_3x3 = [[1.0, 0.0, 1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 1.0]]
    start_3 = time.perf_counter()
    for _ in range(10):
        calculate_mac(dummy_3x3, dummy_3x3)
        calculate_mac(dummy_3x3, dummy_3x3)
    end_3 = time.perf_counter()
    avg_3x3_time = ((end_3 - start_3) / 10) * 1000
    print(f"{'3×3':<10} {avg_3x3_time:<15.3f} {3 * 3}")

    for s in sizes:
        if perf_stats[s]:
            avg_size_time = sum(perf_stats[s]) / len(perf_stats[s])
            ops = s * s
            print(f"{f'{s}×{s}':<10} {avg_size_time:<15.3f} {ops}")

    print("\n#---------------------------------------")
    print("# [4] 결과 요약")
    print("#---------------------------------------")
    total = len(test_results)
    passed = sum(1 for r in test_results if r['is_pass'] == "PASS")
    failed = total - passed
    print(f"총 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")

    if failed > 0:
        print("\n실패 케이스:")
        for r in test_results:
            if r['is_pass'] == "FAIL":
                print(f"- {r['id']}: {r['reason']}에 따라 FAIL")

# ---------------------------------------------------------
# 메인 메뉴
# ---------------------------------------------------------
def main():
    print("=== Mini NPU Simulator ===")
    print("\n[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")
    choice = input("선택: ").strip()

    if choice == '1':
        mode_user_input()
    elif choice == '2':
        mode_json_analysis()
    else:
        print("잘못된 선택입니다.")

if __name__ == "__main__":
    main()
 