from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
import numpy as np

class Equipment(DEVSAtomicModel):

    def __init__(self, strID, globalVar, objLogger, equipmentNodeID, processTime, processType, exchgeTime, yieldRange, jobStart, jobEnd):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar
        self.objLogger = objLogger

        # states
        self.stateList = ["EMPTY", "BUSY", "DONE", "UNLOAD", "INFORM", "LOAD"]
        self.state = self.stateList[0]

        # input Ports
        self.addInputPort("job")
        self.addInputPort("liftDown")
        self.addInputPort("simulationComplete")

        # output Ports
        self.addOutputPort("informDone")
        self.addOutputPort("jobExchange")
        self.addOutputPort("informFree")

        # self variables
        self.addStateVariable("strID", strID)
        self.addStateVariable("strNodeID", str(equipmentNodeID))
        eqpInfo = self.globalVar.getEquipmentInfoByNodeID(equipmentNodeID)
        self.addStateVariable("dblPosX", float(eqpInfo.lstCoordinates[0]))
        self.addStateVariable("dblPosY", float(eqpInfo.lstCoordinates[1]))
        self.addStateVariable("dblProcessTime", float(processTime))
        self.addStateVariable("strProcessType", processType)
        self.addStateVariable("dblExchgeTime", exchgeTime)
        self.addStateVariable("intYieldRange", yieldRange)
        self.addStateVariable("intJobStart", jobStart)
        self.addStateVariable("intJobEnd", jobEnd)
        
        # variables
        self.currentJob = 0
        self.arrivalVehicle = 0

    def funcExternalTransition(self, strPort, objEvent):
        if strPort == "job":
            ## objEvent: [strEquipmentID, intJobID]
            if self.getStateValue("strID") == objEvent[0]:
                self.globalVar.printTerminal("[{}][Equipment(#{})] Job #{} received".format(self.getTime(), self.getStateValue("strID"), objEvent[1]))

                jobInfo = self.globalVar.getTargetJobsByID(objEvent[1])
                equipmentInfo = self.globalVar.getEquipmentInfoByID(objEvent[0])
                
                ## Set Info ##
                jobInfo.setTime('start', objEvent[0], self.getTime())
                jobInfo.setCarryObject('in', objEvent[0], 'Worker')
                jobInfo.setCurrentProcess(equipmentInfo.strType, equipmentInfo.strEquipmentID)

                equipmentInfo.setProcessingJobID(objEvent[1])
                equipmentInfo.setEquipmentState("BUSY")
                self.currentJob = objEvent[1]

                self.state = self.stateList[1]
            else:
                self.continueTimeAdvance()
                # 이 경우는 뭐지..?
            return True
        elif strPort == "liftDown":
            ## objEvent = [vehicleID, equipmentNodeID]
            if self.getStateValue("strNodeID") == objEvent[1]:
                self.arrivalVehicle = objEvent[0]
                vehicleInfo = self.globalVar.getVehicleInfoByID(self.arrivalVehicle)
                equipmentInfo = self.globalVar.getEquipmentInfoByID(self.getStateValue("strID"))
                if self.state == "DONE":
                    equipmentInfo.setEquipmentState("UNLOAD")
                    vehicleInfo.setState("LOAD")
                    self.state = self.stateList[3]
                elif self.state == "EMPTY":
                    self.currentJob = vehicleInfo.intJobID
                    equipmentInfo.setEquipmentState("LOAD")
                    vehicleInfo.setState("UNLOAD")
                    self.state = self.stateList[5]
            else:
                self.continueTimeAdvance()
            return True
        elif strPort == "simulationComplete":
            self.state = self.stateList[0]
            return True        
        else:
            print("ERROR at Equipment ExternalTransition: #{}".format(self.getStateValue("strID")))
            print("inputPort: {}".format(strPort))
            print("CurrentState: {}".format(self.state))
            return False

    def funcOutput(self):
        if self.state == "BUSY":      
            equipmentInfo = self.globalVar.getEquipmentInfoByID(self.getStateValue("strID"))
            jobInfo = self.globalVar.getTargetJobsByID(equipmentInfo.intProcessingJobID)
            # ????
            if jobInfo.intJobID >= self.getStateValue("intJobStart") and jobInfo.intJobID <= self.getStateValue("intJobEnd"):
                equipmentInfo.totalProcessedTime = equipmentInfo.totalProcessedTime + self.getStateValue("dblProcessTime")
            ## set Info ##
            if equipmentInfo.strType == "OUT":
                equipmentInfo.setEquipmentState("EMPTY")
                equipmentInfo.intProcessingJobID = None
                jobInfo.setTime('done', self.getStateValue("strID"), self.getTime())
                jobInfo.setTime('out', self.getStateValue("strID"), self.getTime())
                jobInfo.setCarryObject('out', self.getStateValue("strID"), 'Worker')
                jobInfo.setScore(100.0, self.getStateValue("strID"))
            else:
                equipmentInfo.setEquipmentState("DONE")
                score = float(np.random.normal(equipmentInfo.intPerformanceValue, self.getStateValue("intYieldRange"), 1))
                if score > 100:
                    score = 100
                # score = 100
                jobInfo.setScore(score, self.getStateValue("strID"))

            jobInfo.setTime('done', self.getStateValue("strID"), self.getTime())
            self.globalVar.printTerminal("[{}][Equipment(#{}/{})] Job #{} process done sent".format(self.getTime(), self.getStateValue("strID"), str(equipmentInfo.strEquipmentNodeID), jobInfo.intJobID))
            self.addOutputEvent("informDone", [self.getStateValue("strID"), jobInfo.intJobID])
            return True
        elif self.state == "UNLOAD":
            equipmentInfo = self.globalVar.getEquipmentInfoByID(self.getStateValue("strID"))
            jobInfo = self.globalVar.getTargetJobsByID(self.currentJob)
            vehicleInfo = self.globalVar.getVehicleInfoByID(self.arrivalVehicle)

            equipmentInfo.intProcessingJobID = None #OHT 가 가져가서 없음
            equipmentInfo.setEquipmentState("EMPTY")
            jobInfo.setTime('out', self.getStateValue("strID"), self.getTime())
            jobInfo.setCarryObject('out', self.getStateValue("strID"), self.arrivalVehicle)
            jobInfo.setCommandID(vehicleInfo.strCommandID)
            vehicleInfo.setJobID(self.currentJob)
            self.globalVar.printTerminal("[{}][Equipment(#{}/{})] load job #{} to #{}".format(self.getTime(), self.getStateValue("strID"), str(equipmentInfo.strEquipmentNodeID), self.currentJob, self.arrivalVehicle))
            self.addOutputEvent("jobExchange", [self.getStateValue("strID"), self.arrivalVehicle])
            self.currentJob = 0
            self.arrivalVehicle = 0
            return True
        elif self.state == "LOAD":
            equipmentInfo = self.globalVar.getEquipmentInfoByID(self.getStateValue("strID"))
            vehicleInfo = self.globalVar.getVehicleInfoByID(self.arrivalVehicle)
            jobInfo = self.globalVar.getTargetJobsByID(self.currentJob)
            jobInfo.setCarryObject('in', self.getStateValue("strID"), self.arrivalVehicle)            
            jobInfo.setCurrentProcess(equipmentInfo.strType, equipmentInfo.strEquipmentID)
            jobInfo.setNextProcess(None, None)              
            jobInfo.setTime('start', self.getStateValue("strID"), self.getTime())
            
            jobInfo.setCommandID(vehicleInfo.strCommandID)
            equipmentInfo.setEquipmentState("BUSY")
            equipmentInfo.setProcessingJobID(self.currentJob)
            vehicleInfo.intJobID = None
            
            self.globalVar.printTerminal("[{}][Equipment(#{}/{})] unload job #{} from #{}".format(self.getTime(), self.getStateValue("strID"), str(equipmentInfo.strEquipmentNodeID), self.currentJob, self.arrivalVehicle))
            self.addOutputEvent("jobExchange", [self.getStateValue("strID"), self.arrivalVehicle])
            return True               
        elif self.state == "INFORM":
            equipmentInfo = self.globalVar.getEquipmentInfoByID(self.getStateValue("strID"))
            self.globalVar.printTerminal("[{}][Equipment(#{}/{})] process complete".format(self.getTime(), self.getStateValue("strID"), str(equipmentInfo.strEquipmentNodeID)))
            self.addOutputEvent("informFree", self.getStateValue("strID"))
            return True
        else:
            print("ERROR at Equipment OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcInternalTransition(self):
        if self.state == "BUSY":
            equipmentInfo = self.globalVar.getEquipmentInfoByID(self.getStateValue("strID"))
            if equipmentInfo.strType == "OUT":
                self.state = self.stateList[0]
            else:
                self.state = self.stateList[2]
            return True
        elif self.state == "UNLOAD":
            self.state = self.stateList[4]
            return True
        elif self.state == "LOAD":
            self.state = self.stateList[1]
            return True
        elif self.state == "INFORM":
            self.state = self.stateList[0]
            return True
        else:
            print("ERROR at Equipment InternalTransition: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state == "BUSY":
            return self.getStateValue("dblProcessTime")
        elif self.state == "LOAD" or self.state == "UNLOAD":
            return self.getStateValue("dblExchgeTime")
        elif self.state == "INFORM":
            return 0
        else:
            return 999999999999