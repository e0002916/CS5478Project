import logging
import json
import threading
import sys
import uvicorn
from fastapi.openapi.utils import get_openapi
import pika
from fastapi import FastAPI
from utils import RobotState

class DispenserRobotSwaggerAPI:
    def __init__(self, robot_name:str, log_level:int=logging.INFO, 
                 fastapi_host:str='localhost', fastapi_port:int=8000, 
                 mq_host:str='localhost', mq_port=5672):
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',  # Set the log message format
        )
        self.robot_name = robot_name

        # Connectivity to this server
        self.app = FastAPI()
        self.fastapi_host = fastapi_host
        self.fastapi_port = fastapi_port

        # Connectivity to robot controller
        self.mq_host = mq_host
        self.mq_port = mq_port
        self._init_mq()
        self.dispense_channel = pika.BlockingConnection(pika.ConnectionParameters(self.mq_host, self.mq_port)).channel()
        result = self.dispense_channel.queue_declare(queue=f"dispense.{self.robot_name}", exclusive=False, auto_delete=True)
        self.dispense_channel.queue_bind(exchange='dispense', queue=result.method.queue)

        # Set up FastAPI 
        self._init_api()

    def _init_mq(self):
        state_channel = pika.BlockingConnection(pika.ConnectionParameters(self.mq_host, self.mq_port)).channel()
        state_channel.exchange_declare(exchange='dispense', exchange_type='topic', auto_delete=False)
        threading.Thread(target=state_channel.start_consuming, daemon=True).start()

    def _init_api(self):
        @self.app.put("/dispense/")
        async def dispense(item: str):
            message = { "item": item }
            self.dispense_channel.basic_publish(exchange='dispense', routing_key=f"dispense.{self.robot_name}", body=json.dumps(message))
            return True

    def _generate_swagger(self):
       return get_openapi(
           title=f"{__file__} API",
           version="1.0.0",
           description="",
           routes=self.app.routes
       )

    def run_server(self):
        uvicorn_config = uvicorn.Config(self.app, host=self.fastapi_host, port=self.fastapi_port)
        server = uvicorn.Server(uvicorn_config)
        server.run()

if __name__ == "__main__":
    api = DispenserRobotSwaggerAPI(robot_name=sys.argv[1], fastapi_host=sys.argv[2], fastapi_port=int(sys.argv[3]), log_level=logging.INFO)
    api.run_server()

