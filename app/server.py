import asyncio
import base64
import concurrent.futures
import configparser
import hashlib
import hmac
import json
import os
import sys
from os.path import join, dirname, expanduser
from urllib.parse import quote, urlencode

import yaml
from aiohttp import web, ClientSession

from playbook import PlaybookCLI

try:
    import boto3

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2 import service_account

    HAS_GOOGLE_LIBRARIES = True
except ImportError:
    HAS_GOOGLE_LIBRARIES = False

try:
    from azure.mgmt.automation import AutomationClient
    import azure.mgmt.automation.models as AutomationModel

    HAS_AZURE_LIBRARIES = True
except ImportError:
    HAS_AZURE_LIBRARIES = False

try:
    from cs import AIOCloudStack, CloudStackApiException
    HAS_CS_LIBRARIES = True
except ImportError:
    HAS_CS_LIBRARIES = False

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
        try:
            return web.json_response({'status': 'done', 'program': task_program, 'result': task_future.result()})
        except ValueError as e:
            return web.json_response({'status': 'error', 'program': task_program, 'result': str(e)})
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
async def playbook_delete_handler(_):
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


@routes.get('/do_config')
async def check_do_config(_):
    return web.json_response({'has_secret': 'DO_API_TOKEN' in os.environ})


@routes.post('/do_regions')
async def do_regions(request):
    data = await request.json()
    token = data.get('token', os.environ.get('DO_API_TOKEN'))
    if not token:
        return web.json_response({'error': 'no token provided'}, status=400)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {0}'.format(token),
    }
    async with ClientSession(headers=headers) as session:
        async with session.get('https://api.digitalocean.com/v2/regions') as r:
            json_body = await r.json()
            return web.json_response(json_body, status=r.status)


@routes.get('/aws_config')
async def aws_config(_):
    if not HAS_BOTO3:
        return web.json_response({'error': 'missing_boto'}, status=400)
    return web.json_response(
        {'has_secret': 'AWS_ACCESS_KEY_ID' in os.environ and 'AWS_SECRET_ACCESS_KEY' in os.environ})


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
async def check_gce_config(_):
    if not HAS_REQUESTS:
        return web.json_response({'error': 'missing_requests'}, status=400)
    if not HAS_GOOGLE_LIBRARIES:
        return web.json_response({'error': 'missing_google'}, status=400)
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
    response = {'has_secret': False}
    if 'VULTR_API_CONFIG' in os.environ:
        try:
            open(os.environ['VULTR_API_CONFIG'], 'r').read()
            response['has_secret'] = True
        except IOError:
            pass
    try:
        default_path = expanduser(join('~', '.vultr.ini'))
        open(default_path, 'r').read()
        response['has_secret'] = True
    except IOError:
        pass
    return web.json_response(response)


@routes.post('/vultr_config')
async def save_vultr_config(request):
    data = await request.json()
    token = data.get('token')
    path = os.environ.get('VULTR_API_CONFIG') or expanduser(join('~', '.vultr.ini'))
    with open(path, 'w') as f:
        try:
            f.write('[default]\nkey = {0}'.format(token))
        except IOError:
            return web.json_response({'error': 'can not save config file'}, status=400)
    return web.json_response({'saved_to': path})


@routes.get('/vultr_regions')
async def vultr_regions(_):
    async with ClientSession() as session:
        async with session.get('https://api.vultr.com/v1/regions/list') as r:
            json_body = await r.json()
            return web.json_response(json_body)


@routes.get('/scaleway_config')
async def check_scaleway_config(_):
    return web.json_response({"has_secret": 'SCW_TOKEN' in os.environ})


@routes.get('/hetzner_config')
async def check_hetzner_config(_):
    return web.json_response({"has_secret": 'HCLOUD_TOKEN' in os.environ})


@routes.post('/hetzner_regions')
async def hetzner_regions(request):
    data = await request.json()
    token = data.get('token', os.environ.get('HCLOUD_TOKEN'))
    if not token:
        return web.json_response({'error': 'no token provided'}, status=400)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {0}'.format(token),
    }
    async with ClientSession(headers=headers) as session:
        async with session.get('https://api.hetzner.cloud/v1/datacenters') as r:
            json_body = await r.json()
            return web.json_response(json_body)


@routes.get('/azure_config')
async def azure_config(_):
    if not HAS_REQUESTS:
        return web.json_response({'error': 'missing_requests'}, status=400)
    if not HAS_AZURE_LIBRARIES:
        return web.json_response({'error': 'missing_azure'}, status=400)
    response = {'status': 'ok'}
    return web.json_response(response)


@routes.get('/azure_regions')
async def azure_regions(_):
    with open(join(PROJECT_ROOT, 'roles', 'cloud-azure', 'defaults', 'main.yml'), 'r') as f:
        regions_json = yaml.safe_load(f.read())
        regions = json.loads(regions_json['_azure_regions'])
        return web.json_response(regions)


@routes.get('/linode_config')
async def linode_config(_):
    return web.json_response({"has_secret": 'LINODE_API_TOKEN' in os.environ})


@routes.get('/linode_regions')
async def linode_regions(_):
    async with ClientSession() as session:
        async with session.get('https://api.linode.com/v4/regions') as r:
            json_body = await r.json()
            return web.json_response(json_body)


@routes.get('/cloudstack_config')
async def check_cloudstack_config(_):
    if not HAS_REQUESTS:
        return web.json_response({'error': 'missing_requests'}, status=400)
    if not HAS_CS_LIBRARIES:
        return web.json_response({'error': 'missing_cloudstack'}, status=400)
    response = {'has_secret': _read_cloudstack_config() is not None}
    return web.json_response(response)


def _read_cloudstack_config():
    if 'CLOUDSTACK_CONFIG' in os.environ:
        try:
            return open(os.environ['CLOUDSTACK_CONFIG'], 'r').read()
        except IOError:
            pass
    # check default path
    default_path = expanduser(join('~', '.cloudstack.ini'))
    try:
        return open(default_path, 'r').read()
    except IOError:
        pass
    return None


@routes.post('/cloudstack_regions')
async def cloudstack_regions(request):
    data = await request.json()
    client_config = data.get('token')
    config = configparser.ConfigParser()
    config.read_string(_read_cloudstack_config() or client_config)
    section = config[config.sections()[0]]
    client = AIOCloudStack(**section)
    try:
        zones = await client.listZones(fetch_list=True)
    except CloudStackApiException as resp:
        return web.json_response({
            'cloud_stack_error': resp.error
        }, status=400)
    # if config was passed from client, save it after successful zone retrieval
    if _read_cloudstack_config() is None:
        path = os.environ.get('CLOUDSTACK_CONFIG') or expanduser(join('~', '.cloudstack.ini'))
        with open(path, 'w') as f:
            try:
                f.write(client_config)
            except IOError as e:
                return web.json_response({'error': 'can not save config file'}, status=400)

    return web.json_response(zones)


app = web.Application()
app.router.add_routes(routes)
app.add_routes([web.static('/static', join(PROJECT_ROOT, 'app', 'static'))])
app.add_routes([web.static('/results', join(PROJECT_ROOT, 'configs'))])
web.run_app(app, port=9000)
