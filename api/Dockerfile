FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_DEFAULT_TIMEOUT=120 PIP_DISABLE_PIP_VERSION_CHECK=1

# The `api` package lives at the repo root (context = repo root), so copy it in place
# BEFORE installing so setuptools can discover and build the package correctly.
COPY api/pyproject.toml ./
COPY api ./api
RUN pip install --no-cache-dir --timeout 120 .

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
