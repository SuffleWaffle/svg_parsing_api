# --- Base Debian 12 Bookworm (Ubuntu-family) Python 3.11.4 image
FROM python:3.11.4-bookworm

# - Update and upgrade Ubuntu packages
RUN apt-get clean
RUN apt-get update && apt-get upgrade -y

# - Install basic Ubuntu Linux packages
#RUN apt-get install htop -y
#RUN apt-get install software-properties-common -y
#RUN apt-get update --fix-missing

# - Install basic Python packages
#RUN apt-get install -y python3-pip python-dev
#RUN apt-get install python3-setuptools
#RUN apt-get update --fix-missing

# --- SET THE WORKING DIRECTORY ---
WORKDIR /app

# - Install Python packages
COPY requirements.txt /app
RUN pip install --upgrade pip && pip install --upgrade setuptools
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN apt-get update --fix-missing

# - Copy the APP code to the source
COPY . /app

## - Set default ENV variables
#ENV APP_HOST=0.0.0.0
#ENV APP_PORT=8001
#ENV APP_WORKERS=4
#ENV APP_TIMEOUT_SEC=1800
#ENV APP_GRACEFUL_TO_SEC=120
#
## - Expose Docker image's internal port for API to map it to the host's port
#EXPOSE $APP_PORT/tcp
#
## - Gunicorn PROD command to run FastAPI application
#CMD gunicorn main:app --worker-tmp-dir /dev/shm -b $APP_HOST:$APP_PORT -w $APP_WORKERS -t $APP_TIMEOUT_SEC --graceful-timeout $APP_GRACEFUL_TO_SEC -k uvicorn.workers.UvicornWorker