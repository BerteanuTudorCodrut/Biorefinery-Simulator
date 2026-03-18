import io
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Local module imports
from process_model import calculate_mass_balance
from emissions import calculate_co2
from economics import calculate_economics

# ReportLab imports
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

# ==========================================================
# INITIALIZE SESSION STATE FOR SAVED SCENARIOS
# ==========================================================
if 'saved_scenarios' not in st.session_state:
    st.session_state.saved_scenarios = []

# ==========================================================
# PAGE CONFIG + CLEAN ECO LIGHT THEME
# ==========================================================
st.set_page_config(page_title="Biorefinery Simulator", page_icon="🌱", layout="wide")

st.markdown("""
<style>
/* Adaptive Theme KPI Cards */
.kpi-card {
    background-color: var(--secondary-background-color); /* Adapts to light/dark mode */
    padding: 20px;
    border-radius: 12px;
    border: 1px solid rgba(150, 150, 150, 0.2);
    box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    margin-bottom: 20px;
    color: var(--text-color); /* Adapts to light/dark mode */
    transition: transform 0.2s ease-in-out, box-shadow 0.2s;
}
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0px 6px 16px rgba(0,0,0,0.15);
}

/* KPI Value */
.kpi-value {
    font-size: 34px;
    font-weight: 800;
    margin-top: 8px;
    letter-spacing: -0.5px;
}

/* KPI Label */
.kpi-label {
    font-size: 13px;
    opacity: 0.7;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Earthy Color accents */
.kpi-green { color: #10b981; } /* Emerald */
.kpi-red { color: #ef4444; }   /* Coral */
.kpi-orange { color: #f59e0b; } /* Amber */
.kpi-blue { color: #3b82f6; }  /* Ocean */
</style>
""", unsafe_allow_html=True)

# Main Header
col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.title("🌱 Biomass Biorefinery Simulator")
    st.markdown("Analyze mass balance, emissions, and economics of your biorefinery process.")

# ==========================================================
# LOAD CSV
# ==========================================================
@st.cache_data
def load_data():
    try:
        return pd.read_csv("data.csv")
    except FileNotFoundError:
        return pd.DataFrame({
            "name": ["Baseline", "High Efficiency", "Low Energy"],
            "biomass_flow": [1000, 1000, 1000],
            "conversion_efficiency": [0.35, 0.45, 0.35],
            "energy_consumption": [500, 550, 400],
            "moisture": [0.2, 0.2, 0.2],
            "electricity_co2_factor": [0.45, 0.45, 0.45]
        })

df = load_data()

# ==========================================================
# SIDEBAR (CLEANED UP WITH EXPANDERS & SAVE FEATURE)
# ==========================================================
with st.sidebar:
    st.markdown("<div style='text-align: center; font-size: 65px; margin-bottom: 10px;'>🏭🌱</div>", unsafe_allow_html=True)
    st.title("Control Panel")
    
    with st.expander("🔧 Process Parameters", expanded=True):
        bio = st.slider("Biomass (kg/h)", 100, 2000, 1000, 50)
        eff = st.slider("Efficiency (%)", 10, 80, 35) / 100
        energy = st.slider("Energy (kWh)", 100, 1200, 500, 25)
        moisture = st.slider("Moisture content", 0.0, 0.6, 0.2)
        factor = st.slider("CO₂ factor", 0.1, 1.0, 0.45)

    with st.expander("💰 Economic Parameters", expanded=True):
        feedstock_price = st.slider("Feedstock €/ton", 40, 150, 90)
        product_price = st.slider("Product €/kg", 0.5, 3.0, 1.2)
        electricity_price = st.slider("Electricity €/kWh", 0.05, 0.4, 0.18)
        carbon_price = st.slider("Carbon €/ton", 0, 200, 80)

# ==========================================================
# MAIN CALCULATION (WITH PHYSICS PENALTY FIX)
# ==========================================================
# Apply the exact same energy penalty to the current selection!
actual_energy = energy * (1 + 0.5 * (eff - 0.35))

p_new, w_new, e_new, total_energy, drying_energy = calculate_mass_balance(
    bio, eff, actual_energy, moisture
)
c_new = calculate_co2(total_energy, factor)
rev, e_cost, c_cost, f_cost, profit = calculate_economics(
    p_new, total_energy, c_new, bio, feedstock_price, 
    product_price, electricity_price, carbon_price
)

