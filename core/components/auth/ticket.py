import abc
import time
from ipaddress import ip_address
from ticket_auth import TicketFactory, TicketError
from aiohttp import web


_REISSUE_KEY = 'auth.reissue'


class AbstractAuthentication(object):
    @abc.abstractmethod
    async def remember(self, request, user_id):
        pass

    @abc.abstractmethod
    async def forget(self, request):
        pass

    @abc.abstractmethod
    async def get(self, request):
        pass

    async def process_response(self, request, response):
        pass


class TktAuthentication(AbstractAuthentication):

    def __init__(
            self,
            secret,
            max_age,
            reissue_time=None,
            include_ip=False,
            cookie_name='AUTH_TKT'):

        self._ticket = TicketFactory(secret)
        self._max_age = max_age
        if (self._max_age is not None and
            reissue_time is not None and
            reissue_time < self._max_age):
            self._reissue_time = max_age - reissue_time
        else:
            self._reissue_time = None

        self._include_ip = include_ip
        self._cookie_name = cookie_name

    @property
    def cookie_name(self):
        return self._cookie_name

    async def remember(self, request, user_id):
        ticket = self._new_ticket(request, user_id)
        await self.remember_ticket(request, ticket)

    async def forget(self, request):
        await self.forget_ticket(request)

    async def get(self, request):
        ticket = await self.get_ticket(request)
        if ticket is None:
            return None

        try:
            # Returns a tuple of (user_id, token, userdata, validuntil)
            now = time.time()
            fields = self._ticket.validate(ticket, self._get_ip(request), now)

            # Check if we need to reissue a ticket
            if (self._reissue_time is not None and
                now >= (fields.valid_until - self._reissue_time)):

                # Reissue our ticket, and save it in our request.
                request[_REISSUE_KEY] = self._new_ticket(request, fields.user_id)

            return fields.user_id

        except TicketError as e:
            return None

    async def process_response(self, request, response):
        if _REISSUE_KEY in request:
            if (response.started or
                not isinstance(response, web.Response) or
                response.status < 200 or response.status > 299):
                return

            await self.remember_ticket(request, request[_REISSUE_KEY])

    @abc.abstractmethod
    async def remember_ticket(self, request, ticket):
        pass

    @abc.abstractmethod
    async def forget_ticket(self, request):
        pass

    @abc.abstractmethod
    async def get_ticket(self, request):
        pass

    def _get_ip(self, request):
        ip = None
        if self._include_ip:
            peername = request.transport.get_extra_info('peername')
            if peername:
                ip = ip_address(peername[0])

        return ip

    def _new_ticket(self, request, user_id):
        ip = self._get_ip(request)
        valid_until = int(time.time()) + self._max_age
        return self._ticket.new(user_id, valid_until=valid_until, client_ip=ip)
