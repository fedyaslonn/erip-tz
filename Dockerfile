FROM python:3.13-slim AS builder

WORKDIR /app
RUN pip install --no-cache-dir poetry==2.5.1
COPY pyproject.toml poetry.lock ./
RUN python -m venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
RUN poetry install --only main --no-root

FROM python:3.13-slim
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
COPY . .
COPY entrypoint.sh /entrypoint.sh

RUN sed -i 's/\r$//' /entrypoint.sh
ENTRYPOINT ["sh", "/entrypoint.sh"]
