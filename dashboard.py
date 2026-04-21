import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

# ===== STYLING =====
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #f9f3e9;
}

h1, h2, h3 {
    color:#084422;
}

.kpi-card {
    background:#ffffff;
    padding:20px;
    border-radius:16px;
    box-shadow:0 8px 20px rgba(8,68,34,0.08);
    border-top:4px solid #8cbe26;
    transition:0.3s;
}

.kpi-card:hover {
    transform: translateY(-4px);
}

.kpi-title {
    font-size:13px;
    color:#3f5f4c;
}

.kpi-value {
    font-size:28px;
    font-weight:700;
}
</style>
""", unsafe_allow_html=True)

# ===== DATA INLADEN =====
SHEET_ID = "1h3uj1r-BBGoI3h2qRbYj4Z8FucMqN_0sRX41ejx3aRs"
url = f"https://opensheet.elk.sh/{SHEET_ID}/Sheet1"

df = pd.read_csv(url)

# ===== DATA OPSCHONEN =====
def clean_column(df, col):
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace("€", "").str.replace(",", "").str.replace("%", "")
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

df = clean_column(df, "Omzet")
df = clean_column(df, "Gem. orde waarde")
df = clean_column(df, "% loyalty")

# fallback berekeningen
if "Gem. orde waarde" not in df.columns and "Omzet" in df.columns and "Aantal verkooptransacties" in df.columns:
    df["Gem. orde waarde"] = df["Omzet"] / df["Aantal verkooptransacties"]

# ===== FILTERS =====
col1, col2 = st.columns(2)

vereniging_filter = col1.selectbox("Vereniging", ["Alle"] + sorted(df["Vereniging"].dropna().unique()))
sport_filter = col2.selectbox("Sport", ["Alle"] + sorted(df["Sport"].dropna().unique()))

filtered_df = df.copy()

if vereniging_filter != "Alle":
    filtered_df = filtered_df[filtered_df["Vereniging"] == vereniging_filter]

if sport_filter != "Alle":
    filtered_df = filtered_df[filtered_df["Sport"] == sport_filter]

# ===== KPI BEREKENINGEN =====
total_members = filtered_df["Aantal loyalty members"].sum()
total_revenue = filtered_df["Omzet"].sum()
total_buyers = filtered_df["Aantal kopers"].sum()
total_transactions = filtered_df["Aantal verkooptransacties"].sum()

conversion = (total_buyers / total_members * 100) if total_members > 0 else 0
aov = (total_revenue / total_transactions) if total_transactions > 0 else 0

# ===== KPI CARDS =====
col1, col2, col3, col4 = st.columns(4)

col1.markdown(f"""
<div class="kpi-card">
<div class="kpi-title">Loyalty Members</div>
<div class="kpi-value">{int(total_members)}</div>
</div>
""", unsafe_allow_html=True)

col2.markdown(f"""
<div class="kpi-card">
<div class="kpi-title">Omzet</div>
<div class="kpi-value">€ {total_revenue:,.2f}</div>
</div>
""", unsafe_allow_html=True)

col3.markdown(f"""
<div class="kpi-card">
<div class="kpi-title">Conversie</div>
<div class="kpi-value">{conversion:.1f}%</div>
</div>
""", unsafe_allow_html=True)

col4.markdown(f"""
<div class="kpi-card">
<div class="kpi-title">Gem. orderwaarde</div>
<div class="kpi-value">€ {aov:.2f}</div>
</div>
""", unsafe_allow_html=True)

# ===== TOP VERENIGINGEN =====
st.markdown("### Top verenigingen op omzet")

top_clubs = filtered_df.groupby("Vereniging")["Omzet"].sum().reset_index()
top_clubs = top_clubs.sort_values(by="Omzet", ascending=False)

fig_top = px.bar(
    top_clubs,
    x="Omzet",
    y="Vereniging",
    orientation="h"
)

st.plotly_chart(fig_top, use_container_width=True)

# ===== CONVERSIE PER CLUB =====
st.markdown("### Conversie per vereniging")

filtered_df["Conversie %"] = (filtered_df["Aantal kopers"] / filtered_df["Aantal loyalty members"]) * 100

fig_conv = px.bar(
    filtered_df,
    x="Vereniging",
    y="Conversie %"
)

st.plotly_chart(fig_conv, use_container_width=True)

# ===== OMZET VS MEMBERS =====
st.markdown("### Omzet vs Members")

fig_scatter = px.scatter(
    filtered_df,
    x="Aantal loyalty members",
    y="Omzet",
    size="Aantal kopers",
    hover_name="Vereniging"
)

st.plotly_chart(fig_scatter, use_container_width=True)

# ===== SCORE MODEL =====
def score(row):
    if row["Conversie %"] > 30:
        return "Top"
    elif row["Conversie %"] > 15:
        return "Groei"
    else:
        return "Risico"

filtered_df["Score"] = filtered_df.apply(score, axis=1)

st.markdown("### Club segmentatie")

fig_score = px.pie(filtered_df, names="Score")

st.plotly_chart(fig_score, use_container_width=True)

# ===== GROEI =====
if "Periode" in df.columns:
    st.markdown("### Groei loyalty members")

    growth = df.groupby("Periode")["Aantal loyalty members"].sum().reset_index()

    fig_growth = px.line(growth, x="Periode", y="Aantal loyalty members")

    st.plotly_chart(fig_growth, use_container_width=True)

# ===== CONCLUSIE =====
st.markdown("### Conclusie")

best_club = top_clubs.iloc[0]["Vereniging"] if len(top_clubs) > 0 else "-"

st.info(f"""
Sterkste vereniging: {best_club}  
Totale conversie: {conversion:.1f}%  
Gemiddelde orderwaarde: €{aov:.2f}

➡️ Grootste kans: verhoog conversie bij clubs met veel members  
➡️ Focus: clubs met lage conversie maar hoge instroom  
""")
