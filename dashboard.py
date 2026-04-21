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

/* KPI */
.kpi-card {
    background:#ffffff;
    padding:22px;
    border-radius:18px;
    box-shadow:0 10px 25px rgba(8,68,34,0.08);
    border-top:4px solid #8cbe26;
}

/* TOP 3 */
.top-card {
    background:#ffffff;
    padding:20px;
    border-radius:18px;
    text-align:center;
    box-shadow:0 10px 25px rgba(8,68,34,0.08);
}

.rank-1 {border-top:6px solid gold;}
.rank-2 {border-top:6px solid silver;}
.rank-3 {border-top:6px solid #cd7f32;}

.big {
    font-size:26px;
    font-weight:700;
}

.small {
    color:#3f5f4c;
    font-size:13px;
}
</style>
""", unsafe_allow_html=True)

# ===== DATA =====
SHEET_ID = "1h3uj1r-BBGoI3h2qRbYj4Z8FucMqN_0sRX41ejx3aRs"
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

df = pd.read_csv(url)

# ===== CLEAN =====
def clean(df, col):
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace("€","").str.replace(",","").str.replace("%","")
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

df = clean(df, "Omzet")
df = clean(df, "Gem. orde waarde")

# ===== FILTER =====
col1, col2 = st.columns(2)

vereniging = col1.selectbox("Vereniging", ["Alle"] + sorted(df["Vereniging"].dropna().unique()))
sport = col2.selectbox("Sport", ["Alle"] + sorted(df["Sport"].dropna().unique()))

filtered = df.copy()

if vereniging != "Alle":
    filtered = filtered[filtered["Vereniging"] == vereniging]

if sport != "Alle":
    filtered = filtered[filtered["Sport"] == sport]

# ===== KPI =====
members = filtered["Aantal loyalty members"].sum()
revenue = filtered["Omzet"].sum()
buyers = filtered["Aantal kopers"].sum()
transactions = filtered["Aantal verkooptransacties"].sum()

conversion = (buyers / members * 100) if members > 0 else 0
aov = (revenue / transactions) if transactions > 0 else 0

c1, c2, c3, c4 = st.columns(4)

def kpi(col, title, value):
    col.markdown(f"""
    <div class="kpi-card">
        <div class="small">{title}</div>
        <div class="big">{value}</div>
    </div>
    """, unsafe_allow_html=True)

kpi(c1, "Members", int(members))
kpi(c2, "Omzet", f"€ {revenue:,.0f}")
kpi(c3, "Conversie", f"{conversion:.1f}%")
kpi(c4, "AOV", f"€ {aov:.2f}")

# ===== TOP 3 =====
st.markdown("## Top 3 verenigingen")

top = filtered.groupby("Vereniging")["Omzet"].sum().reset_index()
top = top.sort_values("Omzet", ascending=False).head(3)

cols = st.columns(3)

for i, row in top.iterrows():
    cols[i].markdown(f"""
    <div class="top-card rank-{i+1}">
        <div class="small">#{i+1}</div>
        <div class="big">{row['Vereniging']}</div>
        <div class="small">€ {row['Omzet']:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

# ===== SCORE =====
filtered["Conversie %"] = (filtered["Aantal kopers"] / filtered["Aantal loyalty members"]) * 100

def label(x):
    if x > 30:
        return "Top"
    elif x > 15:
        return "Groei"
    else:
        return "Risico"

filtered["Score"] = filtered["Conversie %"].apply(label)

# ===== BAR MET KLEUR =====
st.markdown("## Omzet per vereniging")

fig = px.bar(
    filtered,
    x="Vereniging",
    y="Omzet",
    color="Score",
    color_discrete_map={
        "Top": "#8cbe26",
        "Groei": "#f2a900",
        "Risico": "#d9534f"
    }
)

st.plotly_chart(fig, use_container_width=True)

# ===== GROEI =====
if "Periode" in df.columns:
    st.markdown("## Groei over tijd")

    growth = df.groupby(["Periode","Vereniging"])["Aantal loyalty members"].sum().reset_index()

    fig2 = px.line(
        growth,
        x="Periode",
        y="Aantal loyalty members",
        color="Vereniging"
    )

    st.plotly_chart(fig2, use_container_width=True)

# ===== INSIGHTS =====
st.markdown("## Inzichten")

insights = []

if len(filtered) > 0:

    low_conv = filtered.sort_values("Conversie %").iloc[0]
    high_growth = filtered.sort_values("Aantal loyalty members", ascending=False).iloc[0]

    insights.append(f"⚠️ {low_conv['Vereniging']} heeft lage conversie ({low_conv['Conversie %']:.1f}%)")
    insights.append(f"🔥 {high_growth['Vereniging']} heeft meeste members ({int(high_growth['Aantal loyalty members'])})")

    opportunity = filtered[
        (filtered["Aantal loyalty members"] > filtered["Aantal loyalty members"].mean()) &
        (filtered["Conversie %"] < filtered["Conversie %"].mean())
    ]

    if len(opportunity) > 0:
        club = opportunity.iloc[0]["Vereniging"]
        insights.append(f"💡 Grootste kans: {club} (veel members, lage conversie)")

for i in insights:
    st.info(i)
