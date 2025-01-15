responsesData = {}


def createResponse(userID, target, payload={}): responsesData[userID] = {
    "target": target, "payload": payload}


def deleteResponse(userID):
    responseData = responsesData.get(userID)
    if responseData:
        responsesData.pop(userID)


def getResponse(userID): return responsesData[userID]


def checkIfTarget(userID, target):
    try:
        responseData = responsesData.get(userID)
        if not responseData:
            return False
        return responseData.get("target") == target
    except Exception as e:
        print(e)
        return False
