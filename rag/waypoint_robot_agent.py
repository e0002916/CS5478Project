from haystack.nodes.prompt import PromptTemplate
import pyrqlite.dbapi2 as dbapi2
from multiprocessing import Process, Queue
import logging
import time
import os
import sys
from functools import partial
from haystack.agents import Agent 
from haystack.nodes import PromptNode 
from base_agent import BaseAgent 
from agent_tools import PythonRequestsGeneratorForSwaggerAPI, SQLGeneratorForSQLite
from waypoint_robot_api import WaypointRobotSwaggerAPI

class WaypointRobotAgent(BaseAgent):
    def __init__(self, robot_name:str, db_host:str, db_port: int, 
                 api_query_host:str, api_query_port: int, 
                 api_backend_host:str, api_backend_port: int, 
                 log_level=logging.INFO, train=False):
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
        # Decide if we valid tool executions will save and bootstrap LLM
        self.train = train
        self.qs = Queue()

        # Initialize Robot Low Level Controller
        self.api = WaypointRobotSwaggerAPI(robot_name=robot_name, fastapi_host=api_backend_host, fastapi_port=api_backend_port, log_level=log_level)

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
        p = Process(target=self.process_qs, args=(self.agent,))
        p.start()
        super().__init__(api_query_host, api_query_port, partial(self.query))
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

        agent.add_tool(
            tool=SQLGeneratorForSQLite(
                robot_name=self.robot_name,
                db_connection=self.db_connection,
                train=self.train).generate_tool())

        return agent 

    def process_qs(self, agent: Agent):
        prompt_template = PromptTemplate(
            prompt="""
            You are a query result analyser. Analyse the given query and determine if the action taken was successful or not. If successful, answer True. Otherwise, answer False. Do not return anything else.
            Query: {query}
            Answer: 
            """)
        node = PromptNode(
            model_name_or_path="gpt-3.5-turbo-0301",
            api_key=self.API_KEY,
            model_kwargs={"temperature": 0.0})

        while True:
            time.sleep(5.0)
            if not self.qs.empty():
                q = self.qs.get()
                logging.info(f"Executing {q}")

                while True:
                    try:
                        results = agent.run(q)
                    except Exception as e:
                        continue

                    if 'answers' in results:
                        if results['answers']:
                            ans = results['answers'][0]
                            success = node.prompt(prompt_template=prompt_template, query=str(ans))
                            logging.info(f"Results: {success}")
                            if 'true' in str(success).lower():
                                break

    def query(self, q: str):
        self.qs.put(q)
        return True

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
        log_level=logging.INFO, train=False)
