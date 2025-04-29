import copy
import json

MAX_EDGE_VALUE = 99999999

class GlobalVar:
    def __init__(self, isTerminalOn, railList, nodeList, equipmentInfo, seqInfo, performanceInfo, vehicleInfo, numJob, jsonPath, numVehicle, isMakeRlEnv):
        self.railInfo = {}
        self.nodeInfo = {}
        self.subNodeInfo = {}
        self.totalNodeInfo = {}
        self.nextNodeInfo = {}
        self.equipmentInfo = {}
        self.sequenceInfo = {}
        self.vehicleInfo = {}
        self.targetJobs = {}
        self.performanceInfo = {}
        self.isTerminalOn = isTerminalOn
        self.jsonPath = jsonPath
        self.initVehicleInfo = {}
        self.nodeToGo = ["256", "255", "254", "253", "252", "251", "298", "297", "296", "295", "294", "293"]

        self.setNodeInfo(nodeList)
        self.setRailInfo(railList)
        self.setSubNodes()
        self.setEquipmentInfo(equipmentInfo)
        self.setSequenceInfo(seqInfo)
        self.setPerformanceInfo(performanceInfo)
        self.setVehicleInfo(vehicleInfo, numVehicle)
        self.setTargetJobs(numJob, 1)
        if isMakeRlEnv == True:
            self.writeRLEnvInfoAsJSON()

    ## write total nodes as json file ##
    def writeRLEnvInfoAsJSON(self):
        fileName = "trainMap"
        totalPath = self.jsonPath + fileName + ".json"
        with open(totalPath, "w") as json_file:
            tempJSON = {}
            tempJSON['fileName'] = fileName
            tempJSON['nodeInfo'] = []
            tempJSON['equipmentInfo'] = []
            tempJSON['nodeConnectionInfo'] = []
            for key, value in self.totalNodeInfo.items():
                tempJSON['nodeInfo'].append({
                    "nodeID": key,
					"coordinates": value.lstCoordinates,
                    "isBranch": value.isBranch,
                    "isEquipment": value.isEquipment,
                    "isSubNode": value.isSubNode,
                    "isBranch": value.isBranch
                })
            for key, value in self.equipmentInfo.items():
                tempJSON['equipmentInfo'].append({
                    "nodeID": value.strEquipmentNodeID,
					"equipmentID": key,
                    "processType": value.strType
                })
            for key, value in self.nextNodeInfo.items():
                tempJSON['nodeConnectionInfo'].append({
                    "fromNodeID": key,
					"toNodeID": value
                })                
            json.dump(tempJSON, json_file, indent = 4)

    ## generate jobs ##
    def setTargetJobs(self, targetNum, seqNum):
        jobID = 1
        for i in range(targetNum):
            self.targetJobs[jobID] = Job(jobID, seqNum, self.getSequenceInfoBySeqNum(seqNum).lstSequence)
            jobID += 1
    def getTargetJobs(self):
        return self.targetJobs
    def getTargetJobsByID(self, ID):
        return self.targetJobs[int(ID)]

    ## function for OHT information ##
    def setVehicleInfo(self, Info, numVehicle):
        for i in range(numVehicle):
            self.vehicleInfo[Info[i]["vehicleID"]] = Vehicle(Info[i]["vehicleID"], Info[i]["coordinates"])
            nodeID = self.getNodeIDByCoordinates(Info[i]["coordinates"])
            if nodeID == None:
                print("Vehicle initiated at the wrong node")
            else:
                self.nodeInfo[nodeID].isReserved = True
                self.vehicleInfo[Info[i]["vehicleID"]].curNodeID = nodeID
                self.initVehicleInfo[Info[i]["vehicleID"]] = copy.deepcopy(self.vehicleInfo[Info[i]["vehicleID"]])
        
    def getVehicleInfo(self):
        return self.vehicleInfo
    def getInitVehicleInfo(self):
        return self.initVehicleInfo
    
    def getVehicleInfoByID(self, ID):
        return self.vehicleInfo[str(ID)]

    ## function for sequence information ##
    def setSequenceInfo(self, Info):
        for i in range(len(Info)):
            self.sequenceInfo[Info[i]["seqNum"]] = Sequence(Info[i]["seqNum"], Info[i]["sequenceList"])
    def getSequenceInfo(self):
        return self.sequenceInfo
    def getSequenceInfoBySeqNum(self, seqNum):
        return self.sequenceInfo[int(seqNum)]
    
    ## funtion for equipment information ##
    def setEquipmentInfo(self, Info):
        for i in range(len(Info)):
            nodeInfo = self.nodeInfo[Info[i]["equipmentNodeID"]]
            self.equipmentInfo[Info[i]["equipmentID"]] = Equipment(Info[i]["equipmentID"], Info[i]["equipmentNodeID"], nodeInfo.lstCoordinates, Info[i]["processTime"], Info[i]["processType"], Info[i]["performance"] )
            nodeInfo.isEquipment = True

    def getEquipmentInfo(self):
        return self.equipmentInfo
    
    def getEquipmentInfoByID(self, ID):
        return self.equipmentInfo[str(ID)]
    def getEquipmentInfoByNodeID(self, nodeID):
        for key, value in self.equipmentInfo.items():
            if nodeID == value.strEquipmentNodeID:
                return self.equipmentInfo[key]
        
    ## function for node information ##
    def setNodeInfo(self, Info):
        for i in range(len(Info)):
            self.nodeInfo[str(Info[i]["nodeID"])] = Node(Info[i]["nodeID"], Info[i]["coordinates"], False)

    def getNodeInfo(self):
        return self.nodeInfo
    def getSubNodeInfo(self):
        return self.subNodeInfo
    def getTotalNodeInfo(self):
        return self.totalNodeInfo
    def getNodeInfoByID(self, ID):
        return self.nodeInfo[str(ID)]
    def getTotalNodeInfoByID(self, ID):
        return self.totalNodeInfo[str(ID)]

    ## function for rail information ##
    def setRailInfo(self, Info):
        tempStartNodeDuplicateCnt = {}
        tempEndNodeDuplicateCnt = {}
        for i in range(len(Info)):
            self.railInfo[str(i+1)] = Rail(i+1, Info[i]["startNode"], Info[i]["endNode"], Info[i]["edgeWeight"], Info[i]["railType"], [])
            if Info[i]["startNode"] not in tempStartNodeDuplicateCnt:
                tempStartNodeDuplicateCnt[Info[i]["startNode"]] = 1
            else:
                tempStartNodeDuplicateCnt[Info[i]["startNode"]] = tempStartNodeDuplicateCnt[Info[i]["startNode"]] + 1
            if Info[i]["endNode"] not in tempEndNodeDuplicateCnt:
                tempEndNodeDuplicateCnt[Info[i]["endNode"]] = 1
            else:
                tempEndNodeDuplicateCnt[Info[i]["endNode"]] = tempEndNodeDuplicateCnt[Info[i]["endNode"]] + 1
        ## set Branch&Confluence of the node
        for key, value in tempStartNodeDuplicateCnt.items():
            if value == 2:
                self.nodeInfo[str(key)].isBranch = True
        for key, value in tempEndNodeDuplicateCnt.items():
            if value == 2:
                self.nodeInfo[str(key)].isConfluence = True
    def getRailInfo(self):
        return self.railInfo
    def getRailInfoByID(self, ID):
        return self.railInfo[str(ID)]
    def getRailInfoByStartNodeID(self, startNodeID):
        for key, value in self.railInfo.items():
            if startNodeID == value.strStartNode:
                return self.railInfo[key]

    ## function for subNode calculation ##
    def setSubNodes(self):
        for key, value in self.railInfo.items():
            self.createSubNode(key, value)
        for key, value in self.nodeInfo.items():
            self.totalNodeInfo[key] = value
        for key, value in self.subNodeInfo.items():
            self.totalNodeInfo[key] = value

    ## function for subNode Calculation
    def createSubNode(self, railID, railInfo):
        railType = railInfo.strType
        divisionResolution = railInfo.intWeight
        startNodeInfo = self.nodeInfo[railInfo.strStartNode]
        isBranch = startNodeInfo.isBranch
        startNodePosX = startNodeInfo.lstCoordinates[0]
        startNodePosY = startNodeInfo.lstCoordinates[1]
        endNodeInfo = self.nodeInfo[railInfo.strEndNode]
        isConfluence = endNodeInfo.isConfluence
        endNodePosX = endNodeInfo.lstCoordinates[0]
        endNodePosY = endNodeInfo.lstCoordinates[1]    
        if isConfluence == True and railType != "X":
            test = 1
        lstTempSubNode = []
        tempNodeX = startNodePosX
        tempNodeY = startNodePosY
        nodeIndex = 1
        if railType == "X":
            for i in range(1, divisionResolution):
                nodeID = str(railID) + '-' + str(nodeIndex)
                if startNodePosX == endNodePosX and startNodePosY < endNodePosY:
                    tempNodeY = tempNodeY + 1
                elif startNodePosX == endNodePosX and startNodePosY > endNodePosY:
                    tempNodeY = tempNodeY - 1
                elif startNodePosY == endNodePosY and startNodePosX < endNodePosX:
                    tempNodeX = tempNodeX + 1
                elif startNodePosY == endNodePosY and startNodePosX > endNodePosX:
                    tempNodeX = tempNodeX - 1
                self.subNodeInfo[nodeID] = Node(nodeID, [tempNodeX, tempNodeY], True)
                lstTempSubNode.append(nodeID)
                nodeIndex = nodeIndex + 1
            self.railInfo[railID].lstSubNode = lstTempSubNode
        elif railType == "L":
            for i in range(1, divisionResolution):
                nodeID = str(railID) + '-' + str(nodeIndex)
                if isBranch == False and isConfluence == False:
                    if startNodePosX < endNodePosX and startNodePosY > endNodePosY:
                        tempNodeY = tempNodeY - 1
                    elif startNodePosX > endNodePosX and startNodePosY < endNodePosY:
                        tempNodeY = tempNodeY + 1
                    elif startNodePosX < endNodePosX and startNodePosY < endNodePosY:
                        tempNodeX = tempNodeX + 1
                    elif startNodePosX > endNodePosX and startNodePosY > endNodePosY:
                        tempNodeX = tempNodeX - 1
                else:
                    if startNodePosX < endNodePosX and startNodePosY > endNodePosY:
                        tempNodeX = tempNodeX + 1
                    elif startNodePosX > endNodePosX and startNodePosY < endNodePosY:
                        tempNodeX = tempNodeX - 1
                    elif startNodePosX < endNodePosX and startNodePosY < endNodePosY:
                        tempNodeY = tempNodeY + 1
                    elif startNodePosX > endNodePosX and startNodePosY > endNodePosY:
                        tempNodeY = tempNodeY - 1
                self.subNodeInfo[nodeID] = Node(nodeID, [tempNodeX, tempNodeY], True)
                lstTempSubNode.append(nodeID)
                nodeIndex = nodeIndex + 1
            self.railInfo[railID].lstSubNode = lstTempSubNode
        elif railType == "R":
            for i in range(1, divisionResolution):
                nodeID = str(railID) + '-' + str(nodeIndex)
                if isBranch == False and isConfluence == False:
                    if startNodePosX > endNodePosX and startNodePosY > endNodePosY:
                        tempNodeY = tempNodeY - 1
                    elif startNodePosX < endNodePosX and startNodePosY < endNodePosY:
                        tempNodeY = tempNodeY + 1
                    elif startNodePosX < endNodePosX and startNodePosY > endNodePosY:
                        tempNodeX = tempNodeX + 1
                    elif startNodePosX > endNodePosX and startNodePosY < endNodePosY:
                        tempNodeX = tempNodeX - 1
                else:
                    if startNodePosX > endNodePosX and startNodePosY > endNodePosY:
                        tempNodeX = tempNodeX - 1
                    elif startNodePosX < endNodePosX and startNodePosY < endNodePosY:
                        tempNodeX = tempNodeX + 1
                    elif startNodePosX < endNodePosX and startNodePosY > endNodePosY:
                        tempNodeY = tempNodeY - 1
                    elif startNodePosX > endNodePosX and startNodePosY < endNodePosY:
                        tempNodeY = tempNodeY + 1
                self.subNodeInfo[nodeID] = Node(nodeID, [tempNodeX, tempNodeY], True)
                lstTempSubNode.append(nodeID)
                nodeIndex = nodeIndex + 1
            self.railInfo[railID].lstSubNode = lstTempSubNode
        elif railType == "LU":
            for i in range(1, divisionResolution):
                nodeID = str(railID) + '-' + str(nodeIndex)
                if startNodePosX > endNodePosX and startNodePosY == endNodePosY:
                    if i == 1:
                        tempNodeY = tempNodeY + 1
                    else:
                        tempNodeX = tempNodeX - 1
                elif startNodePosX == endNodePosX and startNodePosY > endNodePosY:
                    if i == 1:
                        tempNodeX = tempNodeX - 1
                    else:
                        tempNodeY = tempNodeY - 1
                elif startNodePosX < endNodePosX and startNodePosY == endNodePosY:
                    if i == 1:
                        tempNodeY = tempNodeY - 1
                    else:
                        tempNodeX = tempNodeX + 1
                elif startNodePosX == endNodePosX and startNodePosY < endNodePosY:
                    if i == 1:
                        tempNodeX = tempNodeX + 1
                    else:
                        tempNodeY = tempNodeY + 1
                self.subNodeInfo[nodeID] = Node(nodeID, [tempNodeX, tempNodeY], True)
                lstTempSubNode.append(nodeID)
                nodeIndex = nodeIndex + 1
            self.railInfo[railID].lstSubNode = lstTempSubNode
        elif railType == "RU":
            for i in range(1, divisionResolution):
                nodeID = str(railID) + '-' + str(nodeIndex)
                if startNodePosX < endNodePosX and startNodePosY == endNodePosY:
                    if i == 1:
                        tempNodeY = tempNodeY + 1
                    else:
                        tempNodeX = tempNodeX + 1
                elif startNodePosX == endNodePosX and startNodePosY > endNodePosY:
                    if i == 1:
                        tempNodeX = tempNodeX + 1
                    else:
                        tempNodeY = tempNodeY - 1
                elif startNodePosX > endNodePosX and startNodePosY == endNodePosY:
                    if i == 1:
                        tempNodeY = tempNodeY - 1
                    else:
                        tempNodeX = tempNodeX - 1
                elif startNodePosX == endNodePosX and startNodePosY < endNodePosY:
                    if i == 1:
                        tempNodeX = tempNodeX - 1
                    else:
                        tempNodeY = tempNodeY + 1
                self.subNodeInfo[nodeID] = Node(nodeID, [tempNodeX, tempNodeY], True)
                lstTempSubNode.append(nodeID)
                nodeIndex = nodeIndex + 1
            self.railInfo[railID].lstSubNode = lstTempSubNode
        
        if railInfo.strStartNode not in self.nextNodeInfo:
            self.nextNodeInfo[railInfo.strStartNode] = []
        self.nextNodeInfo[railInfo.strStartNode].append(railInfo.lstSubNode[0])
        for i in range(len(railInfo.lstSubNode)):
            if i == len(railInfo.lstSubNode) - 1:
                self.nextNodeInfo[railInfo.lstSubNode[i]] = [railInfo.strEndNode]
            else:            
                self.nextNodeInfo[railInfo.lstSubNode[i]] = [railInfo.lstSubNode[i+1]]

    ## function for performance information ##
    def setPerformanceInfo(self, Info):
        performanceValue = Info[0]   
        for key, value in self.equipmentInfo.items():
            value.intPerformanceValue = performanceValue[value.strPerformance]

    ## function for nodeID returns ##
    def getNodeIDByCoordinates(self, coordinates):
        for key, value in self.totalNodeInfo.items():
            if value.lstCoordinates == coordinates:
                return key
        print("Function getNodeIDByCoordinates() Error")
        return None
    
    ## function for coordinate returns ##
    def getCoordinatesByNodeID(self, nodeID):
        for key, value in self.totalNodeInfo.items():
            if value.strNodeID == nodeID:
                return value.lstCoordinates
        print("Function getCoordinatesByNodeID() Error")
        return None

    ## function for nextNodeID retrieval
    def getNextNodeIDByNodeID(self, nodeID):
        searchID = str(nodeID)
        if searchID in self.nextNodeInfo:
            return self.nextNodeInfo[searchID]
        else:
            print("next node doesn't exist!!")
  
    ## funtion for print ##
    def printTerminal(self, log):
        if self.isTerminalOn == True:
            print(log)