# --- SAVE SCENARIO BUTTON ---
with st.sidebar:
    st.markdown("---")
    st.markdown("### 💾 Save Scenario")
    scenario_name = st.text_input("Name this configuration", "My Custom Run")
    if st.button("Save Current Process", use_container_width=True):
        st.session_state.saved_scenarios.append({
            "name": f"⭐ {scenario_name}",
            "Product": p_new,
            "CO2": c_new,
            "Profit": profit
        })
        st.success(f"Saved '{scenario_name}' to Comparison Tab!")

# ==========================================================
# OPTIMIZATION LOOP
# ==========================================================
# Create range, ensuring we include the current slider 'eff' value!
eff_range = np.linspace(0.1, 0.8, 50)
eff_range = np.sort(np.unique(np.append(eff_range, eff))) 

profit_curve, energy_curve, co2_curve, product_curve = [], [], [], []

for e in eff_range:
    energy_opt = energy * (1 + 0.5 * (e - 0.35))
    p_opt, _, _, total_energy_opt, _ = calculate_mass_balance(bio, e, energy_opt, moisture)
    c_opt = calculate_co2(total_energy_opt, factor)
    _, _, _, _, prof = calculate_economics(
        p_opt, total_energy_opt, c_opt, bio, feedstock_price,
        product_price, electricity_price, carbon_price
    )
    
    profit_curve.append(prof)
    energy_curve.append(total_energy_opt)
    co2_curve.append(c_opt)
    product_curve.append(p_opt)

best_idx = np.argmax(profit_curve)
best_eff = eff_range[best_idx]
best_profit = profit_curve[best_idx]

# ==========================================================
# TABS
# ==========================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Executive Dashboard", "🚀 Optimization", "📈 Scenario Comparison", "📄 Report"
])

