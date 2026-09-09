FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir '.[postgres]' && \
    useradd --uid 1001 --create-home appuser && \
    mkdir -p /data && chown appuser:appuser /data
COPY config ./config
USER 1001:1001
ENV WES_BACKENDS_CONFIG=/app/config/backends.yaml
ENV WES_DATABASE_URL=sqlite:////data/wes-gateway.db
EXPOSE 8090
CMD ["uvicorn", "wes_api_gateway.main:app", "--host", "0.0.0.0", "--port", "8090"]
