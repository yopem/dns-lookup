FROM python:3.11-alpine

WORKDIR /app

COPY *.py ./
COPY web/ ./web/

EXPOSE 7001

CMD ["python3", "server.py"]
