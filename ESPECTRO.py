import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib.ticker import AutoMinorLocator, MultipleLocator

# Configuración de la interfaz de Streamlit
st.set_page_config(
    page_title="Espectro E.030-2026 Oficial", layout="wide"
)

# --- CABECERA ---
st.title("⚙️ Sistema de Espectros Sísmicos Parametrizado")
st.subheader("Norma Técnica E.030 - Edición Oficial 2026")
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

# Tabla de Zonas (Tabla N° 4)
z_opts = {
    "Zona 4 (Z = 0.45)": 0.45,
    "Zona 3 (Z = 0.35)": 0.35,
    "Zona 2 (Z = 0.25)": 0.25,
    "Zona 1 (Z = 0.10)": 0.10,
}
z_sel = st.sidebar.selectbox("Factor de Zona (Z):", list(z_opts.keys()))
Z = z_opts[z_sel]

# Tabla de Categorías y Factor U (Tabla N° 7 de image_ed88ca.png)
cat_sel = st.sidebar.selectbox(
    "Categoría de Edificación (Tabla N° 7):",
    [
        "Cat A1: Establecimientos de Salud (2do y 3er nivel)",
        "Cat A2: Edificaciones Esenciales (Colegios, Univ., Bomberos, etc.)",
        "Cat B: Edificaciones Importantes (Cines, Estadios, Centros Comerciales)",
        "Cat C: Edificaciones Comunes (Viviendas, Oficinas, Hoteles)",
    ],
)

# Lógica condicional dinámica según especifica la Nota al pie de la Tabla N° 7 (image_ed88ca.png)
if "Cat A1" in cat_sel:
    if Z in [0.45, 0.35]:  # Zonas 4 y 3 requieren aislamiento de base obligatorio
        U_default = 1.0
        st.sidebar.info(
            "ℹ️ **Nota de la norma:** Para Cat. A1 en Zonas 3 y 4 se requiere aislamiento sísmico en la base, por tanto **U = 1.0**."
        )
    else:  # Zonas 2 y 1
        U_default = 1.5
        st.sidebar.warning(
            "⚠️ **Nota de la norma:** Para Cat. A1 en Zonas 1 y 2, de no utilizar aislamiento el valor mínimo de **U es 1.5**."
        )
elif "Cat A2" in cat_sel:
    U_default = 1.5
elif "Cat B" in cat_sel:
    U_default = 1.3
else:  # Cat C
    U_default = 1.0

# Campo numérico del Factor U final
U = st.sidebar.number_input(
    "Factor de Uso o Importancia (U):",
    min_value=1.0,
    max_value=2.0,
    value=U_default,
    step=0.05,
)

st.sidebar.markdown("---")
st.sidebar.header("🍂 2. Parámetros de Sitio (Suelo E.030-2026)")

# Selección oficial de los perfiles de suelo según Tabla N° 2 y Tabla N° 3 (image_ed7d45.png)
suelo_sel = st.sidebar.selectbox(
    "Perfil de Suelo:",
    [
        "S0 (Roca)",
        "S1 (Suelos muy rígidos)",
        "S2 (Suelos rígidos)",
        "S3 (Suelos intermedios)",
        "S4 (Suelos blandos)",
    ],
    index=2,
)

# Diccionario oficial de factores S por zona
tabla_4_S = {
    "S0 (Roca)": (0.80, 0.80, 0.80, 0.80),
    "S1 (Suelos muy rígidos)": (1.00, 1.00, 1.00, 1.00),
    "S2 (Suelos rígidos)": ((1.00, 1.10), (1.00, 1.15), (1.00, 1.30), (1.00, 1.30)),
    "S3 (Suelos intermedios)": ((1.10, 1.20), (1.15, 1.20), (1.30, 1.40), (1.30, 1.60)),
    "S4 (Suelos blandos)": ("Análisis Especial", 1.30, 1.70, 2.40),
}

idx_zona = {0.45: 0, 0.35: 1, 0.25: 2, 0.10: 3}[Z]
valor_s_zona = tabla_4_S[suelo_sel][idx_zona]

msg_status = "fijo"

# Asignación estricta del peor escenario por falta de ensayo Vs30 (Nota * de la norma 2026)
if suelo_sel == "S0 (Roca)":
    S_base = float(valor_s_zona)
    Tp_base, TL_base = 0.30, 3.00
elif suelo_sel == "S1 (Suelos muy rígidos)":
    S_base = float(valor_s_zona)
    Tp_base, TL_base = 0.40, 2.50
elif suelo_sel == "S4 (Suelos blandos)":
    if valor_s_zona == "Análisis Especial":
        st.sidebar.error("⚠️ S4 en Zona 4 requiere un análisis de respuesta de sitio obligatorio.")
        S_base, Tp_base, TL_base = 1.20, 1.20, 1.60
    else:
        S_base = float(valor_s_zona)
        Tp_base, TL_base = 1.20, 1.60
else:
    # Criterio normativo sin Vs30 para S2 y S3: Límite superior del intervalo
    S_base = float(valor_s_zona[1])
    if suelo_sel == "S2 (Suelos rígidos)":
        Tp_base, TL_base = 0.60, 2.00
    else:  # S3 (Suelos intermedios)
        Tp_base, TL_base = 0.90, 1.60
    msg_status = "nota_pie"

S = st.sidebar.number_input(
    "Factor de Suelo final (S):", min_value=0.5, max_value=3.0, value=S_base, step=0.01
)
Tp = st.sidebar.number_input(
    "Período de plataforma (Tp) [s]:", min_value=0.05, max_value=4.0, value=Tp_base, step=0.05
)
TL = st.sidebar.number_input(
    "Período de desplazamiento (TL) [s]:", min_value=0.5, max_value=12.0, value=TL_base, step=0.1
)

