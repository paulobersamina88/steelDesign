
import io
import math
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="AISC Steel Checker PRO", layout="wide")

E_DEFAULT = 200000.0  # MPa
PHI = {
    "tension_yield": 0.90,
    "tension_rupture": 0.75,
    "compression": 0.90,
    "flexure": 0.90,
    "shear": 0.90,
}
OMEGA = {
    "tension_yield": 1.67,
    "tension_rupture": 2.00,
    "compression": 1.67,
    "flexure": 1.67,
    "shear": 1.50,
}


@st.cache_data
def load_default_shapes():
    # Expanded starter catalog; user can replace with a fuller office library via CSV upload.
    data = [
        # W sections
        {"shape":"W200x26","family":"W","A_mm2":3310,"d_mm":203,"bf_mm":133,"tw_mm":5.8,"tf_mm":8.5,"Ix_mm4":244e6,"Iy_mm4":34.2e6,"Zx_mm3":270e3,"Zy_mm3":64e3,"Sx_mm3":240e3,"Sy_mm3":51e3,"rx_mm":86.0,"ry_mm":32.0,"J_mm4":140e3,"Cw_mm6":3.3e12},
        {"shape":"W250x33","family":"W","A_mm2":4210,"d_mm":251,"bf_mm":146,"tw_mm":6.1,"tf_mm":9.7,"Ix_mm4":458e6,"Iy_mm4":50.8e6,"Zx_mm3":406e3,"Zy_mm3":82e3,"Sx_mm3":365e3,"Sy_mm3":70e3,"rx_mm":104.0,"ry_mm":34.7,"J_mm4":240e3,"Cw_mm6":7.8e12},
        {"shape":"W310x39","family":"W","A_mm2":4970,"d_mm":303,"bf_mm":165,"tw_mm":6.1,"tf_mm":10.2,"Ix_mm4":821e6,"Iy_mm4":85.6e6,"Zx_mm3":596e3,"Zy_mm3":121e3,"Sx_mm3":542e3,"Sy_mm3":104e3,"rx_mm":128.0,"ry_mm":41.5,"J_mm4":350e3,"Cw_mm6":20.0e12},
        {"shape":"W360x44","family":"W","A_mm2":5600,"d_mm":349,"bf_mm":171,"tw_mm":6.9,"tf_mm":9.1,"Ix_mm4":1160e6,"Iy_mm4":95e6,"Zx_mm3":737e3,"Zy_mm3":129e3,"Sx_mm3":664e3,"Sy_mm3":111e3,"rx_mm":144.0,"ry_mm":41.2,"J_mm4":440e3,"Cw_mm6":28.0e12},
        {"shape":"W360x51","family":"W","A_mm2":6500,"d_mm":360,"bf_mm":171,"tw_mm":7.1,"tf_mm":11.5,"Ix_mm4":1370e6,"Iy_mm4":105e6,"Zx_mm3":868e3,"Zy_mm3":140e3,"Sx_mm3":761e3,"Sy_mm3":123e3,"rx_mm":145.0,"ry_mm":40.2,"J_mm4":520e3,"Cw_mm6":34.0e12},
        {"shape":"W410x60","family":"W","A_mm2":7640,"d_mm":410,"bf_mm":178,"tw_mm":7.6,"tf_mm":12.2,"Ix_mm4":1970e6,"Iy_mm4":126e6,"Zx_mm3":1080e3,"Zy_mm3":161e3,"Sx_mm3":961e3,"Sy_mm3":141e3,"rx_mm":160.0,"ry_mm":40.6,"J_mm4":680e3,"Cw_mm6":50.0e12},
        {"shape":"W460x68","family":"W","A_mm2":8660,"d_mm":455,"bf_mm":190,"tw_mm":8.1,"tf_mm":13.0,"Ix_mm4":2870e6,"Iy_mm4":163e6,"Zx_mm3":1330e3,"Zy_mm3":193e3,"Sx_mm3":1260e3,"Sy_mm3":171e3,"rx_mm":182.0,"ry_mm":43.4,"J_mm4":890e3,"Cw_mm6":79.0e12},
        {"shape":"W530x74","family":"W","A_mm2":9440,"d_mm":525,"bf_mm":209,"tw_mm":9.1,"tf_mm":14.1,"Ix_mm4":4070e6,"Iy_mm4":212e6,"Zx_mm3":1740e3,"Zy_mm3":237e3,"Sx_mm3":1550e3,"Sy_mm3":203e3,"rx_mm":208.0,"ry_mm":47.3,"J_mm4":1200e3,"Cw_mm6":132.0e12},
        {"shape":"W610x82","family":"W","A_mm2":10450,"d_mm":602,"bf_mm":228,"tw_mm":10.2,"tf_mm":14.8,"Ix_mm4":5650e6,"Iy_mm4":282e6,"Zx_mm3":2220e3,"Zy_mm3":287e3,"Sx_mm3":1880e3,"Sy_mm3":247e3,"rx_mm":232.0,"ry_mm":52.0,"J_mm4":1700e3,"Cw_mm6":225.0e12},

        # HSS Rectangular / square
        {"shape":"HSS152x102x6.4","family":"HSS_RECT","A_mm2":2980,"h_mm":152,"b_mm":102,"t_mm":6.4,"Ix_mm4":10.7e6,"Iy_mm4":5.3e6,"Zx_mm3":154e3,"Zy_mm3":105e3,"Sx_mm3":141e3,"Sy_mm3":104e3,"rx_mm":59.9,"ry_mm":42.1,"J_mm4":17.0e6},
        {"shape":"HSS203x102x8.0","family":"HSS_RECT","A_mm2":4350,"h_mm":203,"b_mm":102,"t_mm":8.0,"Ix_mm4":24.0e6,"Iy_mm4":7.8e6,"Zx_mm3":271e3,"Zy_mm3":136e3,"Sx_mm3":236e3,"Sy_mm3":153e3,"rx_mm":74.3,"ry_mm":42.3,"J_mm4":32.0e6},
        {"shape":"HSS203x203x9.5","family":"HSS_RECT","A_mm2":6930,"h_mm":203,"b_mm":203,"t_mm":9.5,"Ix_mm4":41.8e6,"Iy_mm4":41.8e6,"Zx_mm3":462e3,"Zy_mm3":462e3,"Sx_mm3":412e3,"Sy_mm3":412e3,"rx_mm":77.7,"ry_mm":77.7,"J_mm4":67.0e6},
        {"shape":"HSS254x254x9.5","family":"HSS_RECT","A_mm2":8830,"h_mm":254,"b_mm":254,"t_mm":9.5,"Ix_mm4":84.6e6,"Iy_mm4":84.6e6,"Zx_mm3":751e3,"Zy_mm3":751e3,"Sx_mm3":666e3,"Sy_mm3":666e3,"rx_mm":97.9,"ry_mm":97.9,"J_mm4":124.0e6},
        {"shape":"HSS305x203x9.5","family":"HSS_RECT","A_mm2":9540,"h_mm":305,"b_mm":203,"t_mm":9.5,"Ix_mm4":109e6,"Iy_mm4":58e6,"Zx_mm3":859e3,"Zy_mm3":569e3,"Sx_mm3":715e3,"Sy_mm3":476e3,"rx_mm":106.9,"ry_mm":77.9,"J_mm4":151.0e6},

        # Round HSS / tubular
        {"shape":"HSS114.3x6.0","family":"HSS_ROUND","A_mm2":2040,"D_mm":114.3,"t_mm":6.0,"Ix_mm4":3.05e6,"Iy_mm4":3.05e6,"Zx_mm3":66e3,"Zy_mm3":66e3,"Sx_mm3":53e3,"Sy_mm3":53e3,"rx_mm":38.7,"ry_mm":38.7,"J_mm4":6.1e6},
        {"shape":"HSS168.3x6.4","family":"HSS_ROUND","A_mm2":3260,"D_mm":168.3,"t_mm":6.4,"Ix_mm4":10.4e6,"Iy_mm4":10.4e6,"Zx_mm3":161e3,"Zy_mm3":161e3,"Sx_mm3":124e3,"Sy_mm3":124e3,"rx_mm":56.4,"ry_mm":56.4,"J_mm4":20.8e6},
        {"shape":"HSS219.1x8.0","family":"HSS_ROUND","A_mm2":5300,"D_mm":219.1,"t_mm":8.0,"Ix_mm4":28.6e6,"Iy_mm4":28.6e6,"Zx_mm3":327e3,"Zy_mm3":327e3,"Sx_mm3":261e3,"Sy_mm3":261e3,"rx_mm":73.4,"ry_mm":73.4,"J_mm4":57.2e6},
        {"shape":"HSS273.0x9.3","family":"HSS_ROUND","A_mm2":7710,"D_mm":273.0,"t_mm":9.3,"Ix_mm4":63.0e6,"Iy_mm4":63.0e6,"Zx_mm3":529e3,"Zy_mm3":529e3,"Sx_mm3":462e3,"Sy_mm3":462e3,"rx_mm":90.4,"ry_mm":90.4,"J_mm4":126.0e6},
        {"shape":"HSS323.9x9.5","family":"HSS_ROUND","A_mm2":9380,"D_mm":323.9,"t_mm":9.5,"Ix_mm4":103e6,"Iy_mm4":103e6,"Zx_mm3":735e3,"Zy_mm3":735e3,"Sx_mm3":636e3,"Sy_mm3":636e3,"rx_mm":104.8,"ry_mm":104.8,"J_mm4":206e6},

        # Pipe
        {"shape":"PIPE114.3x6.0","family":"PIPE","A_mm2":2040,"D_mm":114.3,"t_mm":6.0,"Ix_mm4":3.05e6,"Iy_mm4":3.05e6,"Zx_mm3":66e3,"Zy_mm3":66e3,"Sx_mm3":53e3,"Sy_mm3":53e3,"rx_mm":38.7,"ry_mm":38.7,"J_mm4":6.1e6},
        {"shape":"PIPE168.3x7.1","family":"PIPE","A_mm2":3590,"D_mm":168.3,"t_mm":7.1,"Ix_mm4":11.2e6,"Iy_mm4":11.2e6,"Zx_mm3":173e3,"Zy_mm3":173e3,"Sx_mm3":133e3,"Sy_mm3":133e3,"rx_mm":55.9,"ry_mm":55.9,"J_mm4":22.4e6},
        {"shape":"PIPE219.1x8.2","family":"PIPE","A_mm2":5420,"D_mm":219.1,"t_mm":8.2,"Ix_mm4":28.8e6,"Iy_mm4":28.8e6,"Zx_mm3":329e3,"Zy_mm3":329e3,"Sx_mm3":263e3,"Sy_mm3":263e3,"rx_mm":72.9,"ry_mm":72.9,"J_mm4":57.6e6},
        {"shape":"PIPE273.1x9.3","family":"PIPE","A_mm2":7720,"D_mm":273.1,"t_mm":9.3,"Ix_mm4":63.3e6,"Iy_mm4":63.3e6,"Zx_mm3":532e3,"Zy_mm3":532e3,"Sx_mm3":464e3,"Sy_mm3":464e3,"rx_mm":90.5,"ry_mm":90.5,"J_mm4":126.6e6},
    ]
    return pd.DataFrame(data)


