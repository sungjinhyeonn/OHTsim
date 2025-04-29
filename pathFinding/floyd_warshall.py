import copy
MAX_EDGE_VALUE = 99999999
from pathFinding.time_tracker import track_algorithm_time

def floyd_warshall(vehicleInfo, EquipmentNodeID, globalVar):
    vehiclePosIndex = globalVar.getNodeIDByCoordinates(vehicleInfo.lstCoordinates)
    destinationPosIndex = str(int(EquipmentNodeID))
    nodeInfo = copy.deepcopy(globalVar.getNodeInfo())
    
    # 거리 행렬 초기화
    dist = {}
    next_node = {}  # 경로 추적을 위한 다음 노드 정보
    
    # 모든 노드 쌍에 대해 초기화
    for i in range(1, len(nodeInfo)+1):
        dist[str(i)] = {}
        next_node[str(i)] = {}
        for j in range(1, len(nodeInfo)+1):
            if i == j:
                dist[str(i)][str(j)] = 0
            else:
                dist[str(i)][str(j)] = MAX_EDGE_VALUE
            next_node[str(i)][str(j)] = None
    
    # 엣지 정보로 초기화
    railInfo = globalVar.getRailInfo()
    for key, value in railInfo.items():
        u = value.strStartNode
        v = value.strEndNode
        w = value.intWeight
        dist[u][v] = w
        next_node[u][v] = v
    
    # 플로이드-워셜 알고리즘 실행
    for k in range(1, len(nodeInfo)+1):
        for i in range(1, len(nodeInfo)+1):
            for j in range(1, len(nodeInfo)+1):
                if dist[str(i)][str(j)] > dist[str(i)][str(k)] + dist[str(k)][str(j)]:
                    dist[str(i)][str(j)] = dist[str(i)][str(k)] + dist[str(k)][str(j)]
                    next_node[str(i)][str(j)] = next_node[str(i)][str(k)]
    
    # 경로 재구성을 위한 nodeMap 생성
    nodeMap = {}
    
    # 시작점에서 목적지까지의 경로 재구성
    if next_node[vehiclePosIndex][destinationPosIndex] is not None:
        path = []
        current = vehiclePosIndex
        while current != destinationPosIndex:
            next_hop = next_node[current][destinationPosIndex]
            path.append(next_hop)
            nodeMap[next_hop] = [dist[vehiclePosIndex][next_hop], current]
            current = next_hop
        
        # 시작점 추가
        nodeMap[vehiclePosIndex] = [0, -1]
    
    return dist[vehiclePosIndex][destinationPosIndex], nodeMap

def floyd_warshallRL(startCoords, GoalCoords, coordConnection):
    start = tuple(startCoords)
    goal = tuple(GoalCoords)
    
    # 모든 노드 목록 생성
    nodes = list(coordConnection.keys())
    nodes = [tuple(node) for node in nodes]
    
    # 거리 행렬과 다음 노드 정보 초기화
    dist = {}
    next_node = {}
    
    for i in nodes:
        dist[i] = {}
        next_node[i] = {}
        for j in nodes:
            if i == j:
                dist[i][j] = 0
            else:
                dist[i][j] = MAX_EDGE_VALUE
            next_node[i][j] = None
    
    # 엣지 정보로 초기화
    for node, neighbors in coordConnection.items():
        node = tuple(node)
        for neighbor in neighbors:
            neighbor = tuple(neighbor)
            dist[node][neighbor] = 1  # 가중치는 1로 가정
            next_node[node][neighbor] = neighbor
    
    # 플로이드-워셜 알고리즘 실행
    for k in nodes:
        for i in nodes:
            for j in nodes:
                if dist[i][j] > dist[i][k] + dist[k][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    next_node[i][j] = next_node[i][k]
    
    # 경로 재구성
    if next_node[start][goal] is None:
        return []
    
    path = []
    current = start
    while current != goal:
        next_hop = next_node[current][goal]
        path.append(next_hop)
        current = next_hop
    
    return path 

def floyd_warshall_with_timing(function_name, vehicle_info, destination_node, global_var, floyd_warshall_func):
    return track_algorithm_time("floyd_warshall", function_name, vehicle_info, destination_node, global_var, floyd_warshall_func) 