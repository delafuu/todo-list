FROM python:3.11-slim
WORKDIR /app

COPY fetch/src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY fetch/src/ .
COPY comun/ ./comun/

EXPOSE 7070
CMD ["python", "app.py"]