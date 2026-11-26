"""The LLA playground, written only in Python (Panel + Plotly).

Run it locally (Python does the work on your computer):
    panel serve docs/geodetic/global/lla/python/lla_python.py --show

Turn it into an HTML page (Python does the work inside the browser):
    panel convert docs/geodetic/global/lla/python/lla_python.py --to pyodide-worker --out docs/geodetic/global/lla/python --requirements panel plotly numpy
"""
import json
import sys

import numpy as np
import panel as pn
import plotly.graph_objects as go

TITLE = "Understanding Lon, Lat, Altitude (LLA)"
LAT, LON, ALT, INK, PIN = "#b84a06", "#1d5fbf", "#15753a", "#1f2933", "#e11d48"
MAX_ALT, MIN_ALT, EARTH_R = 1_000_000, -11_000, 6_371_000
PLACES = {  # name: (latitude, longitude)
    "Greenwich": (51.4779, -0.0015),
    "London": (51.5074, -0.1278),
    "Tokyo": (35.6762, 139.6503),
    "Rome": (41.9028, 12.4964),
}


# ------------------------------------------------------------------ the maths
def to_xyz(lat, lon, r=1.0):
    """Latitude, longitude and distance from the centre -> a 3D point."""
    lat, lon = np.radians(lat), np.radians(lon)
    return r * np.cos(lat) * np.cos(lon), r * np.cos(lat) * np.sin(lon), r * np.sin(lat)


def drawn_height(alt, stretch):
    """How high to draw the pin, in Earth radii."""
    if not stretch:
        return alt / EARTH_R
    return np.sign(alt) * 0.25 * (abs(alt) / MAX_ALT) ** 0.4


# ------------------------------------------------------------------ the land
def load_land():
    """Coastlines as a list of (longitudes, latitudes) outlines. Empty if offline."""
    url = "https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/land-110m.json"
    try:
        if sys.platform == "emscripten":  # running inside the browser
            from pyodide.http import open_url
            topo = json.loads(open_url(url).read())
        else:
            from urllib.request import urlopen
            topo = json.loads(urlopen(url, timeout=10).read())
    except Exception:
        return []

    scale, move = np.array(topo["transform"]["scale"]), np.array(topo["transform"]["translate"])
    arcs = [np.cumsum(a, axis=0) * scale + move for a in topo["arcs"]]
    outlines = []
    for shape in topo["objects"]["land"]["geometries"]:
        polygons = [shape["arcs"]] if shape["type"] == "Polygon" else shape["arcs"]
        for ring in (ring for polygon in polygons for ring in polygon):
            points = np.vstack([arcs[i] if i >= 0 else arcs[~i][::-1] for i in ring])
            lon = np.degrees(np.unwrap(np.radians(points[:, 0])))  # no jump at the date line
            lat = points[:, 1]
            if abs(lon[-1] - lon[0]) > 180:  # Antarctica goes all the way round: close it at the pole
                lon, lat = np.append(lon, [lon[-1], lon[0]]), np.append(lat, [-90, -90])
            outlines.append((lon, lat))
    return outlines


def land_mask(outlines, lats, lons):
    """1 where a grid point is on land, 0 where it's sea."""
    inside = np.zeros((len(lats), len(lons)), bool)
    for lon, lat in outlines:
        for shift in (-360, 0, 360):
            x1, y1, x2, y2 = lon + shift, lat, np.roll(lon, -1) + shift, np.roll(lat, -1)
            for row, y in enumerate(lats):  # count how many edges are crossed, going east
                hit = (y1 > y) != (y2 > y)
                cross = x1[hit] + (y - y1[hit]) / (y2[hit] - y1[hit]) * (x2[hit] - x1[hit])
                inside[row] ^= (cross[:, None] > lons).sum(axis=0) % 2 == 1
    return inside.astype(float)


