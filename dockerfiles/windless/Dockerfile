FROM python:3.5
RUN mkdir -p /code/log
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -i http://pypi.douban.com/simple  -r requirements.txt --trusted-host pypi.douban.com
ADD gunicorn.conf /etc
ADD supervisord.conf /etc
EXPOSE 8080