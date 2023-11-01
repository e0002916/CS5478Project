import logging
import json
import random
import threading
import pika
from controller import Supervisor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',  # Set the log message format
)

class Dispenser:
    def __init__(self, mq_host:str = 'localhost', mq_port:int = 5672):
        self.robot = Supervisor()
        self.mq_host = mq_host
        self.mq_port = mq_port
        self.timestep = int(self.robot.getBasicTimeStep())
        self.all_nodes = self.robot.getRoot().getField('children')

        self._init_mq()

        logging.info(f"{self.robot.getName()} initialization complete.")

    def _init_mq(self):
        channel = pika.BlockingConnection(pika.ConnectionParameters(self.mq_host, self.mq_port)).channel()
        channel.exchange_declare(exchange='dispense', exchange_type='topic', auto_delete=False)
        result = channel.queue_declare(queue=f"dispense.{self.robot.name}", exclusive=False, auto_delete=True)
        channel.queue_bind(exchange='dispense', queue=result.method.queue)
        channel.basic_consume(result.method.queue, self._on_dispense_mq)
        threading.Thread(target=channel.start_consuming).start()

    def _generate_can_node_string(self, x, y, z):
        result = ""
        result += "Can { translation "
        result += f"{x} {y} {z}"
        result += ", name "
        result += f"\"can{random.randint(0, 100)}\""
        result += "}"
        return result

    def _on_dispense_mq(self, channel, method_frame, header_frame, body):
        spawn = self.robot.getSelf().getPosition()
        if json.loads(body)['item'].lower() == 'coke':
            self.all_nodes.importMFNodeFromString(-1, self._generate_can_node_string(spawn[0], spawn[1], spawn[2]))
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def run(self):
        while self.robot.step(self.timestep) != -1:
            pass

robot = Dispenser()
robot.run()
