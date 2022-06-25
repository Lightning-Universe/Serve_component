import argparse

from fastapi import FastAPI, Request
from uvicorn import run

parser = argparse.ArgumentParser()
parser.add_argument("--host", type=str)
parser.add_argument("--port", type=int)
hparams = parser.parse_args()

app = FastAPI()


@app.get("/predict")
async def predict(request: Request):
    print("HERE")
    return globals()["random_kwargs"]


print(f"Running on {hparams.host}:{hparams.port}")

run(
    app,
    host=hparams.host.replace("http://", "").replace("https://", ""),
    port=int(hparams.port),
)
