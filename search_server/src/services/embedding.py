from abc import ABC

from haystack.components.embedders import SentenceTransformersTextEmbedder
from utils.logger import log_on_init


class EmbeddingService(SentenceTransformersTextEmbedder):
    pass


@log_on_init("uvicorn.info")
class BgeM3SetenceEmbedder(EmbeddingService):
    def __init__(self):
        super().__init__(model="BAAI/bge-m3")


@log_on_init("uvicorn.info")
class GPTEmbeddingService(EmbeddingService):
    pass
