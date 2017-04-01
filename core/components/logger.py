#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from utils.period import todate, now

logging.basicConfig(
    filename=f'../log/access_{todate(now(), "%Y_%m")}.log',
    level=logging.INFO,
    format='<%(levelname)s>::%(message)s',
    datefmt='%a, %Y/%m/%d %H:%M:%S',
)

logger = logging.getLogger('aiohttp.access')
logger.setLevel(logging.INFO)

formatters='%t::Request(%r)::Status(%s)::Time(%Tf)::IP(%{X-Real-IP}i)::Referer(%{Referer}i)::User-Agent(%{User-Agent}i)'
