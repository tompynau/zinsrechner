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
        (datetime.date(2004, 1, 1), 1.14), (datetime.date(2004, 7, 1), 1.13),
        (datetime.date(2005, 1, 1), 1.21), (datetime.date(2005, 7, 1), 1.17),
        (datetime.date(2006, 1, 1), 1.37), (datetime.date(2006, 7, 1), 1.95),
        (datetime.date(2007, 1, 1), 2.70), (datetime.date(2007, 7, 1), 3.19),
        (datetime.date(2008, 1, 1), 3.32), (datetime.date(2008, 7, 1), 3.19),
        (datetime.date(2009, 1, 1), 1.62), (datetime.date(2009, 7, 1), 0.12),
        (datetime.date(2010, 1, 1), 0.12), (datetime.date(2010, 7, 1), 0.12),
        (datetime.date(2011, 1, 1), 0.12), (datetime.date(2011, 7, 1), 0.37),
        (datetime.date(2012, 1, 1), 0.12), (datetime.date(2012, 7, 1), 0.12),
        (datetime.date(2013, 1, 1), -0.13), (datetime.date(2013, 7, 1), -0.38),
        (datetime.date(2014, 1, 1), -0.63), (datetime.date(2014, 7, 1), -0.73),
        (datetime.date(2015, 1, 1), -0.83), (datetime.date(2015, 7, 1), -0.83),
        (datetime.date(2016, 1, 1), -0.83), (datetime.date(2016, 7, 1), -0.88),
        (datetime.date(2021, 1, 1), -0.88), (datetime.date(2023, 1, 1), 1.62),
        (datetime.date(2023, 7, 1), 3.12), (datetime.date(2024, 1, 1), 3.62),
        (datetime.date(2024, 7, 1), 3.37), (datetime.date(2025, 1, 1), 2.27),
        (datetime.date(2025, 7, 1), 1.27), (datetime.date(2026, 1, 1), 1.27),
    ]

# --- 2. PDF-Klasse ---
class ZinsPDF(FPDF):
    def __init__(self, az, schuldner):
        super().__init__()
        self.az = az
        self.schuldner = schuldner

    def header(self):
        try:
            self.image("logo.png", x=10, y=8, w=20)
        except: pass
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "Zinsberechnungsprotokoll", ln=True, align="C")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 5, f"AZ: {self.az} | Schuldner: {self.schuldner}", ln=True, align="C")
        self.cell(0, 5, f"Erstellt am: {datetime.date.today().strftime('%d.%m.%Y')}", ln=True, align="R")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Seite {self.page_no()}/{{nb}}", align="C")

def create_pdf(df, betrag, zinsen, start_dat, az, schuldner, zahlung, rest):
    pdf = ZinsPDF(az, schuldner)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Berechnungsgrundlagen", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Hauptforderung: {betrag:,.2f} EUR".replace(".", ","), ln=True)
    pdf.cell(0, 8, f"Zinsbeginn: {start_dat.strftime('%d.%m.%Y')}", ln=True)
    pdf.ln(5)

    # Tabelle
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(60, 10, "Zeitraum", 1, 0, "L", True)
    pdf.cell(30, 10, "Tage", 1, 0, "C", True)
    pdf.cell(40, 10, "Zinssatz", 1, 0, "C", True)
    pdf.cell(50, 10, "Zinsertrag (EUR)", 1, 1, "C", True)

    pdf.set_font("Helvetica", "", 10)
    for _, row in df.iterrows():
        pdf.cell(60, 8, str(row['Zeitraum']), 1)
        pdf.cell(30, 8, str(row['Tage']), 1, 0, "C")
        pdf.cell(40, 8, str(row['Zinssatz']), 1, 0, "C")
        pdf.cell(50, 8, f"{row['Zinsertrag (€)']:,.2f}".replace(".", ","), 1, 1, "R")

    pdf.ln(10)
    if zahlung > 0:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f"Zahlungseingang: {zahlung:,.2f} EUR".replace(".", ","), ln=True, align="R")
        pdf.cell(0, 8, f"Offene Restforderung: {rest:,.2f} EUR".replace(".", ","), ln=True, align="R")
    else:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f"Gesamtforderung: {(betrag + zinsen):,.2f} EUR".replace(".", ","), ln=True, align="R")
    
    return bytes(pdf.output())

# --- 3. Streamlit Interface ---
st.set_page_config(page_title="Zinsrechner UHV Nauen", layout="wide")

# Kopf-Bereich mit zentriertem Logo
col_logo_1, col_logo_2, col_logo_3 = st.columns([1, 1, 1])
with col_logo_2:
    try: st.image("logo.png", width=150)
    except: pass

