import logging
import sys
import uvicorn
from fastapi.openapi.utils import get_openapi
import pika
import json
import tempfile
from fastapi import FastAPI
from haystack.document_stores import InMemoryDocumentStore, KeywordDocumentStore
from haystack.utils import print_answers
from pathlib import Path
from typing import List
from haystack import Document
from abstract_rag_adapter import AbstractRagAdapter
from haystack.nodes import AnswerParser, PromptNode, PromptTemplate, BM25Retriever, TextConverter
from haystack.pipelines import Pipeline

class SwaggerRagAdapterForWaypointRobot(AbstractRagAdapter):
    def __init__(self, robot_name:str, log_level:int=logging.INFO, fastapi_host:str='localhost', fastapi_port:int=8000, mq_host:str='localhost', mq_port=5672):
        self.robot_name = robot_name
        self.app = FastAPI()
        self.fastapi_host = fastapi_host
        self.fastapi_port = fastapi_port
        self.mq_host = mq_host
        self.mq_port = mq_port
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.mq_host, port=self.mq_port))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='move',
                                      exchange_type='direct')
        super().__init__(log_level)

    def get_query_prompt(self):
        prompt = """Create a concise and informative answer using only code for a given question 
        based solely on the given documents. You must only use information from the given documents. 
        Do not explain. Only use code. Tailor your answer to interact with a server on {fastapi_host} and port {fastapi_port} using the curl command using HTTP.
        If multiple documents contain the answer, cite those documents like ‘as stated in Document[number], Document[number], etc.’. 
        If the documents do not contain the answer to the question, say that ‘answering is not possible given the available information.’
        {{join(documents, delimiter=new_line, pattern=new_line+'Document[$idx]: $content', str_replace={{new_line: ' ', '[': '(', ']': ')'}})}}
        Question: {{query}}; Answer:""".format(fastapi_host=self.fastapi_host, fastapi_port=self.fastapi_port)
        return prompt

    def run_server(self):
        uvicorn_config = uvicorn.Config(self.app, host=self.fastapi_host, port=self.fastapi_port)
        server = uvicorn.Server(uvicorn_config)
        server.run()

    def init_backend_api(self):
        @self.app.put("/move/{landmark}")
        async def move(landmark, level:str = '0'):
            message = {"name": landmark, "level": level}
            self.channel.queue_declare(queue=self.robot_name)
            self.channel.basic_publish(exchange='move',
                                  routing_key=self.robot_name,
                                  body=json.dumps(message))
            # TODO: Check success of call
            return True

    def init_rag(self, docs_path: List[Path]):
        document_store = InMemoryDocumentStore(use_bm25=True)
        converter = TextConverter(remove_numeric_tables=True)
        docs = [converter.convert(file_path=Path(file), meta=None)[0] for file in docs_path]
        document_store.write_documents(docs)
        self.pipeline = self.build_pipeline(document_store)

    def get_rag_docs(self) -> List[Path]:
        fd, name = tempfile.mkstemp()
        with open(fd, 'w') as f:
            json.dump(self._generate_swagger(), f)
            f.flush()

        return [Path(name)]

    def init_query_api(self):
        @self.app.get("/query/")
        async def query(q: str):
            return self.query(q)

    def query(self, q: str):
        result = self.pipeline.run(query=q)
        if result:
            return result

    def _generate_swagger(self):
       return get_openapi(
           title=f"{__file__} API",
           version="1.0.0",
           description="",
           routes=self.app.routes
       )

    def build_pipeline(self, document_store: KeywordDocumentStore):
        retriever = BM25Retriever(document_store=document_store, top_k=5)
        prompt_template = PromptTemplate(
            prompt=self.get_query_prompt(),
            output_parser=AnswerParser(reference_pattern=r"Document\[(\d+)\]"),
        )
        prompt_node = PromptNode(
            model_name_or_path="gpt-3.5-turbo-0301",
            api_key=self.API_KEY,
            default_prompt_template=prompt_template)

        query_pipeline = Pipeline()
        query_pipeline.add_node(component=retriever, name="retriever", inputs=["Query"])
        query_pipeline.add_node(component=prompt_node, name="prompt_node", inputs=["retriever"])

        return query_pipeline

if __name__ == "__main__":
    adapter = SwaggerRagAdapterForWaypointRobot(robot_name=sys.argv[1])
    adapter.run_server()

