# Sphero R2-D2 Robot Repair Guide

This guide documents physical repairs and maintenance procedures for the Sphero R2-D2 robot.

## Table of Contents
- [Battery Replacement](#battery-replacement)
- [Common Issues](#common-issues)
- [Tools Required](#tools-required)

---

## Battery Replacement

### Overview

The Sphero R2-D2 uses a 3.7V 1400mAh LiPo battery. Over time, these batteries degrade and may need replacement. Signs of a failing battery include:
- Rapid discharge (robot dies within minutes of unplugging)
- Robot failing to hold charge
- Dome/motor failures at voltages that should be adequate (>3.5V)
- Swelling of the battery (DANGER - do not use, dispose properly)

### Battery Specifications

| Specification | Value |
|---------------|-------|
| Voltage | 3.7V nominal |
| Capacity | 1400mAh |
| Chemistry | Lithium Polymer (LiPo) |
| Thickness | 6.35 mm (0.25") |
| Width | 22.22 mm (0.875") |
| Length | 69.85 mm (2.75") |
| Connector | Proprietary (requires splicing) |

**Note:** The original battery uses a proprietary connector. Replacement batteries will require splicing the original connector onto the new battery.

### Disassembly Guide

Based on the [iFixit Sphero R2-D2 teardown](https://www.ifixit.com/Teardown/Sphero+R2-D2+Teardown/97702):

1. **Remove the dome**
   - The dome lifts off - no screws required
   - Be careful of the dome rotation mechanism

2. **Remove body screws**
   - Locate the screws on the bottom of the robot
   - Use appropriate screwdriver (likely Phillips #00 or #0)

3. **Separate the shell halves**
   - Carefully pry apart the two shell halves
   - Watch for ribbon cables connecting the halves

4. **Locate the battery**
   - The battery is secured inside the body
   - Note the orientation and routing of the battery cable

5. **Disconnect the battery**
   - Carefully disconnect the battery connector from the circuit board
   - Do NOT pull on the wires - pull on the connector itself

6. **Remove the battery**
   - The battery may be held with adhesive tape
   - Gently pry it loose

### Compatible Replacement Batteries

The R2-D2 battery dimensions (6.35mm x 22.22mm x 69.85mm) are unusual and not commonly stocked. **Replacement batteries must be the same size or smaller** - larger batteries will not fit in the cavity.

#### LiPo Battery Model Naming Convention

The model number encodes dimensions: `TTWWLL` where:
- TT = thickness in 0.1mm (60 = 6.0mm)
- WW = width in mm (22 = 22mm)
- LL = length in mm (70 = 70mm)

For the R2-D2, the ideal model would be: **602270** or **LP602270**

#### Recommended Replacement Batteries (Verified to Fit)

These batteries are **smaller than the original** and will fit in the R2-D2 battery cavity:

| Model | Dimensions (T×W×L) | Capacity | Availability | Notes |
|-------|-------------------|----------|--------------|-------|
| **602060** | 6mm × 20mm × 60mm | 700-750mAh | [eBay](https://www.ebay.com/itm/114003061802), [Amazon](https://www.amazon.com/dp/B0B3MPQMWW) | **Best option** - common, good capacity |
| **501965** | 5mm × 19mm × 65mm | 700mAh | [Polybattery](https://polybattery.com/product/5mm-lp501965-700mah-slim-reinventing-lipo-battery-3-7-v-gb31241) | Slim profile, fits easily |
| **502060** | 5mm × 20mm × 60mm | 600mAh | [eBay](https://www.ebay.com/itm/114001910832), [Alibaba](https://www.alibaba.com/showroom/lipo-battery-502060-3.7v-600mah.html) | Very common, lower capacity |

**Capacity comparison:**
- Original R2-D2 battery: 1400mAh
- 602060 replacement: 700-750mAh (~50% of original)
- Runtime will be reduced but adequate for classroom use (1-2 hours)

#### Where to Buy

**Ready-to-ship options (recommended for small quantities):**

| Source | Search Term | Notes |
|--------|-------------|-------|
| [eBay](https://www.ebay.com) | "602060 lipo battery" | Many sellers, ships fast |
| [Amazon](https://www.amazon.com) | "602060 3.7V battery" | Prime shipping available |
| [AliExpress](https://www.aliexpress.com) | "602060 lipo" | Cheapest, slow shipping |
| [Alibaba](https://www.alibaba.com) | "602060 lipo battery" | Bulk orders (10+ units) |

**Custom battery manufacturers (for bulk/exact-match orders):**

| Supplier | MOQ | Notes |
|----------|-----|-------|
| [Whale Battery](https://www.whalebattery.com) | Contact | Custom 6mm batteries, email: info@whalebattery.com |
| [Lipolybatteries.com](https://lipolybatteries.com) | 5000 pcs | Custom sizes available |
| [DNK Power](https://www.dnkpower.com) | Contact | Free custom design services |
| [Batterylipo.com](https://www.batterylipo.com) | Contact | 256 models in 16-20mm width range |

#### Search Terms for Finding Batteries

```
"602060 lipo battery 3.7V"
"501965 lipo battery"
"3.7V 700mAh lipo 6mm"
"LP602060 rechargeable"
```

#### Important Considerations

- **Size constraint**: Battery must be ≤6.35mm thick, ≤22mm wide, ≤70mm long
- **Smaller is OK**: A 600-750mAh battery provides adequate runtime
- **Voltage**: Must be 3.7V nominal (4.2V fully charged)
- **Connector**: Will need to splice the original connector onto new battery
- **Protection circuit**: Most replacement batteries include protection (recommended)

### Connector Splicing Procedure

Since the R2-D2 uses a proprietary connector, you'll need to splice it onto the new battery:

1. **Cut the old connector**
   - Leave as much wire as possible on the connector side
   - Cut the wires from the old battery

2. **Prepare the new battery wires**
   - Strip about 5mm of insulation from each wire
   - Tin the exposed wire with solder

3. **Match polarity**
   - **CRITICAL**: Red to Red (positive), Black to Black (negative)
   - Reversing polarity will damage the robot

4. **Solder the connection**
   - Twist the matching wires together
   - Apply solder to create a solid joint
   - Use heat shrink tubing to insulate each connection

5. **Test before reassembly**
   - Plug in the new battery
   - Verify the robot powers on
   - Check that charging works

### Reassembly

1. Position the new battery in the same location as the original
2. Use double-sided tape or foam tape to secure if needed
3. Route the cable carefully to avoid pinching
4. Reassemble the shell halves
5. Replace all screws
6. Reattach the dome

### Safety Warnings

- **LiPo batteries are dangerous if mishandled**
- Never puncture, bend, or crush the battery
- Do not expose to high temperatures
- If a battery swells, do NOT use it - dispose of it properly
- Always observe correct polarity when connecting
- Do not short-circuit the battery terminals

---

## Common Issues

### Dome Not Rotating

**Possible causes:**
1. Low battery (charge to >3.7V)
2. Mechanical obstruction
3. Motor failure

**Diagnosis:**
- Run the validation tests to check dome at various angles
- Listen for motor sounds when dome commands are sent
- Check battery voltage first - dome failures are common below 3.5V

### Robot Not Connecting via Bluetooth

**Possible causes:**
1. Robot is asleep - place on charger briefly to wake
2. Battery completely dead
3. Bluetooth antenna issue

**Solutions:**
- Place robot on charger for a few seconds
- Try scanning multiple times
- Move closer to the robot (within 2 meters)

### Legs Not Deploying (Tripod Mode Failure)

**Possible causes:**
1. Low battery
2. Mechanical binding
3. Servo/motor failure

**Diagnosis:**
- Check battery voltage
- Listen for motor sounds during stance changes
- Inspect legs for visible damage or obstruction

---

## Tools Required

- Phillips screwdriver set (#00, #0, #1)
- Plastic pry tools (guitar picks work well)
- Soldering iron and solder
- Heat shrink tubing (assorted small sizes)
- Wire strippers
- Multimeter (for checking battery voltage and polarity)
- Double-sided foam tape
- Tweezers

---

## References

- [iFixit Sphero R2-D2 Teardown](https://www.ifixit.com/Teardown/Sphero+R2-D2+Teardown/97702)
- [Sphero R2-D2 Specifications](https://sphero.com/)

---

*Last updated: 2026-01-16*
