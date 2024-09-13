import os

from haystack.components.embedders import SentenceTransformersTextEmbedder
from utils.logger import log_on_init

bge_m3_model_path = os.getenv("BGE_M3_MODEL_PATH", "/app/models/bge-m3")


class EmbeddingService(SentenceTransformersTextEmbedder):
    pass


@log_on_init()
class BgeM3SetenceEmbedder(EmbeddingService):
    def __init__(self):
        super().__init__(model=bge_m3_model_path)


@log_on_init()
class GPTEmbeddingService(EmbeddingService):
    pass