class Rail:
    def __init__(self, railID, startNode, endNode, edgeWeight, railType, lstSubNode):
        self.strRailID = str(railID)
        self.strStartNode = str(startNode)
        self.strEndNode = str(endNode)
        self.lstSubNode = lstSubNode #서브 노드가 들어가 있는 이유 ? 
        self.intWeight = int(edgeWeight) #가중치가 들어가 있는 이유 ? 
        self.strType = str(railType)
        self.blIsBlocked = False
        self.strBlockVehicleID = None
        self.strBlockVehicleStatus = None

class Node:
    def __init__(self, nodeID, coordinates, isSubNode):
        self.strNodeID = str(nodeID)
        self.lstCoordinates = coordinates
        self.isEquipment = False #설비 여부
        self.isReserved = False #예약 여부
        self.usageCnt = 0
        self.isSubNode = isSubNode
        self.isBranch = False
        self.isConfluence = False
        # for dijkstra
        self.dist = MAX_EDGE_VALUE
        self.post = 0

class Equipment:
    def __init__(self, equipmentID, equipmentNodeID, equipmentCoordinates, processTime, processType, performance):
        self.strEquipmentID = str(equipmentID) #ID
        self.strEquipmentNodeID = str(equipmentNodeID)  #node ID
        self.lstCoordinates = equipmentCoordinates # 좌표
        self.dblProcessTime = float(processTime) #process time
        self.strType = str(processType) # A-1 ? B-1 ? 이런건가 ?
        self.strState = "EMPTY"                      # EMPTY, RESERVED, BUSY, DONE
        self.intProcessingJobID = None 
        self.strPerformance = performance           # A, B, ..., S
        self.intPerformanceValue = None
        self.lstProcessingJobID = []
        self.totalProcessedTime = 0

    def setEquipmentState(self, state):
        self.strState = state
    
    def setProcessingJobID(self, ID):
        self.intProcessingJobID = int(ID)
        self.lstProcessingJobID.append(int(ID))

