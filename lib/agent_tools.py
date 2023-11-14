import os
from haystack.agents import Tool
from haystack.agents.base import Pipeline
from haystack.nodes import PromptNode, PromptTemplate 

class PythonRequestsGeneratorForSwaggerAPI(Tool):
    def __init__(self, robot_name: str, swagger_definitions: str, server_connection_string: str):
        self.provider = "openai"
        self.API_KEY = os.environ['OPENAI_API_KEY']

        self.robot_name = robot_name
        self.swagger_definitions = swagger_definitions.replace('{', '{{').replace('}', '}}')
        self.server_connection_string = server_connection_string

    def generate_tool(self):
        prompt_template = PromptTemplate(
            prompt="""
            You are a python code generator. You generate python code to interact with robot {robot_name} using the following Swagger API: {swagger_definitions}.
            The Python code should use the requests library to a server on hosted on {server_connection_string}.
            Generate only one executable line. Do not use assignment to any variables.
            Query: {{query}}
            Answer: 
            """.format(robot_name=self.robot_name, swagger_definitions=self.swagger_definitions, server_connection_string=self.server_connection_string)
        )

        prompt_node = PromptNode(
            model_name_or_path="gpt-3.5-turbo-0301",
            api_key=self.API_KEY,
            default_prompt_template=prompt_template
        )

        pipeline = Pipeline()
        pipeline.add_node(component=prompt_node, name="prompt_node", inputs=["Query"])

        return Tool(name="PythonRequestsGeneratorForSwaggerAPI", pipeline_or_node=pipeline, output_variable="results",
                    description="This tool generates python code that interacts with a Swagger API to answer an agent thought. It uses the Python Requests library.")

