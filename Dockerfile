# Docker là tùy chọn; có thể chạy local trực tiếp bằng Python.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt requirements-production.txt ./
RUN pip install --no-cache-dir -r requirements-production.txt
RUN useradd --create-home --uid 10001 app
COPY --chown=app:app src/ /app/src/
USER app
WORKDIR /app/src
EXPOSE 8000
CMD ["uvicorn", "core.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
