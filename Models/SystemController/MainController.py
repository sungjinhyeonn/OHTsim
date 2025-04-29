from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from Message import Message

class MainController(DEVSAtomicModel):

    def __init__(self, strID, globalVar, objLogger):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar
        self.objLogger = objLogger

        # states
        self.stateList = ["WAIT", "FROM_REQ", "COMMAND", "LIFT_DOWN", "LIFT_UP", "TO_REQ", "COMPLETE", "GO_REQ", "CONTINUE"]
        self.state = self.stateList[0]

        # input Ports
        self.addInputPort("fromToCommand")
        self.addInputPort("fromRes")
        self.addInputPort("arrival")
        self.addInputPort("exchangeDone")
        self.addInputPort("liftUp")
        
        self.addInputPort("toRes")
        self.addInputPort("goRes")
        self.addInputPort("ownPos")
        self.addInputPort("stopInform")
        self.addInputPort("simulationComplete")
        self.addInputPort("goCommand")

        # output Ports
        self.addOutputPort("fromReq")
        self.addOutputPort("toReq")
        self.addOutputPort("goReq")
        self.addOutputPort("moveCommand")
        self.addOutputPort("LDCommand")
        self.addOutputPort("LUCommand")
        self.addOutputPort("informFree")
        self.addOutputPort("continue")
        

        # self variables
        self.addStateVariable("strID", strID)

        # variables
        self.fromToPair = {}                                                # key = fromCommandID , value = toCommandID
        self.fromMsg = {}                                                   # key = fromCommandID , value = fromInformation
        self.toMsg = {}                                                     # key = toCommandID , value = toInformation
        self.goMsg = {}                                                     # key = goCommandID , value = goInformation
        self.commandID = []                                                 # total commandID
        self.completeMsg = {}                                               # mission complete commandID
        self.reservedCommand = []
        self.stopAndGoReserved = {}
        self.currentStopAndGo = None
        self.continueVehicle = None
        self.loadBalance = False
        
        self.currentCommandID = 0                                           # current chosen commandID
        self.fromResult = 0                                                 # current from Result
        self.toResult = 0                                                   # current to Result
        self.goResult = 0                                                   # current go Result
        self.arrivalID = 0                                                  # arrival vehicleID
        self.operationCompleteID = 0                                        # liftUp complete vehicleID


    def funcExternalTransition(self, strPort, objEvent):
        if strPort == "fromToCommand":
            ## objEvent = [jobID, fromCommand, toCommand]
            self.globalVar.printTerminal("[{}][{}] Job #{}::fromCommand #{}::toCommand #{} received".format(self.getTime(), self.getStateValue("strID"), objEvent[0], objEvent[1].strCommandID, objEvent[2].strCommandID))

            self.setFromToCommand(objEvent)

            if self.state == "WAIT":
                self.currentCommandID = objEvent[1].strCommandID
                self.state = self.stateList[1]
            else:
                self.continueTimeAdvance()
            return True
        elif strPort == "fromRes":
            ## objEvent(class) = strDstNodeID, intNumNode, lstNodes, strAcknowledge, strCommandID, strCommandType, strVehicleID
            self.currentCommandID = objEvent.strCommandID
            self.fromResult = objEvent
            self.updateCommand(objEvent)
            self.state = self.stateList[2]
            self.globalVar.printTerminal("[{}][{}] fromResult #{} received".format(self.getTime(), self.getStateValue("strID"),  objEvent.strCommandID))
            return True
        elif strPort == "toRes":
            ## objEvent(class) = strDstNodeID, intNumNode, lstNodes, strAcknowledge, strCommandID, strCommandType, strVehicleID
            self.currentCommandID = objEvent.strCommandID
            self.toResult = objEvent
            self.toMsg[objEvent.strCommandID].lstDstPath = objEvent.lstNodes
            if objEvent.strAcknowledge == "N":
                self.state = self.stateList[7]
                self.globalVar.printTerminal("[{}][{}] toResult #{} -> NACK received".format(self.getTime(), self.getStateValue("strID"),  self.currentCommandID))                
            else:
                self.state = self.stateList[2]
                self.globalVar.printTerminal("[{}][{}] toResult #{} -> ACK received".format(self.getTime(), self.getStateValue("strID"),  self.currentCommandID))
            return True
        elif strPort == "arrival":
            ## objEvent = [vehicleID, posX, posY]
            self.arrivalID = objEvent[0]
            vehicleInfo = self.globalVar.getVehicleInfoByID(objEvent[0])
            self.globalVar.printTerminal("[{}][{}] #{} arrived destination {}/{}".format(self.getTime(), self.getStateValue("strID"),  objEvent[0], objEvent[1], objEvent[2]))
            if vehicleInfo.strCommandID in self.goMsg and (vehicleInfo.strCommandID not in self.toMsg or vehicleInfo.strCommandID not in self.fromMsg):
                self.state = self.stateList[6]
                self.currentCommandID = vehicleInfo.strCommandID
                self.completeMsg[self.currentCommandID] = self.goMsg[self.currentCommandID]
                self.globalVar.printTerminal("[{}][{}] #{} command #{} complete".format(self.getTime(), self.getStateValue("strID"),  vehicleInfo.strVehicleID, self.currentCommandID))
                vehicleInfo.strCommandID = None
                vehicleInfo.strState = "IDLE"
            else:
                self.state = self.stateList[3]
            return True
        elif strPort == "exchangeDone":
            ## objEvent = vehicleID
            self.operationCompleteID = objEvent
            self.globalVar.printTerminal("[{}][{}] #{} operation complete".format(self.getTime(), self.getStateValue("strID"),  objEvent))
            self.state = self.stateList[4]
            return True
        elif strPort == "liftUp":
            ## objEvent = vehicleID
            vehicleInfo = self.globalVar.getVehicleInfoByID(objEvent)
            self.currentCommandID = vehicleInfo.strCommandID
            if self.currentCommandID in self.fromMsg:
                self.completeMsg[self.currentCommandID] = self.fromMsg[self.currentCommandID]
                self.state = self.stateList[5]
                # from 이면 Foup을 들어올린 거니까 다음 목적지를 요청해야함
            elif self.currentCommandID in self.toMsg:
                self.completeMsg[self.currentCommandID] = self.toMsg[self.currentCommandID]
                self.state = self.stateList[6]
                # to 상태에서 up은 내려 놓고 올라온거니까 아무것도 하지 않음
            self.globalVar.printTerminal("[{}][{}] #{} LiftUp & command #{} complete".format(self.getTime(), self.getStateValue("strID"),  objEvent, self.currentCommandID))
            return True
        elif strPort == "goRes":
            ## objEvent(class) = strDstNodeID, intNumNode, lstBlockVehicleID, lstBlockVehicleNode, lstNodes, strAcknowledge, strCommandID, strCommandType, strVehicleID
            if objEvent.strAcknowledge == "A":
                self.currentCommandID = objEvent.strCommandID
                if self.goMsg[objEvent.strCommandID].lstDstPath == None:
                    self.goMsg[objEvent.strCommandID].lstDstPath = objEvent.lstNodes
                    self.loadBalance = True
                self.goResult = objEvent
                self.globalVar.printTerminal("[{}][{}] goResult #{} -> ACK received".format(self.getTime(), self.getStateValue("strID"),  objEvent.strCommandID))
                self.state = self.stateList[2]
            else:
                ## test 필요
                self.state = self.stateList[7]
                self.globalVar.printTerminal("[{}][{}] goResult #{} -> NACK received".format(self.getTime(), self.getStateValue("strID"),  objEvent.strCommandID))
            return True
        elif strPort == "stopInform":
            # 
            self.stopAndGoReserved[objEvent[0]] = [objEvent[1], objEvent[2], objEvent[3]]
            blockVehicleInfo = self.globalVar.getVehicleInfoByID(objEvent[1])
            if blockVehicleInfo.strState == "IDLE":
                self.currentStopAndGo = [objEvent[0], objEvent[1]]
                self.state = self.stateList[7]
                return True
            self.continueTimeAdvance()
            return True
        elif strPort == "ownPos":
            for key, value in self.stopAndGoReserved.items():
                if value[0] == objEvent[0] and (value[1] != objEvent[1] or value[2] != objEvent[2]):
                    self.continueVehicle = key
                    self.state = self.stateList[8]
                    del self.stopAndGoReserved[key]
                    return True
            self.continueTimeAdvance()
            return True
        elif strPort == "simulationComplete":
            self.state = self.stateList[0]
            return True
        elif strPort == "goCommand":
            ## objEvent = goCommand
            self.globalVar.printTerminal("[{}][{}] Vehicle #{}:: goCommand #{} received".format(self.getTime(), self.getStateValue("strID"), objEvent.strVehicleID, objEvent.strCommandID))
            self.goMsg[objEvent.strCommandID] = objEvent
            self.commandID.append(objEvent.strCommandID)
            self.loadBalance = True
            if self.state == "WAIT":
                self.currentCommandID = objEvent.strCommandID
                self.state = self.stateList[7]
            else:
                self.continueTimeAdvance()
            return True
        else:
            print("ERROR at MainController ExternalTransition: #{}".format(self.getStateValue("strID")))
            print("inputPort: {}".format(strPort))
            print("CurrentState: {}".format(self.state))
            return False

    def funcOutput(self):
        if self.state == "FROM_REQ":
            self.addOutputEvent("fromReq", self.fromMsg[self.currentCommandID])
            self.globalVar.printTerminal("[{}][{}] fromCommand #{} schedule request sent".format(self.getTime(), self.getStateValue("strID"), self.currentCommandID))
            return True
        elif self.state == "COMMAND":
            self.currentCommandID = 0
            if self.fromResult != 0:
                self.addOutputEvent("moveCommand", self.fromResult)
                self.globalVar.printTerminal("[{}][{}] fromCommand #{}::#{} sent".format(self.getTime(), self.getStateValue("strID"), self.fromResult.strCommandID, self.fromResult.strVehicleID))
            elif self.toResult != 0:
                self.addOutputEvent("moveCommand", self.toResult)
                self.globalVar.printTerminal("[{}][{}] toCommand #{}::#{} sent".format(self.getTime(), self.getStateValue("strID"), self.toResult.strCommandID, self.toResult.strVehicleID))
            elif self.loadBalance == True:
                self.addOutputEvent("moveCommand", self.goResult)
                self.globalVar.printTerminal("[{}][{}] goCommand #{}::#{} sent".format(self.getTime(), self.getStateValue("strID"), self.goResult.strCommandID, self.goResult.strVehicleID))
            elif self.goResult != 0 or self.goResult == 0 and len(self.reservedCommand) != 0:
                if self.goResult != 0:
                    cmdIDCounts = 0
                    if len(self.goResult.strCommandID) > 8:               
                        cmdIDCounts = int(self.goResult.strCommandID[7:-2])
                        for key, value in self.goMsg.items():
                            if len(key) > 8 and key[:6] == self.goResult.strCommandID[:6]:
                                if cmdIDCounts < int(key[7:-2]):
                                    cmdIDCounts = int(key[7:-2])
                        for i in range(len(self.goResult.lstBlockVehicleID)):
                            cmdIDCounts = cmdIDCounts + 1
                            goCommandID = self.goResult.strCommandID[:7] + str(cmdIDCounts) + "-G"
                            self.goMsg[goCommandID] = Message.GoCommand("G", goCommandID, self.goResult.lstBlockVehicleID[i], self.goResult.lstBlockVehicleNode[i], [])
                            self.reservedCommand.append(Message.scheduleResult(self.goResult.lstBlockVehicleNode[i], "G", goCommandID, self.goResult.lstBlockVehicleID[i], [], []))
                    else:
                        for i in range(len(self.goResult.lstBlockVehicleID)):
                            cmdIDCounts = cmdIDCounts + 1
                            goCommandID = self.goResult.strCommandID[:-1] + str(cmdIDCounts) + "-G"
                            self.goMsg[goCommandID] = Message.GoCommand("G", goCommandID, self.goResult.lstBlockVehicleID[i], self.goResult.lstBlockVehicleNode[i], [])
                            self.reservedCommand.append(Message.scheduleResult(self.goResult.lstBlockVehicleNode[i], "G", goCommandID, self.goResult.lstBlockVehicleID[i], [], []))
                goResult = self.reservedCommand.pop(0)
                self.addOutputEvent("moveCommand", goResult)
                self.globalVar.printTerminal("[{}][{}] goCommand #{}::#{} sent".format(self.getTime(), self.getStateValue("strID"), goResult.strCommandID, goResult.strVehicleID))
            else:
                print ("ERROR Main Controller funcOutput 'COMMAND'")
            return True
        elif self.state == "LIFT_DOWN":
            self.addOutputEvent("LDCommand", self.arrivalID)
            return True
        elif self.state == "LIFT_UP":
            self.addOutputEvent("LUCommand", self.operationCompleteID)
            return True  
        elif self.state == "TO_REQ":
            toMsgID = self.checkToMsg(self.currentCommandID)
            self.addOutputEvent("toReq", self.toMsg[toMsgID])
            self.globalVar.printTerminal("[{}][{}] toCommand #{} schedule request sent".format(self.getTime(), self.getStateValue("strID"), toMsgID))
            return True
        elif self.state == "GO_REQ":
            goCmdID = None
            if self.toResult == 0 and self.currentStopAndGo != None:
                stoppedVehicleInfo = self.globalVar.getVehicleInfoByID(self.currentStopAndGo[0])
                if stoppedVehicleInfo.strCommandID in self.toMsg:
                    prevCmdInfo = self.toMsg[stoppedVehicleInfo.strCommandID]
                elif stoppedVehicleInfo.strCommandID in self.fromMsg:
                    prevCmdInfo = self.fromMsg[stoppedVehicleInfo.strCommandID]
                else:
                    prevCmdInfo = self.goMsg[stoppedVehicleInfo.strCommandID]
                goCmdID = stoppedVehicleInfo.strCommandID[:-1]+"G"
                if goCmdID in self.goMsg:
                    self.goMsg[goCmdID].lstBlockVehicleID = [self.currentStopAndGo[1]]
                else:
                    self.goMsg[goCmdID] = Message.GoCommand("G", goCmdID, stoppedVehicleInfo.strVehicleID, prevCmdInfo.lstDstPath, [[self.currentStopAndGo[1]]])
                    self.commandID.append(goCmdID)
            elif self.loadBalance == True:
                goCmdID = self.currentCommandID
            else:
                goCmdID = self.toResult.strCommandID[:-1] + "G"
                self.goMsg[goCmdID] = Message.GoCommand("G", goCmdID, self.toResult.strVehicleID, self.toResult.lstNodes, self.toResult.lstBlockVehicleID)
                self.commandID.append(goCmdID)
            self.addOutputEvent("goReq", self.goMsg[goCmdID])
            return True
        elif self.state == "COMPLETE":
            if self.currentCommandID in self.toMsg:
                self.globalVar.printTerminal("[{}][{}] #{} free msg sent".format(self.getTime(), self.getStateValue("strID"), self.toMsg[self.currentCommandID].strVehicleID))
                self.addOutputEvent("informFree", self.toMsg[self.currentCommandID].strVehicleID)
            else:
                self.globalVar.printTerminal("[{}][{}] #{} free msg sent".format(self.getTime(), self.getStateValue("strID"), self.goMsg[self.currentCommandID].strVehicleID))
                self.addOutputEvent("informFree", self.goMsg[self.currentCommandID].strVehicleID)
            return True            
        elif self.state == "CONTINUE":
            self.globalVar.printTerminal("[{}][{}] {} continue msg sent".format(self.getTime(), self.getStateValue("strID"), self.continueVehicle))
            self.addOutputEvent("continue", self.continueVehicle)
            return True
        else:
            print("ERROR at MainController OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcInternalTransition(self):
        if self.state == "FROM_REQ" or self.state == "TO_REQ" or self.state == "GO_REQ" or self.state == "LIFT_DOWN" or self.state == "LIFT_UP":
            if self.currentStopAndGo != None:
                self.currentStopAndGo = None
            if self.loadBalance == True:
                self.loadBalance = False
            self.state = self.stateList[0]
            return True
        elif self.state == "CONTINUE":
            self.continueVehicle = None
            self.state = self.stateList[0]
            return True
        elif self.state == "COMMAND":
            if self.fromResult != 0:
                self.fromResult = 0
                self.state = self.stateList[0]
            elif self.toResult != 0:
                self.toResult = 0    
                if self.goResult == 0:
                    self.state = self.stateList[0]
                else:
                    self.state = self.stateList[2]
            elif self.loadBalance == True:
                self.loadBalance = False
                self.goResult = 0
                self.state = self.stateList[0]
            elif self.goResult != 0 or (self.goResult == 0 and len(self.reservedCommand) != 0):
                self.goResult = 0
                if len(self.reservedCommand) == 0:
                    self.state = self.stateList[0]
                else:
                    self.state = self.stateList[2]
            else:
                self.state = self.stateList[0]
            return True
        elif self.state == "COMPLETE":
            self.state = self.stateList[0]
            self.currentCommandID = 0
            return True
        else:
            print("ERROR at MainController InternalTransition: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state == "WAIT":
            return 999999999999
        else:
            return 0

    def setFromToCommand(self, objEvent):
        fromCmdID = objEvent[1].strCommandID
        toCmdID = objEvent[2].strCommandID
        self.fromToPair[fromCmdID] = toCmdID
        self.commandID.append(fromCmdID)
        self.commandID.append(toCmdID)
        self.fromMsg[fromCmdID] = objEvent[1]
        self.toMsg[toCmdID] = objEvent[2]

    def checkToMsg(self, cmdID):
        if cmdID in self.fromToPair:
            return self.fromToPair[cmdID]
        else:
            self.globalVar.printTerminal("fromToPair Error in Main Controller")
            return None

    def updateCommand(self, Info):
        fromMsg = self.fromMsg[Info.strCommandID]
        fromMsg.strVehicleID = Info.strVehicleID
        fromMsg.lstDstPath = Info.lstNodes
        toMsgID = self.checkToMsg(Info.strCommandID)
        toMsg = self.toMsg[toMsgID]
        toMsg.strVehicleID = Info.strVehicleID