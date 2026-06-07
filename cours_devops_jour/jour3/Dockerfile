FROM python:3.13-slim AS builder
WORKDIR /install
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install --prefix=/install --no-cache-dir -r requirements.txt

FROM python:3.13-slim
COPY --from=builder /install /usr/local
WORKDIR /app
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
