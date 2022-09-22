FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy in a very basic django app where we will configure a UI so you can see
# the javascript interaction with the openresty_azure login piece and session refresh.
ADD . /code
WORKDIR /code

COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

