class FromToCommand:
    def __init__(self, strCommandType, strCommandID, strVehicleID, strDestinationNodeID):
        self.strCommandType = strCommandType
        self.strCommandID = strCommandID
        self.strVehicleID = strVehicleID
        self.strDestinationNodeID = strDestinationNodeID
        self.lstDstPath = None
        
class GoCommand:
    def __init__(self, strCommandType, strCommandID, strVehicleID, lstDstPath, lstBlockVehicleID, strDestinationNodeID=None):
        self.strCommandType = strCommandType
        self.strCommandID = strCommandID
        self.strVehicleID = strVehicleID
        self.lstDstPath = lstDstPath
        if lstBlockVehicleID == None:
            self.lstBlockVehicleID = None
        else:
            tempLst = []
            for info in lstBlockVehicleID:
                tempLst.append(info[0])
            self.lstBlockVehicleID = tempLst
        self.strDestinationNodeID = strDestinationNodeID

class scheduleResult:
    def __init__(self, nodeList, cmdType, commandID, chosenID, lstBlockVehicleID, lstBlockVehicleNode):
        self.strAcknowledge = "A" if len(lstBlockVehicleID) == 0 or len(lstBlockVehicleID) != 0 and cmdType == "G" else "N"
        self.strCommandType = cmdType
        self.strCommandID = commandID
        self.strVehicleID = chosenID
        self.intNumNode = len(nodeList)
        self.lstNodes = nodeList
        self.strDstNodeID = str(nodeList[-1]) if len(nodeList) != 0 else None
        self.lstBlockVehicleID = lstBlockVehicleID
        self.lstBlockVehicleNode = lstBlockVehicleNode