from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from Models.SystemController.Scheduler import FromScheduler, ToScheduler, GoScheduler
from Message import Message
import copy

class SAManager(DEVSAtomicModel):

    def __init__(self, strID, globalVar, objLogger):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar
        self.objLogger = objLogger

        # states
        self.stateList = ["WAIT", "SCHEDULE"]
        self.state = self.stateList[0]

        # input Ports
        self.addInputPort("fromReq")
        self.addInputPort("toReq")
        self.addInputPort("goReq")
        self.addInputPort("simulationComplete")

        # output Ports
        self.addOutputPort("fromRes")
        self.addOutputPort("toRes")
        self.addOutputPort("goRes")

        # self variables
        self.addStateVariable("strID", strID)

        # variables
        self.fromScheduler = []
        self.toScheduler = []
        self.goScheduler = []
        self.schedulers = []
        self.goPath = {}

    def funcExternalTransition(self, strPort, objEvent):
        if strPort == "fromReq":
            ## objEvent(class) = strCommandID, strCommandType, strDestinationNodeID, strVehicleID
            self.globalVar.printTerminal("[{}][{}] fromCommand #{} received".format(self.getTime(), self.getStateValue("strID"), objEvent.strCommandID))
            fromScheduler = FromScheduler(objEvent.strCommandID, objEvent.strDestinationNodeID, self.globalVar)
            self.schedulers.append(fromScheduler)
            self.fromScheduler.append(fromScheduler)

            if self.state == "WAIT":
                self.state = self.stateList[1]
            else:
                self.continueTimeAdvance()
            return True
        elif strPort == "toReq":
            ## objEvent(class) = strCommandID, strCommandType, strDestinationNodeID, strVehicleID
            self.globalVar.printTerminal("[{}][{}] toCommand #{} received".format(self.getTime(), self.getStateValue("strID"), objEvent.strCommandID))
            toScheduler = ToScheduler(objEvent.strCommandID, objEvent.strDestinationNodeID, self.globalVar, objEvent.strVehicleID)
            self.schedulers.append(toScheduler)
            self.toScheduler.append(toScheduler)

            if self.state == "WAIT":
                self.state = self.stateList[1]
            else:
                self.continueTimeAdvance()
            return True
        elif strPort == "goReq":
            ## objEvent(class) = strCommandID, strCommandType, strRootVehicleID, lstDstPath, lstBlockVehicleID, strDestinationNodeID
            self.globalVar.printTerminal("[{}][{}] goCommand #{} received".format(self.getTime(), self.getStateValue("strID"), objEvent.strCommandID))
            if objEvent.lstDstPath != None:
                goScheduler = GoScheduler(objEvent.strCommandID, self.globalVar, objEvent.strVehicleID, objEvent.lstDstPath, objEvent.lstBlockVehicleID)
            else:
                goScheduler = GoScheduler(objEvent.strCommandID, self.globalVar, objEvent.strVehicleID, objEvent.lstDstPath, objEvent.lstBlockVehicleID, objEvent.strDestinationNodeID)
            self.schedulers.append(goScheduler)
            self.goScheduler.append(goScheduler)

            if self.state == "WAIT":
                self.state = self.stateList[1]
            else:
                self.continueTimeAdvance()
            return True
        elif strPort == "simulationComplete":
            self.state = self.stateList[0]
            return True        
        else:
            print("ERROR at SAManager ExternalTransition: #{}".format(self.getStateValue("strID")))
            print("inputPort: {}".format(strPort))
            print("CurrentState: {}".format(self.state))
            return False

    def funcOutput(self):
        if self.state == "SCHEDULE":
            chosenScheduler = self.schedulers[0]
            if chosenScheduler.schedulerType == "F":
                vehicleInfo = chosenScheduler.allocateOHT()
                nodeList, blockVehicleID = chosenScheduler.scheduleOHT(vehicleInfo, "F")
                vehicleInfo.setState("Reserved")
                scheduleResult = Message.scheduleResult(nodeList, chosenScheduler.schedulerType, chosenScheduler.strID, vehicleInfo.strVehicleID, blockVehicleID, [])
                self.addOutputEvent("fromRes", scheduleResult)
                self.fromScheduler.remove(chosenScheduler)
                self.schedulers.pop(0)
                self.globalVar.printTerminal("[{}][{}] fromRes #{} sent".format(self.getTime(), self.getStateValue("strID"),  scheduleResult.strCommandID))
            elif chosenScheduler.schedulerType == "T":
                vehicleInfo = self.globalVar.getVehicleInfoByID(chosenScheduler.vehicleID)
                nodeList, blockVehicleID = chosenScheduler.scheduleOHT(vehicleInfo, "T")
                vehicleInfo.setState("Reserved")
                scheduleResult = Message.scheduleResult(nodeList, chosenScheduler.schedulerType, chosenScheduler.strID, vehicleInfo.strVehicleID, blockVehicleID, [])
                self.addOutputEvent("toRes", scheduleResult)
                self.toScheduler.remove(chosenScheduler)
                self.schedulers.pop(0)
                self.globalVar.printTerminal("[{}][{}] toRes #{} sent".format(self.getTime(), self.getStateValue("strID"),  scheduleResult.strCommandID))
            else:
                if chosenScheduler.rootPath != None:
                    self.goScheduling(chosenScheduler.rootPath, chosenScheduler.rootVehicleID, chosenScheduler.lstBlockVehicleID)
                    newBlockVehicleID = []
                    newBlockVehiclePath = []
                    for key, value in self.goPath.items():
                        newBlockVehicleID.append(key)
                        newBlockVehiclePath.append(value)
                    scheduleResult = Message.scheduleResult([], chosenScheduler.schedulerType, chosenScheduler.strID, chosenScheduler.rootVehicleID, newBlockVehicleID, newBlockVehiclePath)
                else:
                    vehicleInfo = self.globalVar.getVehicleInfoByID(chosenScheduler.rootVehicleID)
                    nodeList, blockVehicleID = chosenScheduler.scheduleOHT(vehicleInfo, "G")
                    vehicleInfo.setState("Reserved")
                    scheduleResult = Message.scheduleResult(nodeList, chosenScheduler.schedulerType, chosenScheduler.strID, vehicleInfo.strVehicleID, blockVehicleID, [])
                self.goScheduler.remove(chosenScheduler)
                self.schedulers.pop(0)
                self.addOutputEvent("goRes", scheduleResult)
                self.globalVar.printTerminal("[{}][{}] goRes #{} sent".format(self.getTime(), self.getStateValue("strID"),  scheduleResult.strCommandID))
            return True
        else:
            print("ERROR at SAManager OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcInternalTransition(self):
        if self.state == "SCHEDULE":
            if len(self.schedulers) == 0:
                self.state = self.stateList[0]
                self.goPath.clear()
            else:
                self.state = self.stateList[1]
            return True
        else:
            print("ERROR at SAManager InternalTransition: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state == "WAIT":
            return 999999999999
        else:
            return 0

    def goScheduling(self, rootPath, rootVehicleID, blockVehicleInfo):
        allVehicleInfo = self.globalVar.getVehicleInfo()
        listException = [rootVehicleID] + blockVehicleInfo
        dictReservedNode = {}
        listReservedNode = []
        lstBlockVehicles = []

        ## make list of vehicles that should be considered while scheduling
        for key, value in allVehicleInfo.items():
            if key not in listException and value.strState == "IDLE":
                nodeID = self.globalVar.getNodeIDByCoordinates(value.lstCoordinates)
                dictReservedNode[nodeID] = key
                listReservedNode.append(nodeID)

        ## 1st step: remove to block Vehicles
        for goVehicleInfo in blockVehicleInfo:
            vehicleID = goVehicleInfo
            vehicleInfo = self.globalVar.getVehicleInfoByID(vehicleID)
            vehicleCurCoordinates = vehicleInfo.lstCoordinates
            vehicleCurNodeID = self.globalVar.getNodeIDByCoordinates(vehicleCurCoordinates)
            self.goPath[vehicleID] = []
            
            lstNextNode = self.checkBranch(vehicleCurNodeID)
            
            while len(lstNextNode) != 0:
                nextNodeID = lstNextNode.pop(0)
                ## if nextNode is not in the rootPath
                if nextNodeID not in rootPath:
                    if nextNodeID not in listReservedNode:
                        self.goPath[vehicleID].append(nextNodeID)
                        dictReservedNode[nextNodeID] = vehicleID
                        listReservedNode.append(nextNodeID)
                        break
                    else:
                        self.goPath[vehicleID].append(nextNodeID)
                        blockVehicleID = dictReservedNode[nextNodeID]
                        if blockVehicleID not in listException:
                            dictReservedNode[nextNodeID] = vehicleID
                            if blockVehicleID not in lstBlockVehicles:
                                lstBlockVehicles.append(blockVehicleID)
                            break
                        else:
                            lstNextNode = self.checkBranch(nextNodeID)
                ## if nextNode is in the rootPath
                else:
                    if len(lstNextNode) == 0:
                        self.goPath[vehicleID].append(nextNodeID)
                        lstNextNode = self.checkBranch(nextNodeID)
            
        ## 2nd: remove go block vehicles
        while len(lstBlockVehicles) != 0:
            vehicleID = lstBlockVehicles.pop(0)
            vehicleInfo = self.globalVar.getVehicleInfoByID(vehicleID)
            vehicleCurCoordinates = vehicleInfo.lstCoordinates
            vehicleCurNodeID = self.globalVar.getNodeIDByCoordinates(vehicleCurCoordinates)
            self.goPath[vehicleID] = []
            lstNextNode = self.checkBranch(vehicleCurNodeID)
            
            while len(lstNextNode) != 0:
                nextNodeID = lstNextNode.pop(0)
                if nextNodeID not in listReservedNode:
                    self.goPath[vehicleID].append(nextNodeID)
                    dictReservedNode[nextNodeID] = vehicleID
                    listReservedNode.append(nextNodeID)
                    break
                else:
                    self.goPath[vehicleID].append(nextNodeID)
                    blockVehicleID = dictReservedNode[nextNodeID]
                    if blockVehicleID not in self.goPath:
                        dictReservedNode[nextNodeID] = vehicleID
                        lstBlockVehicles.append(blockVehicleID)
                        break
                    lstNextNode = self.checkBranch(nextNodeID)

        ## 3rd: check rootPath again and remove go block vehicles
        lstBlockVehicles_bak = []
        for key, value in self.goPath.items():
            reservedNode = value[-1]
            if reservedNode in rootPath:
                lstBlockVehicles.append(key)
                lstBlockVehicles_bak.append(key)
        dictReservedNode_bak = copy.deepcopy(dictReservedNode)
        while len(lstBlockVehicles) != 0:
            vehicleID = lstBlockVehicles.pop(0)
            for key, value in dictReservedNode_bak.items():
                if value == vehicleID:
                    vehicleReservedNodeID = key
                    break
            
            lstNextNode = self.checkBranch(vehicleReservedNodeID)
            
            while len(lstNextNode) != 0:
                nextNodeID = lstNextNode.pop(0)
                if nextNodeID in rootPath:
                    self.goPath[vehicleID].append(nextNodeID)
                    lstNextNode = self.checkBranch(nextNodeID) 
                else:
                    if vehicleID not in self.goPath:
                        self.goPath[vehicleID] = [nextNodeID]
                    else:
                        self.goPath[vehicleID].append(nextNodeID)
                    if nextNodeID in listReservedNode:
                        blockVehicleID = dictReservedNode[nextNodeID]
                        if blockVehicleID not in lstBlockVehicles_bak:
                            lstBlockVehicles_bak.append(blockVehicleID)
                            lstBlockVehicles.append(blockVehicleID)
                            for key, value in dictReservedNode.items():
                                if value == vehicleID:
                                    del dictReservedNode[key]
                                    break
                            dictReservedNode[nextNodeID] = vehicleID
                            break
                        else:
                            lstNextNode = self.checkBranch(nextNodeID)
                    else:
                        dictReservedNode[nextNodeID] = vehicleID
                        listReservedNode.append(nextNodeID)
                        break

        for key, value in self.goPath.items():
            vehicleInfo = self.globalVar.getVehicleInfoByID(key)
            vehicleInfo.setState("GoReserved")

    def checkBranch(self, nodeID):
        railInfo = self.globalVar.getRailInfo()
        lstNextNode = []
        for key, value in railInfo.items():
            if value.strStartNode == nodeID:
                lstNextNode.append(value.strEndNode)
        return lstNextNode