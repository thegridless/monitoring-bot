# Use the smallest Python image
FROM python:3.12-alpine

# Set working directory
WORKDIR /app

# Install required system packages
RUN apk add --no-cache gcc musl-dev python3-dev

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Remove build dependencies to reduce image size
RUN apk del gcc musl-dev python3-dev

# Copy the application
COPY main.py .
COPY .env .

# Run the script
CMD ["python", "main.py"] 