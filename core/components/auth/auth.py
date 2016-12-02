from functools import wraps
from aiohttp import web
from .ticket import AbstractAuthentication

POLICY_KEY = 'auth.policy'
AUTH_KEY = 'auth'


def auth_middleware(policy):
    assert isinstance(policy, AbstractAuthentication)

    async def _auth_middleware_factory(app, handler):
        async def _middleware_handler(request):
            request[POLICY_KEY] = policy

            response = await handler(request)

            await policy.process_response(request, response)

            return response

        return _middleware_handler

    return _auth_middleware_factory


async def get_auth(request):
    auth_val = request.get(AUTH_KEY)
    if auth_val:
        return auth_val

    auth_policy = request.get(POLICY_KEY)
    if auth_policy is None:
        raise RuntimeError('auth_middleware not installed')

    request[AUTH_KEY] = await auth_policy.get(request)
    return request[AUTH_KEY]


async def remember(request, user_id):
    auth_policy = request.get(POLICY_KEY)
    if auth_policy is None:
        raise RuntimeError('auth_middleware not installed')

    return await auth_policy.remember(request, user_id)


async def forget(request):
    auth_policy = request.get(POLICY_KEY)
    if auth_policy is None:
        raise RuntimeError('auth_middleware not installed')

    return await auth_policy.forget(request)


def auth_required(func):
    @wraps(func)
    async def wrapper(*args):
        if (await get_auth(args[-1])) is None:
            raise web.HTTPForbidden()

        return await func(*args)

    return wrapper