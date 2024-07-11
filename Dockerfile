FROM python:3.12.4

# Set the working directory in the container
#WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

## Copy the rest of the application code into the container
COPY . .

# Set environment variables
ENV ENVIRONMENT=docker

# Run the application
CMD ["python", "app/app.py"]