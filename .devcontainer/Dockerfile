FROM mcr.microsoft.com/devcontainers/python:3.11

# Install Java 17
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    wget \
    curl \
    screen \
    net-tools \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Create minecraft user
RUN useradd -m -s /bin/bash minecraft

# Install Node.js for web dashboard (optional)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

WORKDIR /workspace

# Expose ports
EXPOSE 25565 8080 8081 3000 25575