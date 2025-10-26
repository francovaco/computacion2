import struct
import json
from typing import Dict, Any

# Constantes del protocolo
HEADER_SIZE = 4
BYTE_ORDER = 'big'

# Tipos de mensajes
MSG_TYPE_SCREENSHOT = "screenshot"
MSG_TYPE_PERFORMANCE = "performance"
MSG_TYPE_IMAGE_PROCESSING = "image_processing"
MSG_TYPE_RESPONSE = "response"
MSG_TYPE_ERROR = "error"

class ProtocolMessage:
    
    def __init__(self, msg_type: str, data: Dict[str, Any]):
        self.msg_type = msg_type
        self.data = data
    
    def to_bytes(self) -> bytes:
        payload = {
            "type": self.msg_type,
            "data": self.data
        }
        json_bytes = json.dumps(payload).encode('utf-8')
        header = struct.pack('>I', len(json_bytes))  # >I = unsigned int big-endian
        return header + json_bytes
    
    @staticmethod
    def from_bytes(data: bytes) -> 'ProtocolMessage':
        payload = json.loads(data.decode('utf-8'))
        return ProtocolMessage(payload["type"], payload["data"])


def encode_message(msg_type: str, data: Dict[str, Any]) -> bytes:
    message = ProtocolMessage(msg_type, data)
    return message.to_bytes()


def decode_header(header: bytes) -> int:
    if len(header) != HEADER_SIZE:
        raise ValueError(f"Header debe tener {HEADER_SIZE} bytes")
    return struct.unpack('>I', header)[0]


def decode_message(data: bytes) -> ProtocolMessage:
    return ProtocolMessage.from_bytes(data)


async def send_message_async(writer, msg_type: str, data: Dict[str, Any]):
    message_bytes = encode_message(msg_type, data)
    writer.write(message_bytes)
    await writer.drain()


async def receive_message_async(reader) -> ProtocolMessage:
    # Leer header
    header = await reader.readexactly(HEADER_SIZE)
    payload_size = decode_header(header)
    
    # Leer payload
    payload = await reader.readexactly(payload_size)
    return decode_message(payload)


def send_message_sync(sock, msg_type: str, data: Dict[str, Any]):
    message_bytes = encode_message(msg_type, data)
    sock.sendall(message_bytes)


def receive_message_sync(sock) -> ProtocolMessage:
    # Leer header
    header = b''
    while len(header) < HEADER_SIZE:
        chunk = sock.recv(HEADER_SIZE - len(header))
        if not chunk:
            raise ConnectionError("Conexión cerrada por el peer")
        header += chunk
    
    payload_size = decode_header(header)
    
    # Leer payload
    payload = b''
    while len(payload) < payload_size:
        chunk = sock.recv(payload_size - len(payload))
        if not chunk:
            raise ConnectionError("Conexión cerrada por el peer")
        payload += chunk
    
    return decode_message(payload)