import logging
import threading
import sys
import uvicorn
from fastapi.openapi.utils import get_openapi
import pika
from fastapi import FastAPI
from utils import RobotState

class WaypointRobotSwaggerAPI:
    def __init__(self, robot_name:str, log_level:int=logging.INFO, 
                 fastapi_host:str='localhost', fastapi_port:int=8000, 
                 mq_host:str='localhost', mq_port=5672):
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',  # Set the log message format
        )
        self.robot_name = robot_name
        self.state: RobotState

        # Connectivity to this server
        self.app = FastAPI()
        self.fastapi_host = fastapi_host
        self.fastapi_port = fastapi_port

        # Connectivity to robot controller
        self.mq_host = mq_host
        self.mq_port = mq_port
        self._init_mq()

        # Set up FastAPI 
        self._init_api()

    def _init_mq(self):
        mq_connection = pika.BlockingConnection(pika.ConnectionParameters(self.mq_host, self.mq_port))
        state_channel = mq_connection.channel()
        state_channel.exchange_declare(exchange='state', exchange_type='topic', auto_delete=False)
        result = state_channel.queue_declare(queue=f"state.{self.robot_name}", exclusive=False, auto_delete=True)
        state_channel.queue_bind(exchange='state', queue=result.method.queue)
        state_channel.basic_consume(result.method.queue, self._on_state_mq)
        threading.Thread(target=state_channel.start_consuming, daemon=True).start()

    def _on_state_mq(self, channel, method_frame, header_frame, body):
        self.state = RobotState(json_str=body.decode('utf-8'))
        logging.info(self.state)
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def _init_api(self):
        @self.app.put("/move/")
        async def move(x, y, level:str = '0'):
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
    api = WaypointRobotSwaggerAPI(robot_name=sys.argv[1], fastapi_host=sys.argv[2], fastapi_port=int(sys.argv[3]), log_level=logging.INFO)
    api.run_server()

