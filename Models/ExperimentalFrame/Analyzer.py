from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches
import copy
import numpy as np

import matplotlib
import datetime
import random

matplotlib.rcParams['figure.max_open_warning'] = 40  
current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

class Analyzer(DEVSAtomicModel):
    def __init__(self, strID, globalVar, objLogger, numJob, jobStart, jobEnd, iter, maxSim, numVehicle, maxVehicle, isShowFigure, isSaveFigure, isVehicleChange):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar
        self.objLogger = objLogger
        self.iter = iter
        self.maxSim = maxSim
        self.numVehicle = numVehicle
        self.maxVehicle = maxVehicle
        self.isShowFigure = isShowFigure
        self.isSaveFigure = isSaveFigure
        self.isVehicleChange = isVehicleChange

        self.colorList = ['red', 'tomato', 'sienna', 'saddlebrown', 'green',\
                         'darkgreen', 'lime', 'teal', 'blue', 'darkblue',\
                         'rebeccapurple', 'royalblue', 'cyan', 'dodgerblue', 'darkslategrey',\
                         'magenta', 'mediumvioletred', 'yellow', 'darkolivegreen', 'black',\
                         'gold', 'lightcoral', 'indianred', 'coral', 'orangered',\
                         'crimson', 'darkkhaki', 'steelblue', 'rosybrown', 'indigo']
        self.gradientColorList = ['green', 'darkgreen', 'lime',  'gold', 'yellow', 'lightcoral', 'indianred', 'coral', 'tomato', 'orangered', 'red']
        # states
        self.stateList = ["WAIT", "ANALYSIS"]
        self.state = self.stateList[0]

        # input Ports
        self.addInputPort("simulationComplete")

        # output Ports
        self.addOutputPort("analyzeComplete")

        # self variables
        self.addStateVariable("strID", strID)
        self.addStateVariable("intNumJob", numJob)
        self.addStateVariable("intJobStart", jobStart)
        self.addStateVariable("intJobEnd", jobEnd)
        
        # variables
        self.dictTotalLeadTime = {}
        self.dictLeadTime = {}
        ## job View ##
        self.dictTotalWaitTimeJob = {}
        self.dictWaitTimeJob = {}
        ## equipment View ##
        self.dictTotalWaitTimeEquipment = {}
        self.dictWaitTimeEquipment = {}
        self.dictWaitTimeEquipmentCnt = {}
        self.vehicleActivationTime = {}
        self.vehicleUtilizationRates = {}
        self.simTime = {}
        self.goCmd = {}
        self.dictEquipmentTotalProcessTime = {}
        self.dictNodeCounts = {}
        self.dictNodeUsage = {}

        ## vehicle focused averaged KPI ##
        self.vehicleDictTotalLeadTime = {}
        self.vehicleDictLeadTime = {}
        self.vehicleDictTotalWaitTimeJob = {}
        self.vehicleDictWaitTimeJob = {}
        self.vehicleDictTotalWaitTimeEquipment = {}
        self.vehicleDictWaitTimeEquipment = {}
        self.vehicleDictWaitTimeEquipmentCnt = {}        
        self.vehicleVehicleActivationTime = {}
        self.vehicleVehicleUtilizationRates = {}
        self.vehicleSimTime = {}
        self.vehicleGoCmd = {}
        self.vehicleDictEquipmentTotalProcessTime = {}
        self.vehicleDictNodeCounts = {}
        self.vehicleDictNodeUsage = {}

    def funcExternalTransition(self, strPort, objEvent):
        if strPort == "simulationComplete":
            print("Leadtime: {:.3f}".format(self.getTime()))
            self.globalVar.printTerminal("[{}][{}] Analysis processing".format(self.getTime(), self.getStateValue("strID")))
            self.state = self.stateList[1]
            return True
        else:
            print("ERROR at Analyzer ExternalTransition: #{}".format(self.getStateValue("strID")))
            print("inputPort: {}".format(strPort))
            print("CurrentState: {}".format(self.state))
            return False

    def funcOutput(self):
        if self.state == "ANALYSIS":
            targetJobs = self.globalVar.getTargetJobs()
            vehicleInfo = self.globalVar.getVehicleInfo()
            eqpInfo = self.globalVar.getEquipmentInfo()
            nodeInfo = self.globalVar.getTotalNodeInfo()
            
            jobStart = self.getStateValue("intJobStart")
            jobEnd = self.getStateValue("intJobEnd")
            numJob = self.getStateValue("intNumJob")

            self.leadTime(targetJobs, jobStart, jobEnd, numJob)
            self.waitTime(targetJobs, jobStart, jobEnd)
            self.vehicleUtilizationRate(targetJobs, jobStart, jobEnd, vehicleInfo)
            self.goCommandCounts(vehicleInfo)
            self.equipmentTotalProcessTime(eqpInfo)
            self.nodeUsageCnt(nodeInfo)

            if self.iter == self.maxSim:
                self.vehicleDictTotalLeadTime[self.numVehicle] = copy.deepcopy(self.dictTotalLeadTime)
                self.logLeadTime(self.numVehicle, self.vehicleDictTotalLeadTime[self.numVehicle])
                self.vehicleDictLeadTime[self.numVehicle] = copy.deepcopy(self.dictLeadTime)
                self.logLeadTimeJob(self.numVehicle, self.vehicleDictLeadTime[self.numVehicle])
                self.vehicleDictTotalWaitTimeJob[self.numVehicle] = copy.deepcopy(self.dictTotalWaitTimeJob)
                self.logWaitTimeJob(self.numVehicle, self.vehicleDictTotalWaitTimeJob[self.numVehicle])
                self.vehicleDictWaitTimeJob[self.numVehicle] = copy.deepcopy(self.dictWaitTimeJob)
                self.logWaitTimeJobbyEqpment(self.numVehicle, self.vehicleDictWaitTimeJob[self.numVehicle])
                self.vehicleDictTotalWaitTimeEquipment[self.numVehicle] = copy.deepcopy(self.dictTotalWaitTimeEquipment)
                self.logWaitTimeEqpment(self.numVehicle, self.vehicleDictTotalWaitTimeEquipment[self.numVehicle])
                # self.vehicleDictWaitTimeEquipment[self.numVehicle] = copy.deepcopy(self.dictWaitTimeEquipment)
                # self.vehicleDictWaitTimeEquipmentCnt[self.numVehicle] = copy.deepcopy(self.dictWaitTimeEquipmentCnt)
                self.vehicleVehicleActivationTime[self.numVehicle] = copy.deepcopy(self.vehicleActivationTime)
                self.logVehicleUtilizationTime(self.numVehicle, self.vehicleVehicleActivationTime[self.numVehicle])
                self.vehicleVehicleUtilizationRates[self.numVehicle] = copy.deepcopy(self.vehicleUtilizationRates)
                self.logVehicleUtilizationRate(self.numVehicle, self.vehicleVehicleUtilizationRates[self.numVehicle])
                self.vehicleSimTime[self.numVehicle] = copy.deepcopy(self.simTime)
                self.logSimTime(self.numVehicle, self.vehicleSimTime[self.numVehicle])
                self.vehicleGoCmd[self.numVehicle] = copy.deepcopy(self.goCmd)
                self.logGoCommandCounts(self.numVehicle, self.vehicleGoCmd[self.numVehicle])
                self.vehicleDictEquipmentTotalProcessTime[self.numVehicle] = copy.deepcopy(self.dictEquipmentTotalProcessTime)
                self.logProcessTime(self.numVehicle, self.vehicleDictEquipmentTotalProcessTime[self.numVehicle])
                self.vehicleDictNodeCounts[self.numVehicle] = copy.deepcopy(self.dictNodeCounts)
                self.vehicleDictNodeUsage[self.numVehicle] = copy.deepcopy(self.dictNodeUsage)
                self.logNodeUsage(self.numVehicle, self.vehicleDictNodeUsage[self.numVehicle])
                self.dictTotalLeadTime.clear()
                self.dictLeadTime.clear()
                self.dictTotalWaitTimeJob.clear()
                self.dictWaitTimeJob.clear()
                self.dictTotalWaitTimeEquipment.clear()
                self.dictWaitTimeEquipment.clear()
                self.dictWaitTimeEquipmentCnt.clear()
                self.vehicleActivationTime.clear()
                self.vehicleUtilizationRates.clear()
                self.simTime.clear()
                self.goCmd.clear()
                self.dictEquipmentTotalProcessTime.clear()
                self.dictNodeCounts.clear()
                self.dictNodeUsage.clear()
                if self.numVehicle == self.maxVehicle:
                    self.plotResults()
            self.globalVar.printTerminal("[{}][{}] Analysis complete".format(self.getTime(), self.getStateValue("strID")))
            self.addOutputEvent("analyzeComplete", True)                
            return True
        else:
            print("ERROR at Analyzer OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcInternalTransition(self):
        if self.state == "ANALYSIS":
            self.state = self.stateList[0]
            return True
        else:
            print("ERROR at Analyzer InternalTransition: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state == "ANALYSIS":
            return 0
        else:
            return 999999999999

    def leadTime(self, jobInfo, jobStart, jobEnd, numJob):
        dictTotalLeadTime = 0
        dictLeadTime = {}
        for key, value in jobInfo.items():
            jobID = int(key)
            if jobID >= jobStart and jobID <= jobEnd:            
                lstStartProcessTime = list(value.dictStartTime.values())
                lstOutProcessTime = list(value.dictOutTime.values())
                startProcessTime = lstStartProcessTime[0]
                outProcessTime = lstOutProcessTime[-1]
                dictLeadTime[key] = outProcessTime - startProcessTime
                dictTotalLeadTime = dictTotalLeadTime + dictLeadTime[key]
        dictTotalLeadTime = dictTotalLeadTime/(jobEnd-jobStart+1)
        
        self.dictTotalLeadTime[self.iter] = dictTotalLeadTime
        self.dictLeadTime[self.iter] = dictLeadTime
    def waitTime(self, jobInfo, jobStart, jobEnd):
        ## job View ##
        dictTotalWaitTimeJob = {}
        dictWaitTimeJob = {}
        ## equipment View ##
        dictTotalWaitTimeEquipment = {}
        dictWaitTimeEquipment = {}
        dictWaitTimeEquipmentCnt = {}
        for key, value in jobInfo.items():
            jobID = int(key)
            if jobID >= jobStart and jobID <= jobEnd:
                dictWaitTimeJob[key] = []
                dictTotalWaitTimeJob[key] = 0
                for eqpID, time in value.dictDoneTime.items():
                    if eqpID[0] != "N":
                        processDoneTime = time
                        processOutTime = value.dictOutTime[eqpID]
                        waitTime = processOutTime - processDoneTime
                        dictWaitTimeJob[key].append([eqpID, waitTime])
                        dictTotalWaitTimeJob[key] = dictTotalWaitTimeJob[key] + waitTime
                    
                        if eqpID not in dictWaitTimeEquipment:
                            dictWaitTimeEquipment[eqpID] = waitTime
                            dictWaitTimeEquipmentCnt[eqpID] = 1
                        else:
                            dictWaitTimeEquipment[eqpID] = dictWaitTimeEquipment[eqpID] + waitTime
                            dictWaitTimeEquipmentCnt[eqpID] = dictWaitTimeEquipmentCnt[eqpID] + 1
                dictTotalWaitTimeJob[key] = dictTotalWaitTimeJob[key]/(len(value.dictDoneTime)-1)

        for key, value in dictWaitTimeEquipment.items():
            dictTotalWaitTimeEquipment[key] = value/dictWaitTimeEquipmentCnt[key]
        
        self.dictTotalWaitTimeJob[self.iter] = dictTotalWaitTimeJob
        self.dictWaitTimeJob[self.iter] = dictWaitTimeJob
        self.dictWaitTimeEquipment[self.iter] = dictWaitTimeEquipment
        self.dictWaitTimeEquipmentCnt[self.iter] = dictWaitTimeEquipmentCnt
        self.dictTotalWaitTimeEquipment[self.iter] = dictTotalWaitTimeEquipment   
        
    def vehicleUtilizationRate(self, jobInfo, jobStart, jobEnd, vehicleInfo):
        vehicleActivationTime = {}
        vehicleUtilizationRates = {}

        simTime = self.getTime()
        for key, value in vehicleInfo.items():
            if key not in vehicleActivationTime:
                vehicleActivationTime[key] = 0
            for completeCmdID in value.lstCommandID:
                if completeCmdID in value.dictActivationTime:
                    vehicleActivationTime[key] = vehicleActivationTime[key] + value.dictActivationTime[completeCmdID]
        for key, value in vehicleActivationTime.items():
            vehicleUtilizationRates[key] = (value/simTime) * 100
        
        self.vehicleActivationTime[self.iter] = vehicleActivationTime
        self.vehicleUtilizationRates[self.iter] = vehicleUtilizationRates
        self.simTime[self.iter] = simTime
        
    def goCommandCounts(self, vehicleInfo):
        goCmd = 0
        for key, value in vehicleInfo.items():
            for cmdID in value.lstCommandID:
                if cmdID[-1] == "G":
                    goCmd = goCmd + 1
        self.goCmd[self.iter] = goCmd
    def equipmentTotalProcessTime(self, eqpInfo):
        dictTotalProcessTime = {}
        for key, value in eqpInfo.items():
            if value.totalProcessedTime != 0:
                dictTotalProcessTime[key] = value.totalProcessedTime
            
        self.dictEquipmentTotalProcessTime[self.iter] = dictTotalProcessTime
    def nodeUsageCnt(self, nodeInfo):
        dictNodeUsage = {}
        dictNodeCounts = {}
        for key, value in nodeInfo.items():
            dictNodeUsage[key] = value.usageCnt
            if value.usageCnt != 0:
                dictNodeCounts[key] = 1
            else:
                dictNodeCounts[key] = 0
        self.dictNodeUsage[self.iter] = dictNodeUsage
        self.dictNodeCounts[self.iter] = dictNodeCounts

    def setSimulationIteration(self, iter):
        self.iter = iter
    def setVehicleIteration(self, numVehicle):
        self.numVehicle = numVehicle
    def setGlobalVar(self, globalVar):
        self.globalVar = globalVar
    def setObjLogger(self, logger):
        self.objLogger = logger

    def getCurrentTime(self):
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    def logLeadTime(self, numVehicle, value):
        dicLog = {}
        for iter, jobLeadTime in value.items():
            dicLog["[#{}] avgLeadTime".format(iter)] = jobLeadTime
        self.objLogger.addLogDictionaryAnalysis(f"logLeadTime_v{numVehicle}_{self.getCurrentTime()}", dicLog)      

    def logLeadTimeJob(self, numVehicle, value):
        dicLog = {}
        for iter, jobLeadTime in value.items():
            for jobIndex, leadTime in jobLeadTime.items():
                dicLog["[#{}] Job #{}".format(iter, jobIndex)] = leadTime
        self.objLogger.addLogDictionaryAnalysis(f"logLeadTimeJob_v{numVehicle}_{self.getCurrentTime()}", dicLog)

    def logWaitTimeJob(self, numVehicle, value):
        dicLog = {}
        for iter, jobWaitTime in value.items():
            for jobIndex, waitTime in jobWaitTime.items():
                dicLog["[#{}] Job #{}".format(iter, jobIndex)] = waitTime
        self.objLogger.addLogDictionaryAnalysis(f"logWaitTimeJob_v{numVehicle}_{self.getCurrentTime()}", dicLog)

    def logWaitTimeJobbyEqpment(self, numVehicle, value):
        dicLog = {}
        for iter, jobWaitTime in value.items():
            for jobIndex, waitTime in jobWaitTime.items():
                for waitTimeByEqpment in waitTime:
                    dicLog["[#{}] Job #{} :: Eqp #{}".format(iter, jobIndex, waitTimeByEqpment[0])] = waitTimeByEqpment[1]
        self.objLogger.addLogDictionaryAnalysis(f"logWaitTimeJobByEquipment_v{numVehicle}_{self.getCurrentTime()}", dicLog)

    def logWaitTimeEqpment(self, numVehicle, value):
        dicLog = {}
        for iter, eqpWaitTime in value.items():
            for eqpIndex, waitTime in eqpWaitTime.items():
                dicLog["[#{}] Eqp #{}".format(iter, eqpIndex)] = waitTime
        self.objLogger.addLogDictionaryAnalysis(f"logWaitTimeEquipment_v{numVehicle}_{self.getCurrentTime()}", dicLog)

    def logVehicleUtilizationTime(self, numVehicle, value):
        dicLog = {}
        for iter, vehicleUtilTime in value.items():
            for vehicleID, utilTime in vehicleUtilTime.items():
                dicLog["[#{}] #{}".format(iter, vehicleID)] = utilTime
        self.objLogger.addLogDictionaryAnalysis(f"logUtilTime_v{numVehicle}_{self.getCurrentTime()}", dicLog)

    def logVehicleUtilizationRate(self, numVehicle, value):
        dicLog = {}
        for iter, vehicleUtilTime in value.items():
            for vehicleID, utilTime in vehicleUtilTime.items():
                dicLog["[#{}] #{}".format(iter, vehicleID)] = utilTime
        self.objLogger.addLogDictionaryAnalysis(f"logUtilRate_v{numVehicle}_{self.getCurrentTime()}", dicLog)

    def logSimTime(self, numVehicle, value):
        dicLog = {}
        for iter, simulationTime in value.items():
            dicLog["[#{}] SimTime".format(iter)] = simulationTime
        self.objLogger.addLogDictionaryAnalysis(f"logSimTime_v{numVehicle}_{self.getCurrentTime()}", dicLog)

    def logGoCommandCounts(self, numVehicle, value):
        dicLog = {}
        for iter, goCmdCnts in value.items():
            dicLog["[#{}] GoCommands".format(iter)] = goCmdCnts
        self.objLogger.addLogDictionaryAnalysis(f"logGoCmd_v{numVehicle}_{self.getCurrentTime()}", dicLog)

    def logProcessTime(self, numVehicle, value):
        dicLog = {}
        for iter, eqpProcessTime in value.items():
            for eqpID, processTime in eqpProcessTime.items():
                dicLog["[#{}] Eqp #{}".format(iter, eqpID)] = processTime
        self.objLogger.addLogDictionaryAnalysis(f"logProcessTime_v{numVehicle}_{self.getCurrentTime()}", dicLog)

    def logNodeUsage(self, numVehicle, value):
        dicLog = {}
        for iter, nodeUsage in value.items():
            for nodeID, nodeCnts in nodeUsage.items():
                dicLog["[#{}] nodeID #{}".format(iter, nodeID)] = nodeCnts
        self.objLogger.addLogDictionaryAnalysis(f"logNodeUsage_v{numVehicle}_{self.getCurrentTime()}", dicLog)         
    
    def plotResults(self):
        ## leadTime ##
        dictMinLeadTime = {}
        dictMaxLeadTime = {}
        dictAvgLeadTime = {}
        for numVehicle, iterInfo in self.vehicleDictTotalLeadTime.items():
            minLeadTime = 99999999999999999999
            maxLeadTime = -99999999999999999999
            avgLeadTime = 0            
            for monteCarlo, leadTime in iterInfo.items():
                if leadTime < minLeadTime:
                    minLeadTime = leadTime
                if leadTime > maxLeadTime:
                    maxLeadTime = leadTime
                avgLeadTime = avgLeadTime + leadTime
            dictMinLeadTime[numVehicle] = minLeadTime
            dictMaxLeadTime[numVehicle] = maxLeadTime
            dictAvgLeadTime[numVehicle] = avgLeadTime/len(iterInfo)
        plt.figure(figsize=(12, 10))
        if self.isVehicleChange == True:
            plt.title("Lead time based on number of the vehicle ", fontsize=13)
        else:
            plt.title("Lead time", fontsize=13)
        plt.xlabel('Utilized number of the vehicle [ea]')
        plt.ylabel('Lead time of the production [s]')
        plt.plot(list(dictMinLeadTime.keys()), list(dictMinLeadTime.values()), marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10, label = 'minimum')
        plt.plot(list(dictMaxLeadTime.keys()), list(dictMaxLeadTime.values()), marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10, label = 'maximum')
        plt.plot(list(dictAvgLeadTime.keys()), list(dictAvgLeadTime.values()), marker = ".", linestyle = 'solid', color = self.colorList[0], markersize=7, label = 'average')

        for key, value in dictMinLeadTime.items():
            plt.text(key, value , "{:.1f}".format(value), color='blue', verticalalignment='top', horizontalalignment='left', fontsize=9)

        for key, value in dictMaxLeadTime.items():
            plt.text(key, value , "{:.1f}".format(value), color='red', verticalalignment='bottom', horizontalalignment='left', fontsize=9)

        for key, value in dictAvgLeadTime.items():
            plt.text(key, value , "{:.1f}".format(value), color='green', verticalalignment='bottom', horizontalalignment='left', fontsize=9)


        plt.legend(loc = "upper left", bbox_to_anchor=(1.05, 1.0))
        plt.tight_layout()
        if self.isShowFigure == True:
            plt.show(block=False)
        if self.isSaveFigure == True:
            plt.savefig(f'LeadTime_{current_time}.png')


        dictJobMinLeadTime = {}
        dictJobMaxLeadTime = {}
        dictJobAvgLeadTime = {}
        for numVehicle, iterInfo in self.vehicleDictLeadTime.items():
            tempJobMinTime = {}
            tempJobMaxTime = {}
            tempJobAvgTime = {}                  
            for monteCarlo, jobInfo in iterInfo.items():
                for numJob, leadTime in jobInfo.items():
                    if numJob not in tempJobMinTime:
                        tempJobMinTime[numJob] = 99999999999999999999
                    if numJob not in tempJobMaxTime:
                        tempJobMaxTime[numJob] = -99999999999999999999
                    if numJob not in tempJobAvgTime:
                        tempJobAvgTime[numJob] = 0                    
                    if leadTime < tempJobMinTime[numJob]:
                        tempJobMinTime[numJob] = leadTime
                    if leadTime > tempJobMaxTime[numJob]:
                        tempJobMaxTime[numJob] = leadTime
                    tempJobAvgTime[numJob] = tempJobAvgTime[numJob] + leadTime
            for numJob, summedLeadTime in tempJobAvgTime.items():
                tempJobAvgTime[numJob] = summedLeadTime/len(iterInfo)                    
            dictJobMinLeadTime[numVehicle] = copy.deepcopy(tempJobMinTime)
            dictJobMaxLeadTime[numVehicle] = copy.deepcopy(tempJobMaxTime)
            dictJobAvgLeadTime[numVehicle] = copy.deepcopy(tempJobAvgTime)
        plt.figure(figsize=(12, 10))
        plt.title("Lead time based on index of the job", fontsize=13)
        if self.isVehicleChange == True:
            numVehicles = 1
        else:
            numVehicles = self.numVehicle
        for i in range(len(self.vehicleDictLeadTime)):
            if self.isVehicleChange == True:
                plt.plot(list(dictJobMinLeadTime[numVehicles].keys()), list(dictJobMinLeadTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10)
                plt.plot(list(dictJobMaxLeadTime[numVehicles].keys()), list(dictJobMaxLeadTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10)
                plt.plot(list(dictJobAvgLeadTime[numVehicles].keys()), list(dictJobAvgLeadTime[numVehicles].values()), marker = ".", linestyle = 'None', color = self.colorList[i], markersize=7, label = "numVehicles: {}".format(numVehicles))
            else:
                plt.plot(list(dictJobMinLeadTime[numVehicles].keys()), list(dictJobMinLeadTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10, label = 'minimum')
                plt.plot(list(dictJobMaxLeadTime[numVehicles].keys()), list(dictJobMaxLeadTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10, label = 'maximum')
                plt.plot(list(dictJobAvgLeadTime[numVehicles].keys()), list(dictJobAvgLeadTime[numVehicles].values()), marker = ".", linestyle = 'None', color = self.colorList[i], markersize=7, label = 'average')
            numVehicles = numVehicles + 1
        plt.xlabel('Index of the Job [Index]')
        plt.ylabel('Lead time of the production [s]')
        plt.legend(loc = "upper left", bbox_to_anchor=(1.05, 1.0))
        plt.tight_layout()
        if self.isShowFigure == True:
            plt.show(block=False)
        if self.isSaveFigure == True:
            plt.savefig(f'LeadTime_Job_{current_time}.png')


        ## waitTime ##
        dictAvgWaitTime = {}
        for numVehicle, iterInfo in self.vehicleDictTotalWaitTimeJob.items():
            tempSumAll = {}
            for monteCarlo, jobInfo in iterInfo.items():
                tempSumAll[monteCarlo] = 0
                for numJob, waitTime in jobInfo.items():
                    tempSumAll[monteCarlo] = tempSumAll[monteCarlo] + waitTime
                tempSumAll[monteCarlo] = tempSumAll[monteCarlo]/len(jobInfo)           
            dictAvgWaitTime[numVehicle] = copy.deepcopy(tempSumAll)
        dictMinAvgWaitTime = {}
        dictMaxAvgWaitTime = {}
        dictAvgAvgWaitTime = {}
        for numVehicle, iterInfo in dictAvgWaitTime.items():
            avgMinWaitTime = 99999999999999999999
            avgMaxWaitTime = -99999999999999999999
            avgAvgWaitTime = 0            
            for monteCarlo, avgWaitTime in iterInfo.items():
                if avgWaitTime < avgMinWaitTime:
                    avgMinWaitTime = avgWaitTime
                if avgWaitTime > avgMaxWaitTime:
                    avgMaxWaitTime = avgWaitTime
                avgAvgWaitTime = avgAvgWaitTime + avgWaitTime
            dictMinAvgWaitTime[numVehicle] = avgMinWaitTime
            dictMaxAvgWaitTime[numVehicle] = avgMaxWaitTime
            dictAvgAvgWaitTime[numVehicle] = avgAvgWaitTime/len(iterInfo)
        plt.figure(figsize=(12, 10))
        if self.isVehicleChange == True:
            plt.title("Wait time based on number of the vehicle", fontsize=13)
        else:
            plt.title("Wait time", fontsize=13)
        plt.xlabel('Utilized number of the vehicle [ea]')
        plt.ylabel('Wait time of the production [s]')
        plt.plot(list(dictMinAvgWaitTime.keys()), list(dictMinAvgWaitTime.values()), marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10, label = 'minimum')
        plt.plot(list(dictMaxAvgWaitTime.keys()), list(dictMaxAvgWaitTime.values()), marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10, label = 'maximum')
        plt.plot(list(dictAvgAvgWaitTime.keys()), list(dictAvgAvgWaitTime.values()), marker = ".", linestyle = 'solid', color = self.colorList[0], markersize=7, label = 'average')
        plt.legend(loc = "upper left", bbox_to_anchor=(1.05, 1.0))
        plt.tight_layout()
        if self.isShowFigure == True:
            plt.show(block=False)
        if self.isSaveFigure == True:
            plt.savefig(f'WaitTime_{current_time}.png')

        dictJobMinWaitTime = {}
        dictJobMaxWaitTime = {}
        dictJobAvgWaitTime = {}     
        for numVehicle, iterInfo in self.vehicleDictTotalWaitTimeJob.items():
            tempJobMinTime = {}
            tempJobMaxTime = {}
            tempJobAvgTime = {}
            for monteCarlo, jobInfo in iterInfo.items():
                for numJob, waitTime in jobInfo.items():
                    if numJob not in tempJobMinTime:
                        tempJobMinTime[numJob] = 99999999999999999999
                    if numJob not in tempJobMaxTime:
                        tempJobMaxTime[numJob] = -99999999999999999999
                    if numJob not in tempJobAvgTime:
                        tempJobAvgTime[numJob] = 0
                    if waitTime < tempJobMinTime[numJob]:
                        tempJobMinTime[numJob] = waitTime
                    if waitTime > tempJobMaxTime[numJob]:
                        tempJobMaxTime[numJob] = waitTime
                    tempJobAvgTime[numJob] = tempJobAvgTime[numJob] + waitTime
            for numJob, summedWaitTime in tempJobAvgTime.items():
                tempJobAvgTime[numJob] = summedWaitTime/len(iterInfo)                    
            dictJobMinWaitTime[numVehicle] = copy.deepcopy(tempJobMinTime)
            dictJobMaxWaitTime[numVehicle] = copy.deepcopy(tempJobMaxTime)
            dictJobAvgWaitTime[numVehicle] = copy.deepcopy(tempJobAvgTime)        
        plt.figure(figsize=(12, 10))
        plt.title("Wait time based on index of the job", fontsize=13)
        if self.isVehicleChange == True:
            numVehicles = 1
        else:
            numVehicles = self.numVehicle    
        for i in range(len(self.vehicleDictTotalWaitTimeJob)):
            if self.isVehicleChange == True:
                plt.plot(list(dictJobMinWaitTime[numVehicles].keys()), list(dictJobMinWaitTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10)
                plt.plot(list(dictJobMaxWaitTime[numVehicles].keys()), list(dictJobMaxWaitTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10)
                plt.plot(list(dictJobAvgWaitTime[numVehicles].keys()), list(dictJobAvgWaitTime[numVehicles].values()), marker = ".", linestyle = 'None', color = self.colorList[i], markersize=7, label = "numVehicles: {}".format(numVehicles))
            else:
                plt.plot(list(dictJobMinWaitTime[numVehicles].keys()), list(dictJobMinWaitTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10, label = 'minimum')
                plt.plot(list(dictJobMaxWaitTime[numVehicles].keys()), list(dictJobMaxWaitTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10, label = 'maximum')
                plt.plot(list(dictJobAvgWaitTime[numVehicles].keys()), list(dictJobAvgWaitTime[numVehicles].values()), marker = ".", linestyle = 'None', color = self.colorList[i], markersize=7, label = 'average')
            numVehicles = numVehicles + 1
        plt.xlabel('Index of the Job [Index]')
        plt.ylabel('Wait time of the production [s]')
        plt.legend(loc = "upper left", bbox_to_anchor=(1.05, 1.0))
        plt.tight_layout()
        if self.isShowFigure == True:
            plt.show(block=False)
        if self.isSaveFigure == True:
            plt.savefig(f'WaitTime_Job_{current_time}.png')


        dictEqpMinWaitTime = {}
        dictEqpMaxWaitTime = {}
        dictEqpAvgWaitTime = {}  
        for numVehicle, iterInfo in self.vehicleDictTotalWaitTimeEquipment.items():
            tempEqpMinTime = {}
            tempEqpMaxTime = {}
            tempEqpAvgTime = {}
            eqpCnt = {}
            for monteCarlo, eqpInfo in iterInfo.items():
                for eqpID, waitTime in eqpInfo.items():
                    if eqpID not in tempEqpMinTime:
                        tempEqpMinTime[eqpID] = 99999999999999999999
                    if eqpID not in tempEqpMaxTime:
                        tempEqpMaxTime[eqpID] = -99999999999999999999
                    if eqpID not in tempEqpAvgTime:
                        tempEqpAvgTime[eqpID] = 0
                    if eqpID not in eqpCnt:
                        eqpCnt[eqpID] = 0

                    if waitTime < tempEqpMinTime[eqpID]:
                        tempEqpMinTime[eqpID] = waitTime
                    if waitTime > tempEqpMaxTime[eqpID]:
                        tempEqpMaxTime[eqpID] = waitTime
                    tempEqpAvgTime[eqpID] = tempEqpAvgTime[eqpID] + waitTime
                    eqpCnt[eqpID] = eqpCnt[eqpID] + 1
            for eqpID, avgTime in tempEqpAvgTime.items():
                tempEqpAvgTime[eqpID] = avgTime/eqpCnt[eqpID]
            dictEqpMinWaitTime[numVehicle] = copy.deepcopy(tempEqpMinTime)
            dictEqpMaxWaitTime[numVehicle] = copy.deepcopy(tempEqpMaxTime)
            dictEqpAvgWaitTime[numVehicle] = copy.deepcopy(tempEqpAvgTime)
        plt.figure(figsize=(12, 10))
        plt.title("Wait time based on the equipment", fontsize=13)
        if self.isVehicleChange == True:
            numVehicles = 1
        else:
            numVehicles = self.numVehicle
        for i in range(len(self.vehicleDictTotalWaitTimeEquipment)):
            if self.isVehicleChange == True:
                plt.plot(list(dictEqpMinWaitTime[numVehicles].keys()), list(dictEqpMinWaitTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10)
                plt.plot(list(dictEqpMaxWaitTime[numVehicles].keys()), list(dictEqpMaxWaitTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10)
                plt.plot(list(dictEqpAvgWaitTime[numVehicles].keys()), list(dictEqpAvgWaitTime[numVehicles].values()), marker = ".", linestyle = 'None', color = self.colorList[i], markersize=7, label = "numVehicles: {}".format(numVehicles))
            else:
                plt.plot(list(dictEqpMinWaitTime[numVehicles].keys()), list(dictEqpMinWaitTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10, label = 'minimum')
                plt.plot(list(dictEqpMaxWaitTime[numVehicles].keys()), list(dictEqpMaxWaitTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10, label = 'maximum')
                plt.plot(list(dictEqpAvgWaitTime[numVehicles].keys()), list(dictEqpAvgWaitTime[numVehicles].values()), marker = ".", linestyle = 'None', color = self.colorList[i], markersize=7, label = 'average')             
            numVehicles = numVehicles + 1
        plt.xlabel('ID of the equipment [ID]')
        plt.ylabel('Wait time of the production [s]')
        plt.legend(loc = "upper left", bbox_to_anchor=(1.05, 1.0))
        plt.tight_layout()
        plt.xticks(rotation=90)
        if self.isShowFigure == True:
            plt.show(block=False)
        if self.isSaveFigure == True:
            plt.savefig(f'WaitTime_Equipment_{current_time}.png')


        ## utilizationTime & Rate ##
        dictAvgUtilTime = {}
        for numVehicle, iterInfo in self.vehicleVehicleActivationTime.items():
            tempSumAll = {}
            for monteCarlo, vehicleInfo in iterInfo.items():
                tempSumAll[monteCarlo] = 0
                for vehicleID, activationTime in vehicleInfo.items():
                    tempSumAll[monteCarlo] = tempSumAll[monteCarlo] + activationTime
                tempSumAll[monteCarlo] = tempSumAll[monteCarlo]/len(vehicleInfo)           
            dictAvgUtilTime[numVehicle] = copy.deepcopy(tempSumAll)
        dictMinAvgUtilTime = {}
        dictMaxAvgUtilTime = {}
        dictAvgAvgUtilTime = {}
        for numVehicle, iterInfo in dictAvgUtilTime.items():
            avgMinUtilTime = 99999999999999999999
            avgMaxUtilTime = -99999999999999999999
            avgAvgUtilTime = 0            
            for monteCarlo, avgUtilTime in iterInfo.items():
                if avgUtilTime < avgMinUtilTime:
                    avgMinUtilTime = avgUtilTime
                if avgUtilTime > avgMaxUtilTime:
                    avgMaxUtilTime = avgUtilTime
                avgAvgUtilTime = avgAvgUtilTime + avgUtilTime
            dictMinAvgUtilTime[numVehicle] = avgMinUtilTime
            dictMaxAvgUtilTime[numVehicle] = avgMaxUtilTime
            dictAvgAvgUtilTime[numVehicle] = avgAvgUtilTime/len(iterInfo)
        plt.figure(figsize=(12, 10))
        if self.isVehicleChange == True:
            plt.title("Utilization time based on number of the vehicle", fontsize=13)
        else:
            plt.title("Utilization time of the vehicle", fontsize=13)
        plt.plot(list(dictMinAvgUtilTime.keys()), list(dictMinAvgUtilTime.values()), marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10, label = 'minimum')
        plt.plot(list(dictMaxAvgUtilTime.keys()), list(dictMaxAvgUtilTime.values()), marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10, label = 'maximum')
        plt.plot(list(dictAvgAvgUtilTime.keys()), list(dictAvgAvgUtilTime.values()), marker = ".", linestyle = 'solid', color = self.colorList[0], markersize=7, label = 'average')
        plt.xlabel('Utilized number of the vehicle [ea]')
        plt.ylabel('Utilized time [s]')
        plt.legend(loc = "upper left", bbox_to_anchor=(1.05, 1.0))
        plt.tight_layout()
        if self.isShowFigure == True:
            plt.show(block=False)
        if self.isSaveFigure == True:
            plt.savefig(f'UtilTime_{current_time}.png')


        dictVehicleMinUtilTime = {}
        dictVehicleMaxUtilTime = {}
        dictVehicleAvgUtilTime = {}     
        for numVehicle, iterInfo in self.vehicleVehicleActivationTime.items():
            tempMinTime = {}
            tempMaxTime = {}
            tempAvgTime = {}
            for monteCarlo, vehicleInfo in iterInfo.items():
                for vehicleID, activatedTime in vehicleInfo.items():
                    if vehicleID not in tempMinTime:
                        tempMinTime[vehicleID] = 99999999999999999999
                    if vehicleID not in tempMaxTime:
                        tempMaxTime[vehicleID] = -99999999999999999999
                    if vehicleID not in tempAvgTime:
                        tempAvgTime[vehicleID] = 0
                    if activatedTime < tempMinTime[vehicleID]:
                        tempMinTime[vehicleID] = activatedTime
                    if activatedTime > tempMaxTime[vehicleID]:
                        tempMaxTime[vehicleID] = activatedTime
                    tempAvgTime[vehicleID] = tempAvgTime[vehicleID] + activatedTime
            for vehicleID, summedActivationTime in tempAvgTime.items():
                tempAvgTime[vehicleID] = summedActivationTime/len(iterInfo)
            dictVehicleMinUtilTime[numVehicle] = copy.deepcopy(tempMinTime)
            dictVehicleMaxUtilTime[numVehicle] = copy.deepcopy(tempMaxTime)
            dictVehicleAvgUtilTime[numVehicle] = copy.deepcopy(tempAvgTime)
        plt.figure(figsize=(12, 10))
        plt.title("Utilization time of the vehicle", fontsize=13)
        if self.isVehicleChange == True:
            numVehicles = 1
        else:
            numVehicles = self.numVehicle
        for i in range(len(self.vehicleVehicleActivationTime)):
            if self.isVehicleChange == True:
                plt.plot(list(dictVehicleMinUtilTime[numVehicles].keys()), list(dictVehicleMinUtilTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10)
                plt.plot(list(dictVehicleMaxUtilTime[numVehicles].keys()), list(dictVehicleMaxUtilTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10)
                plt.plot(list(dictVehicleAvgUtilTime[numVehicles].keys()), list(dictVehicleAvgUtilTime[numVehicles].values()), marker = ".", linestyle = 'None', color = self.colorList[i], markersize=7, label = "numVehicles: {}".format(numVehicles))
            else:
                plt.plot(list(dictVehicleMinUtilTime[numVehicles].keys()), list(dictVehicleMinUtilTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10, label = 'minimum')
                plt.plot(list(dictVehicleMaxUtilTime[numVehicles].keys()), list(dictVehicleMaxUtilTime[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10, label = 'maximum')
                plt.plot(list(dictVehicleAvgUtilTime[numVehicles].keys()), list(dictVehicleAvgUtilTime[numVehicles].values()), marker = ".", linestyle = 'None', color = self.colorList[i], markersize=7, label = 'average')             
            numVehicles = numVehicles + 1
        plt.xlabel('ID of the vehicle [ID]')
        plt.xticks(rotation=90)
        plt.ylabel('Utilized time [s]')
        plt.legend(loc = "upper left", bbox_to_anchor=(1.05, 1.0))
        plt.tight_layout()
        if self.isShowFigure == True:
            plt.show(block=False)
        if self.isSaveFigure == True:
            plt.savefig(f'UtilTime_Vehicle_{current_time}.png')

        
        dictAvgUtilRate = {}
        for numVehicle, iterInfo in self.vehicleVehicleUtilizationRates.items():
            tempSumAll = {}
            for monteCarlo, vehicleInfo in iterInfo.items():
                tempSumAll[monteCarlo] = 0
                for vehicleID, utilRate in vehicleInfo.items():
                    tempSumAll[monteCarlo] = tempSumAll[monteCarlo] + utilRate
                tempSumAll[monteCarlo] = tempSumAll[monteCarlo]/len(vehicleInfo)           
            dictAvgUtilRate[numVehicle] = copy.deepcopy(tempSumAll)
        dictMinAvgUtilRate = {}
        dictMaxAvgUtilRate = {}
        dictAvgAvgUtilRate = {}
        for numVehicle, iterInfo in dictAvgUtilRate.items():
            avgMinUtilRate = 99999999999999999999
            avgMaxUtilRate = -99999999999999999999
            avgAvgUtilRate = 0            
            for monteCarlo, avgUtilRate in iterInfo.items():
                if avgUtilRate < avgMinUtilRate:
                    avgMinUtilRate = avgUtilRate
                if avgUtilRate > avgMaxUtilRate:
                    avgMaxUtilRate = avgUtilRate
                avgAvgUtilRate = avgAvgUtilRate + avgUtilRate
            dictMinAvgUtilRate[numVehicle] = avgMinUtilRate
            dictMaxAvgUtilRate[numVehicle] = avgMaxUtilRate
            dictAvgAvgUtilRate[numVehicle] = avgAvgUtilRate/len(iterInfo)
        plt.figure(figsize=(12, 10))
        if self.isVehicleChange == True:
            plt.title("Utilization rate based on number of the vehicle", fontsize=13)
        else:
            plt.title("Utilization rate of the vehicle", fontsize=13)
        plt.plot(list(dictMinAvgUtilRate.keys()), list(dictMinAvgUtilRate.values()), marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10, label = 'minimum')
        plt.plot(list(dictMaxAvgUtilRate.keys()), list(dictMaxAvgUtilRate.values()), marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10, label = 'maximum')
        plt.plot(list(dictAvgAvgUtilRate.keys()), list(dictAvgAvgUtilRate.values()), marker = ".", linestyle = 'solid', color = self.colorList[0], markersize=7, label = 'average')
        plt.xlabel('Utilized number of the vehicle [ea]')
        plt.ylabel('Utilized rate [%]')
        plt.legend(loc = "upper left", bbox_to_anchor=(1.05, 1.0))
        plt.tight_layout()
        if self.isShowFigure == True:
            plt.show(block=False)
        if self.isSaveFigure == True:
            plt.savefig(f'UtilRate_{current_time}.png')


        dictVehicleMinUtilRate = {}
        dictVehicleMaxUtilRate = {}
        dictVehicleAvgUtilRate = {}     
        for numVehicle, iterInfo in self.vehicleVehicleUtilizationRates.items():
            tempMinRate = {}
            tempMaxRate = {}
            tempAvgRate = {}
            for monteCarlo, vehicleInfo in iterInfo.items():
                for vehicleID, utilRate in vehicleInfo.items():
                    if vehicleID not in tempMinRate:
                        tempMinRate[vehicleID] = 99999999999999999999
                    if vehicleID not in tempMaxRate:
                        tempMaxRate[vehicleID] = -99999999999999999999
                    if vehicleID not in tempAvgRate:
                        tempAvgRate[vehicleID] = 0
                    if utilRate < tempMinRate[vehicleID]:
                        tempMinRate[vehicleID] = utilRate
                    if utilRate > tempMaxRate[vehicleID]:
                        tempMaxRate[vehicleID] = utilRate
                    tempAvgRate[vehicleID] = tempAvgRate[vehicleID] + utilRate
            for vehicleID, summedUtilizedRate in tempAvgRate.items():
                tempAvgRate[vehicleID] = summedUtilizedRate/len(iterInfo)
            dictVehicleMinUtilRate[numVehicle] = copy.deepcopy(tempMinRate)
            dictVehicleMaxUtilRate[numVehicle] = copy.deepcopy(tempMaxRate)
            dictVehicleAvgUtilRate[numVehicle] = copy.deepcopy(tempAvgRate)
        plt.figure(figsize=(12, 10))
        plt.title("Utilization rate of the vehicle", fontsize=13)
        if self.isVehicleChange == True:
            numVehicles = 1
        else:
            numVehicles = self.numVehicle
        for i in range(len(self.vehicleVehicleUtilizationRates)):
            if self.isVehicleChange == True:
                plt.plot(list(dictVehicleMinUtilRate[numVehicles].keys()), list(dictVehicleMinUtilRate[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10)
                plt.plot(list(dictVehicleMaxUtilRate[numVehicles].keys()), list(dictVehicleMaxUtilRate[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10)
                plt.plot(list(dictVehicleAvgUtilRate[numVehicles].keys()), list(dictVehicleAvgUtilRate[numVehicles].values()), marker = ".", linestyle = 'None', color = self.colorList[i], markersize=7, label = "numVehicles: {}".format(numVehicles))
            else:
                plt.plot(list(dictVehicleMinUtilRate[numVehicles].keys()), list(dictVehicleMinUtilRate[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10, label = 'minimum')
                plt.plot(list(dictVehicleMaxUtilRate[numVehicles].keys()), list(dictVehicleMaxUtilRate[numVehicles].values()), marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10, label = 'maximum')
                plt.plot(list(dictVehicleAvgUtilRate[numVehicles].keys()), list(dictVehicleAvgUtilRate[numVehicles].values()), marker = ".", linestyle = 'None', color = self.colorList[i], markersize=7, label = 'average')           
            numVehicles = numVehicles + 1
        plt.xlabel('ID of the vehicle [ID]')
        plt.xticks(rotation=90)
        plt.ylabel('Utilized rate [%]')
        plt.legend(loc = "upper left", bbox_to_anchor=(1.05, 1.0))
        plt.tight_layout()
        if self.isShowFigure == True:
            plt.show(block=False)
        if self.isSaveFigure == True:
            plt.savefig(f'UtilRate_Vehicle_{current_time}.png')


        ## simTime ##
        dictVehicleMinSimTime = {}
        dictVehicleMaxSimTime = {}
        dictVehicleAvgSimTime = {}
        for numVehicle, iterInfo in self.vehicleSimTime.items():
            tempMinSimTime = 99999999999999999999
            tempMaxSimTime = -99999999999999999999
            tempAvgSimTime = 0
            for monteCarlo, simTime in iterInfo.items():
                if simTime < tempMinSimTime:
                    tempMinSimTime = simTime
                if simTime > tempMaxSimTime:
                    tempMaxSimTime = simTime
                tempAvgSimTime = tempAvgSimTime + simTime
            tempAvgSimTime = tempAvgSimTime/len(iterInfo)
            dictVehicleMinSimTime[numVehicle] = copy.deepcopy(tempMinSimTime)
            dictVehicleMaxSimTime[numVehicle] = copy.deepcopy(tempMaxSimTime)
            dictVehicleAvgSimTime[numVehicle] = copy.deepcopy(tempAvgSimTime)
        plt.figure(figsize=(12, 10))
        plt.title("Simulated time", fontsize=13)
        if self.isVehicleChange == True:
            numVehicles = 1
        else:
            numVehicles = self.numVehicle
        for i in range(len(self.vehicleSimTime)):
            if self.isVehicleChange == True:
                if i == 0:
                    plt.plot(numVehicles, dictVehicleMinSimTime[numVehicles], marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10, label = 'minimum')
                    plt.plot(numVehicles, dictVehicleMaxSimTime[numVehicles], marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10, label = 'maximum')
                    plt.plot(numVehicles, dictVehicleAvgSimTime[numVehicles], marker = ".", linestyle = 'None', color = self.colorList[0], markersize=7, label = 'average')
                else:
                    plt.plot(numVehicles, dictVehicleMinSimTime[numVehicles], marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10)
                    plt.plot(numVehicles, dictVehicleMaxSimTime[numVehicles], marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10)
                    plt.plot(numVehicles, dictVehicleAvgSimTime[numVehicles], marker = ".", linestyle = 'None', color = self.colorList[0], markersize=7)
            else:
                plt.plot(numVehicles, dictVehicleMinSimTime[numVehicles], marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10, label = 'minimum')
                plt.plot(numVehicles, dictVehicleMaxSimTime[numVehicles], marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10, label = 'maximum')
                plt.plot(numVehicles, dictVehicleAvgSimTime[numVehicles], marker = ".", linestyle = 'None', color = self.colorList[i], markersize=7, label = 'average') 
            numVehicles = numVehicles + 1
        plt.xlabel('Utilized number of the vehicle [ea]')
        plt.ylabel('Simulated time [s]')
        plt.legend(loc = "upper left", bbox_to_anchor=(1.05, 1.0))
        plt.tight_layout()
        if self.isShowFigure == True:
            plt.show(block=False)
        if self.isSaveFigure == True:
            plt.savefig(f'SimulationTime_{current_time}.png')


        ## go Command ##
        dictVehicleMinGoCmd = {}
        dictVehicleMaxGoCmd = {}
        dictVehicleAvgGoCmd = {}
        for numVehicle, iterInfo in self.vehicleGoCmd.items():
            tempMinGoCmd = 99999999999999999999
            tempMaxGoCmd = -99999999999999999999
            tempAvgGoCmd = 0
            for monteCarlo, goCmd in iterInfo.items():
                if goCmd < tempMinGoCmd:
                    tempMinGoCmd = goCmd
                if goCmd > tempMaxGoCmd:
                    tempMaxGoCmd = goCmd
                tempAvgGoCmd = tempAvgGoCmd + goCmd
            tempAvgGoCmd = tempAvgGoCmd/len(iterInfo)
            dictVehicleMinGoCmd[numVehicle] = copy.deepcopy(tempMinGoCmd)
            dictVehicleMaxGoCmd[numVehicle] = copy.deepcopy(tempMaxGoCmd)
            dictVehicleAvgGoCmd[numVehicle] = copy.deepcopy(tempAvgGoCmd)
        plt.figure(figsize=(12, 10))
        plt.title("Go command counts", fontsize=13)
        if self.isVehicleChange == True:
            numVehicles = 1
        else:
            numVehicles = self.numVehicle
        for i in range(len(self.vehicleGoCmd)):
            if self.isVehicleChange == True:
                if i == 0:
                    plt.plot(numVehicles, dictVehicleMinGoCmd[numVehicles], marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10, label = 'minimum')
                    plt.plot(numVehicles, dictVehicleMaxGoCmd[numVehicles], marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10, label = 'maximum')
                    plt.plot(numVehicles, dictVehicleAvgGoCmd[numVehicles], marker = ".", linestyle = 'None', color = self.colorList[0], markersize=7, label = 'average') 
                else:
                    plt.plot(numVehicles, dictVehicleMinGoCmd[numVehicles], marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10)
                    plt.plot(numVehicles, dictVehicleMaxGoCmd[numVehicles], marker = "_", linestyle = 'None', color = self.colorList[0], markersize=10)
                    plt.plot(numVehicles, dictVehicleAvgGoCmd[numVehicles], marker = ".", linestyle = 'None', color = self.colorList[0], markersize=7)
            else:
                plt.plot(numVehicles, dictVehicleMinGoCmd[numVehicles], marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10, label = 'minimum')
                plt.plot(numVehicles, dictVehicleMaxGoCmd[numVehicles], marker = "_", linestyle = 'None', color = self.colorList[i], markersize=10, label = 'maximum')
                plt.plot(numVehicles, dictVehicleAvgGoCmd[numVehicles], marker = ".", linestyle = 'None', color = self.colorList[i], markersize=7, label = 'average') 
            numVehicles = numVehicles + 1
        plt.xlabel('Utilized number of the vehicle [ea]')
        plt.ylabel('Go commands [ea]')
        plt.legend(loc = "upper left", bbox_to_anchor=(1.05, 1.0))
        plt.tight_layout()
        if self.isShowFigure == True:
            plt.show(block=False)
        if self.isSaveFigure == True:
            plt.savefig(f'GoCommand_{current_time}.png')


        ## processTime ##
        lstEquipmentID = list(self.globalVar.getEquipmentInfo().keys())
        dictEquipmentProcessTime = {}
        for numVehicle, iterInfo in self.vehicleDictEquipmentTotalProcessTime.items():
            sumAll = {}
            cntAll = {}            
            for monteCarlo, equipmentInfo in iterInfo.items():
                for eqpID, processTime in equipmentInfo.items():
                    if eqpID not in sumAll:
                        sumAll[eqpID] = 0
                        cntAll[eqpID] = 0
                    sumAll[eqpID] = sumAll[eqpID] + processTime
                    cntAll[eqpID] = cntAll[eqpID] + 1
            for eqpID, processTime in sumAll.items():
                sumAll[eqpID] = processTime/cntAll[eqpID]
            dictEquipmentProcessTime[numVehicle] = sumAll
        finalDictProcessTime = {}
        for numVehicle, eqpInfo in dictEquipmentProcessTime.items():
            finalDictProcessTime[numVehicle] = {}
            for equipmentID in lstEquipmentID:
                if equipmentID in eqpInfo:
                    finalDictProcessTime[numVehicle][equipmentID] = eqpInfo[equipmentID]
                else:
                    finalDictProcessTime[numVehicle][equipmentID] = 0
        plt.figure(figsize=(12, 10))
        plt.title("Average Equipment process time by vehicles", fontsize=13)
        if self.isVehicleChange == True:
            numVehicles = 1
        else:
            numVehicles = self.numVehicle
        for i in range(len(self.vehicleDictEquipmentTotalProcessTime)):
            if self.isVehicleChange == True:
                plt.plot(list(finalDictProcessTime[numVehicles].keys()), list(finalDictProcessTime[numVehicles].values()), marker = ".", linestyle = 'solid', color = self.colorList[i], markersize=1, label = "numVehicles: {}".format(numVehicles))
            else:
                plt.plot(list(finalDictProcessTime[numVehicles].keys()), list(finalDictProcessTime[numVehicles].values()), marker = ".", linestyle = 'solid', color = self.colorList[i], markersize=1, label = "vehicleIndex: {}".format(numVehicles))
            numVehicles = numVehicles + 1
        plt.xlabel('ID of the equipment [ID]')
        plt.ylabel('Process time of the equipment [s]')
        plt.legend(loc = "upper left", bbox_to_anchor=(1.05, 1.0))
        plt.tight_layout()
        plt.xticks(rotation=90)
        if self.isShowFigure == True:
            plt.show(block=False)
        if self.isSaveFigure == True:
            plt.savefig(f'Average_ProcessTime_{current_time}.png')

            
        ## node usage ##
        dictAvgNodeUsage = {}
        dictMinNodeCnts = {}
        dictMaxNodeCnts = {}
        dictGradient = {}
        for numVehicle, iterInfo in self.vehicleDictNodeUsage.items():
            dictMinNodeCnts[numVehicle] = 99999999999999999999
            dictMaxNodeCnts[numVehicle] = -99999999999999999999
            sumAll = {}
            sumCnt = {}
            for monteCarlo, nodeInfo in iterInfo.items():
                for nodeID, usageCnt in nodeInfo.items():
                    if nodeID not in sumAll:
                        sumAll[nodeID] = 0
                        sumCnt[nodeID] = 0
                    sumAll[nodeID] = sumAll[nodeID] + usageCnt
                    sumCnt[nodeID] = sumCnt[nodeID] + self.vehicleDictNodeCounts[numVehicle][monteCarlo][nodeID]
            for nodeID, summedUsageCnt in sumAll.items():
                if summedUsageCnt != 0:
                    sumAll[nodeID] = summedUsageCnt/sumCnt[nodeID]
                if sumAll[nodeID] < dictMinNodeCnts[numVehicle]:
                    dictMinNodeCnts[numVehicle] = sumAll[nodeID]
                if sumAll[nodeID] > dictMaxNodeCnts[numVehicle]:
                    dictMaxNodeCnts[numVehicle] = sumAll[nodeID]
            dictAvgNodeUsage[numVehicle] = sumAll

        for numVehicle, value in dictAvgNodeUsage.items():
            compare = (dictMaxNodeCnts[numVehicle] - dictMinNodeCnts[numVehicle])/10
            dictGradient[numVehicle] = list(np.arange(dictMinNodeCnts[numVehicle], dictMaxNodeCnts[numVehicle] + compare, compare))
            plt.figure(figsize=(12, 10))
            plt.title("Average Node Usage Plots v{}".format(numVehicle), fontsize=13)
            for nodeID, cnts in value.items():
                coordinates = self.globalVar.getCoordinatesByNodeID(nodeID)
                if cnts <= dictGradient[numVehicle][0]:
                    color = self.gradientColorList[0]
                elif cnts <= dictGradient[numVehicle][1]:
                    color = self.gradientColorList[1]
                elif cnts <= dictGradient[numVehicle][2]:
                    color = self.gradientColorList[2]
                elif cnts <= dictGradient[numVehicle][3]:
                    color = self.gradientColorList[3]
                elif cnts <= dictGradient[numVehicle][4]:
                    color = self.gradientColorList[4]
                elif cnts <= dictGradient[numVehicle][5]:
                    color = self.gradientColorList[5]
                elif cnts <= dictGradient[numVehicle][6]:
                    color = self.gradientColorList[6]
                elif cnts <= dictGradient[numVehicle][7]:
                    color = self.gradientColorList[7]
                elif cnts <= dictGradient[numVehicle][8]:
                    color = self.gradientColorList[8]
                elif cnts <= dictGradient[numVehicle][9]:
                    color = self.gradientColorList[9]
                elif cnts <= dictGradient[numVehicle][10]:
                    color = self.gradientColorList[10]                
                plt.plot(coordinates[0], coordinates[1], marker = ".", linestyle = 'None', color = color, markersize=1)
            patchList = []
            for i in range(len(self.gradientColorList)):
                patchList.append(mpatches.Patch(color = self.gradientColorList[i], label = 'level {}'.format(i+1)))
            plt.legend(handles = patchList, loc = "upper left", bbox_to_anchor=(1.05, 1.0))
            plt.xlabel('X-Coordinate')
            plt.ylabel('Y-Coordinate')       
            plt.gca().invert_xaxis()
            plt.gca().invert_yaxis()            
            plt.tight_layout()
            if self.isShowFigure == True:
                plt.show(block=False)
            if self.isSaveFigure == True:
                plt.savefig(f'nodeMapUsagePlots_v{numVehicle}_{current_time}.png')