def joined(outlines, shifts=(0,)):
    """All the outlines in one line, with gaps (None) between them."""
    xs, ys = [], []
    for lon, lat in outlines:
        for shift in shifts:
            xs += [*(lon + shift), lon[0] + shift, None]
            ys += [*lat, lat[0], None]
    return xs, ys


LAND = load_land()
GRID_LAT, GRID_LON = np.linspace(-90, 90, 91), np.linspace(-180, 180, 181)
MASK = land_mask(LAND, np.clip(GRID_LAT, -89.9, 89.9), GRID_LON)


# ------------------------------------------------------------------ the globe
# Each plot is built once. When something changes, only the pieces that move are updated,
# because rebuilding the whole Earth every time is far too slow.
def line3d(points, color, width, name=None):
    return go.Scatter3d(x=points[0], y=points[1], z=points[2], mode="lines", hoverinfo="skip", name=name,
                        line=dict(color=color, width=width))


def text3d(point, text, color, name=None):
    return go.Scatter3d(x=[point[0]], y=[point[1]], z=[point[2]], mode="text", text=[f"<b>{text}</b>"], name=name,
                        hoverinfo="skip", textfont=dict(color=color, size=14))


def wedge(color, name):
    """A see-through slice: the Earth's centre, then an arc of 49 points."""
    empty = np.zeros(50)
    return go.Mesh3d(x=empty, y=empty, z=empty, i=[0] * 48, j=list(range(1, 49)), k=list(range(2, 50)),
                     color=color, opacity=0.45, hoverinfo="skip", name=name)


def look_from(lat, lon, distance=1.75):
    x, y, z = to_xyz(lat, lon, distance)
    return dict(eye=dict(x=x, y=y, z=z), up=dict(x=0, y=0, z=1))


def build_globe():
    lon, lat = np.meshgrid(GRID_LON, GRID_LAT)
    x, y, z = to_xyz(lat, lon)
    around, up = np.linspace(-180, 180, 121), np.linspace(-90, 90, 61)
    xs, ys = joined(LAND)
    coast = to_xyz(np.array(ys, float), np.array(xs, float), 1.003)
    nowhere = np.zeros((3, 2))

    traces = [  # the parts that never change
        go.Surface(x=x, y=y, z=z, surfacecolor=MASK, cmin=0, cmax=1, showscale=False, opacity=0.55, hoverinfo="skip",
                   colorscale=[[0, "#d6e7f5"], [1, "#b3c79d"]], lighting=dict(ambient=0.9, diffuse=0.2, specular=0)),
        line3d(coast, "rgba(90,110,80,0.7)", 1.5),
        *[line3d(to_xyz(np.full(121, a), around, 1.002), "rgba(70,90,110,0.3)", 1) for a in (-60, -30, 30, 60)],
        *[line3d(to_xyz(up, np.full(61, o), 1.002), "rgba(70,90,110,0.3)", 1) for o in range(-180, 180, 30)],
        line3d(to_xyz(np.zeros(121), around, 1.003), LAT, 4),
        line3d(to_xyz(up, np.zeros(61), 1.003), LON, 4),
        text3d((0, 0, 1.12), "N", INK), text3d((0, 0, -1.12), "S", INK),
        # the parts that move
        wedge(LON, "lon slice"), line3d(nowhere, LON, 8, "lon arc"), text3d((0, 0, 0), "", LON, "lon label"),
        wedge(LAT, "lat slice"), line3d(nowhere, LAT, 8, "lat arc"), text3d((0, 0, 0), "", LAT, "lat label"),
        line3d(nowhere, ALT, 8, "alt line"), text3d((0, 0, 0), "", ALT, "alt label"),
        go.Scatter3d(x=[0], y=[0], z=[0], mode="markers", hoverinfo="skip", name="pin",
                     marker=dict(size=8, color=PIN, line=dict(color="white", width=2))),
    ]
    hidden = dict(visible=False, range=[-1.3, 1.3])
    return go.Figure(traces, dict(
        height=400, margin=dict(l=0, r=0, t=0, b=0), showlegend=False, paper_bgcolor="#f6f8fa", uirevision="keep",
        scene=dict(xaxis=hidden, yaxis=hidden, zaxis=hidden, aspectmode="cube", camera=look_from(20, 10))))


