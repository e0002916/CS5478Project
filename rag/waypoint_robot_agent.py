from haystack import Pipeline
from base_agent import BaseAgent, SQLExecutorNode
from haystack.agents import Agent, Tool
from haystack.nodes import PromptNode, PromptTemplate, TextConverter
from haystack.nodes.retriever import BM25Retriever
from waypoint_robot_api import WaypointRobotSwaggerAPI
from haystack.document_stores import InMemoryDocumentStore
import pyrqlite.dbapi2 as dbapi2
from pathlib import Path
from typing import List
import logging
from base_agent import BaseAgent, PythonRequestsExecutorNode, NonBlockingQueryRestAPI
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
        self.robot_name = robot_name
        self.provider = "openai"
        self.API_KEY = os.environ['OPENAI_API_KEY']
        self.swagger_prompt = None

        # Setup DB
        self.db_host = db_host
        self.db_port = db_port
        self.db_schemas = ""
        self.db_connection = self.init_db()

        # Setup API for query input
        self.api_query_host = api_query_host
        self.api_query_port = api_query_port

        # Setup API to interface with backend
        self.api_backend_host = api_backend_host
        self.api_backend_port = api_backend_port
        self.api = WaypointRobotSwaggerAPI(robot_name=robot_name, fastapi_host=api_backend_host, fastapi_port=api_backend_port, log_level=log_level)
        self.swagger_prompt = str(self.api.generate_swagger()).replace('{', '{{').replace('}', '}}')
        self.agent = self.setup_agent()

        # Run servers
        self.query_api = NonBlockingQueryRestAPI(self.api_query_host, self.api_query_port, self.query)
        self.api.run_server()

    def get_docs(self) -> List[Path]:
        fd_swagger, name_swagger = tempfile.mkstemp()
        with open(fd_swagger, 'r+') as f:
            json.dump(self.swagger_prompt, f)
            f.flush()

        fd_schemas, name_schemas = tempfile.mkstemp()
        with open(fd_schemas, 'r+') as f:
            f.write(f"{self.db_schemas}")
            f.flush()

        # Connection Details
        fd_conn, name_conn = tempfile.mkstemp()
        with open(fd_conn, 'r+') as f:
            f.write(f"The Robot with name f{self.robot_name} has a REST API hosted on server {self.api_backend_host} and port {self.api_backend_port}.")
            f.flush()

        # Naive implementation assumes robot believes it can access all waypoints
        fd_waypoint, name_waypoint = tempfile.mkstemp()
        with open(fd_waypoint, 'r+') as f:
            with self.db_connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM waypoints")
                for result in cursor.fetchall():
                    f.write(f"Robot {self.robot_name} can access the waypoint {result['name']} + \n")
            f.flush()

        return [Path(name_swagger), Path(name_schemas), Path(name_waypoint), Path(name_conn)]

    def setup_agent(self):
        swagger_codegen = self._setup_swagger_codegen_pipeline()
        sql_codegen = self._setup_sql_codegen_pipeline()

        python_executor = PythonRequestsExecutorNode()
        sql_executor = SQLExecutorNode(self.db_connection)
        prompt_node = PromptNode(model_name_or_path="gpt-3.5-turbo-0301", api_key=os.environ["OPENAI_API_KEY"], stop_words=["Observation:"])
        agent = Agent(prompt_node=prompt_node)

        agent.add_tool(Tool(name="python_code_generator_tool", 
                            pipeline_or_node=swagger_codegen, 
                            description="This tool generates python code to answer an agent thought.", output_variable="results"))

        agent.add_tool(Tool(name="python_code_execution_tool", 
                            pipeline_or_node=python_executor, 
                            description="Always use this after running the python_code_generator_tool. This tool executes python code to answer an agent thought. Pass as input the exact output from python_code_generator_tool.", output_variable="results"))

        agent.add_tool(Tool(name="sql_code_generator_tool", 
                            pipeline_or_node=sql_codegen, 
                            description="This tool generates sql queries to answer an agent thought. Use this to translate waypoint names into coordinates for use in moving robots.", output_variable="results"))

        agent.add_tool(Tool(name="sql_code_execution_tool", 
                            pipeline_or_node=sql_executor, 
                            description="Always use this after running the sql_code_generator_tool. This tool executes SQL code to answer an agent thought. Pass as input the exact output from sql_code_generator_tool.", output_variable="results"))


        return agent 

    def query(self, q: str):
        return self.agent.run(q)

    def _setup_sql_codegen_pipeline(self):
        prompt_template = PromptTemplate(
            prompt="""
            You are an sql code generator. You generate sql code to answer queries based on understanding the following relational database SQLite Schema: {schemas}.
            Generate only one executable line. Do not use placeholder for manual replacement. Do not add comments.
            Query: {{query}}
            Answer: 
            """.format(schemas=self.db_schemas)
        )

        prompt_node = PromptNode(
            model_name_or_path="gpt-3.5-turbo-0301",
            api_key=self.API_KEY,
            default_prompt_template=prompt_template
        )

        pipeline = Pipeline()
        pipeline.add_node(component=prompt_node, name="prompt_node", inputs=["Query"])

        return pipeline

    def _setup_swagger_codegen_pipeline(self):
        prompt_template = PromptTemplate(
            prompt="""
            You are a python code generator. You generate python code to interact with robot {robot_name} using the following Swagger API: {swagger_prompt}.
            The Python code should use the requests library to a server on host {api_backend_host} and port {api_backend_port} over HTTP. 
            Generate only one executable line. Do not use assignment to any variables.
            Query: {{query}}
            Answer: 
            """.format(robot_name=self.robot_name, swagger_prompt=self.swagger_prompt, api_backend_host=self.api_backend_host, api_backend_port=self.api_backend_port)
        )

        prompt_node = PromptNode(
            model_name_or_path="gpt-3.5-turbo-0301",
            api_key=self.API_KEY,
            default_prompt_template=prompt_template
        )

        pipeline = Pipeline()
        pipeline.add_node(component=prompt_node, name="prompt_node", inputs=["Query"])

        return pipeline

    def init_db(self):
        db_connection = dbapi2.connect(
            host=self.db_host,
            port=self.db_port,
            connect_timeout = 10
        )

        with db_connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for result in tables:
                table_name = result[0]
                if table_name == 'sqlite_sequence': 
                    continue
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{table_name}';")
                schema_infos = cursor.fetchall()
                for schema_info in schema_infos:
                    schema = schema_info[0]
                    self.db_schemas += f"{schema}\n"
            logging.info(self.db_schemas)

        return db_connection

if __name__ == "__main__":
    agent = WaypointRobotAgent(
        robot_name=sys.argv[1], db_host=sys.argv[2], db_port=int(sys.argv[3]),
        api_query_host=sys.argv[4], api_query_port=int(sys.argv[5]),
        api_backend_host=sys.argv[6], api_backend_port=int(sys.argv[7]), 
        log_level=logging.INFO)
