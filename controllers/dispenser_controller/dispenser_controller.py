"""dispenser_controller controller."""

import logging
import pyrqlite.dbapi2 as dbapi2
from random import randrange
import json
import threading
import pika
import time
from controller import Supervisor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',  # Set the log message format
)

class Dispenser:
    def __init__(self, db_host:str = 'localhost', db_port:int = 4001, mq_host:str = 'localhost'):
        self.robot = Supervisor()
        self.db_host = db_host
        self.db_port = db_port
        self.mq_host = mq_host
        self.timestep = int(self.robot.getBasicTimeStep())
        self.channel = pika.BlockingConnection(
            pika.ConnectionParameters(self.mq_host)).channel()
        self.all_nodes = self.robot.getRoot().getField('children')
        self.dispenser_counter = 0

        self._init_db()
        self._init_mq()

        logging.info(f"{self.robot.getName()} initialization complete.")

    def _init_db(self):
        self.connection = dbapi2.connect(
            host=self.db_host,
            port=self.db_port,
            connect_timeout = 10
        )

    def _init_mq(self):
        mq_connection = pika.BlockingConnection(pika.ConnectionParameters(self.mq_host))
        self.channel = mq_connection.channel()
        self.channel.exchange_declare(exchange='dispense', exchange_type='direct')
        result = self.channel.queue_declare(queue=self.robot.name, exclusive=False)
        self.channel.queue_bind(exchange='dispense', queue=result.method.queue)
        self.channel.basic_consume(queue=result.method.queue,
                      auto_ack=True,
                      on_message_callback=self._message_queue_cb)
        threading.Thread(target=self.channel.start_consuming).start()

    def _generate_can_node_string(self, x, y, z):
        result = ""
        result += "Can { translation "
        result += f"{x} {y} {z}"
        result += ", name "
        result += f"\"can{self.dispenser_counter}\""
        result += "}"
        self.dispenser_counter += 1
        return result

    def _message_queue_cb(self, ch, method, properties, body):
        msg_json = body.decode('utf8').replace("'", '"')
        msg = json.loads(msg_json)
        logging.info(f"Received Dispense: {msg}")
        if "item" in msg.keys() and "dispenserId" in msg.keys():
            if msg["item"] == "Can":
                # TODO: Use DB
                if msg["dispenserId"] == "ConveyorBelt1":
                    self.all_nodes.importMFNodeFromString(-1, self._generate_can_node_string(-4.3, -9.57, 0.37))
                else:
                    logging.error("Unknown dispenserId requested")
            else:
                logging.error("Unknown item requested")
        else:
            logging.error(f"Dispense message has errors.")


    def run(self):
        while self.robot.step(self.timestep) != -1:
            pass

robot = Dispenser()
robot.run()
