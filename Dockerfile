FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
COPY coding_agent/ coding_agent/
RUN pip install --no-cache-dir -e .
EXPOSE 8080
CMD ["coding-agent", "serve", "--host", "0.0.0.0", "--port", "8080"]