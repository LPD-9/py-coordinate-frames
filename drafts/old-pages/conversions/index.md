---
title: Understanding Coordinate Conversions
hide:
  - toc
---

# Understanding Coordinate Conversions

**A conversion describes the same place in a different frame. The place doesn't move. Only the numbers change.**

## ELI5

Think of three people describing the same ant on an orange:

- The first says how far **around, up and off the peel** it is. That's [LLA](../geodetic/global/lla/README.md).
- The second measures with skewers **from the middle**. That's [ECEF](../cartesian/global/ecef/README.md).
- The third stands nearby and points **north, east and down**. That's [NED](../cartesian/local/cart-ned/README.md).

A conversion is a translator between them.

## The map: two links

![LLA, ECEF and NED as three stations in a row, with ECEF in the middle.](stations.svg)

| Link | What it does |
|---|---|
| **LLA ⇄ ECEF** | **Swap** angles and a height for straight distances. It's the same Earth either way. |
| **ECEF ⇄ NED** | **Move** zero from the Earth's centre to your spot, then **turn** the axes to face north, east and down. |

To get from LLA to NED, go through ECEF.

## Playground

Things to try:

- Move one slider in any frame. Which numbers in the others change?
- Compare the three globes. It's the same pin each time, just described differently.
- Press **Tokyo**, then **Rome**. NED stays the same. Why don't the others?
- Set the NED numbers to 0, 0, 0. Where is the pin now?

<iframe class="playground" src="playground.html" title="Interactive conversions playground"></iframe>

<a href="playground.html" target="_blank">Open the playground on its own</a>

## The four recipes

### LLA → ECEF

- **You need:** latitude, longitude and altitude.
- **What happens:**
    1. Work out the Earth's radius at that latitude, because the Earth is slightly squashed.
    2. Add the altitude. That's the length of a line to the pin.
    3. Split the line into up (Z) and sideways, then split sideways into X and Y.

??? example "Python"
    ```python
    import math

    A = 6378137.0            # centre to equator, in metres
    E2 = 0.00669437999014    # how squashed the Earth is

    def lla_to_ecef(lat, lon, h):
        lat, lon = math.radians(lat), math.radians(lon)
        r = A / math.sqrt(1 - E2 * math.sin(lat) ** 2)
        x = (r + h) * math.cos(lat) * math.cos(lon)
        y = (r + h) * math.cos(lat) * math.sin(lon)
        z = (r * (1 - E2) + h) * math.sin(lat)
        return x, y, z

    print(lla_to_ecef(51.5074, -0.1278, 0))   # London: about (3977994, -8873, 4968875)
    ```

### ECEF → LLA

- **You need:** X, Y and Z.
- **What happens:**
    1. Longitude comes straight from X and Y.
    2. Latitude compares up with sideways. Because of the squash, the computer guesses, corrects and repeats.
    3. Altitude is what's left after taking away the Earth underneath.

??? example "Python (also needs the code above)"
    ```python
    def ecef_to_lla(x, y, z):
        p = math.hypot(x, y)              # distance from the Earth's middle line
        lat = math.atan2(z, p)            # first guess
        for _ in range(10):               # correct it, and repeat
            r = A / math.sqrt(1 - E2 * math.sin(lat) ** 2)
            lat = math.atan2(z + E2 * r * math.sin(lat), p)
        r = A / math.sqrt(1 - E2 * math.sin(lat) ** 2)
        h = p * math.cos(lat) + z * math.sin(lat) - A * A / r
        return math.degrees(lat), math.degrees(math.atan2(y, x)), h

    print(ecef_to_lla(3977994, -8873, 4968875))   # back to London
    ```

### ECEF → NED

![Step 1 moves zero from the Earth's centre to your spot. Step 2 turns the axes to face north and down.](move-turn.svg)

- **You need:** the pin's X, Y and Z, **and where zero is**.
- **What happens:**
    1. **Move:** take zero's ECEF away from the pin's ECEF.
    2. **Turn** by zero's longitude. East drops out.
    3. **Turn** by zero's latitude. North and down drop out.

??? example "Python (also needs the code above)"
    ```python
    def ecef_to_ned(x, y, z, zero_lat, zero_lon, zero_h):
        x0, y0, z0 = lla_to_ecef(zero_lat, zero_lon, zero_h)
        dx, dy, dz = x - x0, y - y0, z - z0            # move

        lat, lon = math.radians(zero_lat), math.radians(zero_lon)
        out = math.cos(lon) * dx + math.sin(lon) * dy  # turn by longitude
        e = -math.sin(lon) * dx + math.cos(lon) * dy

        n = -math.sin(lat) * out + math.cos(lat) * dz  # turn by latitude
        d = -math.cos(lat) * out - math.sin(lat) * dz
        return n, e, d

    pin = lla_to_ecef(51.5174, -0.1278, 0)             # a bit north of London
    print(ecef_to_ned(*pin, 51.5074, -0.1278, 0))      # about (1113, 0, 0)
    ```

### NED → ECEF

- **You need:** north, east and down, **and where zero is**.
- **What happens:** the last recipe backwards.
    1. **Turn back** by zero's latitude, then by its longitude.
    2. **Move back:** add zero's ECEF on again.

??? example "Python (also needs the code above)"
    ```python
    def ned_to_ecef(n, e, d, zero_lat, zero_lon, zero_h):
        lat, lon = math.radians(zero_lat), math.radians(zero_lon)
        out = -math.sin(lat) * n - math.cos(lat) * d   # turn back by latitude
        dz = math.cos(lat) * n - math.sin(lat) * d

        dx = math.cos(lon) * out - math.sin(lon) * e   # turn back by longitude
        dy = math.sin(lon) * out + math.cos(lon) * e

        x0, y0, z0 = lla_to_ecef(zero_lat, zero_lon, zero_h)
        return x0 + dx, y0 + dy, z0 + dz               # move back

    pin = ned_to_ecef(600, 450, -300, 51.5074, -0.1278, 0)
    print(ecef_to_lla(*pin))                           # about (51.5128, -0.1213, 300)
    ```

## Going the long way: LLA ⇄ NED

There's no new recipe. Use two of the four:

- **LLA → NED:** LLA → ECEF, then ECEF → NED.
- **NED → LLA:** NED → ECEF, then ECEF → LLA.

## Common traps

??? warning "Degrees or radians?"
    Python's `math.sin` and `math.cos` want radians. The code above converts for you, using `math.radians`.

??? warning "Forgetting where zero is"
    NED conversions always need zero. The wrong zero gives a sensible-looking answer in the wrong place.

??? warning "Moving without turning"
    Taking zero's ECEF away gives you X, Y and Z differences. They aren't north, east and down until you've turned the axes.

??? warning "Up and down"
    D is positive downwards. A drone 100 m above zero has D = −100.

??? warning "Metres and kilometres"
    Use metres everywhere. Mixing units is the easiest way to end up in space.

??? warning "Using the wrong height"
    These recipes use height above the WGS84 model, not above sea level. They can differ by up to about 100 m.

??? warning "This is for places, not speeds"
    To convert a **direction** or a **speed** between ECEF and NED, you only do the *turn*, not the *move*.

## One sentence to remember

> **Swap** to get between LLA and ECEF. **Move, then turn** to get from ECEF to NED.
