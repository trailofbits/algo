import asyncio
import yaml
from os.path import join, dirname
from aiohttp import web
import concurrent.futures
from playbook import PlaybookCLI


routes = web.RouteTableDef()
PROJECT_ROOT = dirname(dirname(__file__))
pool = None
task_future = None
task_program = ''


def run_playbook(data):
    global task_program
    extra_vars = ' '.join(['{0}={1}'.format(key, data[key]) for key in data.keys()])
    task_program = ['ansible-playbook', 'main.yml', '--extra-vars', extra_vars]
    return PlaybookCLI(task_program).run()


@routes.get('/')
async def handle_index(_):
    with open(join(PROJECT_ROOT, 'app', 'static', 'index.html'), 'r') as f:
        return web.Response(body=f.read(), content_type='text/html')


@routes.get('/playbook')
async def playbook_get_handler(request):
    if not task_future:
        return web.json_response({'status': None})

    if task_future.done():
        return web.json_response({'status': 'done', 'program': task_program, 'result': task_future.result()})
    elif task_future.cancelled():
        return web.json_response({'status': 'cancelled', 'program': task_program})
    else:
        return web.json_response({'status': 'running', 'program': task_program})


@routes.post('/playbook')
async def playbook_post_handler(request):
    global task_future
    global pool
    data = await request.json()
    loop = asyncio.get_running_loop()

    pool = concurrent.futures.ThreadPoolExecutor()
    task_future = loop.run_in_executor(pool, run_playbook, data)
    return web.json_response({'ok': True})


@routes.delete('/playbook')
async def playbook_delete_handler(request):
    global task_future
    if not task_future:
        return web.json_response({'ok': False})

    cancelled = task_future.cancel()
    pool.shutdown(wait=False)
    task_future = None
    return web.json_response({'ok': cancelled})


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


app = web.Application()
app.router.add_routes(routes)
app.add_routes([web.static('/static', join(PROJECT_ROOT, 'app', 'static'))])
app.add_routes([web.static('/results', join(PROJECT_ROOT, 'configs'))])
web.run_app(app, port=9000)
