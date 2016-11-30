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

    async def set(self, table, data, many=True, id=None):
        """
        封装 Set 操作，视传入数据的类型以不同形式存入 Redis
        Args:
            table:  表名
            data:   数据
            many:   数据是否多处存储
            id:     数据存储的ID
        Returns:
            *
        """
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
        """
        将数据存入以 List 格式存储的数据
        Args:
            table:  表名
            value:  数据
            isdict: 传入的数据是否是字典
        Returns:
            None
        """
        key = self.prefix(table)
        data = await self.lget(table, isdict)
        if data is None:
            data = []
        elif data.count(value) == 0:
            data.append(value)
        await self._connection.set(key, json.dumps({'list': data}))

    async def lset(self, table, id, value, isdict=False):
        """
        修改以 List 格式存储的数据内容,如不存在则无改动保存
        Args:
            table:  表名
            id:     要修改数据的id
            value： 修改后的值
            isdict: 修改的数据是否是字典
        Returns:
            None
        """
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
        """
        封装 Get 操作，返回 json 数据
        Args:
            table:  表名
            id:     获取数据的id
        Returns:
            json or str
        """
        key = self.prefix(table) + ('.' + str(id) if id is not None else '')
        data = await self._connection.get(key)
        if data is None:
            return None
        try:
            data = json.loads(str(data, encoding='utf-8'))
        except json.decoder.JSONDecodeError:
            data = str(data, encoding='utf-8')
        return data

    async def lget(self, table, isdict=False, reverse=True):
        """
        将数据从以 List 格式存储的数据中取出
        Args:
            table:   表名
            isdict:  取出的数据是否为字典
            reverse：取出的数据是否逆排列
        Returns:
            list
        """
        data = await self.get(table)
        if data is not None:
            li = data['list']
            if isdict is False:
                li.sort(key=lambda x: int(x), reverse=reverse)
            else:
                try:
                    li.sort(key=lambda x: int(x['id']), reverse=reverse)
                except ValueError:
                    li.sort(key=lambda x: x['id'], reverse=reverse)
                except KeyError:
                    pass
            return li
        return []

    async def delete(self, table, id=None):
        """
        封装 Delete 操作，实际上并没有什么用（
        Args:
            table:  表名
            id:     需删除数据的id
        Returns:
            True
        """
        key = self.prefix(table) + ('.' + str(id) if id is not None else '')
        await self._connection.delete(key)
        return True

    async def ldelete(self, table, value=None, isdict=False, _key='id'):
        # value为要删除的值，为空则全部删除
        """
        将数据从以 List 格式存储的数据中删除
        Args:
            table:  表名
            value:  在列表中删除对应值的数据,为空则全部删除
            isdict: 传入的数据格式是否为字典
            _key:   如果要删除的数据是字典则根据_key的名称来删除对应数据
        Returns:
            True
        """
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
        """
        取出以 List 格式存储的数据
        Args:
            table:  表名
            keys:   获取的数据的 id,以 list 形式传入
            isauth: 访问者是否通过认证，返回某些仅所有者可查看的数据
        Returns:
            list
        """
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
        """
        返回当前表有多少条数据
        """
        keys = await self._connection.keys(self.prefix(table) + '.*')
        return str(keys.__len__())

    async def last(self, table):
        """
        计算最后一篇文章的id,用以创建新文章时自增,即计算 Windless:Articles.* 类型的最后id
        """
        id = 0
        keys = await self._connection.keys(self.prefix(table) + '.*')
        for item in keys:
            _id = str(item, encoding='utf-8')[self.prefix(table).__len__() + 1:]
            if int(_id) > id:
                id = int(_id)
        return id

    @staticmethod
    def prefix(table):
        """
        给数据添加数据库名称 如: Windless:Archive
        """
        return config['memory']['database'] + ':' + table

    async def close(self):
        """
        关闭数据库连接，暂时无用
        """
        self._connection.close()


async def fun():
    redis = await aioredis.create_redis(('localhost', 6379), loop=loop)
    redis = RedisFilter(redis)
    # Test COde
    await redis.close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(fun())
    loop.close()
