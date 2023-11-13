from multiprocessing import Process
from abc import ABC, abstractmethod
from haystack.nodes.base import BaseComponent
from fastapi import FastAPI
from requests import Response
import uvicorn
import logging
import json


class PythonRequestsExecutorNode(BaseComponent):
    outgoing_edges = 1
    def __init__(self):
        pass

    def run(self, query: str):
        global r
        exec("import requests; global r; r = {query}".format(query=query))
        logging.info(r.json())
        output={
            "results": r.json()
        }
        return output

    def run_batch(self):
        pass

class NonBlockingQueryRestAPI:
    def __init__(self, fastapi_host, fastapi_port:int, callback): 
        self.app = FastAPI()
        self.fastapi_host = fastapi_host
        self.fastapi_port = fastapi_port
        self.callback = callback

        @self.app.get("/query/")
        async def query(query: str):
            self.callback(query)

        self.proc = Process(target=uvicorn.run,
                            args=(self.app,),
                            kwargs={
                                "host": self.fastapi_host,
                                "port": self.fastapi_port,
                                "log_level": "info"
                            },
                            daemon=True)
        self.proc.start()

class BaseAgent(ABC):
    @abstractmethod
    def __init__(self):
       raise NotImplementedError 

    @abstractmethod
    def get_docs(self):
       raise NotImplementedError 

    @abstractmethod
    def setup_agent(self):
       raise NotImplementedError 

    @abstractmethod
    def query(self, query: str):
       raise NotImplementedError 

if __name__ == "__main__":
    pass
