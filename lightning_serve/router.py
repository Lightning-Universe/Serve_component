from fastapi import FastAPI, Request
from uvicorn import run
import argparse
import asyncio
from copy import deepcopy

parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str)
parser.add_argument("--port", type=int)
hparams = parser.parse_args()

app = FastAPI()
router = globals()["router"]
lock = asyncio.Lock()
router_metadata = None
strategy = globals()["strategy"]

@app.post("/update_router")
async def update_router(request: Request):
    global router_metadata
    local_router_metadata = await request.json()
    async with lock:
        router_metadata = local_router_metadata
        print(router_metadata)

async def fn(request: Request, full_path: str):
    global router_metadata
    async with lock:
        local_router_metadata = deepcopy(router_metadata)

    if not router_metadata:
        return

    return strategy.on_router_request(request, full_path, local_router_metadata)

@app.post("/{full_path:path}")
async def global_post(request: Request, full_path: str):
   return await fn(request, full_path)

@app.get("/{full_path:path}")
async def global_get(request: Request, full_path: str):
    return await fn(request, full_path)

print(f"Running router on {hparams.host}:{hparams.port}")

run(app, host=hparams.host.replace("http://", "").replace("https://", ""), port=int(hparams.port))