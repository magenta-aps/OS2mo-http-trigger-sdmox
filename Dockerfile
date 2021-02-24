# SPDX-FileCopyrightText: Magenta ApS
#
# SPDX-License-Identifier: MPL-2.0

FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

# Install mora_helpers
WORKDIR /srv/
RUN git clone https://github.com/OS2mo/os2mo-data-import-and-export && \
    pip install --no-cache-dir -e os2mo-data-import-and-export/os2mo_data_import

COPY ./requirements.txt /srv/requirements.txt
COPY ./requirements /srv/requirements
RUN pip install --no-cache-dir -r /srv/requirements.txt
RUN pip install --no-cache-dir more-itertools==8.6.0

WORKDIR /app
COPY ./app /app
