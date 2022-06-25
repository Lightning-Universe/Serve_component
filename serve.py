import argparse
import os

from fastapi import FastAPI, Request
from fastapi.responses import UJSONResponse
from uvicorn import run

app = FastAPI()


@app.get("/predict")
async def predict(request: Request):
    # await asyncio.sleep(np.random.uniform(0, .3))
    return UJSONResponse(os.environ["random_kwargs"])


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
