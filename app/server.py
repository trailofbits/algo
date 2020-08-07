import asyncio
import json

import yaml
import boto3
from os.path import join, dirname, expanduser
from aiohttp import web, ClientSession
import concurrent.futures
import sys
import os

from google.auth.transport.requests import AuthorizedSession
from google.oauth2 import service_account
from playbook import PlaybookCLI

routes = web.RouteTableDef()
PROJECT_ROOT = dirname(dirname(__file__))
pool = None
task_future = None
task_program = ''


def run_playbook(data):
    global task_program
    extra_vars = ' '.join(['{0}={1}'.format(key, data[key])
                           for key in data.keys()])
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


@routes.post('/exit')
async def post_exit(_):
    if task_future and task_future.done():
        sys.exit(0)
    else:
        sys.exit(1)


@routes.post('/lightsail_regions')
async def lightsail_regions(request):
    data = await request.json()
    client = boto3.client(
        'lightsail',
        aws_access_key_id=data.get('aws_access_key'),
        aws_secret_access_key=data.get('aws_secret_key')
    )
    response = client.get_regions(
        includeAvailabilityZones=False
    )
    return web.json_response(response)


@routes.post('/ec2_regions')
async def ec2_regions(request):
    data = await request.json()
    client = boto3.client(
        'ec2',
        aws_access_key_id=data.get('aws_access_key'),
        aws_secret_access_key=data.get('aws_secret_key')
    )
    response = client.describe_regions()['Regions']
    return web.json_response(response)


@routes.get('/gce_config')
async def check_gce_config(request):
    gce_file = join(PROJECT_ROOT, 'configs', 'gce.json')
    response = {}
    try:
        json.loads(open(gce_file, 'r').read())['project_id']
        response['status'] = 'ok'
    except IOError:
        response['status'] = 'not_available'
    except ValueError:
        response['status'] = 'wrong_format'

    return web.json_response(response)


@routes.post('/gce_regions')
async def gce_regions(request):
    data = await request.json()
    gce_file_name = join(PROJECT_ROOT, 'configs', 'gce.json')
    if data.get('project_id'):
        # File is missing, save it. We can't get file path from browser :(
        with open(gce_file_name, 'w') as f:
            f.write(json.dumps(data))
    else:
        with open(gce_file_name, 'r') as f:
            data = json.loads(f.read())

    response = AuthorizedSession(
        service_account.Credentials.from_service_account_info(
            data).with_scopes(
                ['https://www.googleapis.com/auth/compute'])).get(
                'https://www.googleapis.com/compute/v1/projects/{project_id}/regions'.format(
                    project_id=data['project_id'])
    )

    return web.json_response(json.loads(response.content))


@routes.get('/vultr_config')
async def check_vultr_config(request):
    default_path = expanduser(join('~', '.vultr.ini'))
    response = {'path': None}
    try:
        open(default_path, 'r').read()
        response['path'] = default_path
    except IOError:
        pass

    if 'VULTR_API_CONFIG' in os.environ:
        try:
            open(os.environ['VULTR_API_CONFIG'], 'r').read()
            response['path'] = os.environ['VULTR_API_CONFIG']
        except IOError:
            pass
    return web.json_response(response)


@routes.get('/vultr_regions')
async def vultr_regions(request):
    async with ClientSession() as session:
        async with session.get('https://api.vultr.com/v1/regions/list') as r:
            json_body = await r.json()
            return web.json_response(json_body)

app = web.Application()
app.router.add_routes(routes)
app.add_routes([web.static('/static', join(PROJECT_ROOT, 'app', 'static'))])
app.add_routes([web.static('/results', join(PROJECT_ROOT, 'configs'))])
web.run_app(app, port=9000)
