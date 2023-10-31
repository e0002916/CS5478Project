"""dropoff_controller controller."""

import logging
import math
from controller import Supervisor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',  # Set the log message format
)

def prune_cans():
    for i in range(children_field.getCount()):
        node = children_field.getMFNode(i)
        node_name = node.getTypeName()
        if "Can" in node_name:
            location = node.getPosition()
            distance = math.sqrt((robot_location[0] - location[0])**2 + (robot_location[1] - location[1])**2)
            if distance < 2.0:
                logging.info(f"DropOff for {node_name}")
                node.remove()

robot = Supervisor()

timestep = int(robot.getBasicTimeStep())
robot_location = robot.getSelf().getPosition()
root_node = robot.getRoot()
children_field = root_node.getField('children')

i = 0
while robot.step(timestep) != -1:
    if i == 100:
        prune_cans()
        i = 0
    else:
        i+=1
    pass
