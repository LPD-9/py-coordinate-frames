---
title: Understanding Earth-Centred, Earth-Fixed (ECEF)
hide:
  - toc
---

# Understanding Earth-Centred, Earth-Fixed (ECEF)

**ECEF says where you are using three straight-line distances from the Earth's centre.**

## ELI5

Imagine pushing three long skewers through the middle of an orange. They cross at the exact centre, each at a right angle to the other two.

To tell a friend where an ant is, you start **in the centre** and give three instructions:

1. <span class="x">X</span>: go this far along the first skewer.
2. <span class="y">Y</span>: turn, and go this far in the direction of the second.
3. <span class="z">Z</span>: turn, and go this far in the direction of the third.

That's all ECEF is: *three walks in straight lines, starting from the middle.* You have to imagine walking through solid rock.

The name says the same thing:

- **Earth-Centred**: zero is at the Earth's centre.
- **Earth-Fixed**: the skewers are stuck in the orange. Spin it, and they spin too.

## ID card

| Question | Answer |
|---|---|
| **Where is zero?** | The centre of the Earth. |
| **Which way do the axes point?** | <span class="x">X</span> comes out where the equator meets 0° longitude. <span class="y">Y</span> comes out of the equator at 90° east. <span class="z">Z</span> comes out of the North Pole. |
| **What is it attached to?** | The spinning Earth. A parked car keeps the same ECEF all day. |
| **What are the numbers?** | Three **distances**, usually in metres. |
| **What range can they have?** | Anything, positive or negative. On the ground, each is between about −6,380 km and +6,380 km. |

!!! tip "Why distances?"
    Angles are awkward for maths. With three straight distances, you can add, subtract and measure in a straight line. That's why GPS works out your position in ECEF first.

## The three axes

![The X, Y and Z axes coming out of the Earth, crossing at its centre.](axes.svg)

Another way to picture it is a **box**. One corner is at the Earth's centre, the edges are X, Y and Z, and you're at the opposite corner.

A **minus** means the opposite way. If Z is negative, you're south of the equator.

## What "Earth-Fixed" means

![The Earth from above, now and six hours later. The axes turn with the Earth, so a person's X and Y stay the same.](earth-fixed.svg)

Someone standing on the equator is being carried around at about 465 metres **every second**. Their ECEF numbers don't change at all, because the axes are carried around with them.

## Playground

Things to try:

- Drag the globe. The box beside it turns too, so you can match up the edges.
- Move <span class="z">Z</span> only. The pin goes up or down the picture, but it doesn't stay on the ground.
- Set all three to 0. Where are you?
- Jump to **Tokyo**. Why is its <span class="x">X</span> negative?
- Tick **spin the Earth** and watch the numbers. Nothing changes.

<iframe class="playground" src="playground.html" title="Interactive ECEF playground"></iframe>

<a href="playground.html" target="_blank">Open the playground on its own</a>

## How is this different from LLA?

ECEF and [LLA](../../../geodetic/global/lla/index.md) are attached to the same Earth and describe the same places. Only the numbers differ, like a grid reference and a street address.

| | LLA | ECEF |
|---|---|---|
| **Numbers** | Two angles and a height | Three distances |
| **Starts from** | The surface, at 0°, 0° | The Earth's centre |
| **Attached to** | The spinning Earth | The spinning Earth |
| **Easy for** | People and maps | Computers and maths |
| **Can you see the height?** | Yes, it's the third number | No, it's mixed into all three |

## Why it's useful: straight lines are easy

To get the straight-line distance between two places, subtract their X, Y and Z, then use Pythagoras in 3D:

> distance = √( (difference in X)² + (difference in Y)² + (difference in Z)² )

London to Tokyo comes out at about **8,709 km**. That's a straight tunnel *through* the Earth. Flying over the surface is longer, at roughly 9,600 km.

## Some real places

At ground level on the model Earth, to the nearest km:

| Place | X (km) | Y (km) | Z (km) |
|---|---|---|---|
| Greenwich | 3,981 | 0 | 4,967 |
| London | 3,978 | −9 | 4,969 |
| Rome | 4,642 | 1,029 | 4,238 |
| Tokyo | −3,953 | 3,358 | 3,699 |

Greenwich's Y is about zero because it's almost exactly on the 0° longitude line.

## Common traps

??? warning "Z is not altitude"
    Z points out of the North Pole, not upwards from where you are.

    ![Arrows at the equator, London and the North Pole showing that local up and the Z direction only match at the pole.](up-is-not-z.svg)

    Climb straight up at the equator and Z doesn't change at all.

??? warning "You can't read the height from one number"
    Going straight up changes X, Y and Z together in most places. If height is what you care about, LLA is the better fit.

??? warning "Metres or kilometres?"
    ECEF is usually in **metres**, so the numbers are huge, such as 3977994. Mixing up metres and kilometres is an easy mistake.

??? warning "Minus signs matter"
    Swap a sign and you could land on the other side of the planet.

??? warning "ECEF is not ECI"
    **ECI** (Earth-Centred Inertial) also starts at the Earth's centre, but its axes don't spin with the Earth. In ECI, a parked car is constantly moving.

??? warning "Straight line or over the ground?"
    ECEF distances go straight through the Earth. Over a few kilometres you won't notice. Between cities, you will.

## When would I use ECEF?

- **Good for:** GPS and satellites, straight-line distances, and as a stepping stone between other frames.
- **Awkward for:** people. Nobody can picture where (3978, −9, 4969) is. It's also hard to see which way is up, north or east, which is what [NED](../../local/cart-ned/index.md) is for.

## One sentence to remember

> ECEF is **three straight walks from the Earth's centre**, along axes that spin with the Earth.