# ==========================================================
# TAB 1 — EXECUTIVE DASHBOARD (SANKEY & WATERFALL)
# ==========================================================
with tab1:
    st.markdown("### 🌿 Mass Balance")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">📦 Product Output</div><div class="kpi-value kpi-green">{p_new:.1f} <span style="font-size: 16px;">kg/h</span></div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">🗑️ Waste Generated</div><div class="kpi-value kpi-orange">{w_new:.1f} <span style="font-size: 16px;">kg/h</span></div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">☁️ CO₂ Emissions</div><div class="kpi-value kpi-red">{c_new:.1f} <span style="font-size: 16px;">kg/h</span></div></div>', unsafe_allow_html=True)

    # Sankey Diagram
    fig_sankey = go.Figure(data=[go.Sankey(
        node = dict(
          pad = 20,
          thickness = 30,
          line = dict(color = "#cbd5e1", width = 1),
          label = ["Biomass Input", "Biorefinery", "Product", "Waste"],
          color = ["#f59e0b", "#94a3b8", "#10b981", "#ef4444"] 
        ),
        link = dict(
          source = [0, 1, 1],
          target = [1, 2, 3],
          value = [bio, p_new, w_new],
          color = ["rgba(245, 158, 11, 0.3)", "rgba(16, 185, 129, 0.3)", "rgba(239, 68, 68, 0.3)"]
      ))])
    
    fig_sankey.update_layout(
        title_text="Physical Mass Flow (kg/h)", 
        font_size=14, 
        template="plotly_white", 
        height=300, 
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig_sankey, use_container_width=True)

    st.markdown("---")
    st.markdown("### 💰 Financial Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">💵 Revenue</div><div class="kpi-value kpi-blue">€{rev:.0f}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">🌾 Feedstock</div><div class="kpi-value kpi-red">€{f_cost:.0f}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">⚡ Energy</div><div class="kpi-value kpi-red">€{e_cost:.0f}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">🌍 Carbon Tax</div><div class="kpi-value kpi-red">€{c_cost:.0f}</div></div>', unsafe_allow_html=True)

    # Waterfall Chart
    fig_waterfall = go.Figure(go.Waterfall(
        orientation = "v",
        measure = ["relative", "relative", "relative", "relative", "total"],
        x = ["Revenue", "Feedstock Cost", "Energy Cost", "Carbon Tax", "Net Profit"],
        textposition = "outside",
        text = [f"€{rev:.0f}", f"-€{f_cost:.0f}", f"-€{e_cost:.0f}", f"-€{c_cost:.0f}", f"€{profit:.0f}"],
        y = [rev, -f_cost, -e_cost, -c_cost, profit],
        connector = {"line":{"color":"#cbd5e1"}},
        decreasing = {"marker":{"color":"#ef4444"}}, 
        increasing = {"marker":{"color":"#3b82f6"}},  
        totals = {"marker":{"color":"#10b981" if profit >= 0 else "#ef4444"}}
    ))
    
    fig_waterfall.update_layout(
        title="Hourly Profit Breakdown (€/h)", 
        template="plotly_white", 
        height=400, 
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

# ==========================================================
# TAB 2 — OPTIMIZATION
# ==========================================================
with tab2:
    st.markdown("### 🚀 Process Optimization Analysis")
    colA, colB = st.columns([2, 1])

    with colA:
        fig_opt = go.Figure()
        fig_opt.add_trace(go.Scatter(x=eff_range*100, y=profit_curve, mode='lines', name='Profit', line=dict(color='#10b981', width=3)))
        fig_opt.add_trace(go.Scatter(x=[best_eff*100], y=[best_profit], mode='markers', name='Optimal Point', marker=dict(color='#ef4444', size=12, symbol='star')))
        
        fig_opt.update_layout(
            title="Profit vs Conversion Efficiency",
            xaxis_title="Conversion Efficiency (%)",
            yaxis_title="Profit (€/h)",
            template="plotly_white",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_opt, use_container_width=True)

    with colB:
        st.info("💡 **Optimal Operating Point** found via simulation.")
        st.metric("Optimal Efficiency", f"{best_eff*100:.1f}%")
        
        # Metric fixed with proper +/- sign placement
        profit_diff = best_profit - profit
        st.metric("Maximum Profit", f"€{best_profit:.1f}/h", delta=f"{profit_diff:+.1f} €/h vs current")
        
        st.metric("Output at Optima", f"{product_curve[best_idx]:.1f} kg/h")

    col1, col2 = st.columns(2)
    with col1:
        fig_energy = px.line(x=eff_range*100, y=energy_curve, title="Energy Demand vs Efficiency", labels={'x': 'Efficiency (%)', 'y': 'Energy (kWh)'}, color_discrete_sequence=['#f59e0b'])
        fig_energy.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_energy, use_container_width=True)
    with col2:
        fig_co2 = px.line(x=eff_range*100, y=co2_curve, title="CO₂ Emissions vs Efficiency", labels={'x': 'Efficiency (%)', 'y': 'CO₂ (kg/h)'}, color_discrete_sequence=['#ef4444'])
        fig_co2.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_co2, use_container_width=True)

