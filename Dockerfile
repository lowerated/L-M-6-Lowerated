# Use the official Python 3.10 image as the base image
FROM python:3.10

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main.py file into the container
COPY . .

# Run the main.py file
CMD ["python", "main.py"]