from pathlib import Path
from urllib.request import Request, urlopen


MODEL_ASSETS_DIR = Path(__file__).resolve().parent / "model_assets"
MODEL_PATH = MODEL_ASSETS_DIR / "squeezenet1.1-7.onnx"
LABELS_PATH = MODEL_ASSETS_DIR / "imagenet_classes.txt"

MODEL_URL = "https://huggingface.co/onnxmodelzoo/squeezenet1.1-7/resolve/main/squeezenet1.1-7.onnx"
LABELS_URL = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"
DOWNLOAD_HEADERS = {"User-Agent": "ml-dev-ops-takehome/1.0"}


def ensure_model_assets() -> None:
    MODEL_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    _download_if_missing(path=MODEL_PATH, url=MODEL_URL)
    _download_if_missing(path=LABELS_PATH, url=LABELS_URL)


def _download_if_missing(*, path: Path, url: str) -> None:
    if path.exists():
        return

    request = Request(url=url, headers=DOWNLOAD_HEADERS)
    with urlopen(request) as response:
        payload = response.read()

    temp_path = path.with_suffix(f"{path.suffix}.tmp")
    temp_path.write_bytes(payload)
    temp_path.replace(path)