def phi_or_omega_strength(nominal, method, check_key):
    if method == "LRFD":
        return PHI[check_key] * nominal
    return nominal / OMEGA[check_key]


def safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default


def fmt(v, nd=2):
    if isinstance(v, str):
        return v
    try:
        if math.isnan(v) or math.isinf(v):
            return "-"
    except Exception:
        pass
    return f"{float(v):,.{nd}f}"


def critical_stress_compression(Fy, slenderness, E=E_DEFAULT):
    if slenderness <= 0:
        return Fy
    Fe = (math.pi ** 2 * E) / (slenderness ** 2)
    lambdac = math.sqrt(Fy / Fe)
    if lambdac <= 1.5:
        Fcr = (0.658 ** (lambdac ** 2)) * Fy
    else:
        Fcr = 0.877 * Fe
    return min(Fcr, Fy), Fe, lambdac


def tension_strength(A_g, A_e, Fy, Fu, method):
    nominal_yield = Fy * A_g / 1000.0
    nominal_rupture = Fu * A_e / 1000.0
    design_yield = phi_or_omega_strength(nominal_yield, method, "tension_yield")
    design_rupture = phi_or_omega_strength(nominal_rupture, method, "tension_rupture")
    return min(design_yield, design_rupture), design_yield, design_rupture, nominal_yield, nominal_rupture


