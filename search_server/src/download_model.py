# use this code to download the model in docker image build

from services.embedding import BgeM3SetenceEmbedder
from services.ranker import BgeReRankder

embedder = BgeM3SetenceEmbedder()
embedder.warm_up()

ranker = BgeReRankder()
ranker.warm_up()
