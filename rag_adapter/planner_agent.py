# import logging
# import os
# from haystack.agents import Tool
# from haystack.document_stores import InMemoryDocumentStore
# from datasets import load_dataset
# from haystack.nodes import BM25Retriever, EmbeddingRetriever, FARMReader
# from haystack.pipelines import ExtractiveQAPipeline
# from haystack.agents import Agent
# from haystack.nodes import PromptNode
#
# logging.basicConfig(format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING)
# logging.getLogger("haystack").setLevel(logging.INFO)
#
# remote_dataset = load_dataset("Tuana/presidents", split="train")
#
# document_store = InMemoryDocumentStore(use_bm25=True)
# document_store.write_documents(remote_dataset)
#
# retriever = BM25Retriever(document_store=document_store)
#
# reader = FARMReader(model_name_or_path="deepset/roberta-base-squad2", use_gpu=True)
# presidents_qa = ExtractiveQAPipeline(reader=reader, retriever=retriever)
#
# prompt_node = PromptNode(model_name_or_path="text-davinci-003", api_key=os.environ["OPENAI_API_KEY"], stop_words=["Observation:"])
# agent = Agent(prompt_node=prompt_node)
#
# search_tool = Tool(
#     name="USA_Presidents_QA",
#     pipeline_or_node=presidents_qa,
#     description="useful for when you need to answer questions related to the presidents of the USA.",
#     output_variable="answers",
# )
# agent.add_tool(search_tool)
#
# result = agent.run("Arrange a robot delivery")

from haystack.agents import Agent, Tool
from haystack.nodes import PromptNode
from haystack.nodes.base import BaseComponent
import requests
import os

class RagQueryNode(BaseComponent):
    outgoing_edges = 1

    def __init__(self, url):
        self.url = url

    def run(self, query: str):
        r = requests.get(self.url, params={"q" :query})
        print(r)
        output={
            "response": r.text
        }
        return output

    def run_batch(self):
        pass

class PlannerAgent:
    def __init__(self):
        self.query_node = RagQueryNode('http://127.0.0.1:8000/query/')
        self.prompt_node = PromptNode(model_name_or_path="gpt-3.5-turbo-0301", api_key=os.environ["OPENAI_API_KEY"], stop_words=["Observation:"])
        self.agent = Agent(prompt_node=self.prompt_node)
        self.query_tool = Tool(name="rag_query_tool", pipeline_or_node=self.query_node, description="Useful for making RAG queries to any robot in the environment", output_variable="response")
        self.agent.add_tool(self.query_tool)

    def run(self, query: str):
        self.agent.run(query)

if __name__ == "__main__":
    planner = PlannerAgent()
    result = planner.run("What landmark is the robot at?")
