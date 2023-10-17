from langchain.text_splitter import Language
from langchain.document_loaders.generic import GenericLoader
from langchain.document_loaders.parsers import LanguageParser
from constants import Constants

loader = GenericLoader.from_filesystem(
    Constants.KNOWLEDGE_BASE_PATH,
    glob="**/*",
    suffixes=[".py"],
    parser=LanguageParser(language=Language.PYTHON, parser_threshold=500)
)
documents = loader.load()
print(len(documents))

