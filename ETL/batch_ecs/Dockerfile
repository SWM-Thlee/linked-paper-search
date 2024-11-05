# Use an official Python runtime as a parent image
# Stage 1: 모델을 미리 다운로드하여 캐시하는 빌더 이미지
FROM python:3.9-slim AS model-builder

RUN pip install --no-cache-dir haystack-ai==2.6.1 sentence-transformers==3.2.1

COPY download_model.py .

# BAAI/bge-m3 모델의 전체 파일 다운로드 및 캐시 저장
RUN python3 download_model.py

# Stage 2: 최종 런타임 이미지
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Stage 1에서 모델 캐시 파일을 복사
COPY --from=model-builder /root/.cache/huggingface/hub /root/.cache/huggingface/hub

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Set environment variables (optional)
ENV OMP_NUM_THREADS=4
ENV KMP_AFFINITY="granularity=fine,compact,1,0"

# Run main.py when the container launches
CMD ["python", "main.py"]
