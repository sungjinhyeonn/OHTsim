from pathFinding.dijkstra import dijkstra
from pathFinding.astar import astar
from pathFinding.bellman_ford import bellman_ford
from pathFinding.floyd_warshall import floyd_warshall
from pathFinding.time_tracker import track_dijkstra_time
from pathFinding.time_tracker import track_algorithm_time
MAX_EDGE_VALUE = 99999999
import time

class Scheduler:
    def __init__(self):
        pass
    
    def allocateOHT(self):
        min = MAX_EDGE_VALUE
        targetOHT = -1
        
        a = []
        
        vehicleInfo = self.globalVar.getVehicleInfo()
        for key, value in vehicleInfo.items():
            if value.strState == "IDLE":
                result, map = track_algorithm_time(
                    "bellman_ford",  # 알고리즘 이름
                    "allocateOHT",  # 함수 이름
                    vehicleInfo[key], 
                    self.strDestinationNode, 
                    self.globalVar,
                    bellman_ford
                )
                if min > result:
                    min = result
                    targetOHT = vehicleInfo[key]
        return targetOHT
    
    def scheduleOHT(self, vehicleInfo, commandInfo):
        nodeList = []
        d = str(int(self.strDestinationNode))
        result, map = track_algorithm_time(
                    "bellman_ford",  # 알고리즘 이름
                    "scheduleOHT",  # 함수 이름
                    vehicleInfo, 
                    self.strDestinationNode, 
                    self.globalVar,
                    bellman_ford
                )
        if result == MAX_EDGE_VALUE:
            print("schedule Error")
        else:
            st = []
            _next = map[d][1]
            while _next != -1:
                st.append(_next)
                _next = map[_next][1]
            while st:
                nodeList.append(st[-1])
                st.pop(-1)
            if len(nodeList) != 0:
                nodeList.pop(0)
            nodeList.append(d)

        blockVehicleID = {}
        sortedBlockVehicleID = []
        if commandInfo == "T" or commandInfo == "G":
            allVehicles = self.globalVar.getVehicleInfo()
            for key, value in allVehicles.items():
                if key != vehicleInfo.strVehicleID and value.strState == "IDLE":
                    blockedCoordinates = value.lstCoordinates
                    nodeCount = 0
                    for nodeID in nodeList:
                        nodeCount = nodeCount + 1
                        pathCoordinates = self.globalVar.getCoordinatesByNodeID(nodeID)
                        if blockedCoordinates == pathCoordinates:
                            blockVehicleID[key] = nodeCount
                            break
        if len(blockVehicleID) != 0:
            sortedBlockVehicleID = sorted(blockVehicleID.items(), key = lambda item: item[1], reverse = False)
            self.globalVar.printTerminal("[Schedule Fail] Vehicle #{} Blocked".format(vehicleInfo.strVehicleID))
        return [nodeList, sortedBlockVehicleID]



class FromScheduler(Scheduler):
    def __init__(self, commandID, dstNode, globalVar):
        super().__init__()
        self.schedulerType = "F"
        self.strID = commandID
        self.strDestinationNode = dstNode
        self.globalVar = globalVar

class ToScheduler(Scheduler):
    def __init__(self, commandID, dstNode, globalVar, vehicleID):
        super().__init__()
        self.schedulerType = "T"
        self.strID = commandID
        self.strDestinationNode = dstNode
        self.globalVar = globalVar
        self.vehicleID = vehicleID

class GoScheduler(Scheduler):
    def __init__(self, commandID, globalVar, rootVehicleID, rootPath, lstBlockVehicleID, dstNode = None):
        super().__init__()
        self.schedulerType = "G"
        self.strID = commandID
        self.globalVar =globalVar
        self.rootVehicleID  = rootVehicleID
        self.rootPath = rootPath
        self.lstBlockVehicleID = lstBlockVehicleID
        self.strDestinationNode = dstNode
