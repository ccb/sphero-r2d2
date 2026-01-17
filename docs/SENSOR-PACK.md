# R2D2 Sensor Pack

The sensor pack is a Raspberry Pi-based accessory that mounts on top of the Sphero R2-D2, adding additional sensors and a camera. Originally developed for the [CIS 5210 Artificial Intelligence course](https://artificial-intelligence-class.org/).

## Hardware Components

| Component | Description |
|-----------|-------------|
| Raspberry Pi Zero | Main controller with 16GB Micro SD card |
| LiPo Battery | Powers the Pi, with power management board |
| Ultrasonic Range Finder | Distance measurement via sound waves |
| IR Cliff Detection Sensor | Detects drops/edges using infrared |
| Camera Module | 1080p video at 30fps |
| 3D Printed Mount | Front and back sections, magnetic attachment |
| AprilTag | Mounted on top for position tracking |

## Physical Assembly

```
        ┌─────────────┐
        │  AprilTag   │  ← For position tracking
        └─────────────┘
        ┌─────────────┐
        │  Camera     │  ← 1080p/30fps
        ├─────────────┤
  ┌─────┤   Pi Zero   ├─────┐
  │     └─────────────┘     │
  │ Ultrasonic        IR    │
  │ Sensor            Sensor│
  └─────────────────────────┘
              │
        ┌─────┴─────┐
        │   R2-D2   │
        │   Dome    │
        └───────────┘
```

The sensor pack attaches magnetically:
- **Front mount**: Raspberry Pi and sensors
- **Back mount**: LiPo battery
- **Top**: AprilTag for external tracking

## Sensors

### Ultrasonic Range Finder

Measures distance to obstacles using sound wave reflection.

| Specification | Value |
|---------------|-------|
| GPIO Pins | Trigger: 4, Echo: 17 |
| Output | Distance in centimeters |
| Method | `.get_obstacle_distance()` |

### IR Cliff Detection Sensor

Detects drops or edges (stairs, table edges) using infrared light.

| Specification | Value |
|---------------|-------|
| GPIO Pin | 21 |
| Output | Binary: 0 = safe, 1 = cliff detected |
| Adjustable | Yes - small screw adjusts sensitivity |

### Camera

Provides video stream for computer vision tasks.

| Specification | Value |
|---------------|-------|
| Resolution | 1080p |
| Frame Rate | 30 fps |
| Library | OpenCV |

## Software Setup

### SD Card Preparation

1. Download the disk image (check course materials for link)
2. Flash to SD card using [balenaEtcher](https://www.balena.io/etcher/)
3. Configure WiFi before first boot:

Edit `wpa_supplicant.conf` on the boot partition:
```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YOUR_WIFI_NAME"
    psk="YOUR_WIFI_PASSWORD"
}
```

4. Insert SD card into Pi Zero's side slot

### Connecting via SSH

**Default credentials:**
- Username: `pi`
- Password: `raspberry`

**Find the Pi's IP address:**
- Use a network scanner app (Fing, LanScan, etc.)
- Or check your router's connected devices

**Connect:**
```bash
ssh pi@<IP_ADDRESS>
```

### Python Interface

```python
from rpi_sensor import RPiSensor

sensor = RPiSensor()

# Get distance to obstacle (cm)
distance = sensor.get_obstacle_distance()

# Check for cliff
cliff_detected = sensor.get_cliff_status()  # 0 or 1

# Camera frame (requires OpenCV)
frame = sensor.get_camera_frame()
```

## Power Management

- **Charging**: Ports located on rear of battery pack
- **Status**: Blue LED indicates battery level
- **Important**: Always shut down properly before unplugging

```bash
sudo shutdown -h now
```

Wait for green LED to stop blinking before disconnecting power.

## Calibration

### IR Sensor Range Adjustment

The IR cliff sensor has a small adjustment screw:
- Turn clockwise to increase detection distance
- Turn counter-clockwise to decrease detection distance
- Test with various surfaces (carpet, tile, wood)

### Ultrasonic Sensor

No calibration needed, but note:
- Soft surfaces may absorb sound (less accurate)
- Very close objects (<2cm) may not register
- Optimal range: 2cm - 400cm

## Integration with R2D2

The sensor pack communicates with the R2D2 via BLE through the Raspberry Pi:

```python
from spherov2 import scanner
from spherov2.sphero_edu import SpheroEduAPI
from rpi_sensor import RPiSensor

# Connect to R2D2
toy = scanner.find_R2D2()
sensor = RPiSensor()

with SpheroEduAPI(toy) as r2:
    while True:
        # Check for obstacles
        distance = sensor.get_obstacle_distance()
        if distance < 20:  # Less than 20cm
            r2.stop_roll()
            r2.play_sound(...)  # Alert sound

        # Check for cliffs
        if sensor.get_cliff_status() == 1:
            r2.stop_roll()
            # Back up
            r2.set_speed(-50)
```

## Potential Enhancements

### Adding Audio I/O

The Raspberry Pi can support external audio devices, enabling features like ggwave communication:

| Addition | Purpose |
|----------|---------|
| USB microphone | Receive ggwave signals |
| USB speaker / I2S DAC | Transmit ggwave signals |
| USB sound card | Combined audio I/O |

```python
# Example: ggwave via Pi audio
import sounddevice as sd
import ggwave

# Pi can transmit ggwave through attached speaker
waveform = ggwave.encode("D2-55E3:LED:RED")
sd.play(waveform, samplerate=48000)

# Pi can receive ggwave through attached microphone
# and relay commands to R2D2 via BLE
```

This would enable true robot-to-robot audio communication, with each sensor pack acting as the audio transceiver.

### Powering R2D2 from Sensor Pack Battery

The sensor pack's LiPo battery could potentially power the R2D2 itself, bypassing the aging internal battery. This would:

**Benefits:**
- Extend robot lifespan (internal batteries degrade)
- Use larger capacity external battery
- Single charging point for both Pi and R2D2
- Easier battery replacement (external vs internal)

**Investigation needed:**
- R2D2 power input requirements (voltage, current)
- Whether R2D2 can operate with internal battery disconnected
- Safe way to inject power (USB port? Direct to PCB?)
- Battery capacity needed for both Pi + R2D2

**Potential approaches:**

| Approach | Pros | Cons |
|----------|------|------|
| USB power injection | Non-invasive | May not work if R2D2 expects battery |
| Direct PCB connection | Full control | Requires disassembly, voids warranty |
| Parallel with internal | Supplements weak battery | Complex wiring |

**Caution:** The R2D2's charging circuit expects specific battery behavior. Injecting external power incorrectly could damage the robot or create fire hazards.

### Additional Sensors

The Pi Zero has available GPIO pins for:
- Additional ultrasonic sensors (side/rear coverage)
- Temperature/humidity sensor
- Light sensor
- Compass/magnetometer

## Resources

- [Sensor Pack Setup Guide](https://artificial-intelligence-class.org/r2d2_assignments/22fall/hw0/sensor-pack-setup.html)
- [HW1: Sensors Assignment](https://artificial-intelligence-class.org/r2d2_assignments/22fall/hw1/hw1.html)
- [balenaEtcher](https://www.balena.io/etcher/) - SD card flasher
- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)

---

*Last updated: 2026-01-16*
