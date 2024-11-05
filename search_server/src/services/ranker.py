import os

from haystack.components.rankers import TransformersSimilarityRanker
from utils.logger import log_on_init

bge_reranker_model_path = os.getenv(
    "BGE_RERANKER_MODEL_PATH", "/app/models/bge-reranker-v2-m3"
)


class Ranker(TransformersSimilarityRanker):
    pass


@log_on_init()
class BgeReRankder(Ranker):
    def __init__(self, top_k: int = 100, device=None):
        super().__init__(
            model="BAAI/bge-reranker-v2-m3",
            top_k=top_k,
            device=device,
        )
