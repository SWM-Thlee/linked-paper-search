# Semantic Search and ETL Pipeline

This project is designed to create a Semantic Search Engine and an Academic Paper ETL pipeline using AWS infrastructure.

## Overview
This project leverages advanced semantic search capabilities and an efficient ETL (Extract, Transform, Load) pipeline to handle academic papers. It is built on AWS and utilizes `Haystack` for retrieval and indexing, ensuring high scalability and performance.

## Search Engine

> Distributed Retriever and Indexing service built with `Haystack`

The search service is powered by `FastAPI` and `Haystack` retriever, providing a REST API for semantic search. This service enables users to submit queries and receive results through a sophisticated semantic search process, ensuring accurate and relevant information retrieval.

### Key Features:
- **FastAPI integration**: Efficient and scalable API management.
- **Haystack-powered retrieval**: Enhanced semantic search capabilities with distributed processing.
- **REST API**: User-friendly API for interacting with the search engine.

## ETL Pipeline

> Extract paper metadata from Arxiv, embed paper data into vectors, and load them into AWS OpenSearch.

The ETL pipeline is built using the `AWS Cloud Development Kit (CDK)` and is modularized into different layers to ensure a robust and stable data flow. The process involves extracting metadata from academic papers, embedding them into vectors, and indexing them into AWS OpenSearch for seamless retrieval.

### Pipeline Stages:
- **Extraction**: Pull metadata from Arxiv.
- **Embedding**: Convert paper data into vector embeddings using `Haystack`.
- **Loading**: Index and store data in AWS OpenSearch.

### Key Features:
- **AWS CDK**: Infrastructure as code for seamless deployment and management.
- **Modular pipeline**: Ensures a stable and scalable data processing flow.
- **Haystack pipeline**: Powers the embedding and indexing stages for optimized performance.
