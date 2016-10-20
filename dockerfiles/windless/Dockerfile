FROM python:3.5
RUN mkdir -p /code/log
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -i http://pypi.douban.com/simple  -r requirements.txt --trusted-host pypi.douban.com
RUN pip install misaka
EXPOSE 8080