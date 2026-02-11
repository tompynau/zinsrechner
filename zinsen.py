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
    # Historische Basiszinssätze der Deutschen Bundesbank
    return [
        (datetime.date(2002, 1, 1), 2.57),
        (datetime.date(2002, 7, 1), 2.47),
        (datetime.date(2003, 1, 1), 1.97),
        (datetime.date(2003, 7, 1), 1.22),
        (datetime.date(2004, 1, 1), 1.14),
        (datetime.date(2004, 7, 1), 1.13),
        (datetime.date(2005, 1, 1), 1.21),
        (datetime.date(2005, 7, 1), 1.17),
        (datetime.date(2006, 1, 1), 1.37),
        (datetime.date(2006, 7, 1), 1.95),
        (datetime.date(2007, 1, 1), 2.70),
        (datetime.date(2007, 7, 1), 3.19),
        (datetime.date(2008, 1, 1), 3.32),
        (datetime.date(2008, 7, 1), 3.19),
        (datetime.date(2009, 1, 1), 1.62),
        (datetime.date(2009, 7, 1), 0.12),
        (datetime.date(2010, 1, 1), 0.12),
        (datetime.date(2010, 7, 1), 0.12),
        (datetime.date(2011, 1, 1), 0.12),
        (datetime.date(2011, 7, 1), 0.37),
        (datetime.date(2012, 1, 1), 0.12),
        (datetime.date(2012, 7, 1), 0.12),
        (datetime.date(2013, 1, 1), -0.13),
        (datetime.date(2013, 7, 1), -0.38),
        (datetime.date(2014, 1, 1), -0.63),
        (datetime.date(2014, 7, 1), -0.73),
        (datetime.date(2015, 1, 1), -0.83),
        (datetime.date(2015, 7, 1), -0.83),
        (datetime.date(2016, 1, 1), -0.83),
        (datetime.date(2016, 7, 1), -0.88),
        (datetime.date(2017, 1, 1), -0.88),
        (datetime.date(2017, 7, 1), -0.88),
        (datetime.date(2018, 1, 1), -0.88),
        (datetime.date(2018, 7, 1), -0.88),
        (datetime.date(2019, 1, 1), -0.88),
        (datetime.date(2019, 7, 1), -0.88),
        (datetime.date(2020, 1, 1), -0.88),
        (datetime.date(2020, 7, 1), -0.88),
        (datetime.date(2021, 1, 1), -0.88),
        (datetime.date(2021, 7, 1), -0.88),
        (datetime.date(2022, 1, 1), -0.88),
        (datetime.date(2022, 7, 1), -0.88),
        (datetime.date(2023, 1, 1), 1.62),
        (datetime.date(2023, 7, 1), 3.12),
        (datetime.date(2024, 1, 1), 3.62),
        (datetime.date(2024, 7, 1), 3.37),
        (datetime.date(2025, 1, 1), 2.27),
        (datetime.date(2025, 7, 1), 1.27),
        (datetime.date(2026, 1, 1), 1.27),
    ]

# --- 2. PDF-Klasse ---
class ZinsPDF(FPDF):

    def header(self):

        try:
            self.image("logo.png", x=10, y=8, w=15)
        except: pass
        
        # Wir nutzen Helvetica (Standard-Font), da Arial systemabhängig ist
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "Zinsberechnungsprotokoll", ln=True, align="C")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 10, f"Erstellt am: {datetime.date.today().strftime('%d.%m.%Y')}", ln=True, align="R")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Seite {self.page_no()}/{{nb}}", align="C")

def create_pdf(df, betrag, gesamt_zinsen, start_dat):
    pdf = ZinsPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Eckdaten
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Berechnungsgrundlagen", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Hauptforderung: {betrag:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", "."), ln=True)
    pdf.cell(0, 8, f"Zinsbeginn: {start_dat.strftime('%d.%m.%Y')}", ln=True)
    pdf.ln(5)

    # Tabellen-Header
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(60, 10, "Zeitraum", border=1, fill=True)
    pdf.cell(30, 10, "Tage", border=1, fill=True)
    pdf.cell(40, 10, "Zinssatz", border=1, fill=True)
    pdf.cell(50, 10, "Zinsertrag (EUR)", border=1, fill=True, ln=True)

    # Tabellen-Daten
    pdf.set_font("Helvetica", "", 10)
    for _, row in df.iterrows():
        pdf.cell(60, 8, str(row['Zeitraum']), border=1)
        pdf.cell(30, 8, str(row['Tage']), border=1)
        pdf.cell(40, 8, str(row['Zinssatz']), border=1)
        pdf.cell(50, 8, f"{row['Zinsertrag (€)']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), border=1, ln=True)

    # Zusammenfassung
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"Zinsen gesamt: {gesamt_zinsen:,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", "."), ln=True, align="R")
    pdf.cell(0, 10, f"Gesamtforderung: {(betrag + gesamt_zinsen):,.2f} EUR".replace(",", "X").replace(".", ",").replace("X", "."), ln=True, align="R")

    # WICHTIG: Rückgabe als bytes für Streamlit
    return bytes(pdf.output())

