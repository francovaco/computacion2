import base64
import json
from typing import Any, Dict
from io import BytesIO
from PIL import Image


def image_to_base64(image_data: bytes, format: str = "PNG") -> str:
    return base64.b64encode(image_data).decode('utf-8')


def base64_to_image(base64_str: str) -> bytes:
    return base64.b64decode(base64_str)


def pil_image_to_base64(image: Image.Image, format: str = "PNG") -> str:
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')


def base64_to_pil_image(base64_str: str) -> Image.Image:
    image_data = base64.b64decode(base64_str)
    return Image.open(BytesIO(image_data))


def serialize_to_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def deserialize_from_json(json_str: str) -> Dict[str, Any]:
    return json.loads(json_str)


def safe_serialize(obj: Any) -> str:
    def default_handler(o):
        if isinstance(o, bytes):
            return base64.b64encode(o).decode('utf-8')
        elif hasattr(o, '__dict__'):
            return o.__dict__
        else:
            return str(o)
    
    return json.dumps(obj, default=default_handler, ensure_ascii=False, indent=2)