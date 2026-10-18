"""Generate App Store QR codes for desktop visitors -> assets/qr/<ct>.svg

Each QR points to the App Store campaign link with its own ct, so App Store Connect
shows scans per placement. Re-run after changing app_store_id or app_store_pt:
    pip install segno && python3 _tools/make_qr.py
"""
import pathlib, re, segno

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLACES = ["qr-hero", "qr-cta", "qr-calculator", "qr-schedule", "qr-template", "qr-pricing", "qr-about", "qr-guide"]

config = (ROOT / "_config.yml").read_text()
app_id = re.search(r'^app_store_id:\s*"(\d+)"', config, re.M).group(1)
pt = re.search(r'^app_store_pt:\s*"(\d*)"', config, re.M).group(1)

out = ROOT / "assets" / "qr"
out.mkdir(parents=True, exist_ok=True)
for ct in PLACES:
    url = f"https://apps.apple.com/app/apple-store/id{app_id}"
    if pt:
        url += f"?pt={pt}&ct={ct}&mt=8"
    qr = segno.make(url, error="m")
    path = out / f"{ct}.svg"
    qr.save(path, border=2, dark="#14151a", xmldecl=False, svgns=True, title="Scan to download Nursly")
    # viewBox lets the SVG scale inside <img>; crispEdges keeps modules sharp.
    size = qr.symbol_size(border=2)[0]
    svg = path.read_text().replace("<svg ", f'<svg viewBox="0 0 {size} {size}" shape-rendering="crispEdges" ', 1)
    path.write_text(svg)
    print(ct, url)
