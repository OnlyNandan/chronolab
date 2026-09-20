# Build context is the repo root (see docker-compose.yml / deploy.sh) so backend/
# can be imported as the "backend" package the same way it runs locally
# (uvicorn backend.server:app from the repo root — see README.md).
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/

RUN useradd --create-home --uid 1000 chronolab
USER chronolab

EXPOSE 8000

CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000"]
