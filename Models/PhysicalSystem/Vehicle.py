from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
import copy

class Vehicle(DEVSAtomicModel):

    def __init__(self, strID, globalVar, objLogger, coordinates, operateTime, moveTime):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar
        self.objLogger = objLogger

        # states
        self.stateList = ["WAIT", "MOVE", "ARRIVAL", "LIFT_DOWN", "EXCHANGE", "LIFT_UP", "STOP_INFORM", "STOP"]
        self.state = self.stateList[0]

        # input Ports
        self.addInputPort("moveCommand")
        self.addInputPort("LDCommand")
        self.addInputPort("jobExchange")
        self.addInputPort("LUCommand")
        self.addInputPort("continue")
        self.addInputPort("simulationComplete")
        
        # output Ports
        self.addOutputPort("ownPos")
        self.addOutputPort("arrival")
        self.addOutputPort("liftDown")
        self.addOutputPort("exchangeDone")
        self.addOutputPort("liftUp")
        self.addOutputPort("stopInform")

        # self variables
        self.addStateVariable("strID", strID)
        self.addStateVariable("dblOperateTime", operateTime)
        self.addStateVariable("dblMoveTime", moveTime)
                
        # variables
        self.initPosX = float(coordinates[0])
        self.initPosY = float(coordinates[1])
        self.curPosX = float(coordinates[0])
        self.curPosY = float(coordinates[1])
        self.curNodeID = self.globalVar.getNodeIDByCoordinates(coordinates)
        self.mission_bak = 0
        self.mission = 0
        self.isBlocked = False

    def funcExternalTransition(self, strPort, objEvent):
        if strPort == "moveCommand":
            if self.getStateValue("strID") == objEvent.strVehicleID:
                if self.curPosX == self.initPosX and self.curPosY == self.initPosY:
                    self.logVehicle(0, self.curPosX, self.curPosY, "INIT")

                if objEvent.strCommandType == "F":
                    self.globalVar.printTerminal("[{}][{}] fromCommand #{} received".format(self.getTime(), self.getStateValue("strID"), objEvent.strCommandID))
                elif objEvent.strCommandType == "T":
                    self.globalVar.printTerminal("[{}][{}] toCommand #{} received".format(self.getTime(), self.getStateValue("strID"), objEvent.strCommandID))
                else:
                    self.globalVar.printTerminal("[{}][{}] goCommand #{} received".format(self.getTime(), self.getStateValue("strID"), objEvent.strCommandID))
                    
                vehicleInfo = self.globalVar.getVehicleInfoByID(objEvent.strVehicleID)
                vehicleInfo.doneWaitStartTime = None
                vehicleInfo.setState("MOVE")
                vehicleInfo.setCommandID(objEvent.strCommandID)
                self.mission_bak = copy.deepcopy(objEvent)
                self.mission = copy.deepcopy(objEvent)

                if objEvent.strDstNodeID == self.curNodeID:
                    self.globalVar.printTerminal("[{}][{}] Already at the destination".format(self.getTime(), self.getStateValue("strID")))
                    self.state = self.stateList[2]
                else:
                    cnt = 0
                    curNodeID = self.curNodeID
                    railInfo = self.globalVar.getRailInfo()
                    lstToMove = []
                    while True:
                        for key, value in railInfo.items():
                            if value.strStartNode == curNodeID and value.strEndNode == self.mission.lstNodes[cnt]:
                                lstToMove = lstToMove + value.lstSubNode
                                lstToMove.append(self.mission.lstNodes[cnt])
                                curNodeID = self.mission.lstNodes[cnt]
                                break
                        cnt = cnt + 1
                        if self.mission.intNumNode == cnt:
                            self.mission.lstNodes = lstToMove
                            self.mission.intNumNode = len(lstToMove)
                            break
                    isReserved = self.checkNextNode()
                    if isReserved == False:
                        self.state = self.stateList[1]
                    else:
                        self.state = self.stateList[6]
            else:
                self.continueTimeAdvance()
            return True
        elif strPort == "LDCommand":
            ## objEvent = vehicleID
            if self.getStateValue("strID") == objEvent:
                self.globalVar.printTerminal("[{}][{}] LiftDown Command received".format(self.getTime(), self.getStateValue("strID")))
                self.state = self.stateList[3]
                return True
            self.continueTimeAdvance()
            return True
        elif strPort == "jobExchange":
            if self.getStateValue("strID") == objEvent[1]:
                if self.mission.strCommandType == "F":
                    self.globalVar.printTerminal("[{}][{}] job loaded from #{}".format(self.getTime(), self.getStateValue("strID"), objEvent[0]))
                    self.logVehicle(self.getTime(), self.curPosX, self.curPosY, "LOAD")
                elif self.mission.strCommandType == "T":
                    self.globalVar.printTerminal("[{}][{}] job unloaded from #{}".format(self.getTime(), self.getStateValue("strID"), objEvent[0]))
                    self.logVehicle(self.getTime(), self.curPosX, self.curPosY, "UNLOAD")
                self.state = self.stateList[4]
            else:
                self.continueTimeAdvance()
            return True
        elif strPort == "LUCommand":
            ## objEvent = vehicleID
            if self.getStateValue("strID") == objEvent:
                self.globalVar.printTerminal("[{}][{}] LiftUp Command received".format(self.getTime(), self.getStateValue("strID")))
                self.state = self.stateList[5]
                return True
            self.continueTimeAdvance()
            return True
        elif strPort == "unload":
            if self.getStateValue("strID") == objEvent[1]:
                self.globalVar.printTerminal("[{}][{}] job #{} unloaded".format(self.getTime(), self.getStateValue("strID"), objEvent[0]))
                vehicleInfo = self.globalVar.getVehicleInfoByID(self.getStateValue("strID"))
                self.logVehicle(self.getTime(), self.curPosX, self.curPosY, "UNLOAD")
                self.state = self.stateList[3]
                return True
            self.continueTimeAdvance()
            return True
        elif strPort == "continue":
            if objEvent == self.getStateValue("strID"):
                self.state = self.stateList[1]
            else:
                self.continueTimeAdvance()
            return True
        elif strPort == "simulationComplete":
            self.state = self.stateList[0]
            return True                  
        else:
            print("ERROR at Vehicle ExternalTransition: #{}".format(self.getStateValue("strID")))
            print("inputPort: {}".format(strPort))
            print("CurrentState: {}".format(self.state))
            return False

    def funcOutput(self):
        if self.state == "MOVE":
            self.globalVar.printTerminal("[{}][{}] Moved from #{} to #{}[Dst: #{}]".format(self.getTime(), self.getStateValue("strID"), self.curNodeID, self.mission.lstNodes[0], self.mission.strDstNodeID))
            self.setCurrentNode()
            vehicleInfo = self.globalVar.getVehicleInfoByID(self.getStateValue("strID"))
            self.addOutputEvent("ownPos", [self.getStateValue("strID"), self.curPosX, self.curPosY])
            if self.mission.intNumNode == 0:    
                self.globalVar.printTerminal("[{}][{}] Arrived Dst: #{} / CmdID: #{}".format(self.getTime(), self.getStateValue("strID"), self.curNodeID, self.mission.strCommandID))
                vehicleInfo = self.globalVar.getVehicleInfoByID(self.getStateValue("strID"))
                vehicleInfo.setState("ARRIVAL")
                self.logVehicle(self.getTime(), self.curPosX, self.curPosY, "ARRIVAL")
            else:
                self.logVehicle(self.getTime(), self.curPosX, self.curPosY, "MOVE")
            return True
        elif self.state == "ARRIVAL":
            self.logVehicle(self.getTime(), self.curPosX, self.curPosY, "ARRIVAL")
            self.addOutputEvent("arrival", [self.getStateValue("strID"), self.curPosX, self.curPosY])
            return True
        elif self.state == "LIFT_DOWN":
            vehicleInfo = self.globalVar.getVehicleInfoByID(self.getStateValue("strID"))
            vehicleInfo.setState("LIFT_DOWN")
            vehicleInfo.setActivationTime(vehicleInfo.strCommandID, self.getStateValue("dblOperateTime"))
            self.logVehicle(self.getTime(), self.curPosX, self.curPosY, "LIFT_DOWN")
            if self.mission.strCommandType == "F":
                self.globalVar.printTerminal("[{}][{}] LiftDown processing, job request to Equipment #{}".format(self.getTime(), self.getStateValue("strID"), self.mission.strDstNodeID))
            elif self.mission.strCommandType == "T":
                self.globalVar.printTerminal("[{}][{}] LiftDown processing, job deliver to Equipment #{}".format(self.getTime(), self.getStateValue("strID"), self.mission.strDstNodeID))
            self.addOutputEvent("liftDown", [self.getStateValue("strID"), self.mission.strDstNodeID])
            return True
        elif self.state == "EXCHANGE":
            vehicleInfo = self.globalVar.getVehicleInfoByID(self.getStateValue("strID"))
            vehicleInfo.setActivationTime(vehicleInfo.strCommandID, self.getStateValue("dblOperateTime"))            
            self.addOutputEvent("exchangeDone", self.getStateValue("strID"))
            return True
        elif self.state == "LIFT_UP":
            vehicleInfo = self.globalVar.getVehicleInfoByID(self.getStateValue("strID"))
            vehicleInfo.setState("LIFT_UP")
            vehicleInfo.setActivationTime(vehicleInfo.strCommandID, self.getStateValue("dblOperateTime"))
            self.logVehicle(self.getTime(), self.curPosX, self.curPosY, "LIFT_UP")
            self.globalVar.printTerminal("[{}][{}] LiftUp processing".format(self.getTime(), self.getStateValue("strID")))
            self.addOutputEvent("liftUp", self.getStateValue("strID"))
            return True
        elif self.state == "STOP_INFORM":
            self.logVehicle(self.getTime(), self.curPosX, self.curPosY, "STOP")
            vehicleInfo = self.globalVar.getVehicleInfo()
            for key, value in vehicleInfo.items():
                nodeID = self.globalVar.getNodeIDByCoordinates(value.lstCoordinates)
                if nodeID == self.mission.lstNodes[0]:
                    self.globalVar.printTerminal("[{}][{}] Stopped, next node #{} is vacant by {}".format(self.getTime(), self.getStateValue("strID"), nodeID, key))
                    self.addOutputEvent("stopInform", [self.getStateValue("strID"), key, value.lstCoordinates[0], value.lstCoordinates[1]])
                    self.isBlocked = True
                    return True
            self.isBlocked = False
            self.globalVar.printTerminal("[{}][{}] Stopped, none Blocked, will continue".format(self.getTime(), self.getStateValue("strID")))
            return True
        else:
            print("ERROR at Vehicle OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcInternalTransition(self):
        if self.state == "MOVE":
            if self.mission.intNumNode == 0:
                self.state = self.stateList[2]
            else:
                isReserved = self.checkNextNode()
                if isReserved == False:
                    self.state = self.stateList[1]
                else:                     
                    self.state = self.stateList[6]
            return True
        elif self.state == "LIFT_DOWN":
            self.state = self.stateList[0]
            return True
        elif self.state == "EXCHANGE":
            self.state = self.stateList[0]
            return True
        elif self.state == "LIFT_UP":
            vehicleInfo = self.globalVar.getVehicleInfoByID(self.getStateValue("strID"))
            if self.mission.strCommandType == "F":
                vehicleInfo.setState("FROM_COMPLETE")
                self.state = self.stateList[0]
            elif self.mission.strCommandType == "T":
                vehicleInfo.strCommandID = None
                vehicleInfo.setState("IDLE")
                vehicleInfo.doneWaitStartTime = self.getTime()
                self.state = self.stateList[0]
            return True
        elif self.state == "ARRIVAL":
            self.state = self.stateList[0]
            return True
        elif self.state == "STOP_INFORM":
            if self.isBlocked == False:
                self.state = self.stateList[1]
            else:
                self.state = self.stateList[7]
            return True
        else:
            print("ERROR at Vehicle InternalTransition: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state == "WAIT" or self.state == "STOP":
            return 999999999999
        elif self.state == "MOVE":
            return self.getStateValue("dblMoveTime")
        elif self.state == "LIFT_DOWN" or self.state == "LIFT_UP":
            return self.getStateValue("dblOperateTime")
        else:
            return 0

    def checkNextNode(self):
        nextNodeID = self.mission.lstNodes[0]
        nextNodeInfo = self.globalVar.getTotalNodeInfoByID(nextNodeID)
        return nextNodeInfo.isReserved

    def setCurrentNode(self):
        prevNodeID = self.curNodeID
        self.curNodeID = self.mission.lstNodes[0]
        prevNodeInfo = self.globalVar.getTotalNodeInfoByID(prevNodeID)
        prevNodeInfo.isReserved = False
        nextNodeInfo = self.globalVar.getTotalNodeInfoByID(self.curNodeID)
        nextNodeInfo.isReserved = True
        nextNodeInfo.usageCnt = nextNodeInfo.usageCnt + 1
        vehicleInfo = self.globalVar.getVehicleInfoByID(self.getStateValue("strID"))
        coordinates = self.globalVar.getCoordinatesByNodeID(self.curNodeID)
        vehicleInfo.setCoordinates(coordinates)
        vehicleInfo.curNodeID = self.curNodeID
        vehicleInfo.setActivationTime(vehicleInfo.strCommandID, self.getStateValue("dblMoveTime"))
        self.curPosX = coordinates[0]
        self.curPosY = coordinates[1]
        self.mission.lstNodes.pop(0)
        self.mission.intNumNode = len(self.mission.lstNodes)        


    def logVehicle(self, time, posX, posY, state):       
        dicLog = {} 
        dicLog["posX"] = posX
        dicLog["posY"] = posY
        dicLog["status"] = state
        self.objLogger.addLogDictionarySimulation("logVehicle", time, self.getStateValue("strID"), dicLog)