def north_south(v):
    return f"{abs(v):.1f}°" + (" N" if v > 0.05 else " S" if v < -0.05 else "")


def east_west(v):
    return f"{abs(v):.1f}°" + (" E" if v > 0.05 else " W" if v < -0.05 else "")


def height_text(metres):
    return f"{metres / 1000:,.1f} km".replace(".0 km", " km") if abs(metres) >= 10_000 else f"{metres:,.0f} m"


def update_globe(lat, lon, alt, show_lat, show_lon, show_alt, stretch):
    part = {trace.name: trace for trace in GLOBE.data if trace.name}

    def place(name, points, show, text=None):
        x, y, z = points
        part[name].update(x=np.atleast_1d(x), y=np.atleast_1d(y), z=np.atleast_1d(z), visible=bool(show))
        if text is not None:
            part[name].text = [f"<b>{text}</b>"]

    def place_wedge(which, arc, show):
        place(which + " slice", [np.append(0, p) for p in arc], show)
        place(which + " arc", arc, show)

    height = drawn_height(alt, stretch)
    foot, tip = to_xyz(lat, lon), to_xyz(lat, lon, 1 + height)
    steps = np.linspace(0, 1, 49)
    with GLOBE.batch_update():  # send all the changes together
        place_wedge("lon", to_xyz(np.zeros(49), lon * steps), show_lon)
        place_wedge("lat", to_xyz(lat * steps, np.full(49, lon)), show_lat)
        # Labels sit outside the ball, because Plotly hides text behind solid shapes.
        place("lon label", to_xyz(0, lon / 2, 1.16), show_lon and abs(lon) > 3, east_west(lon) + " (λ)")
        place("lat label", to_xyz(lat / 2, lon, 1.16), show_lat and abs(lat) > 3, north_south(lat) + " (φ)")
        place("alt line", [np.array([a, b]) for a, b in zip(foot, tip)], show_alt)
        place("alt label", to_xyz(lat, lon, 1.14 + height), show_alt and abs(alt) >= 1, height_text(alt))
        place("pin", tip, True)


# ------------------------------------------------------------------ the flat map
def build_map():
    def line(x, y, color, width, dash="solid", name=None):
        return go.Scatter(x=x, y=y, mode="lines", hoverinfo="skip", name=name,
                          line=dict(color=color, width=width, dash=dash))

    xs, ys = joined(LAND, (-360, 0, 360))
    traces = [
        go.Scatter(x=xs, y=ys, mode="lines", fill="toself", fillcolor="#b9cba6", hoverinfo="skip",
                   line=dict(width=0.5, color="#b9cba6")),
        line([-180, 180], [0, 0], LAT, 1.5),
        line([0, 0], [-90, 90], LON, 1.5),
        line([0, 0], [0, 0], LON, 3, "dash", "across"),
        line([0, 0], [0, 0], LAT, 3, "dash", "up"),
        go.Scatter(x=[0], y=[0], mode="markers", hoverinfo="skip", name="pin",
                   marker=dict(size=13, color=PIN, line=dict(color="white", width=2))),
        # An invisible sheet over the whole map, so that a click anywhere is noticed.
        go.Heatmap(x=np.arange(-180, 181, 2), y=np.arange(-90, 91, 2), z=np.zeros((91, 181)), opacity=0,
                   showscale=False, hoverinfo="none"),
    ]
    axis = dict(showticklabels=False, dtick=30, gridcolor="rgba(70,90,110,0.22)", zeroline=False, fixedrange=True)
    return go.Figure(traces, dict(
        height=230, margin=dict(l=0, r=0, t=0, b=0), showlegend=False, paper_bgcolor="#f6f8fa", plot_bgcolor="#d6e7f5",
        xaxis=dict(range=[-180, 180], **axis), yaxis=dict(range=[-90, 90], **axis)))


