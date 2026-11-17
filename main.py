import json
import time

# ---------------------------------------------------------
# [공통 함수] MAC 연산 및 판정 로직
# ---------------------------------------------------------

def calculate_mac(matrix_a, matrix_b):
    """두 행렬의 MAC(Multiply-Accumulate) 연산을 수행합니다."""
    size = len(matrix_a)
    score = 0.0
    for i in range(size):
        for j in range(size):
            score += matrix_a[i][j] * matrix_b[i][j]
    return score

def judge_pattern(score_a, score_b, label_a="A", label_b="B"):
    """두 점수를 비교하여 판정 결과를 반환합니다. (부동소수점 오차 고려)"""
    epsilon = 1e-9
    if abs(score_a - score_b) < epsilon:
        return "UNDECIDED"
    return label_a if score_a > score_b else label_b

def get_matrix_input(size, name):
    print(f"\n[{name}] ({size}x{size} 행렬 입력)")
    matrix = []
    for i in range(size):
        while True: 
            try:
                # 사용자에게 입력을 받음
                line = input(f"{i+1}행 (숫자 {size}개를 공백으로 구분): ").split()
                
                # 입력된 숫자의 개수가 맞는지 확인
                if len(line) != size:
                    print(f"   ⚠️ 오류: {size}개의 숫자가 필요합니다. (현재 {len(line)}개 입력됨)")
                    continue
                
                # 숫자로 변환해서 행렬에 추가
                row = list(map(float, line))
                matrix.append(row)
                break 
            except ValueError:
                print("   ⚠️ 오류: 숫자만 입력할 수 있습니다. 다시 입력해주세요.")
    return matrix




# def get_matrix_input(size, name):
#     """사용자로부터 N x N 행렬 입력을 받습니다."""
#     print(f"{name} ({size}줄 입력, 공백 구분)")
#     matrix = []
#     for _ in range(size):
#         row = list(map(float, input().split()))
#         matrix.append(row)
#     return matrix

# ---------------------------------------------------------
# [모드 1] 사용자 입력 처리
# ---------------------------------------------------------

def mode_user_input():
    print("\n#----------------------------------------")
    print("# [1] 필터 입력")
    print("#---------------------------------------")
    filter_a = get_matrix_input(3, "필터 A")
    filter_b = get_matrix_input(3, "필터 B")

    print("\n#---------------------------------------")
    print("# [2] 패턴 입력")
    print("#---------------------------------------")
    pattern = get_matrix_input(3, "패턴")

    # 성능 측정을 위해 10회 반복 실행
    start_time = time.perf_counter()
    for _ in range(10):
        score_a = calculate_mac(filter_a, pattern)
        score_b = calculate_mac(filter_b, pattern)
    end_time = time.perf_counter()
    
    avg_time = ((end_time - start_time) / 10) * 1000 # ms 단위
    result = judge_pattern(score_a, score_b)

    print("\n#---------------------------------------")
    print("# [3] MAC 결과")
    print("#---------------------------------------")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    
    if result == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < 1e-9)")
    else:
        print(f"연산 시간(평균/10회): {avg_time:.3f} ms")
        print(f"판정: {result}")

# ---------------------------------------------------------
# [모드 2] JSON 데이터 분석
# ---------------------------------------------------------

def mode_json_analysis():
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("에러: data.json 파일을 찾을 수 없습니다.")
        return

    print("\n#---------------------------------------")
    print("# [1] 필터 로드")
    print("#---------------------------------------")
    sizes = sorted(list(set(case['size'] for case in data['test_cases'])))
    for s in sizes:
        print(f"✓ size_{s}  필터 로드 완료 (Cross, X)")

    print("\n#---------------------------------------")
    print("# [2] 패턴 분석 (라벨 정규화 적용)")
    print("#---------------------------------------")
    
    test_results = []
    perf_stats = {s: [] for s in sizes}

    for i, case in enumerate(data['test_cases']):
        size = case['size']
        case_id = f"size_{size}_{i+1}"
        
        # 성능 측정 (10회 반복)
        start = time.perf_counter()
        for _ in range(10):
            s_cross = calculate_mac(case['filter_cross'], case['pattern'])
            s_x = calculate_mac(case['filter_x'], case['pattern'])
        end = time.perf_counter()
        
        avg_t = ((end - start) / 10) * 1000
        perf_stats[size].append(avg_t)

        prediction = judge_pattern(s_cross, s_x, "Cross", "X")
        is_pass = "PASS" if prediction == case['expected'] else "FAIL"
        
        test_results.append({
            "id": case_id,
            "prediction": prediction,
            "expected": case['expected'],
            "is_pass": is_pass,
            "reason": "동점 규칙" if prediction == "UNDECIDED" else "불일치"
        })

        print(f"- -- {case_id} ---")
        print(f"Cross 점수: {s_cross}")
        print(f"X 점수: {s_x}")
        print(f"판정: {prediction} | expected: {case['expected']} | {is_pass}")

    print("\n#---------------------------------------")
    print("# [3] 성능 분석 (평균/10회)")
    print("#---------------------------------------")
    print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수'}")
    print("-" * 40)
    for s in sizes:
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
    
    choice = input("선택: ")
    if choice == '1':
        mode_user_input()
    elif choice == '2':
        mode_json_analysis()
    else:
        print("잘못된 선택입니다.")

if __name__ == "__main__":
    main()