st.title("⚖️ Zinsrechner 51.5 UHV Nauen")

# Sidebar
with st.sidebar:
    col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
    with col_s2:
        try: st.image("logo.png", width=100)
        except: pass
    st.divider()
    az_eingabe = st.text_input("Aktenzeichen", "AZ 2026/01")
    schuldner_eingabe = st.text_input("Schuldner", "Max Mustermann")
    st.header("Eingaben")
    betrag = st.number_input("Betrag (€)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
    start_datum = st.date_input("Zinsbeginn", value=datetime.date(2023, 1, 1), min_value=datetime.date(2002, 1, 1), format="DD.MM.YYYY")

# Berechnung
heute = datetime.date.today()
historie = get_basiszinssaetze()
zins_termine = [start_datum]
for d, _ in historie:
    if start_datum < d <= heute: zins_termine.append(d)
zins_termine.append(heute + datetime.timedelta(days=1))

total_zinsen, ergebnisse = 0.0, []
for i in range(len(zins_termine) - 1):
    p_start, p_ende = zins_termine[i], zins_termine[i+1] - datetime.timedelta(days=1)
    if p_start > p_ende: continue
    anz_tage = (p_ende - p_start).days + 1
    basis = [s for d, s in historie if d <= p_start][-1]
    zinssatz_prozent = basis + 5.0
    phase_summe, curr = 0.0, p_start
    while curr <= p_ende:
        t_jahr = 366 if ist_schaltjahr(curr.year) else 365
        phase_summe += (betrag * (zinssatz_prozent / 100)) / t_jahr
        curr += datetime.timedelta(days=1)
    total_zinsen += phase_summe
    ergebnisse.append({"Zeitraum": f"{p_start.strftime('%d.%m.%Y')} - {p_ende.strftime('%d.%m.%Y')}", "Tage": anz_tage, "Zinssatz": f"{zinssatz_prozent:.2f} %", "Zinsertrag (€)": round(phase_summe, 4)})

# Tabs
tab1, tab2 = st.tabs(["📊 Berechnung", "📈 Analyse"])
df_tabelle = pd.DataFrame(ergebnisse)

with tab1:
    st.table(df_tabelle)
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Gesamttage", f"{sum(df_tabelle['Tage'])} Tage")
    c2.metric("Zinsen gesamt", f"{total_zinsen:.2f} €")
    c3.metric("Gesamtforderung", f"{total_zinsen + betrag:.2f} €")

# ZAHLUNGSVERRECHNUNG
st.divider()
st.subheader("💳 Zahlungsverrechnung (§ 367 BGB)")
zahlung = st.number_input("Zahlungseingang (€)", min_value=0.0, value=0.0, step=50.0)

verbl_zahlung = zahlung
get_zinsen = min(verbl_zahlung, total_zinsen)
verbl_zahlung -= get_zinsen
get_haupt = min(verbl_zahlung, betrag)
rest_haupt = betrag - get_haupt
offener_gesamtbetrag = (total_zinsen + betrag) - zahlung if (total_zinsen + betrag) > zahlung else 0.0

res1, res2 = st.columns(2)
with res1:
    st.write(f"- Tilgung Zinsen: {get_zinsen:.2f} €")
    st.write(f"- Tilgung Hauptforderung: {get_haupt:.2f} €")
with res2:
    farbe = "green" if offener_gesamtbetrag <= 0 else "red"
    st.markdown(f"### Restforderung: <span style='color:{farbe}'>{offener_gesamtbetrag:.2f} €</span>", unsafe_allow_html=True)

# EXPORT
st.divider()
cd_csv, cd_pdf = st.columns(2)
csv_data = df_tabelle.to_csv(index=False, sep=';', decimal=',', encoding='utf-8-sig')
cd_csv.download_button("📥 CSV Export", csv_data, "zinsen.csv")

pdf_bytes = create_pdf(df_tabelle, betrag, total_zinsen, start_datum, az_eingabe, schuldner_eingabe, zahlung, offener_gesamtbetrag)
cd_pdf.download_button("📄 PDF Export", pdf_bytes, "zinsberechnung.pdf")

with tab2:
    df_plot = pd.DataFrame(get_basiszinssaetze(), columns=["Datum", "Basis"])
    df_plot["Zinssatz"] = df_plot["Basis"] + 5.0
    fig = px.line(df_plot, x="Datum", y="Zinssatz", markers=True, line_shape="hv", title="Historie Verzugszinsen")
    st.plotly_chart(fig, use_container_width=True)
