from abc import ABC

import torch
from sentence_transformers import SentenceTransformer
from transformers import BertModel, BertTokenizer

from utils.logger import log_on_init


class EmbeddingService(ABC):

    def embed_text(self, query: str):
        pass


@log_on_init("uvicorn.info")
class BertEmbeddingService(EmbeddingService):
    def __init__(self):
        self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        self.model = BertModel.from_pretrained("bert-base-uncased")

    def embed_text(self, query: str):
        inputs = self.tokenizer(query, return_tensors="pt")
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state.squeeze(0).mean(dim=0).tolist()


@log_on_init("uvicorn.info")
class SentenceEmbeddingService(EmbeddingService):

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed_text(self, query):
        return self.model.encode(query).tolist()


@log_on_init("uvicorn.info")
class GPTEmbeddingService(EmbeddingService):
    def __init__(self):
        pass

    def embed_text(self, query: str):
        pass
