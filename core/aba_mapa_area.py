import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import zipfile
import math
import xml.etree.ElementTree as ET
import os
import urllib.request
from io import BytesIO

from .ui import place_logo_footer

try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_OK = True
except Exception:
    PIL_OK = False

CANVAS_W, CANVAS_H = 680, 320
R_EARTH = 6_371_000.0
TILE_SIZE = 256
MIN_ZOOM, MAX_ZOOM = 3, 19
OSM_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
USER_AGENT = "Fertisoja/1.0 (educational; contact: example@example.com)"


def make_section(parent, title, font):
    frame = ctk.CTkFrame(parent)
    frame.pack(fill="x", pady=(8, 0))
    header = ctk.CTkLabel(frame, text=title, font=font, anchor="w")
    header.pack(anchor="w", padx=10, pady=(10, 6))
    body = ctk.CTkFrame(frame, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    return body


def _lonlat_to_xy_m(lat0_deg, lon_deg, lat_deg):
    lat0 = math.radians(lat0_deg)
    x = math.radians(lon_deg) * math.cos(lat0) * R_EARTH
    y = math.radians(lat_deg) * R_EARTH
    return x, y


def _ring_area_m2(coords):
    if len(coords) < 3:
        return 0.0
    lat0 = sum(lat for _, lat in coords) / len(coords)
    pts = [_lonlat_to_xy_m(lat0, lon, lat) for lon, lat in coords]
    area2 = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        area2 += x1 * y2 - x2 * y1
    return abs(area2) * 0.5


def _parse_coords_text(text):
    out = []
    if not text:
        return out
    for tok in text.replace('\n', ' ').replace('	', ' ').split():
        parts = tok.split(',')
        if len(parts) >= 2:
            try:
                lon = float(parts[0])
                lat = float(parts[1])
                out.append((lon, lat))
            except ValueError:
                pass
    if len(out) > 1 and out[0] == out[-1]:
        out = out[:-1]
    return out


def _sum_kml_polygon_areas_and_collect_rings(root):
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    total_m2 = 0.0
    polys = []

    def _findall(el, path):
        found = el.findall(path, ns)
        if not found:
            found = el.findall(path.replace("kml:", ""))
        return found

    all_polys = root.findall(".//kml:Polygon", ns) or root.findall(".//Polygon")
    for polygon in all_polys:
        outer_nodes = _findall(polygon, ".//kml:outerBoundaryIs/kml:LinearRing/kml:coordinates")
        inner_nodes = _findall(polygon, ".//kml:innerBoundaryIs/kml:LinearRing/kml:coordinates")

        outers, inners = [], []
        for node in outer_nodes:
            coords = _parse_coords_text(node.text)
            if coords:
                outers.append(coords)
                total_m2 += _ring_area_m2(coords)
        for node in inner_nodes:
            coords = _parse_coords_text(node.text)
            if coords:
                inners.append(coords)
                total_m2 -= _ring_area_m2(coords)

        if outers or inners:
            polys.append({"outer": outers, "inner": inners})

    return max(0.0, total_m2), polys


def _load_kml_from_kmz(path):
    with zipfile.ZipFile(path, "r") as zf:
        kml_name = None
        for name in zf.namelist():
            if name.lower().endswith(".kml"):
                if name.lower().endswith("doc.kml"):
                    kml_name = name
                    break
                if kml_name is None:
                    kml_name = name
        if not kml_name:
            raise ValueError("KMZ não contém arquivo .kml")
        with zf.open(kml_name) as f:
            data = f.read()
    return data


def lonlat_to_pixel(lon, lat, z):
    lat = max(min(lat, 85.05112878), -85.05112878)
    siny = math.sin(math.radians(lat))
    n = 2.0 ** z
    x = (lon + 180.0) / 360.0 * n * TILE_SIZE
    y = (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)) * n * TILE_SIZE
    return x, y


def pixel_to_lonlat(px, py, z):
    n = 2.0 ** z
    lon = px / (n * TILE_SIZE) * 360.0 - 180.0
    y = 0.5 - (py / (n * TILE_SIZE))
    lat = 90.0 - 360.0 * math.atan(math.exp(-y * 2 * math.pi)) / math.pi
    return lon, lat


