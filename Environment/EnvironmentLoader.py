from SimulationEngine.Utility.Configurator import Configurator
import json

class EnvironmentLoader:
    def __init__(self, strPath, lstFileNames):
        objConfiguration = Configurator()

        for fName in lstFileNames:
            strFileName = strPath + fName + ".json"
            print("\nLoading "+ strFileName)
            
            with open(strFileName) as json_file:
                objData = json.load(json_file)
                if objData["fileName"] == "map":
                    objData["railList"]
                    objConfiguration.addConfiguration("railList", objData["railList"])
                    objConfiguration.addConfiguration("nodeList", objData["nodeList"])
                    objConfiguration.addConfiguration("equipmentInfo", objData["equipmentInfo"])
                elif objData["fileName"] == "processInfo":
                    objConfiguration.addConfiguration("seqInfo", objData["seqInfo"])
                    objConfiguration.addConfiguration("performanceInfo", objData["performanceInfo"])
                elif objData["fileName"] == "vehicleInfo":
                    objConfiguration.addConfiguration("vehicleInfo", objData["vehicleInfo"])
                elif objData["fileName"] == "log":
                    objConfiguration.addConfiguration("logVehicle", objData["logVehicle"])
                    objConfiguration.addConfiguration("logPath", objData["logPath"])
                elif objData["fileName"] == "setup":
                    objConfiguration.addConfiguration("monteCarlo", objData["monteCarlo"])
                    objConfiguration.addConfiguration("passingScore", objData["passingScore"])
                    objConfiguration.addConfiguration("yieldRange", objData["yieldRange"])
                    objConfiguration.addConfiguration("isVehicleChange", objData["isVehicleChange"])
                    objConfiguration.addConfiguration("numVehicles", objData["numVehicles"])
                    objConfiguration.addConfiguration("numJob", objData["numJob"])
                    objConfiguration.addConfiguration("jobStart", objData["jobStart"])
                    objConfiguration.addConfiguration("jobEnd", objData["jobEnd"])
                    objConfiguration.addConfiguration("isLogOn", objData["isLogOn"])
                    objConfiguration.addConfiguration("isAnalysisLogOn", objData["isAnalysisLogOn"])
                    objConfiguration.addConfiguration("isTerminalOn", objData["isTerminalOn"])
                    objConfiguration.addConfiguration("isVisualizerOn", objData["isVisualizerOn"])
                    objConfiguration.addConfiguration("isVisualizerLogOn", objData["isVisualizerLogOn"])
                    objConfiguration.addConfiguration("playBackMode", objData["playBackMode"])
                    objConfiguration.addConfiguration("isShowFigure", objData["isShowFigure"])
                    objConfiguration.addConfiguration("isSaveFigure", objData["isSaveFigure"])             
                    objConfiguration.addConfiguration("renderTime", objData["renderTime"])
                    objConfiguration.addConfiguration("simulationMode", objData["simulationMode"])
                    objConfiguration.addConfiguration("isMakeRlEnv", objData["isMakeRlEnv"])
                    objConfiguration.addConfiguration("RLTrainMode", objData["RLTrainMode"])
                else:
                    print("JSON FILE ERROR\n")
        
        self.objConfiguration = objConfiguration

    def getConfiguration(self):
        return self.objConfiguration