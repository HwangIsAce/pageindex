FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt \
    fastapi uvicorn python-multipart slowapi

COPY . .

ENV PYTHONPATH=/app
ENV PAGEINDEX_DATA_DIR=/app/data

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
