from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
import tkinter as tk
import time
import threading
import json
import random
import math
from pathFinding.dijkstra import dijkstraRL

class Visualizer(DEVSAtomicModel, tk.Tk):
    def __init__(self, strID, globalVar, objLogger, isVisualizerOn, isVisualizerLogOn, jsonPath, iter, renderTime, simulationMode, playBackMode, RLTrainMode):
        if simulationMode == True:
            super().__init__(strID)
        else:
            tk.Tk.__init__(self)
        self.iter = iter
        self.renderTime = renderTime
        self.vehicleJobCarry = {}
        self.jsonPath = jsonPath

        ## simulation 모드인 경우 ##
        if simulationMode == True:
            # set Global Variables
            self.globalVar = globalVar
            self.objLogger = objLogger

            # states
            self.stateList = ["DRAW"]
            self.state = self.stateList[0]

            # input Ports
            self.addInputPort("job")
            self.addInputPort("informDone")
            self.addInputPort("ownPos")
            self.addInputPort("arrival")
            self.addInputPort("liftDown")
            self.addInputPort("jobExchange")
            self.addInputPort("liftUp")
            self.addInputPort("analyzeComplete")

            # self variables
            self.addStateVariable("strID", strID)
            
            ## visulizer
            self.isSimulationEnd = False
            self.isVisualizerOn = isVisualizerOn
            self.isVisualizerLogOn = isVisualizerLogOn
            self.objVehicles = {}
            self.objNodes = {}
            self.objNodesState = {}
            self.objNodesText = {}
            self.simulationTimeText = -1
            self.timeEvent = {}             ## key = time / value = [ [portName, equipmentNodeID, posX, posY, jobID]                    job -> creation
                                            ##                      or [portName, equipmentNodeID, posX, posY, jobID]                   informDone -> done
                                            ##                      or [portName, vehicleID, posX, posY]                                ownPos -> move
                                            ##                      or [portName, vehicleID, posX, posY]                                arrival -> move
                                            ##                      or [portName, vehicleID, posX, posY, equipmentNodeID, posX, posY]   liftDown -> lift down
                                            ##                      or [portName, equipmentNodeID, posX, posY, vehicleID, posX, posY]   jobExchange -> load/unload
                                            ##                      or [portName, vehicleID, posX, posY]                                liftUp -> lift up
            if self.isVisualizerOn == True:
                t = threading.Thread(target = self.runVisualizerSim)
                t.start()
        elif playBackMode == True:
            self.totalNode = {}
            self.eqpmentID = {}
        elif RLTrainMode == True:
            ## raw values ##
            self.maxEpisode = 0
            self.maxSteps = 0
            self.cntSteps = 0            
            self.actionSpace = [0, 1]                    # 0: go / 1: turn   
            self.totalNode = {}
            self.eqpmentInfo = {}
            self.processConnection = {}
            self.nodeConnection = {}
            self.coordConnection = {}
            self.toFunctionCoordinates = {}         # from to pair:: eqp to eqp
            self.fromStartCoordintes = []           # from Start Coordiates :: all nodes
            self.eqpmentProcessInfo = {}            # from End Coordinates :: all eqp
            self.loadMapData()                      # load RL train Env above
            self.objNodes = {}                      # nodes
            self.adjustNum = 0
            self.canvas = self.buildCanvas()        # geometry, title, height, width, nodes, equipments
            self.objAgent = {}                      # agent
            self.objGoal = {}
            self.objSubGoal = []
            self.rewardCoords = []
            self.fromProcessType = None
            chosenScenario = self.randomFunction(0)
            self.setAgent(chosenScenario)           # set agent start coordinates
            self.setGoal(chosenScenario)            # set agent goal coordinates
            self.setInitAgentState()
            self.shortestPath = dijkstraRL(self.objAgent["state"], self.objGoal["state"], self.coordConnection)
            self.checkRewardCoords()
            self.setSubGoal()

    def funcExternalTransition(self, strPort, objEvent):
        if strPort == "job":
            # objEvent = [equipmentID, jobID]
            receivedTime = self.getTime()
            eqpInfo = self.globalVar.getEquipmentInfoByID(objEvent[0])
            if receivedTime not in self.timeEvent:
                self.timeEvent[receivedTime] = [[strPort] + [eqpInfo.strEquipmentNodeID] + eqpInfo.lstCoordinates + [objEvent[1]]]
            else:
                self.timeEvent[receivedTime].append([strPort] + [eqpInfo.strEquipmentNodeID] + eqpInfo.lstCoordinates + [objEvent[1]])
            self.continueTimeAdvance()
            return True
        elif strPort == "informDone":
            # objEvent = [equipmentID, jobID]
            receivedTime = self.getTime()
            eqpInfo = self.globalVar.getEquipmentInfoByID(objEvent[0])
            if receivedTime not in self.timeEvent:
                self.timeEvent[receivedTime] = [[strPort] + [eqpInfo.strEquipmentNodeID] + eqpInfo.lstCoordinates + [objEvent[1]]]
            else:
                self.timeEvent[receivedTime].append([strPort] + [eqpInfo.strEquipmentNodeID] + eqpInfo.lstCoordinates + [objEvent[1]])
            self.continueTimeAdvance()
            return True
        elif strPort == "ownPos":
            # objEvent = [vehicleID, posX, posY]
            receivedTime = self.getTime()
            if receivedTime not in self.timeEvent:
                self.timeEvent[receivedTime] = [[strPort] + objEvent]
            else:
                self.timeEvent[receivedTime].append([strPort] + objEvent)
            self.continueTimeAdvance()
            return True
        elif strPort == "arrival":
            # objEvent = [vehicleID, posX, posY]
            receivedTime = self.getTime()
            if receivedTime not in self.timeEvent:
                self.timeEvent[receivedTime] = [[strPort] + objEvent]
            else:
                self.timeEvent[receivedTime].append([strPort] + objEvent)
            self.continueTimeAdvance()
            return True
        elif strPort == "liftDown":
            # objEvent = [vehicleID, equipmentNodeID]
            receivedTime = self.getTime()
            vehicleInfo = self.globalVar.getVehicleInfoByID(objEvent[0])
            eqpInfo = self.globalVar.getEquipmentInfoByNodeID(objEvent[1])
            if receivedTime not in self.timeEvent:
                self.timeEvent[receivedTime] = [[strPort] + [objEvent[0]] + vehicleInfo.lstCoordinates + [objEvent[1]] + eqpInfo.lstCoordinates]
            else:
                self.timeEvent[receivedTime].append([strPort] + [objEvent[0]] + vehicleInfo.lstCoordinates + [objEvent[1]] + eqpInfo.lstCoordinates)
            self.continueTimeAdvance()
            return True
        elif strPort == "jobExchange":
            # objEvent = [equipmentID, vehicleID]
            receivedTime = self.getTime()
            eqpInfo = self.globalVar.getEquipmentInfoByID(objEvent[0])
            vehicleInfo = self.globalVar.getVehicleInfoByID(objEvent[1])
            if receivedTime not in self.timeEvent:
                self.timeEvent[receivedTime] = [[strPort] + [eqpInfo.strEquipmentNodeID] + eqpInfo.lstCoordinates + [objEvent[1]] + vehicleInfo.lstCoordinates]
            else:
                self.timeEvent[receivedTime].append([strPort] + [eqpInfo.strEquipmentNodeID] + eqpInfo.lstCoordinates + [objEvent[1]] + vehicleInfo.lstCoordinates)
            self.continueTimeAdvance()
            return True 
        elif strPort == "liftUp":
            # objEvent = vehicleID
            receivedTime = self.getTime()
            vehicleInfo = self.globalVar.getVehicleInfoByID(objEvent)
            if receivedTime not in self.timeEvent:
                self.timeEvent[receivedTime] = [[strPort] + [objEvent] + vehicleInfo.lstCoordinates]
            else:
                self.timeEvent[receivedTime].append([strPort] + [objEvent] + vehicleInfo.lstCoordinates)
            self.continueTimeAdvance()
            return True
        elif strPort == "analyzeComplete":
            self.isSimulationEnd = objEvent
            if self.isVisualizerLogOn == True:
                self.logTimeResults()
            self.continueTimeAdvance()
            return True
        else:
            print("ERROR at Visualizer ExternalTransition: #{}".format(self.getStateValue("strID")))
            print("inputPort: {}".format(strPort))
            print("CurrentState: {}".format(self.state))
            return False

    def funcOutput(self):
        print("ERROR at Visualizer OutPut: #{}".format(self.getStateValue("strID")))
        print("CurrentState: {}".format(self.state))
        return False

    def funcInternalTransition(self):
        print("ERROR at Visualizer InternalTransition: #{}".format(self.getStateValue("strID")))
        print("CurrentState: {}".format(self.state))
        return False

    def funcTimeAdvance(self):
        if self.state == "DRAW":
            return 999999999999

    def runVisualizerSim(self):
        root = tk.Tk()
        ## calculate maximum display size ##
        widthParameter = root.winfo_screenwidth()
        heightParameter = root.winfo_screenheight()
        adjustNum = 0
        maxWidth = 0
        maxHeight = 0                
        self.totalNode = self.globalVar.getTotalNodeInfo()

        minX = 9999999999
        minY = 9999999999
        maxX = -9999999999
        maxY = -9999999999
        for key, value in self.totalNode.items():
            coordX = value.lstCoordinates[0]
            coordY = value.lstCoordinates[1]
            if minX > coordX:
                minX = coordX
            if maxX < coordX:
                maxX = coordX
            if minY > coordY:
                minY = coordY
            if maxY < coordY:
                maxY = coordY
        tempX = widthParameter//maxX
        tempY = heightParameter//maxY
        
        if tempY < tempX:
            adjustNum = tempY
        else:
            adjustNum = tempX

        maxWidth = int(round(maxX * adjustNum, 1)) + 50
        maxHeight = int(round(maxY * adjustNum, 1)) + 50

        root.title("OHTSim Viewer")
        root.option_add('*Font', '돋음 20')
        root.geometry(str(maxWidth) + 'x' + str(maxHeight))
        root.resizable(True, True)
        canvas = tk.Canvas(root, width = maxWidth, height = maxHeight)
        canvas.pack(fill = "both", expand = True)

        for key, value in self.totalNode.items():
            posX = value.lstCoordinates[0]
            posY = value.lstCoordinates[1]
            ## Main Node ##
            if value.isEquipment == False and value.isSubNode == False:
                self.objNodes[key] = canvas.create_rectangle(posX * adjustNum, posY * adjustNum, posX*adjustNum, posY*adjustNum, outline = "purple", fill = "purple", width = "1")
            ## Sub Node ##
            elif value.isEquipment == False and value.isSubNode == True:
                self.objNodes[key] = canvas.create_rectangle(posX * adjustNum, posY * adjustNum, posX*adjustNum, posY*adjustNum, outline = "ivory4", fill = "ivory4", width = "1")
            ## Equipment ##
            else:
                self.objNodes[key] = canvas.create_rectangle(posX * adjustNum, posY * adjustNum, posX*adjustNum, posY*adjustNum, outline = "blue", fill = "blue", width = "1")
                self.objNodesState[key] = "E"
                self.objNodesText[key] = canvas.create_text(posX * adjustNum, posY * adjustNum, text = self.objNodesState[key], anchor = "ne", fill="black", font=('Helvetica 5 bold'))
            self.objNodesText[key + '_coord'] = canvas.create_text(posX * adjustNum + 10, posY * adjustNum + 10, text=f"({posX}, {posY})", anchor="nw", fill="black", font=('Helvetica', 5))   

        vehicleInfo = self.globalVar.getInitVehicleInfo()
        for key, value in vehicleInfo.items():
            posX = value.lstCoordinates[0]
            posY = value.lstCoordinates[1]
            tmpName = key[0] + key[-3:] + "::I"
            self.objVehicles[key] = canvas.create_rectangle(posX * adjustNum, posY * adjustNum, posX*adjustNum, posY*adjustNum, outline = "red", fill = "red", width = "2")
            self.objNodesText[key] = canvas.create_text(posX * adjustNum, posY * adjustNum, text = tmpName, anchor = "nw", fill="black", font=('Helvetica 5 bold'))
            self.vehicleJobCarry[key] = False
        
        while True:
            if len(self.timeEvent) == 0:
                pass
            else:
                popTime = list(self.timeEvent.keys())[0]
                tmpText = "Simulation Time :: " + str(popTime) + "[s]"
                if self.simulationTimeText == -1:
                    self.simulationTimeText = canvas.create_text(maxWidth-150, maxHeight - 100, text = tmpText, fill="black", font=('Helvetica 15 bold'))
                else:
                    canvas.itemconfig(self.simulationTimeText, text = tmpText)
                chosenEvents = self.timeEvent[popTime]
                del self.timeEvent[popTime]
                for event in chosenEvents:
                    ## processing job ##
                    if event[0] == "job":
                        # event[4] == jobID, 추후 화면 표기 진행
                        self.objNodesState[event[1]] = "P"
                        canvas.itemconfig(self.objNodesText[event[1]], text = self.objNodesState[event[1]])
                    ## process done ##
                    elif event[0] == "informDone":
                        # event[4] == jobID, 추후 화면 표기 진행
                        eqp = self.globalVar.getEquipmentInfoByNodeID(event[1])
                        if eqp.strEquipmentID[0] == "F":
                            self.objNodesState[event[1]] = "D"
                        elif eqp.strEquipmentID[0] == "N":
                            self.objNodesState[event[1]] = "E"
                        canvas.itemconfig(self.objNodesText[event[1]], text = self.objNodesState[event[1]])
                    ## vehicle move ##
                    elif event[0] == "ownPos":
                        canvas.moveto(self.objVehicles[event[1]], event[2] * adjustNum, event[3] * adjustNum)
                        if event[1] in self.objNodesText:
                            canvas.delete(self.objNodesText[event[1]])
                        if self.vehicleJobCarry[event[1]] == False:
                            tmpName = event[1][0] + event[1][-3:] + "::M"
                        else:
                            tmpName = event[1][0] + event[1][-3:] + "::M(J)"
                        self.objNodesText[event[1]] = canvas.create_text(event[2] * adjustNum, event[3] * adjustNum, text = tmpName, anchor = "nw", fill="black", font=('Helvetica 5 bold'))
                        
                    ## vehicle arrival ##
                    elif event[0] == "arrival":
                        canvas.moveto(self.objVehicles[event[1]], event[2] * adjustNum, event[3] * adjustNum)
                        if event[1] in self.objNodesText:
                            canvas.delete(self.objNodesText[event[1]])
                        if self.vehicleJobCarry[event[1]] == False:
                            tmpName = event[1][0] + event[1][-3:] + "::A"
                        else:
                            tmpName = event[1][0] + event[1][-3:] + "::A(J)"
                        self.objNodesText[event[1]] = canvas.create_text(event[2] * adjustNum, event[3] * adjustNum, text = tmpName, anchor = "nw", fill="black", font=('Helvetica 5 bold'))
                    ## lift down ##
                    elif event[0] == "liftDown":
                        ## event[1] = vehicleID, event[2] = posX, event[3] = posY, event[4] = equipmentNodeID, event[5] = posX, event[6] = posY
                        prevPos = canvas.coords(self.objVehicles[event[1]])
                        canvas.delete(self.objNodesText[event[1]])
                        tmpName = event[1][0] + event[1][-3:] + "::LD"
                        self.objNodesText[event[1]] = canvas.create_text(prevPos[0], prevPos[1], text = tmpName, anchor = "nw", fill="black", font=('Helvetica 5 bold'))
                        
                        canvas.itemconfig(self.objNodesText[event[4]], text = "")
                    ## jobExchange ##
                    elif event[0] == "jobExchange":
                        ## event[1] = equipmentNodeID, event[2] = posX, event[3] = posY, event[4] = vehicleID, event[5] = posX, event[6] = posY
                        if self.objNodesState[event[1]] == "D":
                            self.vehicleJobCarry[event[4]] = True
                        else:
                            self.vehicleJobCarry[event[4]] = False
                        prevPos = canvas.coords(self.objVehicles[event[4]])
                        canvas.delete(self.objNodesText[event[4]])
                        tmpName = event[4][0] + event[4][-3:] + "::EX"
                        self.objNodesText[event[4]] = canvas.create_text(prevPos[0], prevPos[1], text = tmpName, anchor = "e", fill="black", font=('Helvetica 5 bold'))
                    ## lift up ##
                    else:
                        ## event[1] = vehicleID, event[2] = posX, event[3] = posY
                        prevPos = canvas.coords(self.objVehicles[event[1]])
                        canvas.delete(self.objNodesText[event[1]])
                        tmpName = event[1][0] + event[1][-3:] + "::LU"
                        nodeID = self.globalVar.getNodeIDByCoordinates([event[2], event[3]])
                        if self.objNodesState[nodeID] == "E":
                            self.objNodesState[nodeID] = "P"
                        elif self.objNodesState[nodeID] == "D":
                            self.objNodesState[nodeID] = "E"
                        canvas.itemconfig(self.objNodesText[nodeID], text = self.objNodesState[nodeID])
                root.update()
                time.sleep(self.renderTime)
                
            if self.isSimulationEnd == True and len(self.timeEvent) == 0:
                break

    def logTimeResults(self):
        fileName = "visualizeLog"
        totalPath = self.jsonPath + fileName + str(self.iter)+ ".json"
        with open(totalPath, "w") as json_file:
            tempJSON = {}
            tempJSON['fileName'] = fileName
            tempJSON['timeEvent'] = []
            for key, value in self.timeEvent.items():
                tempJSON['timeEvent'].append({
                    "simTime": key,
					"events": value
                })
            json.dump(tempJSON, json_file, indent = 4)

    ## for the play back ##
    def runVisualizerAlone(self, jsonPath):
        timeEvent = {}
        timeEvent_bak = {}
        simulationTimeText = -1
        objNodes = {}
        objNodesState = {}
        objNodesText = {}
        objVehicles = {}
        vehicleInfo = {}
        numUtilizedVehicle = []
        ## load visualiztion log ##
        fName = "visualizeLog" + str(self.iter)
        strFileName = jsonPath + fName + ".json"
        print("\nLoading "+ strFileName)
        with open(strFileName) as json_file:
            objData = json.load(json_file)
            if objData["fileName"] == "visualizeLog":
                for data in objData["timeEvent"]:
                    tempKey = 0
                    for key, value in data.items():
                        if key == "simTime":
                            tempKey = value
                        else:
                            timeEvent[tempKey] = value
                            timeEvent_bak[tempKey] = value
                            for info in value:
                                if info[0] == "ownPos":
                                    if info[1] not in numUtilizedVehicle:
                                        numUtilizedVehicle.append(info[1])
                                else:
                                    break
            else:
                print("JSON LOAD ERROR")
                return
        
        ## load map Data ##
        fName = "trainMap"
        strFileName = jsonPath + fName + ".json"
        print("\nLoading "+ strFileName)
        with open(strFileName) as json_file:
            objData = json.load(json_file)
            if objData["fileName"] == "trainMap":
                for data in objData["nodeInfo"]:
                    self.totalNode[data["nodeID"]] = data
            else:
                print("JSON LOAD ERROR")
                return
        
        ## load Vehicle Data ##
        fName = "vehicleInfo"
        strFileName = jsonPath + fName + ".json"
        print("\nLoading "+ strFileName)
        with open(strFileName) as json_file:
            objData = json.load(json_file)
            if objData["fileName"] == "vehicleInfo":
                for data in objData["vehicleInfo"]:
                    if data["vehicleID"] in numUtilizedVehicle:
                        vehicleInfo[data["vehicleID"]] = data
            else:
                print("JSON LOAD ERROR")
                return

        ## load eqpment Data ##
        fName = "map"
        strFileName = jsonPath + fName + ".json"
        print("\nLoading "+ strFileName)
        with open(strFileName) as json_file:
            objData = json.load(json_file)
            if objData["fileName"] == "map":
                for data in objData["equipmentInfo"]:
                    self.eqpmentID[data["equipmentNodeID"]] = data["equipmentID"]
            else:
                print("JSON LOAD ERROR")
                return

        ## calculate maximum display size ##
        widthParameter = self.winfo_screenwidth()
        heightParameter = self.winfo_screenheight()
        adjustNum = 0
        maxWidth = 0
        maxHeight = 0                

        minX = 9999999999
        minY = 9999999999
        maxX = -9999999999
        maxY = -9999999999
        for key, value in self.totalNode.items():
            coordX = value["coordinates"][0]
            coordY = value["coordinates"][1]
            if minX > coordX:
                minX = coordX
            if maxX < coordX:
                maxX = coordX
            if minY > coordY:
                minY = coordY
            if maxY < coordY:
                maxY = coordY
        tempX = widthParameter//maxX
        tempY = heightParameter//maxY
        
        if tempY < tempX:
            adjustNum = tempY
        else:
            adjustNum = tempX

        maxWidth = int(round(maxX * adjustNum, 1)) + 50
        maxHeight = int(round(maxY * adjustNum, 1)) + 50

        self.title("OHTSim Viewer(PlayBack)")
        self.option_add('*Font', '돋음 20')
        self.geometry(str(maxWidth) + 'x' + str(maxHeight))
        self.resizable(True, True)
        canvas = tk.Canvas(self, width = maxWidth, height = maxHeight)
        canvas.pack(fill = "both", expand = True)

        for key, value in self.totalNode.items():
            posX = value["coordinates"][0]
            posY = value["coordinates"][1]
            ## Main Node ##
            if value["isEquipment"] == False and value["isSubNode"] == False:
                objNodes[key] = canvas.create_rectangle(posX * adjustNum, posY * adjustNum, posX*adjustNum, posY*adjustNum, outline = "purple", fill = "purple", width = "1")
            ## Sub Node ##
            elif value["isEquipment"] == False and value["isSubNode"] == True:
                objNodes[key] = canvas.create_rectangle(posX * adjustNum, posY * adjustNum, posX*adjustNum, posY*adjustNum, outline = "ivory4", fill = "ivory4", width = "1")
            ## Equipment ##
            else:
                objNodes[key] = canvas.create_rectangle(posX * adjustNum, posY * adjustNum, posX*adjustNum, posY*adjustNum, outline = "blue", fill = "blue", width = "1")
                objNodesState[key] = "E"
                objNodesText[key] = canvas.create_text(posX * adjustNum, posY * adjustNum, text = objNodesState[key], anchor = "ne", fill="black", font=('Helvetica 5 bold'))
            canvas.create_text(posX * adjustNum + 15, posY * adjustNum + 15, text=f"({posX}, {posY})", anchor="nw", fill="black", font=('Helvetica', 8))

        for key, value in vehicleInfo.items():
            posX = value["coordinates"][0]
            posY = value["coordinates"][1]
            tmpName = key[0] + key[-3:] + "::I"
            objVehicles[key] = canvas.create_rectangle(posX * adjustNum, posY * adjustNum, posX*adjustNum, posY*adjustNum, outline = "red", fill = "red", width = "2")
            objNodesText[key] = canvas.create_text(posX * adjustNum, posY * adjustNum, text = tmpName, anchor = "nw", fill="black", font=('Helvetica 5 bold'))
        
        while True:
            if len(timeEvent) == 0:
                break
            popTime = list(timeEvent.keys())[0]
            tmpText = "Simulation Time :: " + str(popTime) + "[s]"
            if simulationTimeText == -1:
                simulationTimeText = canvas.create_text(maxWidth-150, maxHeight - 100, text = tmpText, fill="black", font=('Helvetica 15 bold'))
            else:
                canvas.itemconfig(simulationTimeText, text = tmpText)
            chosenEvents = timeEvent[popTime]
            del timeEvent[popTime]
            for event in chosenEvents:
                ## processing job ##
                if event[0] == "job":
                    # event[4] == jobID, 추후 화면 표기 진행
                    objNodesState[event[1]] = "P"
                    canvas.itemconfig(objNodesText[event[1]], text = objNodesState[event[1]])
                ## process done ##
                elif event[0] == "informDone":
                    # event[4] == jobID, 추후 화면 표기 진행
                    if self.eqpmentID[event[1]][0] == "F":
                        objNodesState[event[1]] = "D"
                    elif self.eqpmentID[event[1]][0] == "N":
                        objNodesState[event[1]] = "E"                    
                    canvas.itemconfig(objNodesText[event[1]], text = objNodesState[event[1]])
                ## vehicle move ##
                elif event[0] == "ownPos":
                    canvas.moveto(objVehicles[event[1]], event[2] * adjustNum, event[3] * adjustNum)
                    if event[1] in objNodesText:
                        canvas.delete(objNodesText[event[1]])
                    tmpName = event[1][0] + event[1][-3:] + "::M"
                    objNodesText[event[1]] = canvas.create_text(event[2] * adjustNum, event[3] * adjustNum, text = tmpName, anchor = "nw", fill="black", font=('Helvetica 5 bold'))
                ## vehicle arrival ##
                elif event[0] == "arrival":
                    canvas.moveto(objVehicles[event[1]], event[2] * adjustNum, event[3] * adjustNum)
                    if event[1] in objNodesText:
                        canvas.delete(objNodesText[event[1]])
                    tmpName = event[1][0] + event[1][-3:] + "::A"
                    objNodesText[event[1]] = canvas.create_text(event[2] * adjustNum, event[3] * adjustNum, text = tmpName, anchor = "nw", fill="black", font=('Helvetica 5 bold'))
                ## lift down ##
                elif event[0] == "liftDown":
                    ## event[1] = vehicleID, event[2] = posX, event[3] = posY, event[4] = equipmentNodeID, event[5] = posX, event[6] = posY
                    prevPos = canvas.coords(objVehicles[event[1]])
                    canvas.delete(objNodesText[event[1]])
                    tmpName = event[1][0] + event[1][-3:] + "::LD"
                    objNodesText[event[1]] = canvas.create_text(prevPos[0], prevPos[1], text = tmpName, anchor = "nw", fill="black", font=('Helvetica 5 bold'))
                    canvas.itemconfig(objNodesText[event[4]], text = "")
                ## jobExchange ##
                elif event[0] == "jobExchange":
                    ## event[1] = equipmentNodeID, event[2] = posX, event[3] = posY, event[4] = vehicleID, event[5] = posX, event[6] = posY
                    prevPos = canvas.coords(objVehicles[event[4]])
                    canvas.delete(objNodesText[event[4]])
                    tmpName = event[4][0] + event[4][-3:] + "::EX"
                    objNodesText[event[4]] = canvas.create_text(prevPos[0], prevPos[1], text = tmpName, anchor = "e", fill="black", font=('Helvetica 5 bold'))
                ## lift up ##
                else:
                    ## event[1] = vehicleID, event[2] = posX, event[3] = posY
                    prevPos = canvas.coords(objVehicles[event[1]])
                    canvas.delete(objNodesText[event[1]])
                    tmpName = event[1][0] + event[1][-3:] + "::LU"
                    
                    for key, value in self.totalNode.items():
                        if value["coordinates"] == [event[2], event[3]]:
                            nodeID = value["nodeID"]
                            break
                    if objNodesState[nodeID] == "E":
                        objNodesState[nodeID] = "P"
                    elif objNodesState[nodeID] == "D":
                        objNodesState[nodeID] = "E"
                    canvas.itemconfig(objNodesText[nodeID], text = objNodesState[nodeID])
            self.update()
            time.sleep(self.renderTime)

    ## for the RL Training ##
    def loadMapData(self):
        fName = "trainMap"
        strFileName = self.jsonPath + fName + ".json"
        print("\nLoading "+ strFileName)
        with open(strFileName) as json_file:
            objData = json.load(json_file)
            if objData["fileName"] == "trainMap":
                for data in objData["nodeInfo"]:
                    self.totalNode[data["nodeID"]] = data
                    self.fromStartCoordintes.append(data["coordinates"])
                for data in objData["equipmentInfo"]:
                    if data["processType"] not in  self.eqpmentProcessInfo:
                        self.eqpmentProcessInfo[data["processType"]] = []
                    self.eqpmentInfo[data["nodeID"]] = data
                    coordinates = self.totalNode[data["nodeID"]]["coordinates"]
                    self.eqpmentProcessInfo[data["processType"]].append(coordinates)
                for data in objData["nodeConnectionInfo"]:
                    self.nodeConnection[data["fromNodeID"]] = data["toNodeID"]                    
            else:
                print("JSON LOAD ERROR")
                return

        ## load process Data ##
        fName = "processInfo"
        strFileName = self.jsonPath + fName + ".json"
        print("\nLoading "+ strFileName)
        with open(strFileName) as json_file:
            objData = json.load(json_file)
            if objData["fileName"] == "processInfo":
                for data in objData["seqInfo"]:
                    if data["seqNum"] == 1:
                        for i in range(len(data["sequenceList"])-1):
                            processType = data["sequenceList"][i]
                            if processType not in self.processConnection:
                                self.processConnection[processType] = []
                            repairProcess = processType[:-1] + "2"
                            self.processConnection[processType].append(repairProcess)
                            nextProcess = data["sequenceList"][i+1]
                            self.processConnection[processType].append(nextProcess)
                            self.processConnection[repairProcess] = [nextProcess]
                        break
            else:
                print("JSON LOAD ERROR")
                return

        ## toFunction Calculation ##
        for fromProcessType, toProcessTypes in self.processConnection.items():
            self.toFunctionCoordinates[fromProcessType] = []
            for fromCoordinates in self.eqpmentProcessInfo[fromProcessType]:
                for toProcessType in toProcessTypes:
                    for toCoordinates in self.eqpmentProcessInfo[toProcessType]:
                        self.toFunctionCoordinates[fromProcessType].append([fromCoordinates, toCoordinates])

        for key, value in self.nodeConnection.items():
            self.coordConnection[tuple(self.totalNode[key]["coordinates"])] = []
            for toNodeID in value:
                self.coordConnection[tuple(self.totalNode[key]["coordinates"])].append(tuple(self.totalNode[toNodeID]["coordinates"]))

    def buildCanvas(self):
        ## Window Size Calculation ##
        widthParameter = self.winfo_screenwidth()
        heightParameter = self.winfo_screenheight()
        maxWidth = 0
        maxHeight = 0                

        minX = 9999999999
        minY = 9999999999
        maxX = -9999999999
        maxY = -9999999999
        for key, value in self.totalNode.items():
            coordX = value["coordinates"][0]
            coordY = value["coordinates"][1]
            if minX > coordX:
                minX = coordX
            if maxX < coordX:
                maxX = coordX
            if minY > coordY:
                minY = coordY
            if maxY < coordY:
                maxY = coordY
        tempX = widthParameter//maxX
        tempY = heightParameter//maxY
        
        if tempY < tempX:
            self.adjustNum = tempY
        else:
            self.adjustNum = tempX

        maxWidth = int(round(maxX * self.adjustNum, 1)) + 50
        maxHeight = int(round(maxY * self.adjustNum, 1)) + 50

        self.title("OHTSim RL Training")
        self.option_add('*Font', '돋음 20')
        self.geometry(str(maxWidth) + 'x' + str(maxHeight))
        self.resizable(True, True)
        canvas = tk.Canvas(self, width = maxWidth, height = maxHeight)

        ## node&equipment add ##
        self.addNodes(canvas)

        canvas.pack(fill = "both", expand = True)
        # self.update()
        # time.sleep(self.renderTime)
        return canvas

    def addNodes(self, canvas):
        for key, value in self.totalNode.items():
            posX = value["coordinates"][0]
            posY = value["coordinates"][1]
            ## Main Node ##
            if value["isEquipment"] == False and value["isSubNode"] == False:
                self.objNodes[key] = canvas.create_rectangle(posX * self.adjustNum, posY * self.adjustNum, posX * self.adjustNum, posY * self.adjustNum, outline = "purple", fill = "purple", width = "1")
            ## Sub Node ##
            elif value["isEquipment"] == False and value["isSubNode"] == True:
                self.objNodes[key] = canvas.create_rectangle(posX * self.adjustNum, posY * self.adjustNum, posX * self.adjustNum, posY * self.adjustNum, outline = "ivory4", fill = "ivory4", width = "1")
            ## Equipment ##
            else:
                self.objNodes[key] = canvas.create_rectangle(posX * self.adjustNum, posY * self.adjustNum, posX * self.adjustNum, posY * self.adjustNum, outline = "blue", fill = "blue", width = "1")
        # self.update()
            canvas.create_text(posX * self.adjustNum + 10, posY * self.adjustNum - 10, text=f"({posX}, {posY})", anchor="nw", fill="black", font=('Helvetica 5 bold'))

    # Update the canvas to ensure everything is drawn
        canvas.update()
    
    def randomFunction(self, iter):
        # if iter%2 == 0:
        #     return 'from'
        # else:
        #     return 'to'
        # return random.choice(['from', 'to'])
        return 'to'

    def setAgent(self, scenario):
        # if scenario == "from":
        #     self.fromProcessType = None
        #     startCoordinates = random.choice(self.fromStartCoordintes)
        # else:
        #     while True:
        #         processType = random.choice(list(self.eqpmentProcessInfo.keys()))
        #         if processType != "OUT":
        #             break
        #     startCoordinates = random.choice(self.eqpmentProcessInfo[processType])
        #     self.fromProcessType = processType
        processType = list(self.eqpmentProcessInfo.keys())[0]
        startCoordinates = self.toFunctionCoordinates[processType][0][0]
        self.fromProcessType = processType            
        posX = startCoordinates[0]
        posY = startCoordinates[1]
        self.objAgent['txt'] = self.canvas.create_text(posX * self.adjustNum, posY * self.adjustNum, text = "A", anchor = "nw", fill="black", font=('Helvetica 5 bold'))
        self.objAgent['figure'] = self.canvas.create_rectangle(posX * self.adjustNum, posY * self.adjustNum, posX * self.adjustNum, posY * self.adjustNum, outline = "red", fill = "red", width = "2")        
        self.objAgent['coords'] = [posX * self.adjustNum, posY * self.adjustNum]
        self.objAgent['state'] = [int(posX), int(posY)]
        # self.update()
        # time.sleep(self.renderTime)        

    def setGoal(self, scenario):
        # if scenario == "from":
        #     processType = random.choice(list(self.eqpmentProcessInfo.keys()))
        #     endCoordinates = random.choice(self.eqpmentProcessInfo[processType])
        # else:
        #     fromState = self.objAgent['state']
        #     tempList = []
        #     for fromToPairs in self.toFunctionCoordinates[self.fromProcessType]:
        #         if fromToPairs[0] == fromState:
        #             tempList.append(fromToPairs[1])
        #     endCoordinates = random.choice(tempList)
        #     self.fromProcessType = None
        endCoordinates = self.toFunctionCoordinates[self.fromProcessType][0][1]
        posX = endCoordinates[0]
        posY = endCoordinates[1]
        self.objGoal['txt'] = self.canvas.create_text(posX * self.adjustNum, posY * self.adjustNum, text = "G", anchor = "e", fill="black", font=('Helvetica 5 bold'))
        self.objGoal['figure'] = self.canvas.create_rectangle(posX * self.adjustNum, posY * self.adjustNum, posX * self.adjustNum, posY * self.adjustNum, outline = "green", fill = "green", width = "2")
        self.objGoal['coords'] = [posX * self.adjustNum, posY * self.adjustNum]
        self.objGoal['reward'] = 1
        self.objGoal['state'] = [int(posX), int(posY)]
        # self.update()
        # time.sleep(self.renderTime)

    def setSubGoal(self):
        for coords in self.rewardCoords:
            tempDict = {}
            tempDict['txt'] = self.canvas.create_text(coords[0] * self.adjustNum, coords[1] * self.adjustNum, text = "R", anchor = "e", fill="black", font=('Helvetica 5 bold'))
            tempDict['figure'] = self.canvas.create_rectangle(coords[0] * self.adjustNum, coords[1] * self.adjustNum, coords[0] * self.adjustNum, coords[1] * self.adjustNum, outline = "pink", fill = "pink", width = "2")
            tempDict['coords'] = [coords[0] * self.adjustNum, coords[1] * self.adjustNum]
            tempDict['reward'] = 0.3
            tempDict['state'] = [int(coords[0]), int(coords[1])]
            self.objSubGoal.append(tempDict)
        # self.update()
        # time.sleep(self.renderTime)

    def getNextStateByCurState(self, curCoord):
        return self.coordConnection[tuple(curCoord)]
    
    def getNextActionLst(self):
        currentAgentState = tuple(self.objAgent["state"])
        lstNextStates = self.coordConnection[currentAgentState]
        if len(lstNextStates) == 1:
            ## 0: follow the rail
            return [0]
        else:
            ## 0: follow the rail / 1: turn the rail
            return [0, 1]
    
    def reset(self, iter):
        if iter != 0:
            self.cntSteps = 0
            self.canvas.delete(self.objAgent['figure'])
            self.canvas.delete(self.objAgent['txt'])
            self.canvas.delete(self.objGoal['figure'])
            self.canvas.delete(self.objGoal['txt'])
            for i in range(len(self.objSubGoal)):
                self.canvas.delete(self.objSubGoal[i]['figure'])
                self.canvas.delete(self.objSubGoal[i]['txt'])
            self.objAgent.clear()
            self.objGoal.clear()
            self.objSubGoal.clear()
            self.rewardCoords.clear()
            chosenScenario = self.randomFunction(iter)
            self.setAgent(chosenScenario)
            self.setGoal(chosenScenario)
            self.setInitAgentState()
            self.shortestPath = dijkstraRL(self.objAgent["state"], self.objGoal["state"], self.coordConnection)
            self.checkRewardCoords()
            self.setSubGoal()
        self.update()
        time.sleep(self.renderTime)
        return self.getState()

    def getState(self):
        states = []
        initX = self.initAgentState[0]
        initY = self.initAgentState[1]
        goalX = self.objGoal["state"][0]
        goalY = self.objGoal["state"][1]
        curAgentX = self.objAgent["state"][0]
        curAgentY = self.objAgent["state"][1]
        compareX = goalX - curAgentX
        compareY = goalY - curAgentY
        # states.append(initX)
        # states.append(initY)
        # states.append(goalX)
        # states.append(goalY)
        states.append(curAgentX)
        states.append(curAgentY)
        states.append(1)
        # states.append(compareX)
        # states.append(compareY)
        return states

    def getActionSpace(self):
        return self.actionSpace

    def setMaxValues(self, maxEpisode, maxSteps, stepPenalty):
        self.maxEpisode = maxEpisode
        self.maxSteps = maxSteps
        self.stepPenalty = stepPenalty
    
    def timeStep(self, action):
        self.render()
        self.move(action)
        dictReward = self.checkIfReward()
        reward = dictReward["reward"]
        isDone = dictReward["isDone"]
        state = self.getState()
        return state, reward, isDone

    def render(self):
        self.update()
        time.sleep(self.renderTime)

    def move(self, action):
        nextStates = self.getNextStateByCurState(self.objAgent["state"])
        self.objAgent["state"] = list(nextStates[action])
        nextCoord = self.stateToCoord(nextStates[action])
        self.objAgent["coords"] = nextCoord
        self.canvas.moveto(self.objAgent["figure"], nextCoord[0], nextCoord[1])
        self.canvas.moveto(self.objAgent["txt"], nextCoord[0], nextCoord[1])
        # self.canvas.tag_raise(self.objAgent["figure"])
        

    def stateToCoord(self, state):
        coordX = state[0] * self.adjustNum
        coordY = state[1] * self.adjustNum
        return [coordX, coordY]

    def coordToState(self, coord):
        stateX = coord[0] / self.adjustNum
        stateY = coord[1] / self.adjustNum
        return [stateX, stateY]
    
    def checkIfReward(self):
        self.cntSteps = self.cntSteps + 1
        dictReward = {}
        rewards = 0
        if self.objAgent["state"] == self.objGoal["state"]:
            rewards = rewards + self.objGoal["reward"]
            dictReward["isDone"] = True
        elif tuple(self.objAgent["state"]) in self.rewardCoords:
            for i in range(len(self.objSubGoal)):
                if self.objAgent["state"] == self.objSubGoal[i]["state"]:
                    rewards = rewards + self.objSubGoal[i]["reward"]
                    self.canvas.delete(self.objSubGoal[i]["figure"])
                    self.canvas.delete(self.objSubGoal[i]["txt"])
                    del self.objSubGoal[i]
                    self.rewardCoords.remove(tuple(self.objAgent["state"]))
                    break
            if self.cntSteps == self.maxSteps:
                dictReward["isDone"] = True
            else:
                dictReward["isDone"] = False
            # self.update()
            # time.sleep(self.renderTime)
        else:    
            rewards = rewards - self.stepPenalty
            if self.cntSteps == self.maxSteps:
                dictReward["isDone"] = True
            else:
                dictReward["isDone"] = False
        dictReward["reward"] = rewards
        return dictReward

    def setInitAgentState(self):
        self.initAgentState = self.objAgent['state']

    def checkRewardCoords(self):
        for data in list(self.totalNode.values()):
            if tuple(data['coordinates']) in self.shortestPath and data['isBranch'] == True:
                self.rewardCoords.append(tuple(data['coordinates']))