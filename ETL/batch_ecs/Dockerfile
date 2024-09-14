# Use an official Python runtime as a parent image
FROM deepset/haystack:base-main


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

# 모델을 다운로드할 디렉토리 생성
# 모델 다운로드 및 지정된 경로에 저장
RUN mkdir -p /app/models/bge-m3 && \
    python -c "from transformers import AutoModel; AutoModel.from_pretrained('BAAI/bge-m3', cache_dir='/app/models/bge-m3')"

EXPOSE 80

ENV BGE_M3_MODEL_PATH=/app/models/bge-m3

# Run main.py when the container launches
CMD ["python", "main.py"]
