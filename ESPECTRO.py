import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.ticker import AutoMinorLocator, MultipleLocator

# Configuración de la interfaz
st.set_page_config(
    page_title="Espectro E.030-2026 Profesional", layout="wide"
)

# --- CABECERA LIMPIA (SIN LOGO) ---
st.title("⚙️ Sistema de Espectros Sísmicos Parametrizado")
st.subheader("Norma Técnica E.030 - Edición 2026")
st.markdown("---")

# --- SIDEBAR: CONTROLES GENERALES ---
st.sidebar.header("⚙️ 1. Factores Generales")

g = st.sidebar.number_input(
    "Aceleración de la gravedad (g) [m/s²]:",
    min_value=1.0,
    max_value=10.0,
    value=9.81,
    step=0.01,
)

# Tabla de Zonas
z_opts = {
    "Zona 4 (Z = 0.45)": 0.45,
    "Zona 3 (Z = 0.35)": 0.35,
    "Zona 2 (Z = 0.25)": 0.25,
    "Zona 1 (Z = 0.10)": 0.10,
}
z_sel = st.sidebar.selectbox("Factor de Zona (Z):", list(z_opts.keys()))
Z = z_opts[z_sel]

# Tabla de Categorías
u_opts = {
    "Cat A (Edificaciones Esenciales - 1.50)": 1.50,
    "Cat B (Edificaciones Importantes - 1.30)": 1.30,
    "Cat C (Edificaciones Comunes - 1.00)": 1.00,
    "Cat D (Edificaciones Temporales - 1.00)": 1.00,
}
U = u_opts[
    st.sidebar.selectbox("Categoría de Edificación (U):", list(u_opts.keys()))
]

st.sidebar.markdown("---")
st.sidebar.header("🍂 2. Parámetros de Sitio (Suelo)")

# Selección del tipo de suelo
suelo_sel = st.sidebar.selectbox(
    "Perfil de Suelo:",
    [
        "S0 (Roca del lugar)",
        "S1 (Roca o suelo muy rígido)",
        "S2 (Suelos intermedios)",
        "S3 (Suelos blandos)",
        "S4 (Conditions excepcionales)",
    ],
    index=2,
)

# Diccionario de rangos de la Tabla N° 4 y N° 5 (Z4, Z3, Z2, Z1)
tabla_4_S = {
    "S0 (Roca del lugar)": (0.80, 0.80, 0.80, 0.80),
    "S1 (Roca o suelo muy rígido)": (1.00, 1.00, 1.00, 1.00),
    "S2 (Suelos intermedios)": (
        (1.00, 1.10),
        (1.00, 1.15),
        (1.00, 1.30),
        (1.00, 1.30),
    ),
    "S3 (Suelos blandos)": (
        (1.10, 1.20),
        (1.15, 1.20),
        (1.30, 1.40),
        (1.30, 1.60),
    ),
    "S4 (Condiciones excepcionales)": (1.00, 1.30, 1.70, 2.40),
}

idx_zona = {0.45: 0, 0.35: 1, 0.25: 2, 0.10: 3}[Z]
S_base = 1.00
Tp_base, TL_base = 0.40, 2.50
msg_status = ""

# --- LÓGICA SIN ENSAYO GEOFÍSICO (VALORES MÁXIMOS POR DEFECTO EN S2 Y S3) ---
if suelo_sel in ["S0 (Roca del lugar)", "S1 (Roca o suelo muy rígido)", "S4 (Condiciones excepcionales)"]:
    S_base = (
        float(tabla_4_S[suelo_sel][idx_zona])
        if suelo_sel != "S4 (Condiciones excepcionales)"
        else float(np.max(tabla_4_S[suelo_sel][idx_zona]))
    )
    if suelo_sel == "S0 (Roca del lugar)":
        Tp_base, TL_base = 0.3, 3.0
    elif suelo_sel == "S1 (Roca o suelo muy rígido)":
        Tp_base, TL_base = 0.4, 2.5
    else:
        Tp_base, TL_base = 1.2, 1.6
    msg_status = "fijo"
