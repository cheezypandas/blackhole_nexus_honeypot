FROM python:3.9-slim
RUN pip install flask==2.0.1
COPY webdav.py /app/
WORKDIR /app
CMD ["python", "webdav.py"]