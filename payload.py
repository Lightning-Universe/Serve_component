import base64
import json


def create_payload():

    with open("0.png", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())

    with open("payload.json", "w") as file:
        json.dump({"body": encoded_string.decode("utf-8")}, file)


if __name__ == "__main__":
    create_payload()
