from haystack.components.rankers import TransformersSimilarityRanker
from utils.logger import log_on_init


class RankerService(TransformersSimilarityRanker):
    pass


@log_on_init()
class BgeReRankderService(RankerService):
    def __init__(self):
        super().__init__(
            model="BAAI/bge-reranker-v2-m3",
        )
