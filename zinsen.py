import streamlit as st
import datetime
import pandas as pd
import io
from fpdf import FPDF

# --- 1. Logik-Funktionen ---
def ist_schaltjahr(jahr):
    return (jahr % 4 == 0 and jahr % 100 != 0) or (jahr % 400 == 0)

def get_basiszinssaetze():
    # Gekürzte Liste zur Übersichtlichkeit, erweitere sie nach Bedarf
    return [
        (datetime.date(2002, 1, 1), 2.57), (datetime.date(2021, 1, 1), -0.88),
        (datetime.date(2023, 1, 1), 1.62), (datetime.date(2023, 7, 1), 3.12),
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
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Zinsberechnung & Tilgung", ln=True)
        self.set_font("Helvetica", "", 10)
        self.cell(0, 5, f"AZ: {self.az} | Schuldner: {self.schuldner}", ln=True)
        self.ln(10)

def create_pdf(df, betrag, zinsen, start_dat, az, schuldner):
    pdf = ZinsPDF(az, schuldner)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Hauptforderung: {betrag:,.2f} EUR".replace(".", ","), ln=True)
    pdf.cell(0, 8, f"Zinsen: {zinsen:,.2f} EUR".replace(".", ","), ln=True)
    pdf.cell(0, 8, f"Gesamt: {(betrag+zinsen):,.2f} EUR".replace(".", ","), ln=True)
    return bytes(pdf.output())

# --- 3. Streamlit Interface ---
st.set_page_config(page_title="Zins- & Tilgungsrechner", layout="centered")

# CSS für Lesbarkeit
st.markdown("<style>[data-testid='stMetric'] { background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important; border-radius: 10px; padding: 10px; }</style>", unsafe_allow_html=True)

st.title("⚖️ Zins- & Tilgungsrechner")

# Eingabebereich oben (zentriert)
with st.expander("📝 Stammdaten & Forderung", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        az = st.text_input("Aktenzeichen", "AZ 2026/01")
        betrag = st.number_input("Hauptforderung (€)", min_value=0.0, value=1000.0, step=100.0)
    with c2:
        schuldner = st.text_input("Schuldner", "Max Mustermann")
        start_datum = st.date_input("Zinsbeginn", value=datetime.date(2023, 1, 1), min_value=datetime.date(2002, 1, 1))

# --- BERECHNUNG ---
historie = get_basiszinssaetze()
zins_termine = [start_datum]
for d, _ in historie:
    if start_datum < d <= datetime.date.today():
        zins_termine.append(d)
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

# Anzeige Tabelle
st.table(pd.DataFrame(ergebnisse))

# Ergebnisse Metriken
m1, m2, m3 = st.columns(3)
m1.metric("Zinsen", f"{total_zinsen:.2f} €")
m2.metric("Hauptforderung", f"{betrag:.2f} €")
m3.metric("Gesamt", f"{total_zinsen + betrag:.2f} €")

# Download Buttons
c_csv, c_pdf = st.columns(2)
c_csv.download_button("📥 CSV", pd.DataFrame(ergebnisse).to_csv(sep=';', decimal=',', index=False), "zinsen.csv")
c_pdf.download_button("📄 PDF", create_pdf(pd.DataFrame(ergebnisse), betrag, total_zinsen, start_datum, az, schuldner), "zinsen.pdf")

st.divider()

# --- NEU: ZAHLUNGSVERRECHNUNG ---
st.subheader("💳 Zahlungsverrechnung (§ 367 BGB)")
zahlung = st.number_input("Zahlungseingang (€)", min_value=0.0, value=0.0, step=50.0)

# Tilgungslogik
verbleibende_zahlung = zahlung
getilgte_zinsen = min(verbleibende_zahlung, total_zinsen)
verbleibende_zahlung -= getilgte_zinsen

getilgte_hauptforderung = min(verbleibende_zahlung, betrag)
rest_hauptforderung = betrag - getilgte_hauptforderung

# Ergebnisanzeige der Tilgung
res1, res2 = st.columns(2)
with res1:
    st.write("**Verrechnung:**")
    st.write(f"- Tilgung Zinsen: {getilgte_zinsen:.2f} €")
    st.write(f"- Tilgung Hauptforderung: {getilgte_hauptforderung:.2f} €")

with res2:
    st.write("**Offene Restforderung:**")
    farbe = "green" if rest_hauptforderung == 0 else "red"
    st.markdown(f"### <span style='color:{farbe}'>{rest_hauptforderung:.2f} €</span>", unsafe_allow_html=True)
    if rest_hauptforderung == 0 and zahlung > (total_zinsen + betrag):
        st.info(f"Überzahlung: {zahlung - (total_zinsen + betrag):.2f} €")
