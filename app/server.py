import asyncio
import signal
import sys
import aiohttp
import yaml
from os.path import join, dirname
from aiohttp import web

routes = web.RouteTableDef()
PROJECT_ROOT = dirname(dirname(__file__))
jobs = []


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
                jobs.append(p)
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


@routes.get('/config')
async def get_config(_):
    with open(join(PROJECT_ROOT, 'config.cfg'), 'r') as f:
        config = yaml.safe_load(f.read())
        return web.json_response(config)


@routes.post('/config')
async def post_config(request):
    data = await request.json()
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


@routes.post('/do/regions')
async def get_do_regions(request):
    data = await request.json()
    async with aiohttp.ClientSession() as session:
        url = 'https://api.digitalocean.com/v2/regions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {0}'.format(data['token']),
        }
        async with session.get(url, headers=headers) as r:
            json_body = await r.json()
            return web.json_response(json_body)

app = web.Application()
app.router.add_get('/ws', websocket_handler)
app.router.add_get('/', handle_index)
app.router.add_routes(routes)
web.run_app(app)

def signal_handler(sig, frame):
    print('Closing child processes')
    for p in jobs:
        try:
            p.terminate()
        except:
            pass
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
print('Press Ctrl+C to stop')
signal.pause()
