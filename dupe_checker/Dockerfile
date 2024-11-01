FROM ubuntu:latest
LABEL authors="Eivind"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY src/reuirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY /src ./src/
COPY /environment ./environment/

CMD["python", "src/DupeCheck.py"]