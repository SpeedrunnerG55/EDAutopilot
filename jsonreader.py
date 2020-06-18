import json

def cleanList(data):
    return [cleanData(d) for d in data]

def cleanData(data):
    if(type(data) is dict):
        return cleanDict(data)
    elif(type(data) is list):
        return cleanList(data)
    return nullToNone(data)

def nullToNone(v):
    return None if v == 'null' else v

def cleanDict(oldDict):
    newDict = {}
    for k,v in oldDict.items():
        k = nullToNone(k)
        v = cleanData(v)
        newDict[k] = v
    return newDict

def writeToFile(data,fileName='data.json'):
    with open(fileName,"w+") as fp:
        json.dump(data,fp)

def readFromFile(fileName='data.json'):
    with open(fileName,"r") as fp:
        return cleanData(json.load(fp))

#add data to this list and run to save to master file
if __name__ == '__main__':

    #test data

    dictionary = {
    'orange': {
        'A'  :([  0,  25, 200], [ 19, 255, 255]),
        'F'  :([  0,  60, 200], [ 25, 255, 255]),
        'G'  :([  4, 130, 210], [ 45, 255, 255]),
        'B'  :([  0,   0, 120], [ 70, 245, 255]),
        'M'  :([  0, 100, 190], [ 70, 245, 255]),
        'K'  :([  0, 100, 190], [ 70, 245, 255]),
        'H'  :([  0, 100, 190], [ 70, 245, 255]),
        None :([  0, 100, 190], [ 70, 245, 255])
        },
    'blue': {
        'A'  :([  80,  10, 240], [ 110,  60, 255]),
        'G'  :([  30,   0,   0], [ 255, 255, 255]),
        'B'  :([  41,  94, 158], [ 179, 255, 255]),
        'M'  :([  26,   0, 159], [ 170, 245, 255]),
        'F'  :([  26,   0, 159], [ 170, 245, 255]),
        'K'  :([  26,   0, 159], [ 170, 245, 255]),
        'H'  :([  50,  20, 150], [ 160, 255, 255]),
        None :([  50,  20, 150], [ 160, 255, 255])
        }
    }

    writeToFile(dictionary,'HSV.json') #read from dict

    print(readFromFile('HSV.json')) #read from back from file
