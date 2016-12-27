from u2flib_server.jsapi import DeviceRegistration
from u2flib_server.u2f import (start_register, complete_register,
                               start_authenticate, verify_authenticate)
import json

__all__ = [
    'enroll',
    'bind',
    'sign',
    'verify'
]

facet = 'https://wind.moe'


async def init():
    pass

async def enroll(user):
    devices = [DeviceRegistration.wrap(device)
               for device in user.get('_u2f_devices', [])]
    enroll = start_register(facet, devices)
    user['_u2f_enroll_'] = enroll.json
    res = json.loads(enroll.json)
    return user, res['registerRequests'][0]

async def bind(user, data):
    response = data['tokenResponse']
    try:
        binding, cert = complete_register(user.pop('_u2f_enroll_'), response,
                                          [facet])
        devices = [DeviceRegistration.wrap(device)
                   for device in user.get('_u2f_devices_', [])]
        devices.append(binding)
        user['_u2f_devices_'] = [d.json for d in devices]
    except ValueError:
        return user, False
    return user, True

async def sign(user):
    devices = [DeviceRegistration.wrap(device)
               for device in user.get('_u2f_devices_', [])]
    challenge = start_authenticate(devices)
    user['_u2f_challenge_'] = challenge.json
    res = json.loads(challenge.json)
    return user, res['authenticateRequests'][0]

async def verify(user, data):
    response = data['tokenResponse']
    devices = [DeviceRegistration.wrap(device)
               for device in user.get('_u2f_devices_', [])]
    challenge = user.pop('_u2f_challenge_')
    try:
        c, t = verify_authenticate(devices, challenge, response, [facet])
        print(c, t)
    except AttributeError:
        return user, False
    return user, True
