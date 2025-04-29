import copy
import heapq
MAX_EDGE_VALUE = 99999999
from pathFinding.time_tracker import track_algorithm_time

def astar(vehicleInfo, EquipmentNodeID, globalVar):
    vehiclePosIndex = globalVar.getNodeIDByCoordinates(vehicleInfo.lstCoordinates)
    destinationPosIndex = str(int(EquipmentNodeID))
    nodeInfo = copy.deepcopy(globalVar.getNodeInfo())
    eW = initEdge(globalVar.getRailInfo(), len(nodeInfo))
    
    # 목적지 노드의 좌표 가져오기
    destNode = nodeInfo[destinationPosIndex]
    destCoords = [float(destNode.lstCoordinates[0]), float(destNode.lstCoordinates[1])]
    
    dist = {}
    pq = []
    nodeMap = {}    
    nodeMap[vehiclePosIndex] = [0, -1]
    
    for idx in range(1, len(nodeInfo)+1):
        dist[str(idx)] = MAX_EDGE_VALUE
        
    dist[vehiclePosIndex] = 0
    nodeInfo[vehiclePosIndex].dist = 0
    nodeInfo[vehiclePosIndex].post = vehiclePosIndex
    
    # A*에서는 f = g + h 값을 사용 (g: 시작점에서의 거리, h: 휴리스틱 - 목적지까지의 추정 거리)
    startNode = nodeInfo[vehiclePosIndex]
    startCoords = [float(startNode.lstCoordinates[0]), float(startNode.lstCoordinates[1])]
    h = heuristic(startCoords, destCoords)
    
    # pq = [f값, g값, 노드ID, 이전노드]
    heapq.heappush(pq, [h, 0, vehiclePosIndex, vehiclePosIndex])
    
    while pq:
        f, g, index, post = heapq.heappop(pq)
        
        # 이미 더 좋은 경로를 찾았다면 스킵
        if dist[index] < g:
            continue
            
        # 목적지에 도달했다면 종료
        if index == destinationPosIndex:
            break
            
        for i in range(len(eW[index])):
            choosenRail = eW[index][i]
            currentNodeIndex = choosenRail[0]
            nextNodeIndex = choosenRail[1]
            weight = choosenRail[2]
            
            # 새로운 g값 계산
            new_g = g + weight
            
            if dist[nextNodeIndex] > new_g:
                dist[nextNodeIndex] = new_g
                
                # 휴리스틱 계산
                nextNode = nodeInfo[nextNodeIndex]
                nextCoords = [float(nextNode.lstCoordinates[0]), float(nextNode.lstCoordinates[1])]
                h = heuristic(nextCoords, destCoords)
                
                # f = g + h
                f = new_g + h
                
                heapq.heappush(pq, [f, new_g, nextNodeIndex, index])
                nodeMap[nextNodeIndex] = [new_g, index]
    
    return dist[destinationPosIndex], nodeMap

def heuristic(current, destination):
    # 유클리드 거리 계산 (직선 거리)
    return ((current[0] - destination[0]) ** 2 + (current[1] - destination[1]) ** 2) ** 0.5

## for A* ##
def initEdge(railInfo, lenNode):
    eW = {}
    for idx in range(1, lenNode+1):
        eW[str(idx)] = []
    for key, value in railInfo.items():
        eW[value.strStartNode].append([value.strStartNode, value.strEndNode, value.intWeight])
    return eW

def astarRL(startCoords, GoalCoords, coordConnection):
    start = tuple(startCoords)
    goal = tuple(GoalCoords)

    eW = {}
    nodeInfo = {}
    dist = {}
    for key, value in coordConnection.items():
        eW[tuple(key)] = []
        nodeInfo[tuple(key)] = {}

    for key, value in coordConnection.items():
        nodeInfo[tuple(key)]['dist'] = MAX_EDGE_VALUE
        nodeInfo[tuple(key)]['post'] = 0
        dist[tuple(key)] = MAX_EDGE_VALUE
        for dst in value:
            eW[tuple(key)].append([tuple(key), tuple(dst), 1])

    pq = []
    nodeMap = {}    
    nodeMap[start] = [0, -1]
    dist[start] = 0
    nodeInfo[start]['dist'] = 0
    nodeInfo[start]['post'] = start
    
    # 휴리스틱 계산
    h = ((start[0] - goal[0]) ** 2 + (start[1] - goal[1]) ** 2) ** 0.5
    
    # pq = [f값, g값, 노드, 이전노드]
    heapq.heappush(pq, [h, 0, start, start])

    while pq:
        f, g, index, post = heapq.heappop(pq)
        
        if dist[index] < g:
            continue
            
        if index == goal:
            break
            
        for i in range(len(eW[index])):
            choosenRail = eW[index][i]
            currentNodeIndex = choosenRail[0]
            nextNodeIndex = choosenRail[1]
            weight = choosenRail[2]
            
            new_g = g + weight
            
            if dist[nextNodeIndex] > new_g:
                dist[nextNodeIndex] = new_g
                
                # 휴리스틱 계산
                h = ((nextNodeIndex[0] - goal[0]) ** 2 + (nextNodeIndex[1] - goal[1]) ** 2) ** 0.5
                f = new_g + h
                
                heapq.heappush(pq, [f, new_g, nextNodeIndex, index])
                nodeMap[nextNodeIndex] = [new_g, index]
    
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

def astar_with_timing(function_name, vehicle_info, destination_node, global_var, astar_func):
    return track_algorithm_time("astar", function_name, vehicle_info, destination_node, global_var, astar_func) 