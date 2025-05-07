FROM python:3.9-slim
RUN apt-get update && apt-get install -y \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*
RUN pip install impacket==0.10.0
COPY smb_server.py /app/
WORKDIR /app
CMD ["python", "smb_server.py"]