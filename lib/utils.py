from enum import Enum
import json

class Location:
    def __init__(self, x: float|None=None, y: float|None=None, level: str|None=None, json_str: str|None=None):
        if json_str is not None:
            json_dict = json.loads(json_str)
            self.x = float(json_dict['x'])
            self.y = float(json_dict['y'])
            self.level = json_dict['level']
        else:
            self.x = x
            self.y = y
            self.level = level

class RobotStatus(Enum):
    STOPPED = 1
    MOVING = 2
    ERROR = 3

class RobotState:
    def __init__(self, location: Location|None=None, status: RobotStatus|None=None, json_str: str|None=None):
        self.status: RobotStatus
        self.location: Location

        if json_str is not None:
            self.fromJSON(json_str)
        elif location and status:
            self.status = status
            self.location = location

    def toJSON(self):
        return json.dumps({'location': {'x': self.location.x, 'y': self.location.y, 'level': self.location.level}, 
                           'status': str(self.status)})

    def fromJSON(self, json_str: str):
        json_dict = json.loads(json_str)
        location = Location(json_str=json.dumps(json_dict['location']))
        self.location = location

        json_status = json_dict['status']
        if json_status == 'RobotStatus.STOPPED':
            self.status = RobotStatus.STOPPED
        elif json_status == 'RobotStatus.MOVING':
            self.status = RobotStatus.MOVING
        elif json_status == 'RobotStatus.ERROR':
            self.status = RobotStatus.ERROR

    def __str__(self):
        return self.toJSON()
