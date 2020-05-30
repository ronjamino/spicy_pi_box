from tinydb import TinyDB, Query
from threading import RLock

from consts import PUMP_LOG
from consts import SERVICE_LOG

from datetime import datetime

pumpDB = TinyDB(PUMP_LOG)
serviceDB = TinyDB(SERVICE_LOG)

rlock = RLock()

def logPumpRun(entry):
    with rlock:
        pumpDB.insert(entry)

def getLatestPumpRun():
    with rlock:
        pumpRun = Query()
        searchResult = pumpDB.search(pumpRun.event == "Pump Run")
        if (len(searchResult) > 0):
            return searchResult[-1]
        else:
            return None

def getRecentPumpRuns():
    logs = pumpDB.all()
    if (len(logs) > 25):
        return logs[-25:]
    else:
        return logs