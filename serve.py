import argparse
import base64
import io
import os

import torch
from fastapi import FastAPI, Request
from fastapi.responses import UJSONResponse
from PIL import Image
from torchvision.transforms import ToTensor
from uvicorn import run

model = torch.jit.load("model.pt")
for param in model.parameters():
    param.requires_grad = False

transform = ToTensor()

app = FastAPI()


@app.get("/predict")
def predict_get(request: Request):
    # await asyncio.sleep(np.random.uniform(0, .3))
    return UJSONResponse(os.environ["random_kwargs"])


@app.post("/predict")
async def predict_post(request: Request):
    body = await request.json()
    image = body.get("body")
    if isinstance(image, str):
        # if the image is a string of bytesarray.
        image = base64.b64decode(image)

    # If the image is sent as bytesarray
    if isinstance(image, (bytearray, bytes)):
        image = Image.open(io.BytesIO(image))
    else:
        # if the image is a list
        image = torch.FloatTensor(image)

    image = transform(image).unsqueeze(0)

    predictions = model(image).argmax().item()

    return UJSONResponse({"predictions": predictions})


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
