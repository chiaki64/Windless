#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Modules: Redis

import asyncio
import aioredis
import json
from utils.shortcuts import load_config

config = load_config()


class RedisFilter:
    def __init__(self, redis):
        self._connection = redis

    # Key Control
    async def set(self, table, data, many=True, id=None):
        key = self.prefix(table) + (
            '.' + ((str((await self.last(table)) + 1)) if id is None else str(id)) if many else '')

        if type(data) is dict:
            if many:
                data['id'] = key[self.prefix(table).__len__() + 1:] if id is None else id
            dit = json.dumps(data)
        elif type(data) is list:
            dit = json.dumps({'list': data})
        elif type(data) is str:
            dit = data
        else:
            raise TypeError

        await self._connection.set(key, dit)
        return (data['id'] if 'id' in data else data) if many else True

    async def lpush(self, table, value, isdict=False):
        key = self.prefix(table)
        data = await self.lget(table, isdict)
        if data is None:
            data = []
        elif data.count(value) == 0:
            data.append(value)
        await self._connection.set(key, json.dumps({'list': data}))

    async def lset(self, table, id, value, isdict=False):
        key = self.prefix(table)
        data = await self.lget(table, isdict)
        if data is None:
            data = []
        else:
            for item in data:
                if item['id'] == id:
                    data.remove(item)
                    data.append(value)
                    break
        await self._connection.set(key, json.dumps({'list': data}))

    async def get(self, table, id=None):
        key = self.prefix(table) + ('.' + str(id) if id is not None else '')
        data = await self._connection.get(key)
        if data is None:
            return None
        try:
            data = json.loads(str(data, encoding='utf-8'))
        except json.decoder.JSONDecodeError:
            data = str(data, encoding='utf-8')
        return data

    async def lget(self, table, isdict=False):
        data = await self.get(table)
        if data is not None:
            li = data['list']
            if isdict is False:
                li.sort(key=lambda x: int(x), reverse=True)
            else:
                try:
                    li.sort(key=lambda x: int(x['id']), reverse=True)
                except ValueError:
                    li.sort(key=lambda x: x['id'], reverse=True)
                except KeyError:
                    pass
            return li
        return []

    async def delete(self, table, id=None):
        key = self.prefix(table) + ('.' + str(id) if id is not None else '')
        await self._connection.delete(key)
        return True

    async def ldelete(self, table, value=None, isdict=False, _key='id'):
        # value为要删除的值，为空则全部删除
        data = await self.lget(table, isdict)
        if value is not None:
            if isdict is False:
                try:
                    data.remove(str(value))
                except ValueError:
                    pass
            else:
                # 处理列表项
                for item in data:
                    if item[_key] == value:
                        data.remove(item)
        else:
            data = []
        await self.set(table, data, many=False)
        return True

    async def get_list(self, table, keys=None, isauth=False):
        data_list = []
        if keys is None:
            arr = await self._connection.keys(self.prefix(table) + '.*')
            for item in arr:
                _id = str(item, encoding='utf-8')[self.prefix(table).__len__() + 1:]
                # 是否公开
                data = await self.get(table, _id)
                if (isauth is True) or (data['open'] is '0'):
                    data_list.append(data)
        elif type(keys) is list:
            for item in keys:
                data = await self.get(table, item)
                if (isauth is True) or (data['open'] is '0'):
                    data_list.append(data)
        else:
            raise ValueError
        data_list.sort(key=lambda x: int(x['id']), reverse=True)
        return data_list

    async def count(self, table):
        keys = await self._connection.keys(self.prefix(table) + '.*')
        return str(keys.__len__())

    async def last(self, table):
        id = 0
        keys = await self._connection.keys(self.prefix(table) + '.*')
        for item in keys:
            _id = str(item, encoding='utf-8')[self.prefix(table).__len__() + 1:]
            if int(_id) > id:
                id = int(_id)
        return id

    @staticmethod
    def prefix(table):
        return config['memory']['database'] + ':' + table

    # Other
    async def close(self):
        self._connection.close()


async def fun():
    redis = await aioredis.create_redis(('localhost', 6379), loop=loop)
    redis = RedisFilter(redis)

    # await redis.lpush('Test', {'id': '1'}, isdict=True)
    # await redis.lpush('Test', {'id': '5'}, isdict=True)
    # await redis.lpush('Test', {'id': '3'}, isdict=True)
    # await redis.lpush('Test', {'id': '15'}, isdict=True)

    print(await redis.lget('Test', isdict=True))

    # await redis.lset('Test', '16', {'id': '17'},isdict=True)
    await redis.ldelete('Test', isdict=True)
    print(await redis.lget('Test', isdict=True))

    print('finish')

    await redis.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fun())
    loop.close()
