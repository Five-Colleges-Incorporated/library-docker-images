"""Custom entrypoint around the Setae server."""

import ipaddress
import logging
import os
from typing import TYPE_CHECKING

from fastapi.responses import Response
from main import app, read_item

if TYPE_CHECKING:
    from fastapi import Request

allow_list = [
    # https://networksdb.io/ip-addresses-of/amherst-college
    ipaddress.ip_network("148.85.192.0/18"),
    # https://www.hampshire.edu/it/user-support/network-wifi-and-vpn/technical-description-our-network
    # cross-referenced with LDLite ranges
    ipaddress.ip_network("144.121.36.224/27"),
    ipaddress.ip_network("64.254.160.0/20"),
    # https://networksdb.io/ip-addresses-of/mount-holyoke-college
    ipaddress.ip_network("138.110.0.0/16"),
    # https://networksdb.io/ip-addresses-of/smith-college
    # cross-referenced with LDLite ranges
    ipaddress.ip_network("131.229.0.0/17"),
    # https://networksdb.io/ip-addresses-of/university-of-massachusetts-amherst
    # cross-referenced with LDLite ranges
    ipaddress.ip_network("128.119.0.0/16"),
    ipaddress.ip_network("205.172.168.0/22"),
]

SOURCE_IP_HEADER = "do-connecting-ip"

logger = logging.getLogger("uvicorn.error")


@app.middleware("http")
async def filter_ips(request: Request, call_next):
    """FastAPI middleware to filter requests by IP address."""
    if os.getenv("LOCALHOST"):
        return await call_next(request)

    if request.url.path in ["/readyz", "/livez"]:
        return await call_next(request)

    if not (ip := request.headers.get(SOURCE_IP_HEADER)):
        logger.warning(
            "Received request from %s without %s! Headers: %s",
            request.client,
            SOURCE_IP_HEADER,
            request.headers,
        )
        return Response(status_code=407)

    ip_addr = ipaddress.ip_address(ip)
    logger.info("Received %s request from %s", request.url.path, ip_addr)

    if any(ip_addr in cidr for cidr in allow_list):
        return await call_next(request)
    return Response(status_code=401)


@app.get("/readyz")
async def readyz():
    """Implements the Kubernetes readiness endpoint."""
    return Response(status_code=200)


@app.get("/livez")
async def livez():
    """Implements the Kubernetes liveliness endpoint."""
    try:
        res = await read_item(barcode="310212313168477")
        return Response(status_code=res.status_code)
    except:  # noqa: E722
        logger.exception("/livez failed")
        return Response(status_code=503)
