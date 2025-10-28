import ipaddress
import logging

from fastapi.responses import Response

from main import app, read_item

allow_list = [
    ipaddress.ip_network('150.195.159.183/32'), # Katherine's home
    ipaddress.ip_network('64.224.254.198/32'), # Aaron's home

    ipaddress.ip_network('148.85.254.0/23'), # Amherst and FCI
]

SOURCE_IP_HEADER = 'do-connecting-ip'

logger = logging.getLogger('uvicorn.error')

@app.middleware('http')
async def filter_ips(request: Request, call_next):
    if request.url.path in ['/readyz', '/livez']:
        return await(call_next(request))

    if not (ip := request.headers.get(SOURCE_IP_HEADER)):
        logger.warning(
            'Received request from %s without %s! Headers: %s',
            request.client,
            SOURCE_IP_HEADER,
            request.headers,
        )
        return Response(status_code=407)

    ip_addr = ipaddress.ip_address(ip)
    logger.info('Received %s request from %s', request.url.path, ip_addr)

    if any(ip_addr in cidr for cidr in allow_list):
        return await call_next(request)
    return Response(status_code=401)

@app.get('/readyz')
async def readyz():
    return Response(status_code=200)

@app.get('/livez')
async def livez():
    try:
        res = (await read_item(barcode="310212313168477"))
        return Response(status_code=res.status_code)
    except:
        logger.exception('/livez failed')
        return Response(status_code=503)
