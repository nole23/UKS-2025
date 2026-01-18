# Koristi službenu Python sliku
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Postavi radni direktorijum
WORKDIR /app

# Kopiraj requirements i instaliraj zavisnosti
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Kopiraj ostatak Django projekta
COPY . /app/

# Expose port na kojem Django/Gunicorn radi
EXPOSE 8000

# CMD je preuzet iz docker-compose.yml, ovdje ga ne moramo stavljati
