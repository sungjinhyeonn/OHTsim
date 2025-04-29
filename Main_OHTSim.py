from SimulationEngine.SimulationEngine import SimulationEngine
from Environment.EnvironmentLoader import EnvironmentLoader
from Models.OHTSimModel import OHTSimModel
# from Models.RLModel.DeepSARSA import DeepSARSAgent
from Visualizer.Visualizer import Visualizer
import time
import numpy as np
import pylab
from pathFinding.time_tracker import reset_timers, set_current_iteration

## Load JSON setup Files ##
path = "./JSON/"
files = ["map", "processInfo", "vehicleInfo", "log", "setup"]
objConfiguration = EnvironmentLoader(path, files).getConfiguration()

## Mode selection load ##
playBackMode = objConfiguration.getConfiguration("playBackMode")
simulationMode = objConfiguration.getConfiguration("simulationMode")
RLTrainMode = objConfiguration.getConfiguration("RLTrainMode")

## simulation setups load ##
renderTime = objConfiguration.getConfiguration("renderTime")
isVehicleChange = objConfiguration.getConfiguration("isVehicleChange")
monteCarlo = objConfiguration.getConfiguration("monteCarlo")
numVehicles = objConfiguration.getConfiguration("numVehicles")
totalSimStart = 0

## for simulation ##
if simulationMode == True:
    # 시뮬레이션 시작 전에 타이머 초기화
    reset_timers()

    if isVehicleChange == True:
        for numVehicle in range(1, numVehicles + 1):
            if monteCarlo == 0:
                monteCarlo = 1
            for i in range(1, monteCarlo + 1):
                # 현재 반복 번호와 차량 수 설정
                set_current_iteration(i, numVehicle)
                
                if i == 1 and numVehicle == 1:
                    objModels = OHTSimModel(objConfiguration, path, i, monteCarlo, None, None, renderTime, numVehicle, numVehicles, isVehicleChange, simulationMode, playBackMode, RLTrainMode)
                else:
                    objModels = OHTSimModel(objConfiguration, path, i, monteCarlo, objModels.prevAnalysisModel, objModels.objLogger, renderTime, numVehicle, numVehicles, isVehicleChange, simulationMode, playBackMode, RLTrainMode)
                engine = SimulationEngine()
                engine.setOutmostModel(objModels)
                start = time.time()
                if i == 1 and numVehicle == 1:
                    totalSimStart = start
                print("\nSimulation Start numVehicle::#{}/{} | MonteCarlo::#{}/{}".format(numVehicle, numVehicles, i, monteCarlo))
                engine.run(maxTime=999999999)
                print("Simulation End numVehicle::#{}/{} | MonteCarlo::#{}/{}".format(numVehicle, numVehicles, i, monteCarlo))
                print("time: {}[s]".format(time.time()-start))
    else:
        if monteCarlo == 0:
            monteCarlo = 1
        for i in range(1, monteCarlo + 1):
            # 현재 반복 번호와 차량 수 설정
            set_current_iteration(i, numVehicles)
            
            if i == 1:
                objModels = OHTSimModel(objConfiguration, path, i, monteCarlo, None, None, renderTime, numVehicles, numVehicles, isVehicleChange, simulationMode, playBackMode, RLTrainMode)
            else:
                objModels = OHTSimModel(objConfiguration, path, i, monteCarlo, objModels.prevAnalysisModel, objModels.objLogger, renderTime, numVehicles, numVehicles, isVehicleChange, simulationMode, playBackMode, RLTrainMode)
            engine = SimulationEngine()
            engine.setOutmostModel(objModels)
            start = time.time()
            if i == 1:
                totalSimStart = start
            print("\nSimulation Start numVehicle::#{} | MonteCarlo::#{}/{}".format(numVehicles, i, monteCarlo))
            engine.run(maxTime=999999999)
            print("Simulation End numVehicle::#{} | MonteCarlo::#{}/{}".format(numVehicles, i, monteCarlo))
            print("time: {}[s]".format(time.time()-start))        
    print("\ntotal time: {}[s]".format(time.time()-totalSimStart))
    
## for play back ##
elif playBackMode == True:
    playBackModel = Visualizer("Visualizer", None, None, None, None, path, 1, renderTime, simulationMode, playBackMode, RLTrainMode)
    playBackModel.runVisualizerAlone(path)
    