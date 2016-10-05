#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest


@pytest.mark.run_loop
async def test_multi_data(redis):
    data = {
        'title': 'title',
        'content': 'text'
    }
    await redis.set('Article', data)
    await redis.set('Article', data)
    await redis.delete('Article', 1)

    assert await redis.count('Article') == '1'
    assert await redis.last('Article') == 2


@pytest.mark.run_loop
async def test_simple_data(redis):
    data = {
        'open': True
    }
    await redis.set('Config', data, many=False)
    assert (await redis.get('Config'))['open'] is True


@pytest.mark.run_loop
async def test_list_data(redis):
    data = [1, 2, 3]
    await redis.set('Category.Essay', data, many=False)
    assert await redis.lget('Category.Essay') == data


@pytest.mark.run_loop
async def test_list_multi_data(redis):
    await redis.lpush('Category.Essay', '1')
    await redis.lpush('Category.Essay', '1')
    await redis.lpush('Category.Essay', '2')
    await redis.lpush('Category.Essay', '3')
    assert await redis.lget('Category.Essay') == ['1', '2', '3']
    assert await redis.ldelete('Category.Essay', '2') is True
    assert await redis.lget('Category.Essay') == ['1', '3']


@pytest.mark.run_loop
async def test_list_multi_dict_data(redis):
    await redis.lpush('Category.Essay', {'id': 1})
    await redis.lpush('Category.Essay', {'id': 1})
    await redis.lpush('Category.Essay', {'id': 2})
    await redis.lpush('Category.Essay', {'id': 3})
    assert await redis.lget('Category.Essay') == [{'id': 1}, {'id': 2}, {'id': 3}]
    await redis.ldelete('Category.Essay', 2, isdict=True)
    assert await redis.lget('Category.Essay') == [{'id': 1}, {'id': 3}]
