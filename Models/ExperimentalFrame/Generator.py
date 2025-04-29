from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from SharedData import GlobalVar
class Generator(DEVSAtomicModel):

    def __init__(self, strID, globalVar, objLogger, jobStart, jobEnd):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar
        self.objLogger = objLogger

        # states
        self.stateList = ["GEN", "WAIT"]
        self.state = self.stateList[0]

        # input Ports
        self.addInputPort("informFree") #Equipment 비어있음
        self.addInputPort("simulationComplete")

        # output Ports
        self.addOutputPort("job") # 

        # self variables
        self.addStateVariable("strID", strID)
        self.addStateVariable("intJobStart", jobStart)
        self.addStateVariable("intJobEnd", jobEnd)

        # variables
        self.jobID = 0
        self.jobRemains = len(self.globalVar.getTargetJobs())
        self.availableEquipments = []

    def funcExternalTransition(self, strPort, objEvent):
        # 설비가 비어있는지 확인하고 넣어줘야함
        # 처음 설비인 A-1 에만 넣어주기
        if strPort == "informFree":
            ## objEvent = equipmentID("FXX") or MainController("MainController")
            ## For Generator model, only equipmentID is received
            equipmentInfo = self.globalVar.getEquipmentInfoByID(objEvent)
            if equipmentInfo.strType == "A-1":
                self.state = self.stateList[0]
                return True
            self.continueTimeAdvance()
            return True
        elif strPort == "simulationComplete":
            self.state = self.stateList[1]
            return True
        else:
            print("ERROR at Generator ExternalTransition: #{}".format(self.getStateValue("strID")))
            print("inputPort: {}".format(strPort))
            print("CurrentState: {}".format(self.state))
            return False

    def funcOutput(self):
        if self.state == "GEN":
            if self.jobRemains != 0:
                ## checks jobRemains and A-1 Equipment vacancy
                self.checkEquipmentState()
                for equipmentID in self.availableEquipments:
                    self.jobID += 1
                    self.jobRemains -= 1
                    self.addOutputEvent("job", [equipmentID, self.jobID])
                    self.availableEquipments.pop(0)
                    self.globalVar.printTerminal("[{}][{}] Job #{} generated".format(self.getTime(), self.getStateValue("strID"), self.jobID))
                    break
            return True
        else:
            print("ERROR at Generator OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcInternalTransition(self):
        if self.state == "GEN":
            # 초기에 job 수를 정하고 시작
            # 이용가능한 설비가 있거나 job이 남아있으면
            if self.jobRemains != 0 and len(self.availableEquipments) != 0:
                self.state = self.stateList[0]
            else:
                self.state = self.stateList[1]
            return True
        else:
            print("ERROR at Generator InternalTransition: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state == "GEN":
            return 0
        else:
            return 999999999999

    def checkEquipmentState(self):
        equipmentInfo = self.globalVar.getEquipmentInfo()
        
        for key, value in equipmentInfo.items():
            if key not in self.availableEquipments and value.strType == "A-1" and value.strState == "EMPTY":
                self.availableEquipments.append(key)