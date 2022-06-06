from fastapi import FastAPI, Request
from uvicorn import run
import argparse
import asyncio
from copy import deepcopy
import requests

PROXY_ENDPOINT = "/api/v1/proxy"
app = FastAPI()
lock = asyncio.Lock()
proxy_metadata = None

def main():
    global proxy
    global strategy

    proxy = globals()["proxy"]
    strategy = globals()["strategy"]

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str)
    parser.add_argument("--port", type=int)
    hparams = parser.parse_args()

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

    async def make_request(selected_url: str, full_path: str, request: Request) -> requests.Response:
        method = request.method.lower()
        return getattr(requests, method)(selected_url + "/" + full_path, data=await request.body())

    async def fn(request: Request, full_path: str):
        global proxy_metadata

        if not proxy_metadata:
            return

        async with lock:
            local_proxy_metadata = deepcopy(proxy_metadata)

        selected_url = strategy.select_url(request, full_path, local_proxy_metadata)
        response = await make_request(selected_url, full_path, request)
        return response.json()

    @app.post("/{full_path:path}")
    async def global_post(request: Request, full_path: str):
        return await fn(request, full_path)

    @app.get("/{full_path:path}")
    async def global_get(request: Request, full_path: str):
        return await fn(request, full_path)

    print(f"Running proxy on {hparams.host}:{hparams.port}")

    run(app, host=hparams.host.replace("http://", "").replace("https://", ""), port=int(hparams.port))

if __name__ == "__main__":
    main()