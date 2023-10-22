"""dispenser_controller controller."""

import logging
import time
from controller import Supervisor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',  # Set the log message format
)

robot = Supervisor()
root_node = robot.getRoot()
children_field = root_node.getField('children')

timestep = int(robot.getBasicTimeStep())
children_field.importMFNodeFromString(-1, 'Can { translation -4.3 -9.57 0.37, name "CAN" }')

while robot.step(timestep) != -1:
    pass
