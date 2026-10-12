import datetime
import time
from decimal import Decimal
from typing import Union

# A WF timestamp as stored in the database or passed by callers (seconds offset)
Timestamp = Union[str, int, float, Decimal]

# zeroDate is arbitarily 1st Jan 2000 : gives 60 year
zeroDate = datetime.datetime(2000, 1, 1, 0, 0, 0)  # noqa: DTZ001


def getTimeZero() -> datetime.datetime:
    return zeroDate


def getTimeNow() -> Decimal:
    tNow = datetime.datetime.utcnow()  # noqa: DTZ003

    c = tNow - zeroDate
    microSec = ((c.days * 24 * 60 * 60 + c.seconds) * 1000000 + c.microseconds) / 1000000.0

    # must use Decimal(repr(time)) as python in its wisdom will only return 3dp if you are lucky
    return Decimal(repr(microSec))


def getTimeSeconds(timestamp: Timestamp) -> float:
    zero = time.mktime(zeroDate.timetuple())

    d = float(zero) + float(timestamp)
    return d


def getTimeString(timestamp: Timestamp) -> str:
    zero = time.mktime(zeroDate.timetuple())

    fmt = "%Y-%m-%d %H:%M:%S %Z"

    d = float(zero) + float(timestamp)
    return datetime.datetime.fromtimestamp(int(d)).strftime(fmt)  # noqa: DTZ006


def getTimeFromEpoc(timestamp: Timestamp) -> str:
    fmt = "%Y-%m-%d %H:%M:%S %Z"

    d = float(timestamp)
    return datetime.datetime.fromtimestamp(int(d)).strftime(fmt)  # noqa: DTZ006


# getTimeReadable() is not used anywhere, and every call raised AttributeError because zeroDate is a datetime,
# which has no days/seconds/microseconds attributes.  Disabled rather than fixed.
#
# def getTimeReadable(timestamp: Timestamp) -> datetime.datetime:
#     one = ((zeroDate.days * 24 * 60 * 60 + zeroDate.seconds) * 1000000 + zeroDate.microseconds) / 1000000.0
#     two = float(str(timestamp))
#     return datetime.datetime.utcfromtimestamp(one + two)
