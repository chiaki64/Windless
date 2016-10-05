#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import aioredis
import asyncio
import pytest

from core.memory import RedisFilter


@pytest.yield_fixture
def loop():
    """Creates new event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(None)

    yield loop

    if hasattr(loop, 'is_closed'):
        closed = loop.is_closed()
    else:
        closed = loop._closed  # XXX
    if not closed:
        loop.call_soon(loop.stop)
        loop.run_forever()
        loop.close()


@pytest.fixture
def create_redis(_closable, loop):
    """Wrapper around aioredis.create_redis."""

    @asyncio.coroutine
    def f(*args, **kw):
        redis = yield from aioredis.create_redis(*args, **kw)
        _closable(redis)
        return redis

    return f


# @pytest.fixture
# def create_pool(_closable):
#     """Wrapper around aioredis.create_pool."""
#
#     @asyncio.coroutine
#     def f(*args, **kw):
#         redis = yield from aioredis.create_pool(*args, **kw)
#         _closable(redis)
#         return redis
#
#     return f


# @pytest.fixture
# def pool(create_pool, server, loop):
#     """Returns RedisPool instance."""
#     pool = loop.run_until_complete(
#         create_pool(server.tcp_address, loop=loop))
#     return pool


@pytest.fixture
def redis(create_redis, loop):
    """Returns Redis client instance."""
    redis = loop.run_until_complete(
        create_redis(('localhost', 6379), loop=loop))
    loop.run_until_complete(redis.flushall())
    redis = RedisFilter(redis)
    return redis


@pytest.yield_fixture
def _closable(loop):
    conns = []

    yield conns.append

    waiters = []
    while conns:
        conn = conns.pop(0)
        conn.close()
        waiters.append(conn.wait_closed())
    if waiters:
        loop.run_until_complete(asyncio.gather(*waiters, loop=loop))


@pytest.mark.tryfirst
def pytest_pycollect_makeitem(collector, name, obj):
    if collector.funcnamefilter(name):
        if not callable(obj):
            return
        item = pytest.Function(name, parent=collector)
        if 'run_loop' in item.keywords:
            # TODO: re-wrap with asyncio.coroutine if not native coroutine
            return list(collector._genfunctions(name, obj))


@pytest.mark.tryfirst
def pytest_pyfunc_call(pyfuncitem):
    if 'run_loop' in pyfuncitem.keywords:
        funcargs = pyfuncitem.funcargs
        loop = funcargs['loop']
        testargs = {arg: funcargs[arg]
                    for arg in pyfuncitem._fixtureinfo.argnames}
        loop.run_until_complete(
            asyncio.wait_for(pyfuncitem.obj(**testargs),
                             15, loop=loop))
        return True


def pytest_runtest_setup(item):
    if 'run_loop' in item.keywords and 'loop' not in item.fixturenames:
        # inject an event loop fixture for all async tests
        item.fixturenames.append('loop')
