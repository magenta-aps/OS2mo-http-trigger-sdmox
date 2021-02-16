FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

# Install mora_helpers
WORKDIR /srv/
RUN git clone https://github.com/OS2mo/os2mo-data-import-and-export && \
    cd os2mo-data-import-and-export && \
    git fetch && \
    git checkout feature/41008_sd_mox_fastapi && \
    pip install --no-cache-dir -e os2mo_data_import && \
    pip install --no-cache-dir -e integrations/SD_Lon/SDConnector

COPY ./requirements.txt /srv/requirements.txt
RUN pip install --no-cache-dir -r /srv/requirements.txt
RUN pip install --no-cache-dir more_itertools

WORKDIR /app
COPY ./app /app
