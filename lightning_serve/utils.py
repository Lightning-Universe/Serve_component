from lightning.app import LightningWork


def get_url(work: LightningWork) -> str:
    # internal_ip = work.internal_ip
    # if internal_ip:
    #     return f"http://{internal_ip}:{work.port}"
    return work.url
