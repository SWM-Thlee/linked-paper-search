from haystack.components.embedders import SentenceTransformersDocumentEmbedder

embedding_model = "BAAI/bge-m3"
document_embedder = SentenceTransformersDocumentEmbedder(model=embedding_model)
document_embedder.warm_up()