def compression_strength(A_g, kx, ky, Lx, Ly, rx, ry, Fy, E, method):
    sx = kx * Lx / max(rx, 1e-9)
    sy = ky * Ly / max(ry, 1e-9)
    s = max(sx, sy)
    Fcr, Fe, lambdac = critical_stress_compression(Fy, s, E)
    nominal = Fcr * A_g / 1000.0
    design = phi_or_omega_strength(nominal, method, "compression")
    return design, nominal, sx, sy, s, Fcr, Fe, lambdac


def get_shear_area(shape):
    fam = shape["family"]
    if fam == "W":
        return shape.get("d_mm", 0.0) * shape.get("tw_mm", 0.0)
    if fam == "HSS_RECT":
        return 2.0 * shape.get("h_mm", 0.0) * shape.get("t_mm", 0.0)
    if fam in ("HSS_ROUND", "PIPE"):
        return 0.5 * shape.get("A_mm2", 0.0)
    return 0.0


def shear_strength(shape, Fy, method):
    Aw = get_shear_area(shape)
    nominal = 0.6 * Fy * Aw / 1000.0
    design = phi_or_omega_strength(nominal, method, "shear")
    return design, nominal, Aw


def flexural_strength(shape, Fy, method, axis="x", Lb_mm=0.0, Cb=1.0, consider_ltb=True):
    fam = shape["family"]
    Z = safe_float(shape.get("Zx_mm3" if axis == "x" else "Zy_mm3", 0.0))
    S = safe_float(shape.get("Sx_mm3" if axis == "x" else "Sy_mm3", Z), Z)
    ry = safe_float(shape.get("ry_mm", 1.0))
    rts = max(ry * 1.1, 1.0)

    Mp_nom = Fy * Z / 1e6
    note = "Plastic moment used."

    Mn_nom = Mp_nom
    if fam == "W" and axis == "x" and consider_ltb and Lb_mm > 0:
        Lp = 1.76 * rts * math.sqrt(E_DEFAULT / Fy)
        Lr = 1.95 * rts * E_DEFAULT / (0.7 * Fy) * math.sqrt(max(1.0, 1.0))
        if Lb_mm <= Lp:
            Mn_nom = Mp_nom
            note = f"LTB not governing since Lb={fmt(Lb_mm)} mm <= Lp={fmt(Lp)} mm."
        elif Lb_mm <= Lr:
            My_nom = Fy * S / 1e6
            Mn_nom = min(Mp_nom, Cb * (Mp_nom - (Mp_nom - 0.7 * My_nom) * (Lb_mm - Lp) / max(Lr - Lp, 1e-9)))
            note = f"Inelastic LTB screening used with Cb={fmt(Cb)}."
        else:
            Fcr = Cb * (math.pi ** 2) * E_DEFAULT / ((Lb_mm / max(rts, 1e-9)) ** 2)
            Mn_nom = min(Mp_nom, Fcr * S / 1e6)
            note = f"Elastic LTB screening used with Cb={fmt(Cb)}."
    else:
        if axis == "y":
            note = "Minor-axis plastic flexure used."
        elif fam != "W":
            note = "Closed-section plastic flexure used."

    design = phi_or_omega_strength(Mn_nom, method, "flexure")
    return design, Mn_nom, Mp_nom, note


