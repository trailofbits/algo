import asyncio
from os.path import join, dirname

import aiohttp
import yaml
from aiohttp import web

routes = web.RouteTableDef()
PROJECT_ROOT = dirname(dirname(__file__))


async def handle_index(_):
    with open(join(PROJECT_ROOT, 'app', 'index.html'), 'r') as f:
        return web.Response(body=f.read(), content_type='text/html')


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                p = await asyncio.create_subprocess_shell(
                    msg.data,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                while True:
                    line = await p.stdout.readline()
                    if not line:
                        break
                    else:
                        await ws.send_str(line.decode('ascii').rstrip())

        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' % ws.exception())

    print('websocket connection closed')
    return ws


@routes.view("/config")
class UsersView(web.View):
    async def get(self):
        with open(join(PROJECT_ROOT, 'config.cfg'), 'r') as f:
            config = yaml.safe_load(f.read())
            return web.json_response(config)

    async def post(self):
        data = await self.request.json()
        with open(join(PROJECT_ROOT, 'config.cfg'), 'w') as f:
            try:
                config = yaml.safe_dump(data)
            except Exception as e:
                return web.json_response({'error': {
                    'code': type(e).__name__,
                    'message': e,
                }}, status=400)
            else:
                f.write(config)
                return web.json_response({'ok': True})


app = web.Application()
app.router.add_get('/ws', websocket_handler)
app.router.add_get('/', handle_index)
app.router.add_routes(routes)
web.run_app(app)
