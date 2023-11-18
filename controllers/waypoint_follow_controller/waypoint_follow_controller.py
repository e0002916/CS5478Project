from typing import List
from controller import Robot
from controller import GPS, Motor
import threading
import logging
import time
import math
import pika
import json
from utils import RobotState, RobotStatus, Location


class WaypointFollower:
    def __init__(self, log_level = logging.INFO, mq_host: str = 'localhost', mq_port: int = 5672, gps_update_hz:int = 1, translate_vel:float = 5.0, rotation_vel:float = 0.8, 
                 translation_threshold: float = 0.4, rotation_threshold: float = 3.0, model_angle_offset: float = 0.0):
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',  # Set the log message format
        )
        self.robot = Robot()
        self.mq_host = mq_host
        self.mq_port = mq_port
        self.translate_vel = translate_vel
        self.rotation_vel = rotation_vel
        self.rotate_threshold = rotation_threshold
        self.translation_threshold = translation_threshold
        self.model_angle_offset_deg = model_angle_offset
        self.gps_update_hz = gps_update_hz
        self.move_queue: List[Location] = []
        self.timestep = int(self.robot.getBasicTimeStep())
        self.state: RobotState

        self._init_sim_components()
        self._init_mq()

        threading.Thread(target=self._update_state).start()
        threading.Thread(target=self._process_move_queue).start()

        logging.info(f"{self.robot.getName()} initialization complete.")

    def _on_move_mq(self, channel, method_frame, header_frame, body):
        try:
            location = Location(json_str=body)
            self.move_queue.append(location)
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        except Exception as e:
            logging.error(e)

    def _init_mq(self):
        move_channel = pika.BlockingConnection(pika.ConnectionParameters(self.mq_host, self.mq_port)).channel()
        move_channel.exchange_declare(exchange='move', exchange_type='topic', auto_delete=True)
        result = move_channel.queue_declare(queue=f"move.{self.robot.name}", exclusive=False, auto_delete=True)
        move_channel.queue_bind(exchange='move', queue=result.method.queue)
        move_channel.basic_consume(result.method.queue, self._on_move_mq)
        threading.Thread(target=move_channel.start_consuming).start()

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
        
    def _gps_is_working(self):
        return all(not(math.isnan(element)) for element in self.gps.getValues())

    def _get_bearing_deg(self):
        north = self.compass.getValues()
        rad = math.atan2(north[1], north[0])
        bearing = (rad - math.pi / 2) / math.pi * 180.0
        if bearing < 0.0:
            bearing = bearing + 360.0
        return bearing

    def _update_state(self):  
        state_channel = pika.BlockingConnection(pika.ConnectionParameters(self.mq_host, self.mq_port)).channel()
        state_channel.exchange_declare(exchange='state', exchange_type='topic', auto_delete=False)
        while True:
            if self._gps_is_working():
                gps = self.gps.getValues()
                self.state =  RobotState(Location(gps[0], gps[1], "0"), RobotStatus.STOPPED)  # TODO: Update Level
                logging.debug(self.state.toJSON())
                state_channel.basic_publish(exchange='state', routing_key=f"state.{self.robot.name}", body=self.state.toJSON())
            time.sleep(1.0 / self.gps_update_hz)

    def _process_move_queue(self):  
        while True:
            if hasattr(self, 'state'):
                if self.move_queue:
                    location: Location = self.move_queue[0]
                    # TODO: Account for level
                    self.state.status = RobotStatus.MOVING
                    if self._drive_to(location.x, location.y):
                        self.move_queue.pop(0)
                        logging.debug(f"Remaining Waypoints: {self.move_queue}")
                else:
                    self.state.status = RobotStatus.STOPPED

            logging.debug(self.move_queue)
            time.sleep(1.0 / self.gps_update_hz)

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
                return True
            else:
                self.motor_left_wheel.setVelocity(self.translate_vel)
                self.motor_right_wheel.setVelocity(self.translate_vel)
            prev_dist = dist

    def run(self):
        while self.robot.step(self.timestep) != -1:
            pass


robot = WaypointFollower(model_angle_offset=90.0, log_level=logging.INFO)
robot.run()
