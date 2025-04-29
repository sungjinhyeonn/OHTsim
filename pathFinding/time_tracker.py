import time
import csv
import os
from datetime import datetime

# 알고리즘 실행 시간을 누적하기 위한 전역 변수
# 구조: _total_times[algorithm][iteration][function_name] = total_time
_total_times = {}
_call_counts = {}
_current_iteration = 1
_current_vehicle_count = 0

def set_current_iteration(iteration, vehicle_count):
    """
    현재 반복(iteration) 번호와 차량 수를 설정
    
    Parameters:
    - iteration: 현재 몬테카를로 반복 번호
    - vehicle_count: 현재 시뮬레이션의 차량 수
    """
    global _current_iteration, _current_vehicle_count, _total_times, _call_counts
    _current_iteration = iteration
    _current_vehicle_count = vehicle_count
    
    # 모든 알고리즘에 대해 새 반복 초기화
    algorithms = ["dijkstra", "astar", "bellman_ford", "floyd_warshall"]
    iter_key = f"Vehicle_{vehicle_count}_Iter_{iteration}"
    
    for algorithm in algorithms:
        if algorithm not in _total_times:
            _total_times[algorithm] = {}
            _call_counts[algorithm] = {}
            
        if iter_key not in _total_times[algorithm]:
            _total_times[algorithm][iter_key] = {
                "allocateOHT": 0.0,
                "scheduleOHT": 0.0
            }
            _call_counts[algorithm][iter_key] = {
                "allocateOHT": 0,
                "scheduleOHT": 0
            }

def track_algorithm_time(algorithm_name, function_name, vehicle_info, destination_node, global_var, algorithm_func):
    """
    알고리즘 실행 시간을 측정하고 누적하여 CSV 파일에 저장하는 함수
    
    Parameters:
    - algorithm_name: 사용된 알고리즘 이름 (예: "dijkstra", "astar", "bellman_ford", "floyd_warshall")
    - function_name: 알고리즘을 호출한 함수 이름 (예: "allocateOHT" 또는 "scheduleOHT")
    - vehicle_info: 차량 정보
    - destination_node: 목적지 노드
    - global_var: 전역 변수
    - algorithm_func: 실행할 알고리즘 함수
    
    Returns:
    - result, map: 알고리즘의 원래 반환값
    """
    global _total_times, _call_counts, _current_iteration, _current_vehicle_count
    
    # 현재 반복에 대한 키 생성
    iter_key = f"Vehicle_{_current_vehicle_count}_Iter_{_current_iteration}"
    
    # 알고리즘이 _total_times에 없으면 초기화
    if algorithm_name not in _total_times:
        _total_times[algorithm_name] = {}
        _call_counts[algorithm_name] = {}
    
    # 반복 키가 없으면 초기화
    if iter_key not in _total_times[algorithm_name]:
        _total_times[algorithm_name][iter_key] = {}
        _call_counts[algorithm_name][iter_key] = {}
    
    # 시작 시간 기록
    start_time = time.time()
    
    # 알고리즘 실행
    result, map_data = algorithm_func(vehicle_info, destination_node, global_var)
    
    # 종료 시간 기록 및 실행 시간 계산 (밀리초 단위)
    end_time = time.time()
    execution_time_ms = (end_time - start_time) * 1000
    
    # 총 실행 시간 누적
    if function_name in _total_times[algorithm_name][iter_key]:
        _total_times[algorithm_name][iter_key][function_name] += execution_time_ms
        _call_counts[algorithm_name][iter_key][function_name] += 1
    else:
        _total_times[algorithm_name][iter_key][function_name] = execution_time_ms
        _call_counts[algorithm_name][iter_key][function_name] = 1
    
    # CSV 파일에 누적 결과 저장
    save_accumulated_times(algorithm_name)
    
    return result, map_data

def save_accumulated_times(algorithm_name=None):
    """
    누적된 알고리즘 실행 시간을 CSV 파일에 저장
    
    Parameters:
    - algorithm_name: 저장할 알고리즘 이름 (None이면 모든 알고리즘 저장)
    """
    if algorithm_name is None:
        # 모든 알고리즘에 대해 저장
        for alg in _total_times:
            save_accumulated_times(alg)
        return
    
    # 알고리즘별 CSV 파일 이름
    csv_filename = f"{algorithm_name}_total_times_by_iteration.csv"
    
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Iteration', 'Vehicle Count', 'Function', 'Total Execution Time (ms)', 'Call Count', 'Average Time (ms)'])
        
        if algorithm_name in _total_times:
            for iter_key in _total_times[algorithm_name]:
                # 키에서 차량 수와 반복 번호 추출
                parts = iter_key.split('_')
                vehicle_count = parts[1]
                iteration = parts[3]
                
                for func_name in _total_times[algorithm_name][iter_key]:
                    total_time = _total_times[algorithm_name][iter_key][func_name]
                    call_count = _call_counts[algorithm_name][iter_key][func_name]
                    avg_time = total_time / call_count if call_count > 0 else 0
                    
                    writer.writerow([
                        iteration,
                        vehicle_count,
                        func_name,
                        f"{total_time:.3f}",
                        call_count,
                        f"{avg_time:.3f}"
                    ])

def reset_timers():
    """
    타이머 초기화 함수 (필요시 호출)
    """
    global _total_times, _call_counts, _current_iteration, _current_vehicle_count
    _total_times = {}
    _call_counts = {}
    _current_iteration = 1
    _current_vehicle_count = 0
    
    # 모든 알고리즘에 대한 CSV 파일 초기화
    algorithms = ["dijkstra", "astar", "bellman_ford", "floyd_warshall"]
    for algorithm in algorithms:
        csv_filename = f"{algorithm}_total_times_by_iteration.csv"
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Iteration', 'Vehicle Count', 'Function', 'Total Execution Time (ms)', 'Call Count', 'Average Time (ms)'])

# 다익스트라 알고리즘 시간 추적 함수 (이전 버전과의 호환성 유지)
def track_dijkstra_time(function_name, vehicle_info, destination_node, global_var, dijkstra_func):
    """
    다익스트라 알고리즘 실행 시간을 측정하고 누적하여 CSV 파일에 저장하는 함수
    
    Parameters:
    - function_name: 다익스트라를 호출한 함수 이름 (예: "allocateOHT" 또는 "scheduleOHT")
    - vehicle_info: 차량 정보
    - destination_node: 목적지 노드
    - global_var: 전역 변수
    - dijkstra_func: 다익스트라 알고리즘 함수
    
    Returns:
    - result, map: 다익스트라 알고리즘의 원래 반환값
    """
    return track_algorithm_time("dijkstra", function_name, vehicle_info, destination_node, global_var, dijkstra_func)