def update_map(lat, lon):
    part = {trace.name: trace for trace in MAP.data if trace.name}
    with MAP.batch_update():
        part["across"].update(x=[0, lon], y=[lat, lat])
        part["up"].update(x=[lon, lon], y=[0, lat])
        part["pin"].update(x=[lon], y=[lat])


GLOBE, MAP = build_globe(), build_map()


# ------------------------------------------------------------------ the words
def plain_words(lat, lon, alt):
    def bold(text, color):
        return f'<b style="color:{color}">{text}</b>'

    if abs(alt) < 0.5:
        rise = "stay " + bold("on the model surface", ALT)
    else:
        rise = ("rise " if alt > 0 else "sink ") + bold(height_text(abs(alt)), ALT)
    if abs(lat) > 89.999:
        pole = bold("North" if lat > 0 else "South", LAT)
        return f"You're at the {pole} Pole. Every longitude line meets here, so longitude makes no difference. Then {rise}."
    around = ("don't turn at all" if abs(lon) < 0.005
              else "go " + bold(f"{abs(lon):.2f}° {'east' if lon > 0 else 'west'}", LON) + " around")
    up = ("stay on the equator" if abs(lat) < 0.005
          else "go " + bold(f"{abs(lat):.2f}° {'north' if lat > 0 else 'south'}", LAT))
    return f"Start where the equator meets the 0° longitude line: {around}, then {up}, then {rise}."


# ------------------------------------------------------------------ the controls
STYLE = """
html { color-scheme: light; }
body { background: white !important; color: #1f2933; font-family: 'Segoe UI', Helvetica, Arial, sans-serif; }
"""
pn.extension("plotly", raw_css=[STYLE], theme="default")


def slider_and_box(label, color, value, low, high, step):
    name = pn.pane.HTML(f'<b style="color:{color};font-size:15px">{label}</b>', sizing_mode="stretch_width")
    box = pn.widgets.FloatInput(value=value, start=low, end=high, step=step, width=125)
    slider = pn.widgets.FloatSlider(value=value, start=low, end=high, step=step, show_value=False, tooltips=False, name="",
                                    bar_color=color, sizing_mode="stretch_width")
    return name, box, slider


lat_name, lat_box, lat_slider = slider_and_box("Latitude, φ (up / down)", LAT, 40.0, -90, 90, 0.1)
lon_name, lon_box, lon_slider = slider_and_box("Longitude, λ (around)", LON, 50.0, -180, 180, 0.1)
alt_name, alt_box, alt_slider = slider_and_box("Altitude in metres", ALT, 300_000.0, MIN_ALT, MAX_ALT, 100)
# The altitude slider is gentler near the ground, so you can pick low heights too.
alt_slider.param.update(start=0, end=1, step=0.001, value=(300_000 / MAX_ALT) ** (1 / 3))

show_lat = pn.widgets.Checkbox(name="latitude angle", value=True)
show_lon = pn.widgets.Checkbox(name="longitude angle", value=True)
show_alt = pn.widgets.Checkbox(name="altitude line", value=True)
stretch = pn.widgets.Checkbox(name="stretch altitude so I can see it", value=True)

globe = pn.pane.Plotly(GLOBE, config=dict(displayModeBar=False, scrollZoom=False), sizing_mode="stretch_width", height=400)
flat_map = pn.pane.Plotly(MAP, config=dict(displayModeBar=False), sizing_mode="stretch_width", height=230)
words, scale_note, alt_km = pn.pane.HTML(), pn.pane.HTML(), pn.pane.HTML(width=110)


def hint(text):
    return f'<span style="color:#5b7083;font-size:14px">{text}</span>'


