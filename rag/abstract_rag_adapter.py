from abc import ABC, abstractmethod
import os
import logging
from typing import List
from pathlib import Path

from haystack.document_stores import KeywordDocumentStore

class AbstractRagAdapter(ABC):
    def __init__(self, log_level=logging.INFO):
        self.provider = "openai"
        self.API_KEY = os.environ['OPENAI_API_KEY']
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s')

        self.init_backend_api()
        self.init_rag(self.get_rag_docs())
        self.init_query_api()

    @abstractmethod
    def init_db(self):
        pass

    @abstractmethod
    def init_backend_api(self):
        pass

    @abstractmethod
    def init_rag(self, docs_path: List[Path]):
        pass

    @abstractmethod
    def get_rag_docs(self) -> List[Path]:
        pass

    @abstractmethod
    def init_query_api(self):
        pass

    @abstractmethod
    def query(self):
        pass

    @abstractmethod
    def get_query_prompt(self):
        pass

    @abstractmethod
    def build_pipeline(self, docs: KeywordDocumentStore):
        pass
