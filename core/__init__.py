#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# TODO 把 etrnity 的数据加载进redis
# pytest -s

# sudo docker exec -it 9c5621253095  /bin/bash
#  sudo docker ps -a
# sudo docker-compose up -d
# sudo docker rm -f $(sudo docker ps -aq)

# gunicorn -k gevent  melody -b 127.0.0.1:8081 --worker-class  aiohttp.worker.GunicornUVLoopWebWorker