# ------------------------------------------------------------------ what happens when something changes
def redraw(*events):
    lat, lon, alt = lat_box.value or 0, lon_box.value or 0, alt_box.value or 0
    update_globe(lat, lon, alt, show_lat.value, show_lon.value, show_alt.value, stretch.value)
    update_map(lat, lon)
    words.object = f'<span style="font-size:16px">{plain_words(lat, lon, alt)}</span>'
    alt_km.object = f'<span style="color:{ALT}">= {alt / 1000:,.3f}'.rstrip("0").rstrip(".") + " km</span>"
    scale_note.object = hint(("Altitude is drawn far taller than real life." if stretch.value else
                              "True scale: even a cruising plane looks glued to the ground.")
                             + " The Earth is drawn as a perfect ball.")


busy = False


def move_to(lat=None, lon=None, alt=None):
    """Set the numbers, keep the sliders in step, then draw once."""
    global busy
    if busy:
        return
    busy = True
    for value, box, slider in ((lat, lat_box, lat_slider), (lon, lon_box, lon_slider)):
        if value is not None:
            box.value = slider.value = round(float(value), 4)
    if alt is not None:
        alt_box.value = round(float(alt))
        alt_slider.value = (max(0, alt) / MAX_ALT) ** (1 / 3)
    busy = False
    redraw()


def jump(place):
    lat, lon = PLACES[place]
    move_to(lat, lon, 0)
    GLOBE.layout.scene.camera = look_from(float(np.clip(lat * 0.5, -40, 40)), lon - 28)  # turn to face it


def clicked_map(event):
    if event.new:
        point = event.new["points"][0]
        move_to(point["y"], point["x"])


lat_slider.param.watch(lambda e: move_to(lat=e.new), "value")
lon_slider.param.watch(lambda e: move_to(lon=e.new), "value")
alt_slider.param.watch(lambda e: move_to(alt=MAX_ALT * e.new ** 3), "value")
lat_box.param.watch(lambda e: move_to(lat=e.new), "value")
lon_box.param.watch(lambda e: move_to(lon=e.new), "value")
alt_box.param.watch(lambda e: move_to(alt=e.new), "value")
for box in (show_lat, show_lon, show_alt, stretch):
    box.param.watch(redraw, "value")
flat_map.param.watch(clicked_map, "click_data")

buttons = []
for place in PLACES:
    button = pn.widgets.Button(name=place)
    button.on_click(lambda event, place=place: jump(place))
    buttons.append(button)


# ------------------------------------------------------------------ the page
def card(*items, **options):
    style = {"background": "#f6f8fa", "border": "1px solid #d5dbe1", "border-radius": "10px", "padding": "12px"}
    return pn.Column(*items, styles=style, sizing_mode="stretch_width", margin=6, **options)


def heading(text):
    return pn.pane.HTML(f'<b style="font-size:16px">{text}</b>', margin=(0, 5))


redraw()
pn.Column(
    pn.pane.HTML(f'<h1 style="font-size:26px;margin:0">{TITLE}</h1>'),
    pn.Row(
        card(heading("On the globe"), globe, pn.FlexBox(show_lat, show_lon, show_alt, stretch), scale_note),
        card(heading("The same spot on a flat map"), pn.Spacer(height=75), flat_map, pn.Spacer(height=75),
             pn.pane.HTML(hint("On this map, longitude is simply left–right and latitude is up–down. Click it to move the pin."))),
        sizing_mode="stretch_width"),
    card(heading("In plain words: how to reach the pin"), words,
         pn.pane.HTML(hint("Around and up/down appear on both plots. Height only shows on the globe."))),
    pn.Row(
        card(pn.Row(lat_name, lat_box, pn.pane.HTML("°", width=110)), lat_slider,
             pn.Row(lon_name, lon_box, pn.pane.HTML("°", width=110)), lon_slider,
             pn.Row(alt_name, alt_box, alt_km), alt_slider),
        card(heading("Jump to"), pn.Row(*buttons)),
        sizing_mode="stretch_width"),
    max_width=1100, sizing_mode="stretch_width",
).servable(title=TITLE)
