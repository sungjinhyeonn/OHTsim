import copy
MAX_EDGE_VALUE = 99999999
from pathFinding.time_tracker import track_algorithm_time

def bellman_ford(vehicleInfo, EquipmentNodeID, globalVar):
    vehiclePosIndex = globalVar.getNodeIDByCoordinates(vehicleInfo.lstCoordinates)
    destinationPosIndex = str(int(EquipmentNodeID))
    nodeInfo = copy.deepcopy(globalVar.getNodeInfo())
    
    # 모든 엣지 정보 가져오기
    edges = []
    railInfo = globalVar.getRailInfo()
    for key, value in railInfo.items():
        edges.append((value.strStartNode, value.strEndNode, value.intWeight))
    
    # 거리 초기화
    dist = {}
    nodeMap = {}
    
    for idx in range(1, len(nodeInfo)+1):
        dist[str(idx)] = MAX_EDGE_VALUE
        
    dist[vehiclePosIndex] = 0
    nodeMap[vehiclePosIndex] = [0, -1]
    
    # 벨만-포드 알고리즘 실행
    # |V|-1번 반복
    for _ in range(len(nodeInfo) - 1):
        for u, v, w in edges:
            if dist[u] != MAX_EDGE_VALUE and dist[v] > dist[u] + w:
                dist[v] = dist[u] + w
                nodeMap[v] = [dist[v], u]
    
    # 음수 사이클 검사 (이 시뮬레이션에서는 필요 없을 수 있음)
    for u, v, w in edges:
        if dist[u] != MAX_EDGE_VALUE and dist[v] > dist[u] + w:
            print("Graph contains negative weight cycle")
            return -1, {}
    
    return dist[destinationPosIndex], nodeMap

def bellman_fordRL(startCoords, GoalCoords, coordConnection):
    start = tuple(startCoords)
    goal = tuple(GoalCoords)
    
    # 모든 노드와 엣지 정보 초기화
    edges = []
    dist = {}
    nodeMap = {}
    
    for key, value in coordConnection.items():
        node = tuple(key)
        dist[node] = MAX_EDGE_VALUE
        for dst in value:
            dst_node = tuple(dst)
            edges.append((node, dst_node, 1))  # 가중치는 1로 가정
    
    dist[start] = 0
    nodeMap[start] = [0, -1]
    
    # 벨만-포드 알고리즘 실행
    for _ in range(len(coordConnection) - 1):
        for u, v, w in edges:
            if dist[u] != MAX_EDGE_VALUE and dist[v] > dist[u] + w:
                dist[v] = dist[u] + w
                nodeMap[v] = [dist[v], u]
    
    # 음수 사이클 검사
    for u, v, w in edges:
        if dist[u] != MAX_EDGE_VALUE and dist[v] > dist[u] + w:
            print("Graph contains negative weight cycle")
            return []
    
    # 경로 재구성
    st = []
    nodeList = []
    _next = nodeMap[goal][1]
    while _next != -1:
        st.append(_next)
        _next = nodeMap[_next][1]
    while st:
        nodeList.append(st[-1])
        st.pop(-1)
    if len(nodeList) != 0:
        nodeList.pop(0)
    nodeList.append(goal)
    return nodeList

def bellman_ford_with_timing(function_name, vehicle_info, destination_node, global_var, bellman_ford_func):
    return track_algorithm_time("bellman_ford", function_name, vehicle_info, destination_node, global_var, bellman_ford_func) 