from haystack import Pipeline
from haystack.agents import Agent, Tool
from haystack.nodes import PromptNode, PromptTemplate 
from waypoint_robot_api import WaypointRobotSwaggerAPI
import pyrqlite.dbapi2 as dbapi2
from pathlib import Path
from typing import List
import logging
from base_agent import BaseAgent, NonBlockingQueryRestAPI
import tempfile
import json
import os
import sys

class WaypointRobotAgent(BaseAgent):
    def __init__(self, robot_name:str, db_host:str, db_port: int, 
                 api_query_host:str, api_query_port: int, 
                 api_backend_host:str, api_backend_port: int, 
                 log_level=logging.INFO):
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
        super().__init__(api_query_host, api_query_port, self.query)

        # Initialize Robot Low Level Controller
        api = WaypointRobotSwaggerAPI(robot_name=robot_name, fastapi_host=api_backend_host, fastapi_port=api_backend_port, log_level=log_level)

        # Load configuration values
        self.robot_name = robot_name
        self.provider = "openai"
        self.API_KEY = os.environ['OPENAI_API_KEY']
        self.swagger_prompt = None

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
        api.run_server()

    def setup_agent(self):
        prompt_node = PromptNode(model_name_or_path="gpt-3.5-turbo-0301", api_key=os.environ["OPENAI_API_KEY"], stop_words=["Observation:"])
        agent = Agent(prompt_node=prompt_node)

        return agent 

    def query(self, q: str):
        return self.agent.run(q)

    def init_db(self):
        db_connection = dbapi2.connect(
            host=self.db_host,
            port=self.db_port,
            connect_timeout = 10
        )

        return db_connection

if __name__ == "__main__":
    agent = WaypointRobotAgent(
        robot_name=sys.argv[1], db_host=sys.argv[2], db_port=int(sys.argv[3]),
        api_query_host=sys.argv[4], api_query_port=int(sys.argv[5]),
        api_backend_host=sys.argv[6], api_backend_port=int(sys.argv[7]), 
        log_level=logging.INFO)
