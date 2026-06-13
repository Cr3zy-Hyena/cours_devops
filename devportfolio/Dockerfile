#importation de python
FROM python:3.11-slim AS builder 
WORKDIR /build
COPY requirements.txt .
#installe les dependances 
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

#importation de python sans les builds
FROM python:3.11-slim

#utilisateur non-root (securite)
RUN useradd -m -u 1000 appuser
WORKDIR /app

#copier les deps du stage 1
COPY --from=builder /install /usr/local

#copier le code
COPY . . 
RUN chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
#les environnemnts pour Flask et Python
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONYWRITEBYTHECODE=1

#Gunicorn : serveur WSGI de production
CMD ["gunicorn","--bind","0.0.0.0:5000","--workers","2","run:app"]
