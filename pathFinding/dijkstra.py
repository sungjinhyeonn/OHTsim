import copy
import heapq
MAX_EDGE_VALUE = 99999999

def dijkstra(vehicleInfo, EquipmentNodeID, globalVar):
    vehiclePosIndex = globalVar.getNodeIDByCoordinates(vehicleInfo.lstCoordinates)
    destinationPosIndex = str(int(EquipmentNodeID))
    nodeInfo = copy.deepcopy(globalVar.getNodeInfo())
    eW = initEdge(globalVar.getRailInfo(), len(nodeInfo))

    dist = {}
    pq = []
    nodeMap = {}    
    nodeMap[vehiclePosIndex] = [0, -1]
    for idx in range(1, len(nodeInfo)+1):
        dist[str(idx)] = MAX_EDGE_VALUE
        
    dist[vehiclePosIndex] = 0
    nodeInfo[vehiclePosIndex].dist = 0
    nodeInfo[vehiclePosIndex].post = vehiclePosIndex

    for idx in range(1, len(nodeInfo)+1):
        # pq = [weight, index, post]
        heapq.heappush(pq, [nodeInfo[str(idx)].dist, nodeInfo[str(idx)].strNodeID, nodeInfo[str(idx)].post])

    while pq:
        cost, index, post = heapq.heappop(pq)
        if dist[index] > cost:
            continue
        for i in range(len(eW[index])):
            choosenRail = eW[index][i]
            currentNodeIndex = choosenRail[0]
            nextNodeIndex = choosenRail[1]
            weight = choosenRail[2]

            if dist[nextNodeIndex] > (dist[index] + weight):
                dist[nextNodeIndex] = dist[index] + weight
                heapq.heappush(pq, [dist[nextNodeIndex], nextNodeIndex, index])
                nodeMap[nextNodeIndex] = [dist[nextNodeIndex], index]
    return dist[destinationPosIndex], nodeMap

## for dijkstra ##
def initEdge(railInfo, lenNode):
    eW = {}
    for idx in range(1, lenNode+1):
        eW[str(idx)] = []
    for key, value in railInfo.items():
        eW[value.strStartNode].append([value.strStartNode, value.strEndNode, value.intWeight])
    return eW

def dijkstraRL(startCoords, GoalCoords, coordConnection):
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

    for idx in nodeInfo:
        # pq = [weight, index, post]
        heapq.heappush(pq, [nodeInfo[idx]['dist'], idx, nodeInfo[idx]['post']])

    while pq:
        cost, index, post = heapq.heappop(pq)
        if dist[index] > cost:
            continue
        for i in range(len(eW[index])):
            choosenRail = eW[index][i]
            currentNodeIndex = choosenRail[0]
            nextNodeIndex = choosenRail[1]
            weight = choosenRail[2]

            if dist[nextNodeIndex] > (dist[index] + weight):
                dist[nextNodeIndex] = dist[index] + weight
                heapq.heappush(pq, [dist[nextNodeIndex], nextNodeIndex, index])
                nodeMap[nextNodeIndex] = [dist[nextNodeIndex], index]
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