class Sequence:
    def __init__(self, seqNum, seqList):
        self.intSeqNum = int(seqNum)
        self.lstSequence = seqList

class Vehicle:
    def __init__(self, vehicleID, coordinates):
        self.strVehicleID = str(vehicleID)
        self.lstCoordinates = coordinates
        self.strState = "IDLE"                      # IDLE, RESERVED, MOVE, ARRIVAL, LIFTDOWN, LOAD, LIFTUP, FROMDONE, UNLOAD
        self.intJobID = None
        self.lstJobID = []
        self.strCommandID = None
        self.lstCommandID = []
        self.dictActivationTime = {}
        self.curNodeID = None
        self.doneWaitStartTime = None
        
    def setState(self, state):
        self.strState = state

    def setCoordinates(self, coorinates):
        self.lstCoordinates = coorinates
    
    def setJobID(self, jobID):
        self.intJobID = jobID
        self.lstJobID.append(jobID)
    
    def setCommandID(self, commandID):
        self.strCommandID = commandID 
        if commandID not in self.lstCommandID:
            self.lstCommandID.append(commandID)

    def setActivationTime(self, commandID, time):
        if commandID not in self.dictActivationTime:
            self.dictActivationTime[commandID] = time
        else:
            self.dictActivationTime[commandID] = self.dictActivationTime[commandID] + time

