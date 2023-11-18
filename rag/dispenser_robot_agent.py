import pyrqlite.dbapi2 as dbapi2
import logging
import os
import sys
from functools import partial
from haystack.agents import Agent 
from haystack.nodes import PromptNode 
from base_agent import BaseAgent 
from agent_tools import PythonRequestsGeneratorForSwaggerAPI, SQLGeneratorForSQLite
from dispenser_robot_api import DispenserRobotSwaggerAPI

class DispenserRobotAgent(BaseAgent):
    def __init__(self, robot_name:str, db_host:str, db_port: int, 
                 api_query_host:str, api_query_port: int, 
                 api_backend_host:str, api_backend_port: int, 
                 log_level=logging.INFO, train=False):
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
        # Decide if we valid tool executions will save and bootstrap LLM
        self.train = train

        # Initialize Robot Low Level Controller
        self.api = DispenserRobotSwaggerAPI(robot_name=robot_name, fastapi_host=api_backend_host, fastapi_port=api_backend_port, log_level=log_level)

        # Load configuration values
        self.robot_name = robot_name
        self.provider = "openai"
        self.API_KEY = os.environ['OPENAI_API_KEY']

        # Setup DB
        self.db_host = db_host
        self.db_port = db_port
        self.db_connection = self.init_db()

        # Setup API for query input
        self.api_query_host = api_query_host
        self.api_query_port = api_query_port

        # Setup API to interface with backend
        self.api_backend_host = api_backend_host
        self.api_backend_port = api_backend_port
        self.agent = self.setup_agent()

        # Run server
        super().__init__(api_query_host, api_query_port, partial(self.query, self.agent))
        self.api.run_server()

    def setup_agent(self):
        prompt_node = PromptNode(model_name_or_path="gpt-3.5-turbo-0301", api_key=os.environ["OPENAI_API_KEY"], stop_words=["Observation:"])
        agent = Agent(prompt_node=prompt_node)

        agent.add_tool(
            tool=PythonRequestsGeneratorForSwaggerAPI(
                robot_name=self.robot_name, 
                swagger_definitions=str(self.api.generate_swagger()), 
                server_connection_string=f"http://{self.api_backend_host}:{self.api_backend_port}",
                train=self.train).generate_tool())

        return agent 

    def query(self, agent: Agent, q: str):
        results = agent.run(q)

        if 'answers' in results:
            return {"answers": [ answer.answer for answer in results['answers'] ] }

    def init_db(self):
        db_connection = dbapi2.connect(
            host=self.db_host,
            port=self.db_port,
            connect_timeout = 10
        )

        return db_connection

if __name__ == "__main__":
    agent = DispenserRobotAgent(
        robot_name=sys.argv[1], db_host=sys.argv[2], db_port=int(sys.argv[3]),
        api_query_host=sys.argv[4], api_query_port=int(sys.argv[5]),
        api_backend_host=sys.argv[6], api_backend_port=int(sys.argv[7]), 
        log_level=logging.INFO, train=False)