# ==========================================================
# TAB 3 — COMPARISON (WITH SESSION STATE & UNITS)
# ==========================================================
with tab3:
    st.markdown("### 📈 Scenario Comparison")
    
    # Process CSV data for comparison
    df_slider = pd.DataFrame({
        "name": ["Current Selection"], "Product": [p_new], "CO2": [c_new], "Profit": [profit]
    })
    
    # Recalculate for CSV data
    profits_csv, products_csv, co2s_csv = [], [], []
    for _, row in df.iterrows():
        p, _, _, t_e, _ = calculate_mass_balance(
            row["biomass_flow"], row["conversion_efficiency"], row["energy_consumption"], row["moisture"]
        )
        c = calculate_co2(t_e, row["electricity_co2_factor"])
        _, _, _, _, pr = calculate_economics(
            p, t_e, c, row["biomass_flow"], feedstock_price, product_price, electricity_price, carbon_price
        )
        profits_csv.append(pr)
        products_csv.append(p)
        co2s_csv.append(c)
    
    df["Profit"] = profits_csv
    df["Product"] = products_csv
    df["CO2"] = co2s_csv
    
    # Fetch User Saved Scenarios from Session State
    if st.session_state.saved_scenarios:
        df_saved = pd.DataFrame(st.session_state.saved_scenarios)
    else:
        df_saved = pd.DataFrame(columns=["name", "Product", "CO2", "Profit"])
    
    # Concatenate everything
    df_all = pd.concat([df[["name", "Product", "CO2", "Profit"]], df_saved, df_slider], ignore_index=True)

    # Define a cohesive eco-color palette for your scenarios
    eco_color_sequence = ["#94a3b8", "#3b82f6", "#f59e0b", "#8b5cf6", "#10b981", "#ef4444"]

    eco_color_sequence = ["#94a3b8", "#3b82f6", "#f59e0b", "#8b5cf6", "#10b981", "#ef4444"]

    col1, col2 = st.columns(2)
    with col1:
        fig_prod = px.bar(
            df_all, x="name", y="Product", title="Product Output Comparison", 
            color="name", text_auto='.1f', 
            labels={"Product": "Product (kg/h)", "name": "Scenario"},
            color_discrete_sequence=eco_color_sequence
        )
        fig_prod.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
        # MAKE TEXT BIGGER AND PUSH OUTSIDE
        fig_prod.update_traces(textfont_size=18, textposition="outside") 
        st.plotly_chart(fig_prod, use_container_width=True)

    with col2:
        fig_prof = px.bar(
            df_all, x="name", y="Profit", title="Profit Comparison", 
            color="name", text_auto='.1f',
            labels={"Profit": "Profit (€/h)", "name": "Scenario"},
            color_discrete_sequence=eco_color_sequence
        )
        fig_prof.update_layout(showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
        # MAKE TEXT BIGGER AND PUSH OUTSIDE
        fig_prof.update_traces(textfont_size=18, textposition="outside") 
        st.plotly_chart(fig_prof, use_container_width=True) 

# ==========================================================
# TAB 4 — REPORT CENTER
# ==========================================================
with tab4:
    st.markdown("### 📄 Export & Report Center")
    
    carbon_intensity = c_new / p_new if p_new > 0 else 0
    
    if carbon_intensity < 0.5:
        score, color = "A", "#10b981" # Emerald
    elif carbon_intensity < 1.0:
        score, color = "B", "#f59e0b" # Amber
    else:
        score, color = "C", "#ef4444" # Coral

    st.markdown(f"""
    <div style="padding: 20px; border-radius: 10px; border: 2px solid {color}; text-align: center; margin-bottom: 20px; background-color: var(--secondary-background-color); color: var(--text-color);">
        <h3 style="margin:0;">Sustainability Grade</h3>
        <h1 style="color:{color}; font-size: 60px; margin:0;">{score}</h1>
        <p style="opacity: 0.7; margin:0;">{carbon_intensity:.2f} kg CO₂ / kg product</p>
    </div>
    """, unsafe_allow_html=True)

    csv_data = df.to_csv(index=False).encode("utf-8")
    
    def create_pdf():
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = [
            Paragraph("Biomass Biorefinery Executive Report", styles["Title"]),
            Spacer(1, 12),
            Table([
                ["Metric", "Value"],
                ["Profit", f"€{profit:.1f}/h"],
                ["Carbon Intensity", f"{carbon_intensity:.2f}"],
                ["Sustainability Grade", score]
            ])
        ]
        doc.build(elements)
        buffer.seek(0)
        return buffer

    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📊 Download Scenarios (CSV)", csv_data, "results.csv", "text/csv", use_container_width=True)
    with col2:
        st.download_button("📑 Download Executive Report (PDF)", create_pdf(), "report.pdf", "application/pdf", use_container_width=True)

# ==========================================================
# GLOBAL FOOTER (LEGAL DISCLAIMER)
# ==========================================================
st.markdown("""
    <div style="text-align: center; font-size: 12px; opacity: 0.6; margin-top: 50px; padding-top: 20px; border-top: 1px solid rgba(150,150,150,0.2);">
        <b>Legal Disclaimer:</b> This application is provided for educational and non-profit purposes only. 
        The underlying mathematical models are simplified approximations and do not constitute professional engineering or financial advice. 
        The developer assumes no liability or responsibility for any operational, financial, or strategic decisions made based on the outputs of this simulator. 
        Always consult certified professionals and perform rigorous physical testing before implementing real-world biorefinery projects.
    </div>
""", unsafe_allow_html=True)