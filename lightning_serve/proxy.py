import asyncio
import pickle
from copy import deepcopy

from fastapi import FastAPI, Request, Response
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.concurrency import run_in_threadpool
from fastapi.responses import UJSONResponse

PROXY_ENDPOINT = "/api/v1/proxy"

app = FastAPI()
lock = asyncio.Lock()
proxy_metadata = None

with open("strategy.p", "rb") as f:
    strategy = pickle.load(f)

#Instrumentator().instrument(app).expose(app)


@app.post(PROXY_ENDPOINT)
async def post_proxy(request: Request):
    global proxy_metadata
    local_proxy_metadata = await request.json()
    async with lock:
        proxy_metadata = local_proxy_metadata
        print(proxy_metadata)


@app.get(PROXY_ENDPOINT)
async def get_proxy(request: Request):
    global proxy_metadata
    async with lock:
        return proxy_metadata


def fn(request: Request, full_path: str):
    global proxy_metadata

    if not proxy_metadata:
        resp = Response()
        resp.status_code = 404
        return resp

    # async with lock:
    #     local_proxy_metadata = deepcopy(proxy_metadata)

    response = strategy.make_request(request, full_path, proxy_metadata)
    return UJSONResponse(response.json())


@app.post("/{full_path:path}")
def global_post(request: Request, full_path: str):
    return fn(request, full_path)


@app.get("/{full_path:path}")
def global_get(request: Request, full_path: str):
    return fn(request, full_path)


if __name__ == "__main__":
    import argparse

    from uvicorn import run

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str)
    parser.add_argument("--port", type=int)
    hparams = parser.parse_args()

    run(
        app,
        host=hparams.host.replace("http://", "").replace("https://", ""),
        port=int(hparams.port),
    )
