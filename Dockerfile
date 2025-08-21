FROM python:3.11-alpine

WORKDIR /app

COPY server.py dns_lookup.py ./
COPY index.html ./
COPY assets/ ./assets/

EXPOSE 7001

CMD ["python3", "server.py"]
