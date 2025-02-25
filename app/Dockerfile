FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app -r requirements.txt
COPY app.py .

FROM gcr.io/distroless/python3:nonroot
WORKDIR /app
COPY --from=builder /app /app

ARG SERVER_PORT=5000
EXPOSE ${SERVER_PORT}
USER nonroot
CMD ["app.py"]
