import os
import logging
from pathlib import Path
from haystack.agents import Tool
from haystack.agents.base import Pipeline
from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import BM25Retriever, PromptNode, PromptTemplate 
from haystack.nodes.base import BaseComponent
from haystack.utils import convert_files_to_docs

class PythonRequestsExecutorNode(BaseComponent):
    outgoing_edges = 1
    def __init__(self, codegen_node: PromptNode, data_store_path:str, log_level=logging.INFO, train=False):
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.codegen_node = codegen_node
        self.data_store_path = data_store_path
        self.train = train

    def run(self, query: str):
        codegen = self.codegen_node(query)
        logging.debug(codegen)
        code = codegen[0]

        logging.info(f"Attempting to execute code {code}..")
        try:
            import requests
            r = eval(code)
            if r.status_code != 200:
                error_msgs = r.json()['detail']
                output={
                    "results": f"The server failed to return a valid response, returning {error_msgs} instead. Please regenerate the code."
                }
            else:
                output={
                    "results": r.json()
                }
                if self.train:
                    f = open(self.data_store_path, 'r+')
                    if code not in f.read():
                        f.write(f"{code} \n")
                    f.close()
            return output, "output_1"
        except Exception as e:
            output = {
                "results": f"Execution failed with error: {e}. Please regenerate code that fixes this error."
            }

            return output, "output_1"

    def run_batch(self):
        pass

class PythonRequestsGeneratorForSwaggerAPI(Tool):
    def __init__(self, robot_name: str, swagger_definitions: str, server_connection_string: str, train=False):
        self.provider = "openai"
        self.API_KEY = os.environ['OPENAI_API_KEY']

        self.robot_name = robot_name
        self.swagger_definitions = swagger_definitions.replace('{', '{{').replace('}', '}}')
        self.server_connection_string = server_connection_string
        self.data_store_path = f"data/{self.robot_name}_PythonRequestsGeneratorForSwaggerAPI.txt"
        self.train = train

    def generate_tool(self):
        f = open(self.data_store_path, "r+")
        prompt_template = PromptTemplate(
            prompt="""
            You are a python code generator. You generate python code to interact with robot {robot_name} strictly following the following Swagger API: {swagger_definitions}.
            The Python code must use the requests library to a server on hosted on {server_connection_string}.
            Generate only one executable line. Do not assign the requests command to any variables.
            The following list of python functions are valid. Use them to improve your code generation accuracy.
            {data_store}
            Query: {{query}}
            Answer: 
            """.format(robot_name=self.robot_name, swagger_definitions=self.swagger_definitions, server_connection_string=self.server_connection_string, data_store=f.read())
        )
        f.close()

        node = PythonRequestsExecutorNode(PromptNode(
            model_name_or_path="gpt-3.5-turbo-0301",
            api_key=self.API_KEY,
            default_prompt_template=prompt_template,
            model_kwargs={"temperature": 0.0}
        ), data_store_path=self.data_store_path, train=self.train)

        pipeline = Pipeline()
        pipeline.add_node(component=node, name="prompt_node", inputs=["Query"])

        return Tool(name="PythonRequestsGeneratorForSwaggerAPI", pipeline_or_node=pipeline, output_variable="results",
                    description=f"This tool interacts with a Swagger API to control or get information about the robot {self.robot_name}.")

class SQLExecutorNode(BaseComponent):
    outgoing_edges = 1
    def __init__(self, codegen_node: PromptNode, db_connection, data_store_path: str, log_level=logging.INFO, train=False):
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.codegen_node = codegen_node
        self.db_connection = db_connection
        self.data_store_path = data_store_path
        open(self.data_store_path, 'a+').close()
        self.train = train

    def run(self, query: str):
        code = self.codegen_node(query)[0]

        logging.info(f"Attempting to execute code {code}..")
        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(code)
                results = cursor.fetchall()
                output = ""
                for result in results:
                    output += f"{result}\n"
            output={
                "results": output
            }

            if self.train:
                f = open(self.data_store_path, 'r+')
                if code not in f.read():
                    f.write(f"{code} \n")
                f.close()
            return output, "output_1"
        except Exception as e:
            output = {
                "results": f"Execution failed with error: {e}. Please regenerate code that fixes this error."
            }

            return output, "output_1"

    def run_batch(self):
        pass

class SQLGeneratorForSQLite(Tool):
    def __init__(self, robot_name: str, db_connection, train=False):
        self.robot_name = robot_name
        self.provider = "openai"
        self.API_KEY = os.environ['OPENAI_API_KEY']
        self.db_connection = db_connection
        self.data_store_path = f"data/{self.robot_name}_SQLGeneratorForSQLite.txt"
        open(self.data_store_path, 'a+').close()
        self.train = train

    def generate_tool(self):
        db_schemas = ""
        with self.db_connection.cursor() as cursor:
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
                    db_schemas += f"{schema}\n"

        f = open(self.data_store_path, "a+")
        prompt_template = PromptTemplate(
            prompt="""
            You are an sql code generator. You generate sql code to answer queries based on understanding the following relational database SQLite Schema: {db_schemas}.
            Do not use placeholders. Do not add comments. Only generate a single SQL Query. Do not use nested queries. Only use SELECT * in this query.
            The following list of SQL functions are valid. Use them to improve your code generation accuracy.
            {data_store}
            Query: {{query}}
            Answer: 
            """.format(db_schemas=db_schemas, data_store=f.read())
        )
        f.close()

        node = SQLExecutorNode(PromptNode(
            model_name_or_path="gpt-3.5-turbo-0301",
            api_key=self.API_KEY,
            default_prompt_template=prompt_template,
            model_kwargs={"temperature": 0.0}
        ), self.db_connection, data_store_path=self.data_store_path, train=self.train)

        pipeline = Pipeline()
        pipeline.add_node(component=node, name="prompt_node", inputs=["Query"])

        return Tool(name="SQLGenerateForSQLite", pipeline_or_node=pipeline, output_variable="results",
                    description="This tool provides coordinate information about waypoints, and the coordinates of dispensers.")
