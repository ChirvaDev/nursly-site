"""Generate printable nurse shift calendars -> assets/downloads/*.pdf

    pip install reportlab && python3 _tools/make_pdfs.py

Letter files start weeks on Sunday (US/Canada); A4 files start on Monday (UK/Australia).
Each page has a small QR code to the App Store (ct=pdf-calendar / pdf-template).
"""
import calendar, pathlib, re
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

YEAR = 2027
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "downloads"

INK = HexColor("#14151a")
MUTED = HexColor("#6b6f84")
LINE = HexColor("#d9dbe8")
ACCENT = HexColor("#5468ee")
SOFT = HexColor("#eef0ff")
WEEKEND = HexColor("#f7f8fc")

config = (ROOT / "_config.yml").read_text()
APP_ID = re.search(r'^app_store_id:\s*"(\d+)"', config, re.M).group(1)
PT = re.search(r'^app_store_pt:\s*"(\d*)"', config, re.M).group(1)


def store_url(ct):
    url = f"https://apps.apple.com/app/apple-store/id{APP_ID}"
    return url + (f"?pt={PT}&ct={ct}&mt=8" if PT else "")


def qr(c, url, x, y, size):
    w = QrCodeWidget(url, barLevel="M")
    x0, y0, x1, y1 = w.getBounds()
    d = Drawing(size, size, transform=[size / (x1 - x0), 0, 0, size / (y1 - y0), 0, 0])
    d.add(w)
    renderPDF.draw(d, c, x, y)


def footer(c, W, M, ct):
    qs = 34
    qr(c, store_url(ct), W - M - qs, 10, qs)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawRightString(W - M - qs - 6, 26, "Track your shifts and pay automatically —")
    c.setFont("Helvetica-Bold", 8)
    c.drawRightString(W - M - qs - 6, 16, "Nursly for iPhone · nursly.app")
    c.setFont("Helvetica", 8)
    c.drawString(M, 21, "Free printable from nursly.app")


def legend(c, x, y):
    c.setFont("Helvetica", 8.5)
    items = [("D", "Day"), ("N", "Night"), ("E", "Evening"), ("O", "Off"), ("OC", "On-call"), ("PTO", "Paid time off")]
    for code, name in items:
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(x, y, code)
        x += c.stringWidth(code, "Helvetica-Bold", 8.5) + 3
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8.5)
        c.drawString(x, y, name)
        x += c.stringWidth(name, "Helvetica", 8.5) + 12


def month_page(c, size, first_weekday, year=None, month=None, ct="pdf-calendar"):
    W, H = size
    M = 30
    # Header
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 24)
    if year:
        c.drawString(M, H - M - 18, f"{calendar.month_name[month]} {year}")
    else:
        c.drawString(M, H - M - 18, "Month: ____________   Year: ______")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9.5)
    c.drawString(M, H - M - 34, "Nurse shift schedule  ·  Name: __________________________   Unit: ______________")
    legend(c, W - M - 330, H - M - 12)

    # Totals box (right column)
    side = 150
    gx0, gx1 = M, W - M - side - 14
    top, bottom = H - M - 50, 52
    bx = W - M - side
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    c.setFillColor(SOFT)
    c.roundRect(bx, bottom, side, top - bottom, 8, stroke=0, fill=1)
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(bx + 12, top - 20, "THIS MONTH")
    rows = ["Shifts worked", "Total hours", "Night shifts", "Weekend shifts", "Overtime hours", "Holiday hours", "Estimated pay"]
    yy = top - 46
    for r in rows:
        c.setFillColor(INK)
        c.setFont("Helvetica", 9)
        c.drawString(bx + 12, yy, r)
        c.setStrokeColor(HexColor("#b9bfe8"))
        c.line(bx + 12, yy - 14, bx + side - 12, yy - 14)
        yy -= 36
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(bx + 12, yy - 4, "NOTES")
    c.setStrokeColor(HexColor("#b9bfe8"))
    ny = yy - 26
    while ny > bottom + 12:
        c.line(bx + 12, ny, bx + side - 12, ny)
        ny -= 20

    # Calendar grid
    cal = calendar.Calendar(firstweekday=first_weekday)
    weeks = cal.monthdayscalendar(year, month) if year else [[0] * 7 for _ in range(6)]
    names = [calendar.day_abbr[(first_weekday + i) % 7] for i in range(7)]
    cw = (gx1 - gx0) / 7
    head = 18
    c.setFillColor(INK)
    c.roundRect(gx0, top - head, gx1 - gx0, head, 5, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 9)
    for i, n in enumerate(names):
        c.drawCentredString(gx0 + cw * i + cw / 2, top - 12.5, n.upper())
    rh = (top - head - 4 - bottom) / len(weeks)
    y0 = top - head - 4
    for r, week in enumerate(weeks):
        for i, day in enumerate(week):
            x = gx0 + cw * i
            y = y0 - rh * (r + 1)
            weekday = (first_weekday + i) % 7  # 5 = Sat, 6 = Sun
            c.setFillColor(WEEKEND if weekday in (5, 6) else white)
            c.setStrokeColor(LINE)
            c.rect(x, y, cw, rh, stroke=1, fill=1)
            if year and day == 0:
                continue
            c.setFillColor(INK)
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x + 6, y + rh - 15, str(day) if day else "")
            # write-in lines: shift and hours
            c.setFont("Helvetica", 6.5)
            c.setFillColor(MUTED)
            c.drawString(x + 6, y + 18, "Shift")
            c.drawString(x + 6, y + 6, "Hours")
            c.setStrokeColor(HexColor("#e6e8f2"))
            c.line(x + 26, y + 17, x + cw - 6, y + 17)
            c.line(x + 28, y + 5, x + cw - 6, y + 5)
    footer(c, W, M, ct)