def classify_section(shape, Fy, seismic=False):
    rootFy = math.sqrt(Fy)
    fam = shape["family"]
    rows = []

    if fam == "W":
        bf = shape.get("bf_mm", 0.0)
        tf = shape.get("tf_mm", 0.0)
        tw = shape.get("tw_mm", 0.0)
        d = shape.get("d_mm", 0.0)
        lam_f = (bf / 2.0) / max(tf, 1e-9)
        lam_w = (d - 2 * tf) / max(tw, 1e-9)
        compact_f = 0.38 * math.sqrt(E_DEFAULT) / rootFy
        compact_w = 3.76 * math.sqrt(E_DEFAULT) / rootFy
        seismic_f = 0.30 * math.sqrt(E_DEFAULT) / rootFy
        seismic_w = 2.45 * math.sqrt(E_DEFAULT) / rootFy
        lim_f = seismic_f if seismic else compact_f
        lim_w = seismic_w if seismic else compact_w
        rows += [
            {"Element":"Flange slenderness", "Lambda":lam_f, "Limit":lim_f, "Status":"OK" if lam_f <= lim_f else "NG"},
            {"Element":"Web slenderness", "Lambda":lam_w, "Limit":lim_w, "Status":"OK" if lam_w <= lim_w else "NG"},
        ]

    elif fam == "HSS_RECT":
        b = shape.get("b_mm", 0.0)
        h = shape.get("h_mm", 0.0)
        t = shape.get("t_mm", 0.0)
        lam_b = (b - 3*t) / max(t, 1e-9)
        lam_h = (h - 3*t) / max(t, 1e-9)
        compact = 1.40 * math.sqrt(E_DEFAULT) / rootFy
        seismic_lim = 1.12 * math.sqrt(E_DEFAULT) / rootFy
        lim = seismic_lim if seismic else compact
        rows += [
            {"Element":"Wall b/t", "Lambda":lam_b, "Limit":lim, "Status":"OK" if lam_b <= lim else "NG"},
            {"Element":"Wall h/t", "Lambda":lam_h, "Limit":lim, "Status":"OK" if lam_h <= lim else "NG"},
        ]

    elif fam in ("HSS_ROUND", "PIPE"):
        D = shape.get("D_mm", 0.0)
        t = shape.get("t_mm", 0.0)
        lam = D / max(t, 1e-9)
        compact = 0.11 * E_DEFAULT / Fy
        seismic_lim = 0.07 * E_DEFAULT / Fy
        lim = seismic_lim if seismic else compact
        rows += [
            {"Element":"D/t", "Lambda":lam, "Limit":lim, "Status":"OK" if lam <= lim else "NG"},
        ]

    df = pd.DataFrame(rows)
    return df, bool((df["Status"] == "OK").all()) if not df.empty else True