def bbox_lonlat(polys):
    lons, lats = [], []
    for poly in polys:
        for ring in poly["outer"]:
            for lon, lat in ring:
                lons.append(lon)
                lats.append(lat)
    if not lons:
        return -46, -23, -46, -23
    return min(lons), min(lats), max(lons), max(lats)


def best_zoom_to_fit(polys, canvas_w, canvas_h, margin_px=20):
    minlon, minlat, maxlon, maxlat = bbox_lonlat(polys)
    for z in range(MAX_ZOOM, MIN_ZOOM - 1, -1):
        px1, py1 = lonlat_to_pixel(minlon, maxlat, z)
        px2, py2 = lonlat_to_pixel(maxlon, minlat, z)
        width = abs(px2 - px1)
        height = abs(py2 - py1)
        if width <= (canvas_w - 2 * margin_px) and height <= (canvas_h - 2 * margin_px):
            return z
    return MIN_ZOOM


def center_pixel_from_polys(polys, z):
    minlon, minlat, maxlon, maxlat = bbox_lonlat(polys)
    clon = (minlon + maxlon) / 2.0
    clat = (minlat + maxlat) / 2.0
    return lonlat_to_pixel(clon, clat, z)


def tile_cache_dir():
    base = os.path.dirname(os.path.abspath(__file__))
    cache = os.path.abspath(os.path.join(base, "..", "assets", "tile_cache"))
    os.makedirs(cache, exist_ok=True)
    return cache


def load_tile(z, x, y):
    if not PIL_OK:
        return None
    cache = tile_cache_dir()
    path = os.path.join(cache, f"{z}_{x}_{y}.png")
    if os.path.exists(path):
        try:
            return Image.open(path).convert("RGB")
        except Exception:
            pass
    url = OSM_URL.format(z=z, x=x, y=y)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
        with open(path, "wb") as f:
            f.write(data)
        return Image.open(BytesIO(data)).convert("RGB")
    except Exception:
        img = Image.new("RGB", (TILE_SIZE, TILE_SIZE), "#dddddd")
        draw = ImageDraw.Draw(img)
        draw.line((0, 0, TILE_SIZE, TILE_SIZE), fill="#bbbbbb")
        draw.line((0, TILE_SIZE, TILE_SIZE, 0), fill="#bbbbbb")
        return img


def draw_tiles(center_px, center_py, z, canvas_w, canvas_h):
    if not PIL_OK:
        return None
    base = Image.new("RGB", (canvas_w, canvas_h), "#ffffff")
    top_left_world_x = center_px - canvas_w / 2
    top_left_world_y = center_py - canvas_h / 2
    x0 = int(math.floor(top_left_world_x / TILE_SIZE))
    y0 = int(math.floor(top_left_world_y / TILE_SIZE))
    offset_x = int(round(top_left_world_x - x0 * TILE_SIZE))
    offset_y = int(round(top_left_world_y - y0 * TILE_SIZE))
    nx = int(math.ceil((offset_x + canvas_w) / TILE_SIZE))
    ny = int(math.ceil((offset_y + canvas_h) / TILE_SIZE))
    max_index = (1 << z)
    for ix in range(nx):
        for iy in range(ny):
            tx = (x0 + ix) % max_index
            ty = y0 + iy
            if ty < 0 or ty >= max_index:
                continue
            tile = load_tile(z, tx, ty)
            paste_x = ix * TILE_SIZE - offset_x
            paste_y = iy * TILE_SIZE - offset_y
            base.paste(tile, (paste_x, paste_y))
    return base


def rings_to_pixel(polys, z, center_px, center_py, canvas_w, canvas_h):
    all_rings = []
    for poly in polys:
        out_outer, out_inner = [], []
        for ring in poly["outer"]:
            pts = []
            for lon, lat in ring:
                px, py = lonlat_to_pixel(lon, lat, z)
                X = px - center_px + canvas_w / 2
                Y = py - center_py + canvas_h / 2
                pts.append((X, Y))
            out_outer.append(pts)
        for ring in poly["inner"]:
            pts = []
            for lon, lat in ring:
                px, py = lonlat_to_pixel(lon, lat, z)
                X = px - center_px + canvas_w / 2
                Y = py - center_py + canvas_h / 2
                pts.append((X, Y))
            out_inner.append(pts)
        all_rings.append({"outer": out_outer, "inner": out_inner})
    return all_rings


