FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    python3 \
    curl && \
    rm -rf /var/lib/apt/lists/*
    
RUN curl -fsSL https://opencode.ai/install | bash
