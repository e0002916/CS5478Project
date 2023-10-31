from controller import Robot
from enum import Enum
from controller import GPS, Motor
import pyrqlite.dbapi2 as dbapi2
import threading
import logging
import time
import json
import math
import pika


class RobotStatus(Enum):
    STOPPED = 1
    MOVING = 2
    ERROR = 3

class RobotState:
    def __init__(self, x: float | None, y: float | None, level: float | None, landmark: str | None, status: RobotStatus):
        self.status: RobotStatus = status
        self.x = x
        self.y = y
        self.level = level
        self.landmark = landmark

    def to_dict(self):
        return {'x': self.x, 'y': self.y, 'level': self.level, 'landmark': self.landmark, 'status': self.status}

    def toJSON(self):
        return json.dumps({'x': self.x, 'y': self.y, 'level': self.level, 'landmark': self.landmark, 'status': str(self.status)})

class WaypointFollower:
    def __init__(self, db_host:str = 'localhost', db_port:int = 4001, mq_host:str = 'localhost', mq_port:int = 5672, gps_update_hz:int = 1, translate_vel:float = 5.0, rotation_vel:float = 0.8, translation_threshold: float = 0.4, rotation_threshold: float = 3.0, model_angle_offset: float = 0.0, log_level=logging.INFO):
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',  # Set the log message format
        )
        self.robot = Robot()
        self.state =  RobotState(None, None, 0, None, RobotStatus.STOPPED)
        self.db_host = db_host
        self.db_port = db_port
        self.mq_host = mq_host
        self.mq_port = mq_port
        self.translate_vel = translate_vel
        self.rotation_vel = rotation_vel
        self.rotate_threshold = rotation_threshold
        self.translation_threshold = translation_threshold
        self.model_angle_offset_deg = model_angle_offset
        self.gps_update_hz = gps_update_hz
        self.move_queue = []
        self.timestep = int(self.robot.getBasicTimeStep())
        self.move_channel = pika.BlockingConnection(
            pika.ConnectionParameters(self.mq_host, self.mq_port)).channel()
        self.state_channel = pika.BlockingConnection(
            pika.ConnectionParameters(self.mq_host, self.mq_port)).channel()

        self._init_sim_components()
        self._init_db()
        self._init_mq()
        
        threading.Thread(target=self._log_state).start()
        threading.Thread(target=self._process_move_queue).start()
        threading.Thread(target=self._update_nearest_landmark).start()

        logging.info(f"{self.robot.getName()} initialization complete.")

    def _init_sim_components(self):
        self.motor_left_wheel: Motor = self.robot.getDevice("middle_left_wheel_joint")
        self.motor_right_wheel: Motor = self.robot.getDevice("middle_right_wheel_joint")
        self.motor_left_wheel.setPosition(math.inf)
        self.motor_right_wheel.setPosition(math.inf)
        self.motor_left_wheel.setVelocity(0.0)
        self.motor_right_wheel.setVelocity(0.0)

        self.gps: GPS = self.robot.getDevice("gps")
        self.gps.enable(1)

        self.compass: GPS = self.robot.getDevice("compass")
        self.compass.enable(1)

    def _init_db(self):
        self.connection = dbapi2.connect(
            host=self.db_host,
            port=self.db_port,
            connect_timeout = 10
        )

    def _init_mq(self):
        self.move_channel.exchange_declare(exchange='move', exchange_type='topic', auto_delete=True)
        self.state_channel.exchange_declare(exchange='state', exchange_type='topic', auto_delete=True)

        move_queue = self.move_channel.queue_declare(queue=f"{self.robot.name}.move", exclusive=False, auto_delete=True, arguments={'x-max-length': 1}) 
        self.move_channel.queue_bind(exchange='move', queue=move_queue.method.queue)
        self.move_channel.basic_consume(queue=move_queue.method.queue,
                                        auto_ack=True,
                                        on_message_callback=self._message_queue_cb)
        threading.Thread(target=self.move_channel.start_consuming).start()

    def _message_queue_cb(self, ch, method, properties, body):
        msg_json = body.decode('utf8').replace("'", '"')
        msg = json.loads(msg_json)
        logging.debug(f"Received Move: {msg}")
        if "name" in msg.keys() and "level" in msg.keys():
            if msg["level"] == self.state.level:
                self.move_queue.append(msg["name"])
                logging.debug(f"Updated Move Queue: {self.move_queue}")
            else:
                logging.error(f"Robot on Wrong Level.")
        else:
                logging.error(f"Move message has errors.")

    def _gps_is_working(self):
        return all(not(math.isnan(element)) for element in self.gps.getValues())

    def _update_nearest_landmark(self):
        while True:
            if self._gps_is_working() and self.state.landmark is None:
                current_xy = self.gps.getValues()[0:2]
                min_dist = math.inf
                with self.connection.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM landmarks WHERE level == '{self.state.level}'")
                    for result in cursor.fetchall():
                        current_dist = math.sqrt((current_xy[0] - result['x'])**2 + (current_xy[1] - result['y'])**2)
                        if current_dist < min_dist:
                            self.state.landmark = result['name']
                            min_dist = current_dist
            time.sleep(1.0 / self.gps_update_hz)

    def _get_bearing_deg(self):
        north = self.compass.getValues()
        rad = math.atan2(north[1], north[0])
        bearing = (rad - math.pi / 2) / math.pi * 180.0
        if bearing < 0.0:
            bearing = bearing + 360.0
        return bearing

    def _log_state(self):  
        while True:
            if self._gps_is_working():
                message = self.state.toJSON()
                logging.debug(message)
                self.state_channel.basic_publish(exchange='state',
                                          routing_key=f"{self.robot.name}.state",
                                          body=message)
            time.sleep(1.0 / self.gps_update_hz)

    def _process_move_queue(self):  
        while True:
            if self.move_queue:
                landmark = self.move_queue[0]
                self.state.status = RobotStatus.MOVING
                if self.goto(landmark):
                    self.move_queue.pop(0)
                    logging.debug(f"Remaining Waypoints: {self.move_queue}")
            else:
                self.state.status = RobotStatus.STOPPED

            time.sleep(1.0 / self.gps_update_hz)

    def _get_landmark(self, name: str):
        with self.connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM landmarks WHERE name == '{name}'")
            return cursor.fetchone()

    def _rotate_to(self, x:float, y:float): 
        current_xy = self.gps.getValues()[0:2]
        target_xy = [x, y]
        rad = math.atan2(target_xy[1] - current_xy[1], target_xy[0] - current_xy[0])
        bearing =  (-rad) / math.pi * 180.0
        if bearing < 0.0:
            bearing = bearing + 360.0

        while self.robot.step(self.timestep) != -1:
            angle = bearing - self._get_bearing_deg()

            if (abs(angle) < self.rotate_threshold):
                self.motor_left_wheel.setVelocity(0.0)
                self.motor_right_wheel.setVelocity(0.0)
                return

            angle_delta = self._get_bearing_deg() - bearing
            logging.debug(f"Angle to Target: {angle_delta}")

            if angle_delta < 0.0:
                angle_delta += 360.0

            if angle_delta > 180.0:
                self.motor_left_wheel.setVelocity(self.rotation_vel)
                self.motor_right_wheel.setVelocity(-self.rotation_vel)
            else:
                self.motor_left_wheel.setVelocity(-self.rotation_vel)
                self.motor_right_wheel.setVelocity(self.rotation_vel)

    def _drive_to(self, x: float, y: float): 
        prev_dist = None
        self._rotate_to(x, y)

        while self.robot.step(self.timestep) != -1:
            current_xy = self.gps.getValues()[0:2]
            dist = math.sqrt((current_xy[0] - x)**2 + (current_xy[1] - y)**2)
            logging.debug(f"Distance to Target: {dist}")

            if prev_dist is not None and dist > prev_dist:
                self._rotate_to(x, y)

            if (dist < self.translation_threshold):
                self.motor_left_wheel.setVelocity(0.0)
                self.motor_right_wheel.setVelocity(0.0)
                return
            else:
                self.motor_left_wheel.setVelocity(self.translate_vel)
                self.motor_right_wheel.setVelocity(self.translate_vel)
            prev_dist = dist


    def goto(self, landmark: str) -> bool:
        if self._gps_is_working():
            dest = self._get_landmark(landmark)
            if dest is None:
                logging.error(f"Destination {landmark} does not exist. Considering it done.")
                return True 
            self._drive_to(dest['x'], dest['y'])
            self.state.landmark = landmark
            return True

        else:
            logging.error("GPS is not initialized yet. Try again later")
            return False

    def run(self):
        while self.robot.step(self.timestep) != -1:
            pass


robot = WaypointFollower(model_angle_offset=90.0, log_level=logging.INFO)
robot.run()