class Job:
    def __init__(self, jobID, seqNum, lstInitProcess):
        self.intJobID = int(jobID)
        self.intSeqNum = seqNum
        self.lstInitProcess = lstInitProcess
        self.lstFinalProcess = copy.deepcopy(lstInitProcess) #deepcopy ?
        self.dictStartTime = {}
        self.dictStartCarryObject = {}
        self.dictDoneTime = {}
        self.dictOutTime = {}
        self.dictOutCarryObject = {}
        self.dictYieldScore = {}
        self.dblYieldScore = 0
        self.lstCommandID = []
        
        self.strCurrentProcess = None
        self.strCurrentProcessEqpID = None
        self.strNextProcess = None
        self.strNextProcessEqpID = None
        
    def setTime(self, state, equipmentID, time):
        if state == "start":
            self.dictStartTime[equipmentID] = time
        elif state == "done":
            self.dictDoneTime[equipmentID] = time
        elif state == "out":
            self.dictOutTime[equipmentID] = time
        else:
            print("Wrong input 'state', must be ['start' or 'done' or 'out]")

    def setCarryObject(self, port, equipmentID, objID):
        if port == 'in':
            self.dictStartCarryObject[equipmentID] = objID
        elif port == 'out':
            self.dictOutCarryObject[equipmentID] = objID
        else:
            print("Wrong input 'port', must be ['in' or 'out']")

    def setScore(self, score, eqpID):
        self.dblYieldScore = score
        self.dictYieldScore[eqpID] = score

    def setCurrentProcess(self, processType, equipmentID):
        self.strCurrentProcess = processType
        self.strCurrentProcessEqpID = equipmentID
    
    def setNextProcess(self, processType, equipmentID):
        self.strNextProcess = processType
        self.strNextProcessEqpID = equipmentID

    def setCommandID(self, commandID):
        if commandID not in self.lstCommandID:
            self.lstCommandID.append(commandID)