else:
    # Para S2 y S3 se toma automáticamente el valor máximo del rango (Criterio Conservador)
    rango_S = tabla_4_S[suelo_sel][idx_zona]
    S_base = float(rango_S[1])
    
    if suelo_sel == "S2 (Suelos intermedios)":
        Tp_base, TL_base = 0.6, 2.0
    else:
        Tp_base, TL_base = 0.9, 1.6
    msg_status = "nota_pie"

# Parámetros finales (Editables en la barra lateral)
S = st.sidebar.number_input(
    "Factor de Suelo final (S):",
    min_value=0.5,
    max_value=2.5,
    value=float(S_base),
    step=0.01,
)
Tp = st.sidebar.number_input(
    "Período de plataforma (Tp) [s]:",
    min_value=0.05,
    max_value=3.0,
    value=Tp_base,
    step=0.05,
)
TL = st.sidebar.number_input(
    "Período de desplazamiento (TL) [s]:",
    min_value=0.5,
    max_value=10.0,
    value=TL_base,
    step=0.1,
)

# --- CONFIGURACIÓN DE SISTEMAS E IRREGULARIDADES POR EJE ---
st.subheader(
    "📐 Coeficientes de Reducción Sísmica Corregidos ($R = R_0 \\cdot I_a \\cdot I_p$)"
)
col_x, col_y = st.columns(2)

ia_opts = {
    "Regular (1.00)": 1.00,
    "Irregularidad de Rigidez - Piso Blando (0.75)": 0.75,
    "Irregularidad de Resistencia - Piso Débil (0.75)": 0.75,
    "Irregularidad Extrema de Rigidez (0.50)": 0.50,
    "Irregularidad Extrema de Resistencia (0.50)": 0.50,
    "Irregularidad de Masa o Peso (0.90)": 0.90,
    "Irregularidad Geometría Vertical (0.90)": 0.90,
    "Discontinuidad en Sistemas Resistentes (0.80)": 0.80,
    "Discontinuidad Extrema en Sistemas Resistentes (0.60)": 0.60,
}

ip_opts = {
    "Regular (1.00)": 1.00,
    "Irregularidad Torsional (0.75)": 0.75,
    "Irregularidad Torsional Extrema (0.60)": 0.60,
    "Esquinas Entrantes (0.90)": 0.90,
    "Discontinuidad del Diafragma (0.85)": 0.85,
}

sistemas_opts = {
    "Pórticos de Concreto Armado (R0 = 8)": 8,
    "Sistema Dual (R0 = 7)": 7,
    "Muros Estructurales / Placas (R0 = 6)": 6,
    "Albañilería Confinada (R0 = 3)": 3,
    "Muros de Ductilidad Limitada (R0 = 4)": 4,
    "Análisis Elástico Puro (R = 1)": 1,
}

with col_x:
    st.markdown("### **Eje X-X**")
    sis_x = st.selectbox("Sistema Estructural en X:", list(sistemas_opts.keys()))
    R0_x = sistemas_opts[sis_x]

    if R0_x > 1:
        Ia_x = ia_opts[
            st.selectbox(
                "Irregularidad en Altura (Ia) - X:",
                list(ia_opts.keys()),
                key="ia_x",
            )
        ]
        Ip_x = ip_opts[
            st.selectbox(
                "Irregularidad en Planta (Ip) - X:",
                list(ip_opts.keys()),
                key="ip_x",
            )
        ]
        Rx = R0_x * Ia_x * Ip_x
        st.info(
            f"**R efectivo en X:** {R0_x} × {Ia_x} × {Ip_x} = **{Rx:.3f}**"
        )
    else:
        Rx = 1.0
        st.info("**Análisis Elástico Puro (R = 1.0)**")

with col_y:
    st.markdown("### **Eje Y-Y**")
    sis_y = st.selectbox("Sistema Estructural en Y:", list(sistemas_opts.keys()))
    R0_y = sistemas_opts[sis_y]

    if R0_y > 1:
        Ia_y = ia_opts[
            st.selectbox(
                "Irregularidad en Altura (Ia) - Y:",
                list(ia_opts.keys()),
                key="ia_y",
            )
        ]
        Ip_y = ip_opts[
            st.selectbox(
                "Irregularidad en Planta (Ip) - Y:",
                list(ip_opts.keys()),
                key="ip_y",
            )
        ]
        Ry = R0_y * Ia_y * Ip_y
        st.info(
            f"**R efectivo en Y:** {R0_y} × {Ia_y} × {Ip_y} = **{Ry:.3f}**"
        )
    else:
        Ry = 1.0
        st.info("**Análisis Elástico Puro (R = 1.0)**")


