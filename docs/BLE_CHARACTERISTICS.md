# Sphero R2-D2 BLE Characteristics

This document describes the Bluetooth Low Energy (BLE) GATT services and characteristics used by the Sphero R2-D2.

## Overview

The R2-D2 uses BLE for all communication with the controlling device. The protocol is based on the Sphero V2 protocol, with some R2-D2/BB-9E specific extensions.

## Service UUIDs

### Sphero Robot Service (V2)

The V2 protocol uses a custom service with the base UUID pattern:

```
XXXXXXXX-574f-4f20-5370-6865726f2121
```

The suffix `574f-4f20-5370-6865726f2121` decodes to ASCII: `WO O Sphero!!`

## Characteristic UUIDs

### R2-D2 / BB-9E Specific

| Characteristic | UUID | Direction | Description |
|---------------|------|-----------|-------------|
| **API V2** | `00010002-574f-4f20-5370-6865726f2121` | Read/Write/Notify | Main command/response channel |
| **Handshake** | `00020005-574f-4f20-5370-6865726f2121` | Write | Anti-DoS handshake ("usetheforce...band") |

### Legacy Sphero (V1 - for reference)

| Characteristic | UUID | Direction | Description |
|---------------|------|-----------|-------------|
| BLE Service | `22bb746f-2bb0-7554-2d6f-726568705327` | - | Main BLE service |
| Wake | `22bb746f-2bbf-7554-2d6f-726568705327` | Write | Wake device |
| TX Power | `22bb746f-2bb2-7554-2d6f-726568705327` | Write | Set TX power level |
| Anti-DoS | `22bb746f-2bbd-7554-2d6f-726568705327` | Write | Anti-DoS handshake |
| Robot Control | `22bb746f-2ba0-7554-2d6f-726568705327` | - | Control service |
| Commands | `22bb746f-2ba1-7554-2d6f-726568705327` | Write | Send commands |
| Response | `22bb746f-2ba6-7554-2d6f-726568705327` | Notify | Receive responses |

## Connection Sequence

### 1. Scan for Device

R2-D2 robots advertise with local name prefix `D2-` followed by 4 hex characters (e.g., `D2-55E3`).

```python
# Scan for R2-D2 devices
devices = await BleakScanner.discover(timeout=5.0)
r2d2_devices = [d for d in devices if d.name and d.name.startswith('D2-')]
```

### 2. Connect

```python
client = BleakClient(device.address)
await client.connect()
```

### 3. Anti-DoS Handshake

Before sending commands, write the handshake string to the handshake characteristic:

```python
HANDSHAKE_UUID = "00020005-574f-4f20-5370-6865726f2121"
await client.write_gatt_char(HANDSHAKE_UUID, b"usetheforce...band")
```

The handshake string `usetheforce...band` is a Star Wars reference (R2-D2 is from Star Wars).

### 4. Subscribe to Notifications

Subscribe to the API characteristic for responses:

```python
API_UUID = "00010002-574f-4f20-5370-6865726f2121"
await client.start_notify(API_UUID, response_callback)
```

### 5. Send Commands

Write V2 protocol packets to the API characteristic:

```python
await client.write_gatt_char(API_UUID, packet_data)
```

## MTU and Packet Fragmentation

- Default BLE MTU is 20 bytes
- Packets larger than 20 bytes must be fragmented
- The library sends packets in 20-byte chunks with timing delays

```python
while payload:
    await client.write_gatt_char(API_UUID, payload[:20])
    payload = payload[20:]
    await asyncio.sleep(0.12)  # R2D2 safe command interval
```

## Command Safe Interval

The R2-D2 requires a minimum delay between commands:

| Robot | Safe Interval |
|-------|---------------|
| R2-D2 | 0.12 seconds (120ms) |
| BB-8 | 0.06 seconds (60ms) |
| BB-9E | 0.12 seconds (120ms) |

Sending commands too rapidly can cause:
- Dropped commands
- Garbled responses
- Connection instability

## Available Characteristics (Full List)

These UUIDs have been observed on Sphero devices (availability may vary by model):

```
# V2 Protocol Characteristics
00010001-574f-4f20-5370-6865726f2121
00010002-574f-4f20-5370-6865726f2121  # Main API (R2-D2/BB-9E)
00010003-574f-4f20-5370-6865726f2121
00020001-574f-4f20-5370-6865726f2121
00020002-574f-4f20-5370-6865726f2121
00020004-574f-4f20-5370-6865726f2121
00020005-574f-4f20-5370-6865726f2121  # Handshake (R2-D2/BB-9E)

# V1 Protocol Characteristics (Legacy)
22bb746f-2ba0-7554-2d6f-726568705327  # Robot Control Service
22bb746f-2ba1-7554-2d6f-726568705327  # Commands
22bb746f-2ba6-7554-2d6f-726568705327  # Response
22bb746f-2bb0-7554-2d6f-726568705327  # BLE Service
22bb746f-2bb2-7554-2d6f-726568705327  # TX Power
22bb746f-2bbd-7554-2d6f-726568705327  # Anti-DoS
22bb746f-2bbf-7554-2d6f-726568705327  # Wake
```

## Example: Minimal Connection

```python
import asyncio
from bleak import BleakClient, BleakScanner

HANDSHAKE_UUID = "00020005-574f-4f20-5370-6865726f2121"
API_UUID = "00010002-574f-4f20-5370-6865726f2121"

async def connect_r2d2():
    # Scan for R2-D2
    device = await BleakScanner.find_device_by_filter(
        lambda d, a: a.local_name and a.local_name.startswith("D2-"),
        timeout=10.0
    )

    if not device:
        print("No R2-D2 found!")
        return

    print(f"Found: {device.name}")

    async with BleakClient(device) as client:
        # Handshake
        await client.write_gatt_char(HANDSHAKE_UUID, b"usetheforce...band")
        print("Handshake complete")

        # Subscribe to responses
        responses = []
        def callback(sender, data):
            responses.append(data)
            print(f"Response: {data.hex()}")

        await client.start_notify(API_UUID, callback)

        # Send a command (e.g., wake)
        # This would be a properly encoded V2 packet
        # See R2D2_PROTOCOL.md for packet format

        await asyncio.sleep(2)

        await client.stop_notify(API_UUID)

asyncio.run(connect_r2d2())
```

## Troubleshooting

### Robot Not Found

- Ensure robot is awake (briefly place on charger)
- Robot may be connected to another device
- Try moving closer (within 2 meters)

### Connection Fails

- Check battery level
- Robot may need firmware update
- Try power cycling the robot

### Commands Not Executing

- Verify handshake was sent first
- Check command safe interval timing
- Ensure packet format is correct (SOP, EOP, checksum)

### Responses Not Received

- Verify notification subscription is active
- Check that packet requests a response (FLAGS bit set)
- Response may be arriving in multiple BLE packets (fragmentation)

## References

- [Bleak BLE Library](https://bleak.readthedocs.io/)
- [Sphero V2 Protocol](R2D2_PROTOCOL.md)
- [Sphero SDK Documentation](https://sdk.sphero.com/docs/api_spec/general_api)

---

*Last updated: 2026-01-16*
