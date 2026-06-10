FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /backend

RUN mkdir -p uploads

RUN pip install --no-cache-dir uv

# Copy the backend files
COPY . .

# Sync dependencies
RUN uv sync --no-dev

# Ensure entrypoint is executable
RUN chmod +x /backend/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/bin/bash", "/backend/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