# --- CONFIGURACIÓN DE SISTEMAS E IRREGULARIDADES POR EJE ---
st.subheader("📐 Coeficientes de Reducción Sísmica ($R = R_0 \\cdot I_a \\cdot I_p$)")
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

# Tabla N° 10 Oficial actualizada al 100% (image_ed8984.png)
sistemas_opts = {
    # Concreto Armado
    "Concreto Armado: Pórticos (R0 = 8)": 8,
    "Concreto Armado: Dual (R0 = 7)": 7,
    "Concreto Armado: De muros estructurales (R0 = 6)": 6,
    "Concreto Armado: Muros de ductilidad limitada (R0 = 3.5)": 3.5,  # Modificado de 4 a 3.5 según la tabla
    # Albañilería
    "Albañilería Armada o Confinada (R0 = 3)": 3,
    # Acero Estructural
    "Acero: Pórticos Especiales Resistentes a Momentos (SMF) (R0 = 8)": 8,
    "Acero: Pórticos Excentricamente Arriostrados (EBF) (R0 = 8)": 8,
    "Acero: Pórticos Especiales Concéntricamente Arriostrados (SCBF) (R0 = 7)": 7,
    "Acero: Pórticos Intermedios Resistentes a Momentos (IMF) (R0 = 5)": 5,
    "Acero: Pórticos Ordinarios Resistentes a Momentos (OMF) (R0 = 4)": 4,
    "Acero: Pórticos Ordinarios Concéntricamente Arriostrados (OCBF) (R0 = 4)": 4,
    # Otros
    "Madera (R0 = 7)": 7,
    "Estructuras tipo péndulo invertido (Art. 22.3) (R0 = 2.5)": 2.5,
    "Análisis Elástico Puro (R = 1.0)": 1,
}

with col_x:
    st.markdown("### **Eje X-X**")
    sis_x = st.selectbox("Sistema Estructural en X:", list(sistemas_opts.keys()))
    R0_x = sistemas_opts[sis_x]

    if R0_x > 1:
        Ia_x = ia_opts[st.selectbox("Irregularidad en Altura (Ia) - X:", list(ia_opts.keys()), key="ia_x")]
        Ip_x = ip_opts[st.selectbox("Irregularidad en Planta (Ip) - X:", list(ip_opts.keys()), key="ip_x")]
        Rx = R0_x * Ia_x * Ip_x
        st.info(f"**R efectivo en X:** {R0_x} × {Ia_x} × {Ip_x} = **{Rx:.3f}**")
    else:
        Rx = 1.0
        st.info("**Análisis Elástico Puro (R = 1.0)**")

with col_y:
    st.markdown("### **Eje Y-Y**")
    sis_y = st.selectbox("Sistema Estructural en Y:", list(sistemas_opts.keys()))
    R0_y = sistemas_opts[sis_y]

    if R0_y > 1:
        Ia_y = ia_opts[st.selectbox("Irregularidad en Altura (Ia) - Y:", list(ia_opts.keys()), key="ia_y")]
        Ip_y = ip_opts[st.selectbox("Irregularidad en Planta (Ip) - Y:", list(ip_opts.keys()), key="ip_y")]
        Ry = R0_y * Ia_y * Ip_y
        st.info(f"**R efectivo en Y:** {R0_y} × {Ia_y} × {Ip_y} = **{Ry:.3f}**")
    else:
        Ry = 1.0
        st.info("**Análisis Elástico Puro (R = 1.0)**")


# --- ALGORITMO OFICIAL DEL FACTOR C (Art. 18.3 - MESETA CONSTANTE EN C = 2.5 DESDE T = 0) ---
def calcular_sa(t, R):
    # Corrección estricta: C = 2.5 estable en todo el rango inicial de la meseta (image_ed7d9f.png)
    if t <= Tp:
        C = 2.5
    elif t <= TL:
        C = 2.5 * (Tp / t)
    else:
        C = 2.5 * (Tp * TL) / (t**2)

    return (Z * U * C * S * g) / R


# --- GENERACIÓN DE CURVAS ---
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
        f"⚠️ **Nota (*):** Al no disponer de información relativa a la velocidad de ondas de corte ($V_{{s30}}$), se adopta el límite superior del intervalo ($S = {S:.2f}$, $T_P = {Tp:.2f}$ s, $T_L = {TL:.2f}$ s) según el Art. 17."
    )

g_col1, g_col2 = st.columns(2)


def graficar_eje(col, y_col, titulo, color_linea):
    with col:
        fig, ax = plt.subplots(figsize=(6, 3.8))
        ax.plot(data["Periodo"], data[y_col], color=color_linea, linewidth=2.5)
        ax.fill_between(data["Periodo"], data[y_col], color=color_linea, alpha=0.08)

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

        # Formato de exportación directa a ETABS
        lineas_formateadas = [f"{fila['Periodo']:.3f}\t{fila[y_col]:.4f}" for _, fila in data.iterrows()]
        txt_final = "\n".join(lineas_formateadas)

        st.download_button(
            label=f"📥 Descargar Espectro ETABS ({titulo})",
            data=txt_final,
            file_name=f"espectro_e030_2026_{y_col}.txt",
            mime="text/plain",
        )


graficar_eje(g_col1, "Sa_X", "Dirección X-X", "#D32F2F")
graficar_eje(g_col2, "Sa_Y", "Dirección Y-Y", "#1F77B4")