def year_page(c, size, first_weekday, year):
    W, H = size
    M = 30
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(M, H - M - 6, "NURSE SHIFT CALENDAR")
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 30)
    c.drawString(M, H - M - 38, f"{year} at a glance")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9.5)
    c.drawString(M, H - M - 54, "Mark each day with your shift code, then use the monthly pages for hours and pay.")
    legend(c, W - M - 330, H - M - 6)
    cal = calendar.Calendar(firstweekday=first_weekday)
    cols, rows = 4, 3
    top, bottom = H - M - 72, 52
    gw = (W - 2 * M) / cols
    gh = (top - bottom) / rows
    for m in range(12):
        cx = M + gw * (m % cols) + 6
        cy = top - gh * (m // cols)
        w = gw - 12
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(cx, cy - 14, calendar.month_name[m + 1])
        cw = w / 7
        c.setFont("Helvetica-Bold", 6.5)
        c.setFillColor(MUTED)
        for i in range(7):
            c.drawCentredString(cx + cw * i + cw / 2, cy - 27, calendar.day_abbr[(first_weekday + i) % 7][:2].upper())
        weeks = cal.monthdayscalendar(year, m + 1)
        ch = (gh - 40) / 6
        for r, week in enumerate(weeks):
            for i, day in enumerate(week):
                if not day:
                    continue
                x = cx + cw * i
                y = cy - 32 - ch * (r + 1)
                weekday = (first_weekday + i) % 7
                c.setFillColor(WEEKEND if weekday in (5, 6) else white)
                c.setStrokeColor(LINE)
                c.setLineWidth(0.5)
                c.rect(x, y, cw, ch, stroke=1, fill=1)
                c.setFillColor(INK)
                c.setFont("Helvetica", 6)
                c.drawString(x + 2, y + ch - 7, str(day))
    footer(c, W, M, "pdf-calendar")


def build(name, size, first_weekday, dated):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    c = canvas.Canvas(str(path), pagesize=size)
    if dated:
        c.setTitle(f"{YEAR} Nurse Shift Calendar — Nursly")
        c.setSubject("Printable nurse shift calendar with monthly hours and pay totals")
        year_page(c, size, first_weekday, YEAR)
        c.showPage()
        for m in range(1, 13):
            month_page(c, size, first_weekday, YEAR, m)
            c.showPage()
    else:
        c.setTitle("Nurse Shift Schedule Template — Nursly")
        c.setSubject("Blank printable monthly nurse shift schedule")
        month_page(c, size, first_weekday, ct="pdf-template")
        c.showPage()
    c.setAuthor("Nursly · nursly.app")
    c.save()
    print(path.relative_to(ROOT), f"{path.stat().st_size // 1024} KB")


build(f"nurse-shift-calendar-{YEAR}-letter.pdf", landscape(letter), calendar.SUNDAY, True)
build(f"nurse-shift-calendar-{YEAR}-a4.pdf", landscape(A4), calendar.MONDAY, True)
build("nurse-shift-schedule-template-letter.pdf", landscape(letter), calendar.SUNDAY, False)
build("nurse-shift-schedule-template-a4.pdf", landscape(A4), calendar.MONDAY, False)
