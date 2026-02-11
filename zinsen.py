import streamlit as st
import datetime
import pandas as pd
import io
from fpdf import FPDF

# --- 1. Logik-Funktionen ---
def ist_schaltjahr(jahr):
    return (jahr % 4 == 0 and jahr % 100 != 0) or (jahr % 400 == 0)

def get_basiszinssaetze():
    return [
        (datetime.date(2002, 1, 1), 2.57), (datetime.date(2013, 1, 1), -0.13),
        (datetime.date(2021, 1, 1), -0.88), (datetime.date(2023, 1, 1), 1.62),
        (datetime.date(2024, 1, 1), 3.62), (datetime.date(2024, 7, 1), 3.37),
        (datetime.date(2025, 1, 1), 3.12), (datetime.date(2025, 7, 1), 2.27),
        (datetime.date(2026, 1, 1), 1.27),
    ]

# --- 2. PDF-Klasse ---
class ZinsPDF(FPDF):
    def __init__(self, az, schuldner):
        super().__init__()
        self.az, self.schuldner = az, schuldner
    def header(self):
        try:
            self.image("logo.png", x=10, y=8, w=30)
        except: pass
        self.set_x(50)
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Zinsberechnung & Tilgungsplan", ln=True)
        self.set_x(50)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 5, f"AZ: {self.az} | Schuldner: {self.schuldner}", ln=True)
        self.ln(15)

def create_pdf(df, betrag, zinsen, az, schuldner, zahlung, rest):
    pdf = ZinsPDF(az, schuldner)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"Forderungsaufstellung", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Hauptforderung: {betrag:,.2f} EUR".replace(".", ","), ln=True)
    pdf.cell(0, 6, f"Zinsen: {zinsen:,.2f} EUR".replace(".", ","), ln=True)
    pdf.ln(5)
    # Tabelle
    pdf.set_fill_color(240, 240, 240)
    for h in ["Zeitraum", "Tage", "Zins", "Betrag"]:
        pdf.cell(45 if h=="Zeitraum" else 30, 8, h, 1, 0, "C", True)
    pdf.ln()
    for _, r in df.iterrows():
        pdf.cell(45, 7, str(r['Zeitraum']), 1)
        pdf.cell(30, 7, str(r['Tage']), 1, 0, "C")
        pdf.cell(30, 7, str(r['Zins']), 1, 0, "C")
        pdf.cell(30, 7, f"{r['Betrag (€)']:,.2f}".replace(".", ","), 1, 1, "R")
    if zahlung > 0:
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f"Zahlung: {zahlung:,.2f} EUR | Rest: {rest:,.2f} EUR".replace(".", ","), ln=True)
    return bytes(pdf.output())

# --- 3. Streamlit Interface ---
st.set_page_config(page_title="Zinsrechner Pro", layout="centered")

# LOGO IM KOPF DER WEBSEITE
c_l1, c_l2, c_l3 = st.columns([1, 1, 1])
with c_l2:
    try: st.image("logo.png", width=150)
    except: pass

st.title("⚖️ Zins- & Tilgungsrechner")

# Sidebar
with st.sidebar:
    try: st.image("logo.png", width=120)
    except: pass
    st.header("Stammdaten")
    az = st.text_input("Aktenzeichen", "AZ 2026/01")
    schuldner = st.text_input("Schuldner", "Max Mustermann")
    st.divider()
    betrag = st.number_input("Hauptforderung (€)", min_value=0.0, value=1000.0)
    start_datum = st.date_input("Zinsbeginn", value=datetime.date(2023, 1, 1), min_value=datetime.date(2002, 1, 1))

# Berechnung
historie = get_basiszinssaetze()
zins_termine = [start_datum]
for d, _ in historie:
    if start_datum < d <= datetime.date.today(): zins_termine.append(d)
zins_termine.append(datetime.date.today() + datetime.timedelta(days=1))

total_zinsen, ergebnisse = 0.0, []
for i in range(len(zins_termine) - 1):
    p_start, p_ende = zins_termine[i], zins_termine[i+1] - datetime.timedelta(days=1)
    if p_start > p_ende: continue
    basis = [s for d, s in historie if d <= p_start][-1]
    zinssatz = basis + 5.0
    phase_summe, curr = 0.0, p_start
    while curr <= p_ende:
        t_jahr = 366 if ist_schaltjahr(curr.year) else 365
        phase_summe += (betrag * (zinssatz / 100)) / t_jahr
        curr += datetime.timedelta(days=1)
    total_zinsen += phase_summe
    ergebnisse.append({"Zeitraum": f"{p_start.strftime('%d.%m.%Y')} - {p_ende.strftime('%d.%m.%Y')}", "Tage": (p_ende-p_start).days+1, "Zins": f"{zinssatz:.2f}%", "Betrag (€)": round(phase_summe, 2)})

df_res = pd.DataFrame(ergebnisse)
st.table(df_res)

# Metriken
m1, m2, m3 = st.columns(3)
m1.metric("Zinsen", f"{total_zinsen:.2f} €")
m2.metric("Forderung", f"{betrag:.2f} €")
m3.metric("Gesamt", f"{total_zinsen + betrag:.2f} €")

# Tilgung
st.divider()
st.subheader("💳 Zahlungsverrechnung")
zahlung = st.number_input("Zahlungseingang (€)", min_value=0.0, value=0.0)
rest = max(0.0, (total_zinsen + betrag) - zahlung)

c_t1, c_t2 = st.columns(2)
c_t1.write(f"Tilgung Zinsen: {min(zahlung, total_zinsen):.2f} €")
c_t2.markdown(f"**Offener Restbetrag: {rest:.2f} €**")

# Downloads
st.write("---")
col_d1, col_d2 = st.columns(2)
col_d1.download_button("📥 CSV Export", df_res.to_csv(sep=';', decimal=',', index=False), "zinsen.csv")
pdf_bytes = create_pdf(df_res, betrag, total_zinsen, az, schuldner, zahlung, rest)
col_d2.download_button("📄 PDF Export", pdf_bytes, "berechnung.pdf")
