FROM python:3.12-slim
WORKDIR /app
COPY src/ ./src/
EXPOSE 8889
CMD ["python3", "src/main.py"]