def add_tab(tabhost, ctx):
    titulo_font = ctk.CTkFont(size=13, weight="bold")
    logo_image = getattr(ctx, 'logo_image', None)
    aba = tabhost.add_tab("Mapa do Talhão")
    frame = ctk.CTkFrame(aba, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=16, pady=16)

    sec_arq = make_section(frame, "ARQUIVO", titulo_font)
    linha_arq = ctk.CTkFrame(sec_arq, fg_color="transparent")
    linha_arq.pack(fill="x", pady=4)
    caminho_var = ctk.StringVar()
    entrada = ctk.CTkEntry(linha_arq, textvariable=caminho_var, width=360)
    entrada.pack(side="left", padx=(0, 10), fill="x", expand=True)

    def escolher():
        path = filedialog.askopenfilename(
            title="Selecione KMZ ou KML",
            filetypes=[("KMZ", "*.kmz"), ("KML", "*.kml"), ("Todos os arquivos", "*.*")],
        )
        if path:
            caminho_var.set(path)

    ctk.CTkButton(linha_arq, text="Escolher arquivo", command=escolher).pack(side="left")

    sec_res = make_section(frame, "RESULTADO", titulo_font)
    resultado_frame = ctk.CTkFrame(sec_res, fg_color="transparent")
    resultado_frame.pack(fill="x")
    ctk.CTkLabel(resultado_frame, text="Área do Talhão (Hectares):").pack(side="left")
    res_ha_val = ctk.CTkLabel(resultado_frame, text="", anchor="w")
    res_ha_val.pack(side="left", padx=10)

    sec_prev = make_section(frame, "MAPA (arraste p/ mover, roda p/ zoom, duplo clique p/ ajustar)", titulo_font)
    canvas = tk.Canvas(sec_prev, width=CANVAS_W, height=CANVAS_H, highlightthickness=0, bg="white")
    canvas.pack(fill="both", expand=True)
    ctk.CTkLabel(sec_prev, text="© OpenStreetMap contributors", anchor="e", font=ctk.CTkFont(size=10)).pack(fill="x", pady=(6, 0))

    state = {
        "polys_ll": [],
        "area_ha": None,
        "z": 12,
        "center_px": 0.0,
        "center_py": 0.0,
        "drag": None,
        "photo": None,
    }

    def _fit_view():
        if not state["polys_ll"]:
            return
        z = best_zoom_to_fit(state["polys_ll"], canvas.winfo_width() or CANVAS_W, canvas.winfo_height() or CANVAS_H, margin_px=30)
        cx, cy = center_pixel_from_polys(state["polys_ll"], z)
        state["z"] = z
        state["center_px"] = cx
        state["center_py"] = cy

    def _redraw():
        if not PIL_OK:
            canvas.delete("all")
            canvas.create_text(CANVAS_W // 2, CANVAS_H // 2, text="Instale Pillow para visualizar o mapa.", fill="gray")
            return
        w = canvas.winfo_width() or CANVAS_W
        h = canvas.winfo_height() or CANVAS_H
        tiles = draw_tiles(state["center_px"], state["center_py"], state["z"], w, h)
        draw = ImageDraw.Draw(tiles, "RGBA")
        rings_px = rings_to_pixel(state["polys_ll"], state["z"], state["center_px"], state["center_py"], w, h)
        for poly in rings_px:
            for ring in poly["outer"]:
                if len(ring) >= 3:
                    draw.polygon(ring, fill=(106, 168, 79, 120), outline=(34, 95, 16, 255), width=2)
            for ring in poly["inner"]:
                if len(ring) >= 3:
                    draw.polygon(ring, fill=(255, 255, 255, 255), outline=(34, 95, 16, 255), width=1)
        photo = ImageTk.PhotoImage(tiles)
        state["photo"] = photo
        canvas.delete("all")
        canvas.create_image(0, 0, image=photo, anchor="nw")
        for poly in rings_px:
            for ring in poly["outer"]:
                if len(ring) >= 3:
                    flat = [coord for p in ring for coord in p]
                    canvas.create_polygon(*flat, outline="#225f10", fill="", width=2)

    def _on_button1_press(event):
        state["drag"] = (event.x, event.y)

    def _on_button1_motion(event):
        if state["drag"] is None:
            return
        ox, oy = state["drag"]
        dx, dy = event.x - ox, event.y - oy
        state["drag"] = (event.x, event.y)
        state["center_px"] -= dx
        state["center_py"] -= dy
        _redraw()

    def _on_button1_release(_event):
        state["drag"] = None

    def _zoom_at(canvas_x, canvas_y, factor):
        z_old = state["z"]
        z_new = min(MAX_ZOOM, max(MIN_ZOOM, z_old + (1 if factor > 1 else -1)))
        if z_new == z_old:
            return
        px_world = state["center_px"] - (canvas.winfo_width() or CANVAS_W) / 2 + canvas_x
        py_world = state["center_py"] - (canvas.winfo_height() or CANVAS_H) / 2 + canvas_y
        lon, lat = pixel_to_lonlat(px_world, py_world, z_old)
        new_px, new_py = lonlat_to_pixel(lon, lat, z_new)
        state["center_px"] += (new_px - px_world)
        state["center_py"] += (new_py - py_world)
        state["z"] = z_new
        _redraw()

    def _on_mousewheel(event):
        if hasattr(event, "delta") and event.delta != 0:
            factor = 1.12 if event.delta > 0 else 1 / 1.12
            _zoom_at(event.x, event.y, factor)
        else:
            if getattr(event, "num", None) == 4:
                _zoom_at(event.x, event.y, 1.12)
            elif getattr(event, "num", None) == 5:
                _zoom_at(event.x, event.y, 1 / 1.12)

    def _on_double_click(_event):
        _fit_view()
        _redraw()

    canvas.bind("<ButtonPress-1>", _on_button1_press)
    canvas.bind("<B1-Motion>", _on_button1_motion)
    canvas.bind("<ButtonRelease-1>", _on_button1_release)
    canvas.bind("<MouseWheel>", _on_mousewheel)
    canvas.bind("<Button-4>", _on_mousewheel)
    canvas.bind("<Button-5>", _on_mousewheel)
    canvas.bind("<Double-Button-1>", _on_double_click)

    btns_wrap = ctk.CTkFrame(frame, fg_color="transparent")
    btns_wrap.pack(fill="x", pady=(4, 0))

    def calcular_area():
        path = caminho_var.get().strip()
        if not path:
            messagebox.showwarning("Arquivo", "Selecione um arquivo KMZ/KML.")
            return
        try:
            if path.lower().endswith(".kmz"):
                data = _load_kml_from_kmz(path)
                root = ET.fromstring(data)
            else:
                with open(path, "rb") as f:
                    data = f.read()
                root = ET.fromstring(data)
            m2, polys = _sum_kml_polygon_areas_and_collect_rings(root)
            ha = m2 / 10_000.0
            res_ha_val.configure(text=f"{ha:.4f}")
            state["polys_ll"] = polys
            _fit_view()
            _redraw()
            if messagebox.askyesno("Confirmar Área", f"Deseja aplicar {ha:.4f} ha no campo 'Área (Ha)' da aba principal?"):
                campo = ctx.campos.get("Área (Ha)")
                if hasattr(campo, "delete") and hasattr(campo, "insert"):
                    campo.delete(0, "end")
                    campo.insert(0, f"{ha:.4f}")
                else:
                    messagebox.showwarning("Aplicar", "Campo 'Área (Ha)' não encontrado.")
        except Exception as e:
            messagebox.showerror("Erro ao calcular", str(e))

    ctk.CTkButton(btns_wrap, text="Calcular Área", command=calcular_area).pack(pady=4)

    if logo_image is not None:
        place_logo_footer(frame, logo_image, padx=12, pady=12)
