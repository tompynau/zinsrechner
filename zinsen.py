import streamlit as st
import datetime
import pandas as pd
import plotly.express as px
import io
from fpdf import FPDF

# --- 1. Logik-Funktionen ---
def ist_schaltjahr(jahr):
    return (jahr % 4 == 0 and jahr % 100 != 0) or (jahr % 400 == 0)

def get_basiszinssaetze():
    return [
        (datetime.date(2002, 1, 1), 2.57), (datetime.date(2002, 7, 1), 2.47),
        (datetime.date(2003, 1, 1), 1.97), (datetime.date(2003, 7, 1), 1.22),
        (datetime.date(2013, 1, 1), -0.13), (datetime.date(2013, 7, 1), -0.38),
        (datetime.date(2021, 1, 1), -0.88), (datetime.date(2023, 1, 1), 1.62),
        (datetime.date(2023, 7, 1), 3.12), (datetime.date(2024, 1, 1), 3.62),
        (datetime.date(2024, 7, 1), 3.37), (datetime.date(2025, 1, 1), 3.12),
        (datetime.date(2025, 7, 1), 2.27), (datetime.date(2026, 1, 1), 1.27),
    ]

# --- 2. PDF-Klasse mit Kopfzeile ---
class ZinsPDF(FPDF):
    def __init__(self, az, schuldner):
        super().__init__()
        self.az = az
        self.schuldner = schuldner

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Zinsberechnungsprotokoll", ln=True, align="L")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 5, f"Aktenzeichen: {self.az}", ln=True)
        self.cell(0, 5, f"Schuldner: {self.schuldner}", ln=True)
        self.cell(0, 5, f"Datum: {datetime.date.today().strftime('%d.%m.%Y')}", ln=True)
        self.ln(10)

def create_pdf(df, betrag, gesamt_zinsen, start_dat, az, schuldner):
    pdf = ZinsPDF(az, schuldner)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Berechnungsdaten", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Hauptforderung: {betrag:,.2f} EUR".replace(".", ","), ln=True)
    pdf.cell(0, 8, f"Zinsbeginn: {start_dat.strftime('%d.%m.%Y')}", ln=True)
    pdf.ln(5)

    # Tabelle
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(50, 10, "Zeitraum", 1, 0, "C", True)
    pdf.cell(20, 10, "Tage", 1, 0, "C", True)
    pdf.cell(40, 10, "Zinssatz", 1, 0, "C", True)
    pdf.cell(50, 10, "Zinsertrag (EUR)", 1, 1, "C", True)

    pdf.set_font("Helvetica", "", 10)
    for _, row in df.iterrows():
        pdf.cell(50, 8, str(row['Zeitraum']), 1)
        pdf.cell(20, 8, str(row['Tage']), 1, 0, "C")
        pdf.cell(40, 8, str(row['Zinssatz']), 1, 0, "C")
        pdf.cell(50, 8, f"{row['Zinsertrag (€)']:,.2f}".replace(".", ","), 1, 1, "R")

    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"Gesamtforderung: {(betrag + gesamt_zinsen):,.2f} EUR".replace(".", ","), ln=True, align="R")
    return bytes(pdf.output())

# --- 3. Streamlit Interface ---
st.set_page_config(page_title="Zinsrechner Pro", layout="wide")

# Sidebar mit Logo-Skalierung
# Option 1: Über die Breite (width=150)
# Option 2: Über Spalten für Zentrierung
with st.sidebar:
    try:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("logo.png", width=120) # Hier kannst du die Breite (Pixel) anpassen
    except:
        pass

    st.header("Stammdaten")
    az = st.text_input("Aktenzeichen", "AZ 2026/01")
    schuldner = st.text_input("Schuldner", "Vorname Nachname")
    
    st.divider()
    st.header("Berechnung")
    betrag = st.number_input("Betrag (€)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
    start_datum = st.sidebar.date_input("Zinsbeginn", value=datetime.date(2023, 1, 1), format="DD.MM.YYYY", min_value=datetime.date(2002, 1, 1))

# Hauptbereich
st.title("⚖️ Zinsrechner")

historie = get_basiszinssaetze()
zins_termine = [start_datum]
for d, _ in historie:
    if start_datum < d <= datetime.date.today():
        zins_termine.append(d)
zins_termine.append(datetime.date.today() + datetime.timedelta(days=1))

total_zinsen = 0.0
total_tage = 0
ergebnisse = []

for i in range(len(zins_termine) - 1):
    p_start = zins_termine[i]
    p_ende = zins_termine[i+1] - datetime.timedelta(days=1)
    if p_start > p_ende: continue
    anz_tage = (p_ende - p_start).days + 1
    basis = [s for d, s in historie if d <= p_start][-1]
    zinssatz_prozent = basis + 5.0
    
    phase_summe = 0.0
    curr = p_start
    while curr <= p_ende:
        t_jahr = 366 if ist_schaltjahr(curr.year) else 365
        phase_summe += (betrag * (zinssatz_prozent / 100)) / t_jahr
        curr += datetime.timedelta(days=1)

    total_zinsen += phase_summe
    total_tage += anz_tage
    ergebnisse.append({
        "Zeitraum": f"{p_start.strftime('%d.%m.%Y')} - {p_ende.strftime('%d.%m.%Y')}",
        "Tage": anz_tage,
        "Zinssatz": f"{zinssatz_prozent:.2f} %",
        "Zinsertrag (€)": round(phase_summe, 4)
    })

df_tabelle = pd.DataFrame(ergebnisse)
st.table(df_tabelle)

st.divider()
c1, c2, c3 = st.columns(3)
c1.metric("Tage", f"{total_tage}")
c2.metric("Zinsen", f"{total_zinsen:.2f} €")
c3.metric("Gesamt", f"{total_zinsen + betrag:.2f} €")

# Download Bereich
st.subheader("Export")
csv_data = df_tabelle.to_csv(index=False, sep=';', decimal=',', encoding='utf-8-sig')
st.download_button("📥 CSV", csv_data, "zinsen.csv")

pdf_bytes = create_pdf(df_tabelle, betrag, total_zinsen, start_datum, az, schuldner)
st.download_button("📄 PDF", pdf_bytes, "zinsberechnung.pdf")
