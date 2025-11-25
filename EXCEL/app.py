import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==============================================================================
# 1. CONFIGURACIÓN VISUAL (ESTILO NEON DARK)
# ==============================================================================
st.set_page_config(
    page_title="Retail Command Center",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Paleta de Colores Personalizada (Vibrante sobre fondo oscuro)
COLOR_PALETTE = ['#2E86C1', '#E74C3C', '#1ABC9C', '#9B59B6', '#F1C40F', '#E67E22']

st.markdown("""
<style>
    /* Fondo General */
    .stApp {background-color: #0E1117; color: white;}
    
    /* Tarjetas KPI */
    div[data-testid="metric-container"] {
        background-color: #1A1C24;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    label[data-testid="stMetricLabel"] {color: #A0A0A0; font-size: 14px;}
    
    /* Estilos de Texto Beneficio */
    .profit-pos {color: #00E676; font-weight: 800; font-size: 26px; text-shadow: 0 0 10px rgba(0,230,118,0.2);}
    .profit-neg {color: #FF5252; font-weight: 800; font-size: 26px; text-shadow: 0 0 10px rgba(255,82,82,0.2);}
    
    /* Etiquetas de Filtro Activo */
    .filter-tag {
        background-color: #2E86C1;
        color: white;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 12px;
        margin-right: 5px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. CARGAR DATOS
# ==============================================================================
@st.cache_data
def load_data():
    return pd.read_excel("Datos_Retail_Pro.xlsx")

try:
    df = load_data()
    df["Fecha"] = pd.to_datetime(df["Fecha"])
except:
    st.error("⚠️ Error: Ejecuta 'python generador_retail.py' primero.")
    st.stop()

# ==============================================================================
# 3. SIDEBAR (FILTROS BASE)
# ==============================================================================
with st.sidebar:
    st.title("🎛️ MANDO DE CONTROL")
    pagina = st.radio("Secciones:", ["1. Visión CEO (Interactivo)", "2. Financiero (P&L)", "3. Estrategia & Calidad"])
    
    st.markdown("---")
    st.caption("FILTROS GLOBALES")
    
    todas_marcas = [m for m in df["Marca"].unique() if m != "ESTRUCTURA"]
    sel_marcas = st.multiselect("Marcas:", todas_marcas, default=todas_marcas)
    filtro_base = sel_marcas + ["ESTRUCTURA"] 
    
    fechas = st.date_input("Periodo:", [df["Fecha"].min(), df["Fecha"].max()])
    
    if st.button("🔄 Resetear Todo"):
        st.rerun()

# DataFrame Base (Filtrado por Sidebar)
df_base = df[
    (df["Marca"].isin(filtro_base)) &
    (df["Fecha"] >= pd.to_datetime(fechas[0])) &
    (df["Fecha"] <= pd.to_datetime(fechas[1]))
]

# ==============================================================================
# PÁGINA 1: VISIÓN CEO (DOBLE INTERACCIÓN)
# ==============================================================================
if pagina == "1. Visión CEO (Interactivo)":
    st.title("🚀 Centro de Mando Interactivo")
    st.markdown("Pincha en las **Barras** (Marcas) y en la **Tarta** (Canales) para cruzar datos.")

    # --- A. GRÁFICOS MAESTROS (TRIGGERS) ---
    col_bar, col_pie = st.columns([2, 1])
    
    sel_marca = None
    sel_canal = None

    with col_bar:
        st.subheader("🏆 Ranking Ventas (Brutas vs Netas)")
        # Preparar datos superpuestos
        df_rank = df_base[df_base["Marca"]!="ESTRUCTURA"].groupby("Marca").apply(
            lambda x: pd.Series({
                "Brutas": x[x["Concepto_PL"]=="Ventas Brutas"]["Importe"].sum(),
                "Netas": x[x["Concepto_PL"]=="Ventas Brutas"]["Importe"].sum() + x[x["Concepto_PL"]=="Devoluciones"]["Importe"].sum()
            })
        ).reset_index().sort_values("Brutas", ascending=False)

        fig_bar = go.Figure()
        # Barra Fondo (Brutas)
        fig_bar.add_trace(go.Bar(
            x=df_rank["Marca"], y=df_rank["Brutas"], name="Brutas",
            marker_color='rgba(255, 255, 255, 0.1)', # Gris muy suave
            text=df_rank["Brutas"].apply(lambda x: f"{x/1000:.0f}k"), textposition='auto'
        ))
        # Barra Frente (Netas) - Usamos la paleta personalizada
        fig_bar.add_trace(go.Bar(
            x=df_rank["Marca"], y=df_rank["Netas"], name="Netas (Reales)",
            marker_color=COLOR_PALETTE, # COLORES NUEVOS
            text=df_rank["Netas"].apply(lambda x: f"{x/1000:.0f}k"), textposition='inside'
        ))
        
        fig_bar.update_layout(
            barmode='overlay', template="plotly_dark", 
            clickmode='event+select', showlegend=False, 
            margin=dict(t=0, b=0, l=0, r=0), height=320,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        
        # CAPTURAR CLIC BARRA
        event_bar = st.plotly_chart(fig_bar, on_select="rerun", selection_mode="points", use_container_width=True)
        if len(event_bar["selection"]["points"]) > 0:
            sel_marca = event_bar["selection"]["points"][0]["x"]

    with col_pie:
        st.subheader("🛒 Mix de Canales")
        
        # Datos para la tarta (Adaptados a la marca si ya se seleccionó)
        df_pie_data = df_base[df_base["Concepto_PL"]=="Ventas Brutas"]
        if sel_marca:
            df_pie_data = df_pie_data[df_pie_data["Marca"] == sel_marca]
            
        fig_pie = px.pie(
            df_pie_data, values="Importe", names="Canal", 
            hole=0.6, template="plotly_dark",
            color_discrete_sequence=COLOR_PALETTE # COLORES NUEVOS
        )
        fig_pie.update_layout(
            clickmode='event+select', showlegend=False, 
            margin=dict(t=20, b=0, l=0, r=0), height=320,
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        # CAPTURAR CLIC TARTA
        event_pie = st.plotly_chart(fig_pie, on_select="rerun", selection_mode="points", use_container_width=True)
        if len(event_pie["selection"]["points"]) > 0:
            try: sel_canal = event_pie["selection"]["points"][0]["label"]
            except: sel_canal = event_pie["selection"]["points"][0]["x"]

    # --- B. LÓGICA DE FILTRADO INTELIGENTE ---
    df_final = df_base.copy()
    filtros_txt = []

    # 1. Filtro Marca
    if sel_marca:
        df_final = df_final[(df_final["Marca"] == sel_marca) | (df_final["Marca"] == "ESTRUCTURA")]
        filtros_txt.append(f"🏷️ Marca: {sel_marca}")

    # 2. Filtro Canal (Mejorado para no perder costes fijos)
    if sel_canal:
        # Mantenemos filas que coinciden con canal O que son costes estructurales/generales
        df_final = df_final[
            (df_final["Canal"] == sel_canal) | 
            (df_final["Marca"] == "ESTRUCTURA") |
            (df_final["Concepto_PL"].str.contains("Gastos"))
        ]
        filtros_txt.append(f"🛒 Canal: {sel_canal}")

    # Mostrar etiquetas de filtro
    if filtros_txt:
        st.markdown(" ".join([f"<span class='filter-tag'>{f}</span>" for f in filtros_txt]), unsafe_allow_html=True)
    else:
        st.info("🌍 Viendo datos Globales")

    # --- C. CÁLCULOS SOBRE DATOS FILTRADOS ---
    ventas = df_final[df_final["Concepto_PL"] == "Ventas Brutas"]["Importe"].sum()
    devoluciones = df_final[df_final["Concepto_PL"] == "Devoluciones"]["Importe"].sum()
    netas = ventas + devoluciones
    
    # Costes
    c_ventas = df_final[df_final["Concepto_PL"] == "Coste de Ventas"]["Importe"].sum()
    c_mkt = df_final[df_final["Concepto_PL"] == "Gastos de Marketing"]["Importe"].sum()
    c_fix = df_final[df_final["Concepto_PL"].isin(["Gastos Generales", "Gastos de Personal"])]["Importe"].sum()
    
    beneficio = netas - (c_ventas + c_mkt + c_fix)
    tasa_dev = abs(devoluciones) / ventas if ventas > 0 else 0
    
    # Score Salud
    factor = 0.6 if beneficio < 0 else 1.05
    score = min(100, (1 - tasa_dev) * 100 * factor)

    # --- D. MOSTRAR KPIs ---
    st.markdown("---")
    k1, k2, k3, k4 = st.columns(4)
    
    k1.metric("Ventas Netas", f"{netas:,.0f} €", delta=f"{devoluciones:,.0f} € Devueltos")
    
    css_prof = "profit-pos" if beneficio >= 0 else "profit-neg"
    k2.markdown(f"""
        <div style="background-color: #1A1C24; padding: 12px; border-radius: 12px; border: 1px solid #333;">
            <label style="color: #A0A0A0; font-size: 14px;">Beneficio Neto</label>
            <div class="{css_prof}">{beneficio:,.0f} €</div>
        </div>
    """, unsafe_allow_html=True)
    
    k3.metric("Costes Totales", f"{(c_ventas+c_mkt+c_fix):,.0f} €", delta="-Salidas", delta_color="inverse")
    
    col_score = "normal" if score > 60 else "inverse"
    k4.metric("Score Salud", f"{score:.1f}/100", delta=f"{tasa_dev*100:.1f}% Tasa Dev.", delta_color=col_score)

# ==============================================================================
# PÁGINA 2: P&L
# ==============================================================================
elif pagina == "2. Financiero (P&L)":
    st.title("💰 Cuenta de Resultados")
    
    # Usamos df_base (solo filtros sidebar)
    ventas = df_base[df_base["Concepto_PL"] == "Ventas Brutas"]["Importe"].sum()
    devoluciones = df_base[df_base["Concepto_PL"] == "Devoluciones"]["Importe"].sum()
    netas = ventas + devoluciones
    c_ventas = df_base[df_base["Concepto_PL"] == "Coste de Ventas"]["Importe"].sum()
    c_mkt = df_base[df_base["Concepto_PL"] == "Gastos de Marketing"]["Importe"].sum()
    c_fix = df_base[df_base["Concepto_PL"].isin(["Gastos Generales", "Gastos de Personal"])]["Importe"].sum()
    beneficio = netas - (c_ventas + c_mkt + c_fix)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Tabla Contable")
        df_pl = pd.DataFrame({
            "Partida": ["(+) Ventas Brutas", "(-) Devoluciones", "= VENTAS NETAS", "(-) Coste Ventas", "(-) Marketing", "(-) Estructura", "= BENEFICIO NETO"],
            "Importe": [ventas, devoluciones, netas, -c_ventas, -c_mkt, -c_fix, beneficio]
        })
        def highlight_total(s):
            return ['background-color: #1c3b2a' if s["Partida"] == "= BENEFICIO NETO" else '' for v in s]
        st.dataframe(df_pl.style.format({"Importe": "{:,.0f} €"}).apply(highlight_total, axis=1), use_container_width=True, hide_index=True)

    with c2:
        st.subheader("Evolución Mensual")
        df_base["Mes"] = df_base["Fecha"].dt.strftime('%Y-%m')
        ingresos = df_base[df_base["Concepto_PL"]=="Ventas Brutas"].groupby("Mes")["Importe"].sum()
        gastos = df_base[df_base["Importe"] > 0]
        gastos = gastos[gastos["Concepto_PL"].isin(["Coste de Ventas", "Gastos de Marketing", "Gastos Generales", "Gastos de Personal"])].groupby("Mes")["Importe"].sum()
        df_ev = pd.DataFrame({"Ingresos": ingresos, "Gastos": gastos}).fillna(0).reset_index()
        fig_ev = px.bar(
            df_ev, x="Mes", y=["Ingresos", "Gastos"], barmode="group", 
            template="plotly_dark", 
            color_discrete_map={"Ingresos": "#1ABC9C", "Gastos": "#E74C3C"} # COLORES NUEVOS
        )
        st.plotly_chart(fig_ev, use_container_width=True)

# ==============================================================================
# PÁGINA 3: ESTRATEGIA
# ==============================================================================
elif pagina == "3. Estrategia & Calidad":
    st.title("💎 Análisis de Viabilidad")
    
    # Cálculos rápidos
    ventas = df_base[df_base["Concepto_PL"] == "Ventas Brutas"]["Importe"].sum()
    devoluciones = df_base[df_base["Concepto_PL"] == "Devoluciones"]["Importe"].sum()
    netas = ventas + devoluciones
    c_ventas = df_base[df_base["Concepto_PL"] == "Coste de Ventas"]["Importe"].sum()
    c_mkt = df_base[df_base["Concepto_PL"] == "Gastos de Marketing"]["Importe"].sum()
    c_fix = df_base[df_base["Concepto_PL"].isin(["Gastos Generales", "Gastos de Personal"])]["Importe"].sum()
    beneficio = netas - (c_ventas + c_mkt + c_fix)
    tasa_dev = abs(devoluciones) / ventas if ventas > 0 else 0
    score = min(100, (1-tasa_dev)*100 * (0.6 if beneficio < 0 else 1.05))

    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Waterfall")
        fig_water = go.Figure(go.Waterfall(
            measure = ["relative", "relative", "total", "relative", "relative", "relative", "total"],
            x = ["Brutas", "Devol.", "NETAS", "Coste", "Mkt", "Fijos", "BENEFICIO"],
            y = [ventas, devoluciones, 0, -c_ventas, -c_mkt, -c_fix, 0],
            connector = {"line":{"color":"white"}},
            decreasing = {"marker":{"color":"#E74C3C"}}, # Rojo nuevo
            increasing = {"marker":{"color":"#1ABC9C"}}, # Verde nuevo
            totals = {"marker":{"color":"#2E86C1"}}      # Azul nuevo
        ))
        fig_water.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_water, use_container_width=True)
        
    with c2:
        st.subheader("Score Salud")
        color_g = "#E74C3C" if score < 60 else "#1ABC9C"
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number", value = score,
            gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': color_g}}
        ))
        fig_gauge.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_gauge, use_container_width=True)