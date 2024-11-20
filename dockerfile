# Use the official Python image as a base
FROM python:3.10.15-slim-bullseye

# Update the package list and install Python and cron
RUN apt-get update && apt-get install -y \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /usr/src/app

# Copy contents in this repo to docker image
COPY requirements.txt /app/requirements.txt

RUN pip3 install --no-cache-dir -r /app/requirements.txt

WORKDIR /app

COPY . /app

#Expose the port your app runs on
EXPOSE 5000

# Command to run your application
CMD ["python3", "main.py"]