# --- 3. Streamlit Interface ---
st.set_page_config(page_title="Zinsrechner UHV Nauen", layout="wide")
# st.set_page_config(page_title="Zinsrechner Pro", layout="centered")

# CSS für Lesbarkeit (Dunkle Schrift auf hellem Grund)
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #f8f9fa !important; border: 1px solid #dee2e6 !important; border-radius: 10px !important; padding: 15px !important; }
    [data-testid="stMetricValue"] > div { color: #212529 !important; }
    [data-testid="stMetricLabel"] > div { color: #495057 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚖️ Zinsrechner 51.5 UHV Nauen")

# Sidebar
with st.sidebar:
    # Drei Spalten: [Platz links, Bild-Bereich, Platz rechts]
    # Das Verhältnis 1:2:1 sorgt dafür, dass die Mitte am breitesten ist
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.image("logo.png", width=120) 
    
    st.divider() # Optionale Linie unter dem Logo
with st.sidebar:
    az_eingabe = st.text_input("Aktenzeichen", "AZ 2026/01")
    schuldner_eingabe = st.text_input("Schuldner", "Max Mustermann")
min_datum = datetime.date(2002, 1, 1) # Erlaubt die Auswahl bis zum Jahr 1900
max_datum = datetime.date(2100, 12, 31)
st.sidebar.header("Eingaben")
betrag = st.sidebar.number_input("Betrag (€)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
start_datum = st.sidebar.date_input("Zinsbeginn", value=datetime.date(2023, 1, 1), min_value=min_datum, max_value=max_datum, format="DD.MM.YYYY")
heute = datetime.date.today()

#with st.sidebar:
#    st.subheader("§ 367 BGB")
#    st.write("Hat der Schuldner außer der Hauptleistung Zinsen und Kosten zu entrichten, so wird eine zur Tilgung der ganzen Schuld nicht ausreichende Leistung zunächst auf die Kosten, dann auf die Zinsen und zuletzt auf die Hauptleistung angerechnet. Bestimmt der Schuldner eine andere Anrechnung, so kann der Gläubiger die Annahme der Leistung ablehnen.")

tab1, tab2 = st.tabs(["📊 Berechnung", "📈 Analyse"])

with tab1:
    historie = get_basiszinssaetze()
    zins_termine = [start_datum]
    for d, _ in historie:
        if start_datum < d <= heute:
            zins_termine.append(d)
    zins_termine.append(heute + datetime.timedelta(days=1))

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
    c1.metric("Gesamttage", f"{total_tage} Tage")
    c2.metric("Zinsen gesamt", f"{total_zinsen:.2f} €")
    c3.metric("Gesamtforderung", f"{total_zinsen + betrag:.2f} €")

    st.subheader("Export")
    cd_csv, cd_pdf = st.columns(2)

    # CSV Export
    csv_data = df_tabelle.to_csv(index=False, sep=';', decimal=',', encoding='utf-8-sig')
    cd_csv.download_button("📥 CSV Export", csv_data, "zinsen.csv", "text/csv")

    # PDF Export
    pdf_bytes = create_pdf(df_tabelle, betrag, total_zinsen, start_datum)
    cd_pdf.download_button("📄 PDF Export", pdf_bytes, "zinsberechnung.pdf", "application/pdf")

with tab2:
    st.subheader("Verlauf des Verzugszinssatzes")
    df_plot = pd.DataFrame(get_basiszinssaetze(), columns=["Datum", "Basis"])
    df_plot["Zinssatz"] = df_plot["Basis"] + 5.0
    fig = px.line(df_plot, x="Datum", y="Zinssatz", markers=True, line_shape="hv")
    fig.update_yaxes(ticksuffix="%")
    st.plotly_chart(fig, use_container_width=True)

# --- NEU: ZAHLUNGSVERRECHNUNG ---

st.divider()  # Hier wird die Linie gezeichnet

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
