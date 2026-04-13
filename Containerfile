ARG API_VERSION=1.2.0

FROM python:3.13-slim-trixie AS client-library

ARG API_VERSION

RUN DEBIAN_FRONTEND=noninteractive apt-get update                  \
    && DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes \
         git

RUN git clone -b "v${API_VERSION}" https://github.com/umg-minai/indicate-data-exchange-api-client

WORKDIR indicate-data-exchange-api-client

RUN python3 -m venv .venv

RUN . .venv/bin/activate && pip install -r requirements.txt && pip install build

RUN . .venv/bin/activate && python3 -m build

RUN cp dist/indicate_data_exchange_api_client-${API_VERSION}-py3-none-any.whl \
       /indicate_data_exchange_api_client-${API_VERSION}-py3-none-any.whl

FROM python:3.13-slim-trixie

ARG API_VERSION

RUN DEBIAN_FRONTEND=noninteractive apt-get update                  \
    && DEBIAN_FRONTEND=noninteractive apt-get install --assume-yes \
         curl                                                      \
    && apt-get clean

COPY --from=client-library                                       \
       /indicate_data_exchange_api_client-${API_VERSION}-py3-none-any.whl \
       /tmp
RUN pip install /tmp/indicate_data_exchange_api_client-${API_VERSION}-py3-none-any.whl

COPY requirements.txt              /app/
COPY indicate_data_exchange_client /app/indicate_data_exchange_client
COPY static                        /app/static

WORKDIR /app

RUN pip install --root-user-action=ignore -r requirements.txt

ENV PYTHONPATH=.

ENV LISTEN_ADDRESS=0.0.0.0
ENV LISTEN_PORT=8080

EXPOSE ${LISTEN_PORT}

CMD ["python3", "indicate_data_exchange_client/main.py"]

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${LISTEN_PORT}/review
