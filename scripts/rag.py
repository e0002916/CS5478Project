from fastapi import Path
from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import TextConverter
from haystack.utils import build_pipeline, add_example_data, print_answers
import os
from pathlib import Path

provider = "openai"
API_KEY = os.environ['OPENAI_API_KEY']

document_store = InMemoryDocumentStore(use_bm25=True)
converter = TextConverter(remove_numeric_tables=True)

files_to_index = ["api/waypoint_robot.py.swagger.json"]
docs = [converter.convert(file_path=Path(file), meta=None)[0] for file in files_to_index]
document_store.write_documents(docs)

pipeline = build_pipeline(provider, API_KEY, document_store)
result = pipeline.run(query="Write an example PUT call to move a robot to a landmark called 'dropoff' and as a curl command.")

if result:
    print_answers(result, details="medium")
