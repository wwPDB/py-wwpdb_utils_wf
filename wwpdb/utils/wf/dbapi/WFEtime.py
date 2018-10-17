import time
import datetime
from decimal import Decimal

# zeroDate is arbitarily 1st Jan 2000 : gives 60 year
zeroDate = datetime.datetime(2000, 1, 1, 0, 0, 0)

def getTimeZero():

   return zeroDate
    
def getTimeNow():

   tNow = datetime.datetime.utcnow()

   c = tNow - zeroDate
   microSec =  ((c.days * 24 * 60 * 60 + c.seconds) * 1000000 +  c.microseconds) / 1000000.0
  

# must use Decimal(repr(time)) as python in its wisdom will only return 3dp if you are lucky
   return Decimal(repr(microSec))

def getTimeSeconds(timestamp):

   zero = time.mktime(zeroDate.timetuple())

   d = float(zero) + float(timestamp)
   return d

def getTimeString(timestamp):

   zero = time.mktime(zeroDate.timetuple())

   fmt = '%Y-%m-%d %H:%M:%S %Z'

   d = float(zero) + float(timestamp)
   return datetime.datetime.fromtimestamp(int(d)).strftime(fmt)

def getTimeFromEpoc(timestamp):

   fmt = '%Y-%m-%d %H:%M:%S %Z'

   d =  float(timestamp)
   return datetime.datetime.fromtimestamp(int(d)).strftime(fmt)

def getTimeReadable(timestamp):

   one  = ((zeroDate.days * 24 * 60 * 60 + zeroDate.seconds) * 1000000 +  zeroDate.microseconds) / 1000000.0
   two = float(str(timestamp))
   return datetime.datetime.utcfromtimestamp(one + two)
   


