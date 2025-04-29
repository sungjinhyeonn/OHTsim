from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from Message import Message

class MCS(DEVSAtomicModel):

    def __init__(self, strID, globalVar, objLogger, passScore, targetJob, jobStart, jobEnd):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar
        self.objLogger = objLogger
        # states
        self.stateList = ["WAIT", "COMMAND", "ANALYZE"]
        self.state = self.stateList[0]

        # input Ports
        self.addInputPort("informDone")
        self.addInputPort("informFree")
        self.addInputPort("informOHT")
        

        # output Ports
        self.addOutputPort("fromToCommand")
        self.addOutputPort("goCommand")
        self.addOutputPort("simulationComplete")

        # self variables
        self.addStateVariable("strID", strID)
        self.addStateVariable("dblPassScore", passScore)
        self.addStateVariable("dblTargetJob", targetJob)
        self.addStateVariable("intJobStart", jobStart)
        self.addStateVariable("intJobEnd", jobEnd)

        # variables
        self.countDone = 0
        self.lstCompleteJob = []
        self.commandID = 111111
        self.reservedGoNodeList = []
        self.reservedGoNodeDict = {}

    def funcExternalTransition(self, strPort, objEvent):
        if strPort == "informDone":
            # Equipment 한테서 정보가 들어오면
            ## objEvent = [equipmentID, jobID]
            jobInfo = self.globalVar.getTargetJobsByID(objEvent[1])
            if jobInfo.strCurrentProcess == "OUT":
                jobInfo.setCurrentProcess(None, None)
                if jobInfo.intJobID >= self.getStateValue("intJobStart") and jobInfo.intJobID <= self.getStateValue("intJobEnd"):
                    self.countDone += 1
                self.globalVar.printTerminal("[{}][{}] Job #{} Production complete".format(self.getTime(), self.getStateValue("strID"), objEvent[1]))
                if self.countDone == (self.getStateValue("intJobEnd") - self.getStateValue("intJobStart")) + 1:
                    self.state = self.stateList[2]
                else:
                    self.continueTimeAdvance()
            else:
                self.checkJobQuality(jobInfo)
                self.lstCompleteJob.append(jobInfo.intJobID)

                self.globalVar.printTerminal("[{}][{}] Job #{} Process done received".format(self.getTime(), self.getStateValue("strID"), objEvent[1]))

                if self.state == "WAIT":
                    self.state = self.stateList[1] #command 로 감
                else:
                    self.continueTimeAdvance()
            return True
        elif strPort == "informFree":
            ## objEvent = equipmentID("FXX") or MainController("MainController")
            # 차량 Free or 장비 Free
            if objEvent[0] == "F":
                equipmentInfo = self.globalVar.getEquipmentInfoByID(objEvent)
                if equipmentInfo.strType != "A-1":
                    self.state = self.stateList[1]
                    return True
            elif objEvent[0] == "V":
                if objEvent in self.reservedGoNodeDict:
                    self.reservedGoNodeList.remove(self.reservedGoNodeDict[objEvent])
                    del self.reservedGoNodeDict[objEvent]
                self.state = self.stateList[1]
                return True
            self.continueTimeAdvance()
            return True
        elif strPort == "informOHT":
            self.state = self.stateList[1]
            return True
        else:
            print("ERROR at MCS ExternalTransition: #{}".format(self.getStateValue("strID")))
            print("inputPort: {}".format(strPort))
            print("CurrentState: {}".format(self.state))
            return False

    def funcOutput(self):
        if self.state == "COMMAND":
            chosenJobID, chosenVehicleID, currentEquipID, nextEquipID =  self.checkCommandCondition()
            # Job
            if chosenJobID != None and chosenVehicleID != None and nextEquipID != None:
                fromCommand = Message.FromToCommand("F", str(self.commandID)+"-"+"F", chosenVehicleID, currentEquipID)
                self.commandID += 1
                toCommand = Message.FromToCommand("T", str(self.commandID)+"-"+"T", chosenVehicleID, nextEquipID)
                self.commandID += 1
                self.globalVar.printTerminal("[{}][{}] Job #{}::fromCommand #{}::toCommand #{} sent".format(self.getTime(), self.getStateValue("strID"), chosenJobID, fromCommand.strCommandID, toCommand.strCommandID))
                self.addOutputEvent("fromToCommand", [chosenJobID, fromCommand, toCommand])
            elif chosenVehicleID != None and currentEquipID != None and chosenJobID == None and nextEquipID == None:
                goCommand = Message.GoCommand("G", str(self.commandID)+"-"+"G", chosenVehicleID, None, None, currentEquipID)
                self.commandID += 1
                self.globalVar.printTerminal("[{}][{}] Vehicle #{}:: goCommand #{} sent".format(self.getTime(), self.getStateValue("strID"), chosenVehicleID, goCommand.strCommandID))
                self.addOutputEvent("goCommand", goCommand)
            return True
        elif self.state == "ANALYZE":
            self.globalVar.printTerminal("[{}][{}] Job #{}/#{} simulation complete".format(self.getTime(), self.getStateValue("strID"), self.countDone, (self.getStateValue("intJobEnd") - self.getStateValue("intJobStart") + 1)))
            self.addOutputEvent("simulationComplete", True)            
            return True
        else:
            print("ERROR at MCS OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcInternalTransition(self):
        if self.state == "COMMAND":
            self.state = self.stateList[0]
            return True
        elif self.state == "ANALYZE":
            self.state = self.stateList[0]
            return True
        else:
            print("ERROR at MCS InternalTransition: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state == "WAIT":
            return 999999999999
        else:
            return 0

    def checkJobQuality(self, jobInfo):
        currentIndex = jobInfo.lstFinalProcess.index(jobInfo.strCurrentProcess)
        if jobInfo.dblYieldScore < self.getStateValue("dblPassScore") and jobInfo.strCurrentProcess[-1] == '1':
            repairProcess = jobInfo.strCurrentProcess[:-1] + '2'
            jobInfo.lstFinalProcess.insert(currentIndex+1, repairProcess)
            jobInfo.setNextProcess(repairProcess, None)
        else:
            jobInfo.setNextProcess(jobInfo.lstFinalProcess[currentIndex+1], None)


    def checkCommandCondition(self):
        currentTime = self.getTime()
        vehicleInfo = self.globalVar.getVehicleInfo()
        equipmentInfo = self.globalVar.getEquipmentInfo()
        for jobID in self.lstCompleteJob:
            jobInfo = self.globalVar.getTargetJobsByID(jobID) 
            for vehicleID, vehicleValue in vehicleInfo.items():
                if vehicleValue.strState == "IDLE":
                    for equipmentID, equipmentValue in equipmentInfo.items():
                        if equipmentValue.strType == jobInfo.strNextProcess and equipmentValue.strState == "EMPTY":
                            jobInfo.setNextProcess(equipmentValue.strType, equipmentID)
                            self.lstCompleteJob.remove(jobID)
                            equipmentInfo[equipmentID].setEquipmentState("RESERVED")
                            return [jobID, vehicleID, self.zeroPadding(equipmentInfo[jobInfo.strCurrentProcessEqpID].strEquipmentNodeID), self.zeroPadding(equipmentValue.strEquipmentNodeID)]
        for vehicleID, value in vehicleInfo.items():
            if value.doneWaitStartTime != None:
                wastedTime = value.doneWaitStartTime - currentTime
                curNodeInfo = self.globalVar.getEquipmentInfoByNodeID(value.curNodeID)
                if curNodeInfo.strType == "OUT":
                    for nodeTogo in self.globalVar.nodeToGo:
                        nodeInfo = self.globalVar.getNodeInfoByID(nodeTogo)
                        if nodeInfo.isReserved != True and nodeInfo.strNodeID not in self.reservedGoNodeList:
                            self.reservedGoNodeList.append(nodeInfo.strNodeID)
                            self.reservedGoNodeDict[vehicleID] = nodeInfo.strNodeID
                            return [None, vehicleID, nodeTogo, None]
        return [None, None, None, None]
                            

    def zeroPadding(self, value):
        if int(value) < 10:
            return "00000" + str(value)
        elif int(value) < 100:
            return "0000" + str(value)
        elif int(value) < 1000:
            return "000" + str(value)
        elif int(value) < 10000:
            return "00" + str(value)
        elif int(value) < 100000:
            return "0" + str(value)
        elif int(value) < 1000000:
            return str(value)
        else:
            print("too big number")

