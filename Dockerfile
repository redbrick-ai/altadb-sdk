FROM python:3.12-slim
WORKDIR /usr/src/app

ENV VIRTUAL_ENV="/usr/src/lib/.venv" PATH="/usr/src/lib/.venv/bin:$PATH" ALTADB_DISABLE_VERSION_CHECK="1"
RUN apt-get update && \
    apt-get -y install gcc && \
    python -m venv /usr/src/lib/.venv && \
    pip install --upgrade pip setuptools psutil gputil

COPY altadb*.whl ./
RUN pip install altadb*.whl && rm altadb*.whl

CMD ["python", "-i", "-c", "import altadb"]
