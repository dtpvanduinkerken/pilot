import streamlit as st
import pandas as pd
import requests
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
SHEET_ID = "JOUW_SHEET_ID"
url = f"https://opensheet.elk.sh/{SHEET_ID}/Sheet1"

df = pd.read_csv(url)

# ===== DATA OPSCHONEN =====
df["Omzet"] = df["Omzet"].replace('[€,]', '', regex=True).astype(float)
df["Gem. orde waarde"] = df["Gem. orde waarde"].replace('[€,]', '', regex=True).astype(float)
df["% loyalty"] = df["% loyalty"].replace('%', '', regex=True).astype(float)

# ===== FILTERS =====
col1, col2 = st.columns(2)

vereniging_filter = col1.selectbox("Selecteer vereniging", ["Alle"] + list(df["Vereniging"].unique()))
sport_filter = col2.selectbox("Selecteer sport", ["Alle"] + list(df["Sport"].unique()))

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
st.markdown("### 🏆 Top verenigingen op omzet")

top_clubs = filtered_df.groupby("Vereniging")["Omzet"].sum().reset_index()
top_clubs = top_clubs.sort_values(by="Omzet", ascending=False)

fig_top = px.bar(
    top_clubs,
    x="Omzet",
    y="Vereniging",
    orientation="h",
)

st.plotly_chart(fig_top, use_container_width=True)

# ===== CONVERSIE PER CLUB =====
st.markdown("### 📈 Conversie per vereniging")

filtered_df["Conversie %"] = (filtered_df["Aantal kopers"] / filtered_df["Aantal loyalty members"]) * 100

fig_conv = px.bar(
    filtered_df,
    x="Vereniging",
    y="Conversie %",
)

st.plotly_chart(fig_conv, use_container_width=True)

# ===== OMZET VS MEMBERS =====
st.markdown("### 💡 Omzet vs Members")

fig_scatter = px.scatter(
    filtered_df,
    x="Aantal loyalty members",
    y="Omzet",
    size="Aantal kopers",
    hover_name="Vereniging",
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

st.markdown("### 🚦 Club segmentatie")

fig_score = px.pie(filtered_df, names="Score")

st.plotly_chart(fig_score, use_container_width=True)

# ===== GROEI (ALS JE PERIODE HEBT) =====
if "Periode" in df.columns:
    st.markdown("### 📅 Groei loyalty members")

    growth = df.groupby("Periode")["Aantal loyalty members"].sum().reset_index()

    fig_growth = px.line(growth, x="Periode", y="Aantal loyalty members")

    st.plotly_chart(fig_growth, use_container_width=True)

# ===== CONCLUSIE BOX =====
st.markdown("### 🧠 Conclusie")

best_club = top_clubs.iloc[0]["Vereniging"] if len(top_clubs) > 0 else "-"

st.info(f"""
Sterkste vereniging: {best_club}  
Totale conversie: {conversion:.1f}%  
Gemiddelde orderwaarde: €{aov:.2f}

➡️ Focus op verhogen van conversie bij lage clubs = grootste groeikans  
➡️ Clubs met veel members maar lage omzet = quick wins  
""")