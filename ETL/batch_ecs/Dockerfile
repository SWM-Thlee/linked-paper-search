# Use an official Python runtime as a parent image
# Stage 1: 모델을 미리 다운로드하여 캐시하는 빌더 이미지
FROM python:3.9-slim AS model-builder

RUN pip install --no-cache-dir huggingface_hub[cli]==0.24.6

# BAAI/bge-m3 모델의 전체 파일 다운로드 및 캐시 저장
RUN huggingface-cli download BAAI/bge-m3 config_sentence_transformers.json --cache-dir=/model_cache && \
    huggingface-cli download BAAI/bge-m3 modules.json --cache-dir=/model_cache && \
    huggingface-cli download BAAI/bge-m3 README.md --cache-dir=/model_cache && \
    huggingface-cli download BAAI/bge-m3 sentence_bert_config.json --cache-dir=/model_cache && \
    huggingface-cli download BAAI/bge-m3 config.json --cache-dir=/model_cache && \
    huggingface-cli download BAAI/bge-m3 pytorch_model.bin --cache-dir=/model_cache && \
    huggingface-cli download BAAI/bge-m3 tokenizer_config.json --cache-dir=/model_cache && \
    huggingface-cli download BAAI/bge-m3 sentencepiece.bpe.model --cache-dir=/model_cache && \
    huggingface-cli download BAAI/bge-m3 tokenizer.json --cache-dir=/model_cache && \
    huggingface-cli download BAAI/bge-m3 special_tokens_map.json --cache-dir=/model_cache && \
    huggingface-cli download BAAI/bge-m3 1_Pooling/config.json --cache-dir=/model_cache


# Stage 2: 최종 런타임 이미지
FROM python:3.9-slim


# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Set environment variables (optional)
ENV OMP_NUM_THREADS=4
ENV KMP_AFFINITY="granularity=fine,compact,1,0"

# Stage 1에서 모델 캐시 파일을 복사
COPY --from=model-builder /model_cache /root/.cache/huggingface/hub

# Run main.py when the container launches
CMD ["python", "main.py"]
