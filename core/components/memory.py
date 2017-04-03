#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Modules: Redis

import aioredis
import asyncio
import pickle
from components.eternity import config


class RedisFilter:
    def __init__(self, redis):
        self._connection: aioredis.create_connection = redis

    def __repr__(self):
        return f"<RedisFilter [db:{config.redis['database']}]>"

    async def set(self, table: str, data, many: bool = True, id: str = None) -> str:
        """
        将数据处理后存入Redis
        Args:
            table:  表名
            data:   数据
            many:   数据是否统一存储
            id:     数据ID
        Returns:
            str or None
        """
        key = self.prefix(table) + (
            '.' + ((str((await self.last(table)) + 1)) if id is None else str(id)) if many else '')
        if many:
            data['id'] = key[len(self.prefix(table)) + 1:] if id is None else id
        value = pickle.dumps(data)
        await self._connection.set(key, value)
        return (data['id'] if 'id' in data else data) if many else None

    async def get(self, table: str, id: str = None):
        """
        取出并解析对应键值的数据
        Args:
            table:  表名
            id:     数据ID
        Returns:
            what you want
        """
        key = self.prefix(table) + ('.' + str(id) if id is not None else '')
        value = await self._connection.get(key)
        if value is None:
            return None
        return pickle.loads(value)

    async def delete(self, table: str, id: str = None) -> bool:
        """
        删除数据，实际上并没有什么用（
        Args:
            table:  表名
            id:     数据ID
        Returns:
            True
        """
        key = self.prefix(table) + ('.' + str(id) if id is not None else '')
        await self._connection.delete(key)
        return True

    async def lset(self, table: str, id: str, value, isdict: bool = False, _key: str = 'id'):
        """
        修改list中的数据
        Args:
            table:  表名
            id:     修改数据的ID
            value： 修改后的值
            isdict: 数据是否是字典
        Returns:
            None
        """
        data = await self.lget(table, isdict)
        if data is None:
            data = []
        else:
            for item in data:
                if item[_key] == id:
                    data.remove(item)
                    data.append(value)
                    break
        await self.set(table, data, many=False)

    async def lpush(self, table: str, value, isdict: bool = False):
        """
        将数据存入list
        Args:
            table:  表名
            value:  数据
            isdict: 数据是否是字典
        Returns:
            None
        """
        data = await self.lget(table, isdict)
        if data is None:
            data = []
        elif data.count(value) == 0:
            data.append(value)
        await self.set(table, data, many=False)

    async def lget(self, table: str, isdict: bool = False, reverse: bool = False) -> list:
        """
        取出list数据
        Args:
            table:   表名
            isdict:  数据是否为字典
            reverse：数据是否逆序排列
        Returns:
            list
        """
        data = await self.get(table)
        if data is not None:
            if isdict is False:
                data.sort(key=lambda x: int(x), reverse=reverse)
            else:
                try:
                    data.sort(key=lambda x: int(x['id']), reverse=reverse)
                except ValueError:
                    # 玄学
                    data.sort(key=lambda x: x['id'], reverse=reverse)
                except KeyError:
                    data.sort(key=lambda x: int(x['order']), reverse=reverse)
            return data
        return []

    async def lrem(self, table: str, value=None, isdict: bool = False, _key: str = 'id'):
        """
        删除数据，放空则全部删除
        Args:
            table:  表名
            value:  在列表中删除对应值的数据,为空则全部删除
            isdict: 数据格式是否为字典
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
                # 列表中删除
                for item in data:
                    if item[_key] == value:
                        data.remove(item)
        else:
            data = []
        await self.set(table, data, many=False)

    async def get_list(self, table: str, keys: list = None, isauth: bool = False, istop:bool=False) -> list:
        """
        将非list的数据以list形式返回
        Args:
            table:  表名
            keys:   获取的数据的 id,以 list 形式传入
            isauth: 访问者是否通过认证，返回某些仅所有者可查看的数据
        Returns:
            list
        """
        data_list = []
        if istop:
            top_list = await self.lget('Top')
        if keys is None:
            arr = await self._connection.keys(self.prefix(table) + '.*')
            for item in arr:
                # 将bytes转为字符串
                _id = str(item, encoding='utf-8')[len(self.prefix(table)) + 1:]
                data = await self.get(table, _id)
                if istop and (data['id'] in top_list):
                    data['_id'] = 0x_FF_FF_FF_FF
                else:
                    data['_id'] = data['id']
                if (isauth is True) or (data['open'] == 'on'):
                    data_list.append(data)
        elif type(keys) is list:
            for item in keys:
                data = await self.get(table, item)
                if istop and (data['id'] in top_list):
                    data['_id'] = 0x_FF_FF_FF_FF
                else:
                    data['_id'] = data['id']
                if (isauth is True) or (data['open'] == 'on'):
                    data_list.append(data)
        else:
            raise ValueError
        if data_list:
            try:
                data_list.sort(key=lambda x: int(x['_id']), reverse=True)
            except KeyError:
                data_list.sort(key=lambda x: int(x['id']), reverse=True)
        return data_list

    async def count(self, table: str) -> str:
        """
        返回当前表有多少条数据
        """
        keys = await self._connection.keys(self.prefix(table) + '.*')
        return str(len(keys))

    async def last(self, table: str) -> int:
        """
        计算最后一篇文章的id,用以创建新文章时自增,即计算类似 Windless:Articles.* 类型的最后id
        """
        id = 0
        keys = await self._connection.keys(self.prefix(table) + '.*')
        for item in keys:
            # max()
            _id = str(item, encoding='utf-8')[self.prefix(table).__len__() + 1:]
            if int(_id) > id:
                id = int(_id)
        return id

    @staticmethod
    def prefix(table: str) -> str:
        """
        给数据添加数据库名称 如: Windless:Archive
        """
        return f"{config.redis['database']}" + ':' + table

    async def close(self):
        """
        关闭数据库连接
        """
        self._connection.close()