# --- ALGORITMO DEL FACTOR C (Art. 18 - TABLA N° 6) ---
def calcular_sa(t, R):
    if t < 0.2 * Tp:
        if R > 1:
            C = 1.0 + 7.5 * (t / Tp)
        else:
            C = 2.5
    elif t <= Tp:
        C = 2.5
    elif t <= TL:
        C = 2.5 * (Tp / t)
    else:
        C = 2.5 * (Tp * TL) / (t**2)

    return (Z * U * C * S * g) / R


# --- GENERACIÓN DE DATOS CORREGIDA ---
t_vals = np.arange(0.0, 5.01, 0.01)
data = pd.DataFrame(
    {
        "Periodo": t_vals,
        "Sa_X": [calcular_sa(t, Rx) for t in t_vals],
        "Sa_Y": [calcular_sa(t, Ry) for t in t_vals],
    }
)

# --- VISUALIZACIÓN Y GRÁFICAS ---
st.markdown("---")
st.subheader("📈 Espectros Sísmicos de Diseño E.030-2026")

if msg_status == "nota_pie":
    st.warning(
        f"⚠️ **Criterio Conservador Automático (Sin Vs30):** Al no considerar el ensayo de ondas de corte, la norma exige adoptar los valores más desfavorables del intervalo ($S = {S:.2f}$, Tp = {Tp:.2f}s, TL = {TL:.2f}s) para proteger la estructura."
    )

g_col1, g_col2 = st.columns(2)


def graficar_eje(col, y_col, titulo, color_linea, R_act):
    with col:
        fig, ax = plt.subplots(figsize=(6, 3.8))
        ax.plot(
            data["Periodo"], data[y_col], color=color_linea, linewidth=2.5
        )
        ax.fill_between(
            data["Periodo"], data[y_col], color=color_linea, alpha=0.08
        )

        if R_act > 1:
            ax.axvline(
                x=0.2 * Tp, color="#7f8c8d", linestyle=":", label="0.2 Tp"
            )
        ax.axvline(x=Tp, color="#e74c3c", linestyle="--", label="Tp")
        ax.axvline(x=TL, color="#27ae60", linestyle="-.", label="TL")

        ax.set_title(titulo, fontsize=11, fontweight="bold")
        ax.set_xlabel("Periodo T (s)", fontsize=9)
        ax.set_ylabel(
            "Acel. Sa (m/s²)" if g > 1.0 else "Acel. Espectral Sa / g",
            fontsize=9,
        )
        ax.set_xlim(0.0, 5.0)
        ax.set_ylim(0.0, max(data[y_col]) * 1.15)

        ax.xaxis.set_major_locator(MultipleLocator(0.5))
        ax.xaxis.set_minor_locator(AutoMinorLocator(5))
        ax.grid(which="major", color="#b0b0b0", linestyle="-", linewidth=0.6)
        ax.grid(which="minor", color="#e0e0e0", linestyle=":", linewidth=0.5)
        ax.legend(fontsize=8)

        st.pyplot(fig)

        # EXPORTACIÓN CORREGIDA: Periodos limpios con 3 decimales consecutivos para ETABS
        lineas_formateadas = []
        for _, fila in data.iterrows():
            p_fmt = f"{fila['Periodo']:.3f}"
            sa_fmt = f"{fila[y_col]:.4f}"
            lineas_formateadas.append(f"{p_fmt}\t{sa_fmt}")
        
        txt_final = "\n".join(lineas_formateadas)

        st.download_button(
            label=f"📥 Descargar Espectro ETABS ({titulo})",
            data=txt_final,
            file_name=f"espectro_etabs_{y_col}.txt",
            mime="text/plain",
        )


graficar_eje(g_col1, "Sa_X", "Dirección X-X", "#D32F2F", Rx)
graficar_eje(g_col2, "Sa_Y", "Dirección Y-Y", "#1F77B4", Ry)