def axial_flexure_interaction(ir_a, ir_mx, ir_my):
    if ir_a >= 0.2:
        return ir_a + (8/9) * (ir_mx + ir_my)
    return ir_a / 2.0 + ir_mx + ir_my


def demand_capacity_ratio(demand, capacity):
    if capacity <= 0:
        return float("inf")
    return abs(demand) / capacity


def build_summary_download(df, filename):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="results")
    st.download_button(
        "Download Excel results",
        data=buffer.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


st.title("AISC Steel Beam / Column Checker PRO")
st.caption("Preliminary AISC 360 member checker with optional high-seismic screening and conceptual Zone 4 / NSCP-oriented workflow.")

with st.sidebar:
    st.header("Global Controls")
    method = st.selectbox("Design method", ["LRFD", "ASD"])
    code_basis = st.selectbox("Specification basis", ["AISC 360-22", "AISC 360-16"])
    seismic_mode = st.toggle("Enable seismic / Zone 4 screening", value=True)
    seismic_system = st.selectbox("System", ["SMF", "IMF", "OMF", "SCBF", "OCBF", "BRBF", "EBF", "Other"])
    shape_upload = st.file_uploader("Upload office shape CSV", type=["csv"])
    st.markdown("### Conceptual NSCP / Seismic Inputs")
    Ss = st.number_input("Ss", value=1.20)
    S1 = st.number_input("S1", value=0.60)
    R = st.number_input("Response modification factor R", value=8.0)
    Ie = st.number_input("Importance factor Ie", value=1.0)
    Cd = st.number_input("Deflection amplification Cd", value=5.5)
    st.info("These seismic values are used only for screening notes and drift prompts in this PRO starter.")

if shape_upload is not None:
    shapes = pd.read_csv(shape_upload)
else:
    shapes = load_default_shapes()

tabs = st.tabs(["Dashboard", "Single Member", "Batch Checker", "Seismic Screen", "Section Library", "User Guide"])

with tabs[0]:
    st.subheader("PRO Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Loaded sections", len(shapes))
    c2.metric("Families", shapes["family"].nunique())
    c3.metric("Method", method)
    c4.metric("Seismic screen", "ON" if seismic_mode else "OFF")

    fam_count = shapes.groupby("family").size().reset_index(name="count")
    st.bar_chart(fam_count.set_index("family"))

    st.markdown("### What this PRO version adds")
    st.write("- LRFD / ASD switch")
    st.write("- Better W-shape flexural screening with simple LTB logic")
    st.write("- Seismic slenderness screening")
    st.write("- Strong-column / weak-beam panel")
    st.write("- Batch member checker")
    st.write("- Drift prompt panel for conceptual zone-4 workflow")
    st.write("- Downloadable Excel results")

with tabs[1]:
    st.subheader("Single Member Design Check")

    g1, g2, g3, g4 = st.columns(4)
    family = g1.selectbox("Section family", sorted(shapes["family"].unique()))
    family_df = shapes[shapes["family"] == family].copy()
    shape_name = g2.selectbox("Section", family_df["shape"].tolist())
    shape = family_df[family_df["shape"] == shape_name].iloc[0].to_dict()
    member_role = g3.selectbox("Role", ["Beam", "Column", "Brace", "Beam-Column"])
    axis = g4.selectbox("Primary axis", ["x", "y"])

    m1, m2, m3, m4 = st.columns(4)
    Fy = m1.number_input("Fy (MPa)", value=345.0)
    Fu = m2.number_input("Fu (MPa)", value=450.0)
    E = m3.number_input("E (MPa)", value=E_DEFAULT)
    ae_ratio = m4.number_input("Ae / Ag", min_value=0.10, max_value=1.00, value=0.85, step=0.01)

    st.markdown("### Unbraced Length / Effective Length")
    l1, l2, l3, l4, l5 = st.columns(5)
    Lx = l1.number_input("Lx (mm)", value=3000.0)
    Ly = l2.number_input("Ly (mm)", value=3000.0)
    Lb = l3.number_input("Lb for major flexure (mm)", value=3000.0)
    Kx = l4.number_input("Kx", value=1.0)
    Ky = l5.number_input("Ky", value=1.0)
    Cb = st.number_input("Cb", value=1.0)

    st.markdown("### Factored / Service Demands")
    d1, d2, d3, d4 = st.columns(4)
    Pu = d1.number_input("Pu: tension(+), compression(-) kN", value=-400.0)
    Mux = d2.number_input("Mux (kN-m)", value=80.0)
    Muy = d3.number_input("Muy (kN-m)", value=10.0)
    Vu = d4.number_input("Vu (kN)", value=120.0)

    st.markdown("### Optional Project-level Checks")
    k1, k2, k3 = st.columns(3)
    clear_span = k1.number_input("Beam clear span for deflection note (mm)", value=6000.0)
    delta_service = k2.number_input("Estimated service deflection (mm)", value=8.0)
    story_drift = k3.number_input("Estimated elastic story drift ratio", value=0.008)

    A = safe_float(shape.get("A_mm2", 0.0))
    rx = safe_float(shape.get("rx_mm", 0.0))
    ry = safe_float(shape.get("ry_mm", 0.0))
    Ae = A * ae_ratio

    sec_df, sec_ok = classify_section(shape, Fy, seismic=seismic_mode)
    T_design, T_yield, T_rupture, Tn_y, Tn_r = tension_strength(A, Ae, Fy, Fu, method)
    C_design, C_nom, sx, sy, smax, Fcr, Fe, lambdac = compression_strength(A, Kx, Ky, Lx, Ly, rx, ry, Fy, E, method)
    V_design, V_nom, Aw = shear_strength(shape, Fy, method)
    Mx_design, Mx_nom, Mpx, note_x = flexural_strength(shape, Fy, method, "x", Lb_mm=Lb, Cb=Cb, consider_ltb=True)
    My_design, My_nom, Mpy, note_y = flexural_strength(shape, Fy, method, "y", Lb_mm=Ly, Cb=1.0, consider_ltb=False)

    axial_capacity = T_design if Pu >= 0 else C_design
    axial_mode = "Tension" if Pu >= 0 else "Compression"

    ir_a = demand_capacity_ratio(Pu, axial_capacity)
    ir_mx = demand_capacity_ratio(Mux, Mx_design)
    ir_my = demand_capacity_ratio(Muy, My_design)
    ir_v = demand_capacity_ratio(Vu, V_design)
    ir_int = axial_flexure_interaction(ir_a, ir_mx, ir_my)

    defl_ratio = clear_span / max(delta_service, 1e-9)
    amplified_drift = Cd * story_drift / max(Ie, 1e-9)

    top = st.columns(6)
    top[0].metric("Axial mode", axial_mode)
    top[1].metric("Axial IR", fmt(ir_a, 3))
    top[2].metric("Mx IR", fmt(ir_mx, 3))
    top[3].metric("My IR", fmt(ir_my, 3))
    top[4].metric("V IR", fmt(ir_v, 3))
    top[5].metric("Interaction IR", fmt(ir_int, 3))

    r1, r2 = st.columns([1.3, 1.0])

    with r1:
        result = pd.DataFrame([
            {"Check":"Axial", "Demand":abs(Pu), "Capacity":axial_capacity, "IR":ir_a, "Status":"OK" if ir_a <= 1 else "NG"},
            {"Check":"Major flexure", "Demand":abs(Mux), "Capacity":Mx_design, "IR":ir_mx, "Status":"OK" if ir_mx <= 1 else "NG"},
            {"Check":"Minor flexure", "Demand":abs(Muy), "Capacity":My_design, "IR":ir_my, "Status":"OK" if ir_my <= 1 else "NG"},
            {"Check":"Shear", "Demand":abs(Vu), "Capacity":V_design, "IR":ir_v, "Status":"OK" if ir_v <= 1 else "NG"},
            {"Check":"Combined interaction", "Demand":ir_int, "Capacity":1.0, "IR":ir_int, "Status":"OK" if ir_int <= 1 else "NG"},
        ])
        st.dataframe(result, use_container_width=True)
        build_summary_download(result, f"{shape_name}_pro_single_check.xlsx")

        st.markdown("### Capacity Breakdown")
        cap = pd.DataFrame([
            {"Item":"Tension yield", "Nominal":Tn_y, "Design/Allowable":T_yield},
            {"Item":"Tension rupture", "Nominal":Tn_r, "Design/Allowable":T_rupture},
            {"Item":"Compression", "Nominal":C_nom, "Design/Allowable":C_design},
            {"Item":"Major flexure", "Nominal":Mx_nom, "Design/Allowable":Mx_design},
            {"Item":"Minor flexure", "Nominal":My_nom, "Design/Allowable":My_design},
            {"Item":"Shear", "Nominal":V_nom, "Design/Allowable":V_design},
        ])
        st.dataframe(cap, use_container_width=True)

    with r2:
        st.markdown("### Section Slenderness")
        st.dataframe(sec_df, use_container_width=True)

        st.markdown("### Detailed Notes")
        st.write(f"- KL/r major = {fmt(sx)}")
        st.write(f"- KL/r minor = {fmt(sy)}")
        st.write(f"- Governing KL/r = {fmt(smax)}")
        st.write(f"- Fe = {fmt(Fe)} MPa")
        st.write(f"- λc = {fmt(lambdac, 3)}")
        st.write(f"- Fcr = {fmt(Fcr)} MPa")
        st.write(f"- Shear area used = {fmt(Aw)} mm²")
        st.write(f"- Major flexure note: {note_x}")
        st.write(f"- Minor flexure note: {note_y}")

        st.markdown("### Serviceability / Seismic Prompts")
        st.write(f"- Deflection ratio estimate = L / Δ = {fmt(defl_ratio, 1)}")
        st.write(f"- Amplified story drift ratio = Cd × Δe / Ie = {fmt(amplified_drift, 4)}")
        if defl_ratio >= 360:
            st.success("Beam serviceability screen looks favorable against an L/360-type benchmark.")
        else:
            st.warning("Beam serviceability screen may be soft against an L/360-type benchmark.")
        if seismic_mode:
            if amplified_drift <= 0.02:
                st.success("Conceptual drift screen is within a typical 2% limit.")
            else:
                st.error("Conceptual drift screen exceeds a typical 2% limit.")

        if seismic_mode and seismic_system in ["SMF", "IMF", "OMF"] and member_role in ["Beam", "Beam-Column", "Column"]:
            st.markdown("### Strong-Column / Weak-Beam Screen")
            j1, j2 = st.columns(2)
            mpr = j1.number_input("ΣMpr beams at joint (kN-m)", value=250.0)
            mpc = j2.number_input("ΣMpc columns at joint (kN-m)", value=320.0)
            ratio = mpc / max(mpr, 1e-9)
            st.metric("ΣMpc / ΣMpr", fmt(ratio, 3))
            if ratio > 1.0:
                st.success("Pass on conceptual strong-column / weak-beam screen.")
            else:
                st.error("Fail on conceptual strong-column / weak-beam screen.")

with tabs[2]:
    st.subheader("Batch Checker")
    st.write("Upload a CSV with multiple members for rapid office screening.")
    st.code(
        "member_id,shape,Pu_kN,Mux_kNm,Muy_kNm,Vu_kN,Lx_mm,Ly_mm,Lb_mm,Kx,Ky,Fy_MPa,Fu_MPa,Ae_ratio",
        language="text"
    )
    batch_file = st.file_uploader("Upload batch CSV", type=["csv"], key="batch_csv")
    if batch_file is not None:
        batch = pd.read_csv(batch_file)
        merged = batch.merge(shapes, on="shape", how="left")
        if merged["A_mm2"].isna().any():
            st.error("Some shapes were not found in the current library.")
        else:
            output = []
            for _, row in merged.iterrows():
                shp = row.to_dict()
                A = safe_float(shp.get("A_mm2"))
                rx = safe_float(shp.get("rx_mm"))
                ry = safe_float(shp.get("ry_mm"))
                Fy = safe_float(row["Fy_MPa"])
                Fu = safe_float(row["Fu_MPa"])
                Ae = safe_float(row.get("Ae_ratio", 0.85)) * A
                Pu = safe_float(row["Pu_kN"])
                Mux = safe_float(row["Mux_kNm"])
                Muy = safe_float(row["Muy_kNm"])
                Vu = safe_float(row["Vu_kN"])
                Lx = safe_float(row["Lx_mm"])
                Ly = safe_float(row["Ly_mm"])
                Lb = safe_float(row.get("Lb_mm", Lx))
                Kx = safe_float(row["Kx"])
                Ky = safe_float(row["Ky"])

                T_design, *_ = tension_strength(A, Ae, Fy, Fu, method)
                C_design, *_ = compression_strength(A, Kx, Ky, Lx, Ly, rx, ry, Fy, E_DEFAULT, method)
                V_design, *_ = shear_strength(shp, Fy, method)
                Mx_design, *_ = flexural_strength(shp, Fy, method, "x", Lb_mm=Lb, Cb=1.0, consider_ltb=True)
                My_design, *_ = flexural_strength(shp, Fy, method, "y", Lb_mm=Ly, Cb=1.0, consider_ltb=False)
                sec_df, sec_ok = classify_section(shp, Fy, seismic=seismic_mode)

                axial_cap = T_design if Pu >= 0 else C_design
                ir_a = demand_capacity_ratio(Pu, axial_cap)
                ir_x = demand_capacity_ratio(Mux, Mx_design)
                ir_y = demand_capacity_ratio(Muy, My_design)
                ir_v = demand_capacity_ratio(Vu, V_design)
                ir_int = axial_flexure_interaction(ir_a, ir_x, ir_y)

                output.append({
                    "member_id": row["member_id"],
                    "shape": row["shape"],
                    "family": row["family"],
                    "axial_IR": ir_a,
                    "Mx_IR": ir_x,
                    "My_IR": ir_y,
                    "V_IR": ir_v,
                    "interaction_IR": ir_int,
                    "seismic_slenderness_ok": sec_ok,
                    "overall": "OK" if max(ir_a, ir_x, ir_y, ir_v, ir_int) <= 1.0 and sec_ok else "NG"
                })

            out = pd.DataFrame(output)
            st.dataframe(out, use_container_width=True)
            build_summary_download(out, "aisc_steel_checker_pro_batch.xlsx")

with tabs[3]:
    st.subheader("Seismic / Zone 4 Screen")
    st.write("This page is a conceptual prompt panel, not a replacement for full seismic design.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Ss", fmt(Ss, 2))
    c2.metric("S1", fmt(S1, 2))
    c3.metric("R / Ie", fmt(R / max(Ie, 1e-9), 2))

    st.markdown("### Typical design reminders")
    st.write("- Confirm governing steel seismic system first.")
    st.write("- Use compact / seismically qualified sections for the selected system.")
    st.write("- Check expected strength hierarchy, not just nominal strength.")
    st.write("- Review drift, P-Delta, panel zone, brace/gusset, and connection requirements.")
    st.write("- For high-seismic frames, beam-column connection qualification can govern.")

    if seismic_system in ["SMF", "IMF", "OMF"]:
        st.info("Moment-frame workflow: prioritize beam compactness, column continuity, strong-column / weak-beam, and drift.")
    elif seismic_system in ["SCBF", "OCBF", "BRBF", "EBF"]:
        st.info("Braced-frame workflow: prioritize brace slenderness, gusset detailing, expected brace strength, and collector load path.")
    else:
        st.info("Use project-specific seismic detailing requirements.")

with tabs[4]:
    st.subheader("Section Library")
    st.dataframe(shapes, use_container_width=True)
    st.download_button(
        "Download current section library CSV",
        shapes.to_csv(index=False).encode("utf-8"),
        file_name="aisc_checker_pro_section_library.csv",
        mime="text/csv"
    )

with tabs[5]:
    st.subheader("User Guide")
    st.markdown(
        """
        ### How to use
        1. Select LRFD or ASD.
        2. Pick a section family and section.
        3. Input Fy, Fu, lengths, K-factors, and demands.
        4. Turn on seismic screening if you want stricter compactness checks.
        5. Review the interaction ratio and the section slenderness table.
        6. For project studies, use the batch checker.

        ### Recommended next office upgrade
        - full office database import from your preferred steel table
        - direct NSCP load combination generator
        - frame drift module
        - panel-zone and connection checks
        - brace expected-strength checks
        - report export to Word/PDF
        """
    )

st.markdown("---")
st.warning(
    "This PRO package is still a preliminary design and compliance screening tool. "
    "Final engineering design must still be based on the full governing code, "
    "official section properties, connection design, global analysis, and project-specific seismic detailing."
)
