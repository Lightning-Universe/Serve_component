from fastapi import FastAPI, Request
from uvicorn import run
import argparse
import asyncio
import numpy as np
import requests
from copy import deepcopy

parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str)
parser.add_argument("--port", type=int)
hparams = parser.parse_args()

app = FastAPI()
router = globals()["router"]
lock = asyncio.Lock()
routing = None

@app.post("/update_router")
async def update_router(request: Request):
    global routing
    routing = await request.json()
    async with lock:
        print(routing)

@app.post("/{full_path:path}")
async def global_post(request: Request, full_path: str):
    global routing
    async with lock:
        local_routing = deepcopy(routing)

    print(local_routing)

    if not local_routing:
        return

    random_url = np.random.choice(list(local_routing.keys()), p=list(local_routing.values()))
    response = requests.post(random_url + "/" + full_path, data=await request.body())
    return response.json()

@app.get("/{full_path:path}")
async def global_get(request: Request, full_path: str):
    global routing
    async with lock:
        local_routing = deepcopy(routing)

    print(local_routing)

    if not routing:
        return

    random_url = np.random.choice(list(local_routing.keys()), p=list(local_routing.values()))
    response = requests.get(random_url + "/" + full_path, data=await request.body())
    return response.json()

print(f"Running router on {hparams.host}:{hparams.port}")

run(app, host=hparams.host.replace("http://", "").replace("https://", ""), port=int(hparams.port))