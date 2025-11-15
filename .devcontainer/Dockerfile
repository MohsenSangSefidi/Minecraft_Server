FROM mcr.microsoft.com/devcontainers/python:3.11

# Install Java 17 and required dependencies
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    wget \
    curl \
    screen \
    net-tools \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Create minecraft user (optional)
RUN useradd -m -s /bin/bash minecraft

WORKDIR /workspace

# Expose ports
EXPOSE 25565 8080 8081 3000 25575