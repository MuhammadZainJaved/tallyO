FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=5

WORKDIR /app

ARG REQUIREMENTS_FILE=base.txt
COPY requirements/ /app/requirements/
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r "/app/requirements/${REQUIREMENTS_FILE}"

COPY pytest.ini /app/pytest.ini
COPY backend/ /app/backend/

RUN addgroup --system django \
    && adduser --system --ingroup django django \
    && chown -R django:django /app

USER django
WORKDIR /app/backend

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

