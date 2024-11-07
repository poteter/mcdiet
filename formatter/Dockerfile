FROM python:3.9-slim
LABEL authors="Eivind"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY environment/ ./environment/

CMD ["python", "src/main.py"]