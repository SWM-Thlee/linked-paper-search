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

# Make port 80 available to the world outside this container (if needed)
EXPOSE 80

# Run main.py when the container launches
CMD ["python", "main.py"]
