from SimulationEngine.ClassicDEVS.DEVSCoupledModel import DEVSCoupledModel

from SharedData.GlobalVar import GlobalVar
from Log.OHTSimLogger import OHTSimLogger
from Models.ExperimentalFrame.Generator import Generator
from Models.ExperimentalFrame.Analyzer import Analyzer
from Models.PhysicalSystem.Vehicle import Vehicle
from Models.PhysicalSystem.Equipment import Equipment
from Models.SystemController.MCS import MCS
from Models.SystemController.MainController import MainController
from Models.SystemController.SAManager import SAManager
from Visualizer.Visualizer import Visualizer

class OHTSimModel(DEVSCoupledModel):
    def __init__(self, objConfiguration, jsonPath, iter, maxSim, prevAnalysisModel, preObjLogger, renderTime, numVehicle, maxVehicle, isVehicleChange, simulationMode, playBackMode, RLTrainMode):
        super().__init__("OHTSimModel")                 
        self.objConfiguration = objConfiguration
        self.iter = iter
        self.maxSim = maxSim
        self.numVehicle = numVehicle
        self.maxVehicle = maxVehicle
        self.isVehicleChange = isVehicleChange

        ## map.json ##
        railList = objConfiguration.getConfiguration("railList")
        nodeList = objConfiguration.getConfiguration("nodeList")
        equipmentInfo = objConfiguration.getConfiguration("equipmentInfo")
        
        ## processInfo.json ##
        seqInfo = objConfiguration.getConfiguration("seqInfo")
        performanceInfo = objConfiguration.getConfiguration("performanceInfo")
        
        ## vehicleInfo.json ##
        vehicleInfo = objConfiguration.getConfiguration("vehicleInfo")
        ## log.json ##
        logVehicle = objConfiguration.getConfiguration("logVehicle")
        logPath = objConfiguration.getConfiguration("logPath")
        
        
        ## setup.json ##
        passingScore = objConfiguration.getConfiguration("passingScore")
        numJob = objConfiguration.getConfiguration("numJob")
        yieldRange = objConfiguration.getConfiguration("yieldRange")
        jobStart = objConfiguration.getConfiguration("jobStart")
        jobEnd = objConfiguration.getConfiguration("jobEnd")
        isLogOn = objConfiguration.getConfiguration("isLogOn")
        isAnalysisLogOn = objConfiguration.getConfiguration("isAnalysisLogOn")
        isTerminalOn = objConfiguration.getConfiguration("isTerminalOn")
        isVisualizerOn = objConfiguration.getConfiguration("isVisualizerOn")
        isVisualizerLogOn = objConfiguration.getConfiguration("isVisualizerLogOn")
        isMakeRlEnv = objConfiguration.getConfiguration("isMakeRlEnv")
        
        if self.isVehicleChange == True and isVisualizerLogOn == True:
            print("Too many files to save, visualize log turned off")
            isVisualizerLogOn = False

        isShowFigure = objConfiguration.getConfiguration("isShowFigure")
        isSaveFigure = objConfiguration.getConfiguration("isSaveFigure") 

        ## init GlobalVar ##
        self.globalVar = GlobalVar(isTerminalOn, railList, nodeList, equipmentInfo, seqInfo, performanceInfo, vehicleInfo, numJob, jsonPath, self.numVehicle, isMakeRlEnv)

        if prevAnalysisModel == None and preObjLogger == None:
            ## set up the logger ##
            self.objLogger = OHTSimLogger(logPath, logVehicle, isLogOn, self.iter, self.maxSim, isAnalysisLogOn)
            ## init Analyzer ##
            self.objAnalyzer = Analyzer("Analyzer", self.globalVar, self.objLogger, numJob, jobStart, jobEnd, self.iter, self.maxSim, self.numVehicle, self.maxVehicle, isShowFigure, isSaveFigure, self.isVehicleChange)
        else:
            preObjLogger.setIter(self.iter)
            self.objLogger = preObjLogger
            prevAnalysisModel.setSimulationIteration(self.iter)
            prevAnalysisModel.setVehicleIteration(self.numVehicle)
            prevAnalysisModel.setGlobalVar(self.globalVar)
            prevAnalysisModel.setObjLogger(self.objLogger)
            self.objAnalyzer = prevAnalysisModel
        self.addModel(self.objAnalyzer)
        self.prevAnalysisModel = self.objAnalyzer
        self.preObjLogger = self.objLogger

        ## init Generator ##
        self.objGenerator = Generator("Generator", self.globalVar, self.objLogger, jobStart, jobEnd)
        self.addModel(self.objGenerator)
        ## init MCS ##
        self.objMCS = MCS("MCS", self.globalVar, self.objLogger, passingScore, numJob, jobStart, jobEnd)
        self.addModel(self.objMCS)
        ## init MainController ##
        self.objMainController = MainController("MainController", self.globalVar, self.objLogger)
        self.addModel(self.objMainController)
        ## init SAManager ##
        self.objSAManager = SAManager("SAManager", self.globalVar, self.objLogger)
        self.addModel(self.objSAManager)
        ## init Visualizer ##
        if maxSim > 1 and isVisualizerOn == True:
            isVisualizerOn = False
            print("MonteCarlo Simulation으로 인한 visualizer는 off 되었습니다.")
        self.objVisualizer = Visualizer("Visualizer", self.globalVar, self.objLogger, isVisualizerOn, isVisualizerLogOn, jsonPath, self.iter, renderTime, simulationMode, playBackMode, RLTrainMode)
        self.addModel(self.objVisualizer)

        self.addCoupling(self.objMCS, "fromToCommand", self.objMainController, "fromToCommand")
        self.addCoupling(self.objMCS, "goCommand", self.objMainController, "goCommand")
        self.addCoupling(self.objMCS, "simulationComplete", self.objAnalyzer, "simulationComplete")
        self.addCoupling(self.objMCS, "simulationComplete", self.objSAManager, "simulationComplete")
        self.addCoupling(self.objMCS, "simulationComplete", self.objMainController, "simulationComplete")
        self.addCoupling(self.objMCS, "simulationComplete", self.objGenerator, "simulationComplete")
        self.addCoupling(self.objAnalyzer, "analyzeComplete", self.objVisualizer, "analyzeComplete")
        self.addCoupling(self.objSAManager, "fromRes", self.objMainController, "fromRes")
        self.addCoupling(self.objSAManager, "toRes", self.objMainController, "toRes")
        self.addCoupling(self.objSAManager, "goRes", self.objMainController, "goRes")
        self.addCoupling(self.objMainController, "fromReq", self.objSAManager, "fromReq")
        self.addCoupling(self.objMainController, "toReq", self.objSAManager, "toReq")
        self.addCoupling(self.objMainController, "goReq", self.objSAManager, "goReq")
        self.addCoupling(self.objMainController, "informOHT", self.objMCS, "informOHT")
        self.addCoupling(self.objMainController, "informFree", self.objMCS, "informFree")
        self.addCoupling(self.objGenerator, "job", self.objVisualizer, "job")

        ## init Equipment ##
        self.objEquipment = []
        for info in equipmentInfo:
            objEquipment = Equipment(info['equipmentID'], self.globalVar, self.objLogger, info['equipmentNodeID'], info["processTime"], info["processType"], info["exchgeTime"], yieldRange, jobStart, jobEnd)
            self.objEquipment.append(objEquipment)
            self.addModel(objEquipment)
            if info["processType"] == 'A-1':
                self.addCoupling(self.objGenerator, "job", objEquipment, "job")
            self.addCoupling(self.objMCS, "simulationComplete", objEquipment, "simulationComplete")
            self.addCoupling(objEquipment, "informDone", self.objMCS, "informDone")
            self.addCoupling(objEquipment, "informDone", self.objVisualizer, "informDone")
            self.addCoupling(objEquipment, "informFree", self.objMCS, "informFree")
            self.addCoupling(objEquipment, "informFree", self.objGenerator, "informFree")
            self.addCoupling(objEquipment, "jobExchange", self.objVisualizer, "jobExchange")

        ## init OHTs ##
        self.objVehicle = []
        for info in vehicleInfo:
            objVehicle = Vehicle(info['vehicleID'], self.globalVar, self.objLogger, info['coordinates'], info['operateTime'], info['moveTime'])
            self.objVehicle.append(objVehicle)
            self.addModel(objVehicle)
            self.addCoupling(self.objMainController, "moveCommand", objVehicle, "moveCommand")
            self.addCoupling(objVehicle, "ownPos", self.objMainController, "ownPos")
            self.addCoupling(objVehicle, "ownPos", self.objVisualizer, "ownPos")
            self.addCoupling(objVehicle, "arrival", self.objVisualizer, "arrival")
            self.addCoupling(objVehicle, "arrival", self.objMainController, "arrival")
            self.addCoupling(self.objMainController, "LDCommand", objVehicle, "LDCommand")
            self.addCoupling(objVehicle, "exchangeDone", self.objMainController, "exchangeDone")
            self.addCoupling(self.objMainController, "LUCommand", objVehicle, "LUCommand")
            self.addCoupling(objVehicle, "liftUp", self.objMainController, "liftUp")
            self.addCoupling(objVehicle, "liftUp", self.objVisualizer, "liftUp")
            self.addCoupling(objVehicle, "liftDown", self.objVisualizer, "liftDown")
            self.addCoupling(objVehicle, "stopInform", self.objMainController, "stopInform")
            self.addCoupling(self.objMainController, "continue", objVehicle, "continue")
            self.addCoupling(self.objMCS, "simulationComplete", objVehicle, "simulationComplete")
            for equipment in self.objEquipment:
                self.addCoupling(objVehicle, "liftDown", equipment, "liftDown")
                self.addCoupling(equipment, "jobExchange", objVehicle, "jobExchange")
