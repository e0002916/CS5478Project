from multiprocessing import Process
from abc import ABC, abstractmethod
from fastapi import FastAPI
import uvicorn


class NonBlockingQueryRestAPI:
    def __init__(self, fastapi_host: str, fastapi_port:int, callback): 
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
    def __init__(self, fastapi_host: str, fastapi_port: int, query_callback):
        NonBlockingQueryRestAPI(fastapi_host, fastapi_port, query_callback)

    @abstractmethod
    def setup_agent(self):
       raise NotImplementedError 

    @abstractmethod
    def query(self, query: str):
       raise NotImplementedError 

if __name__ == "__main__":
    pass
