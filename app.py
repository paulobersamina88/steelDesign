import io, math, re
import pandas as pd
import streamlit as st

st.set_page_config(page_title="AISC Steel Checker ULTRA Phase 2.5", layout="wide")

E_DEFAULT = 200000.0  # MPa
IN2_TO_MM2 = 645.16
IN_TO_MM = 25.4
IN3_TO_MM3 = 16387.064
IN4_TO_MM4 = 416231.4256
IN6_TO_MM6 = 268435456.0

PHI = {"tension_yield":0.90,"tension_rupture":0.75,"compression":0.90,"flexure":0.90,"shear":0.90}
OMEGA = {"tension_yield":1.67,"tension_rupture":2.00,"compression":1.67,"flexure":1.67,"shear":1.50}

AISC_FAMILY_MAP = {
    "W":"W","M":"W","S":"W","HP":"W",
    "C":"C","MC":"MC",
    "L":"L","2L":"2L",
    "WT":"WT","MT":"WT","ST":"WT",
    "HSS":"HSS","PIPE":"PIPE"
}

def safe_float(val):
    try:
        if val is None:
            return 0.0
        if isinstance(val, str):
            v = val.strip()
            if v in {"", "-", "—", "–", "na", "n/a", "N/A"}:
                return 0.0
            v = v.replace(",", "")
            return float(v)
        return float(val)
    except Exception:
        return 0.0

def phi_or_allowable(nominal, method, key):
    return PHI[key] * nominal if method == "LRFD" else nominal / OMEGA[key]

def fmt(v, nd=2):
    try:
        fv = float(v)
        if math.isnan(fv) or math.isinf(fv):
            return "-"
        return f"{fv:,.{nd}f}"
    except Exception:
        return str(v)

@st.cache_data
def load_example_shapes():
    return pd.DataFrame([
        {"shape":"W14X90","family":"W","aisc_type":"W","A_mm2":17100,"d_mm":362,"bf_mm":368,"tw_mm":12.8,"tf_mm":20.6,"Ix_mm4":5300e6,"Iy_mm4":1700e6,"Zx_mm3":3130e3,"Zy_mm3":924e3,"Sx_mm3":2920e3,"Sy_mm3":924e3,"rx_mm":176.0,"ry_mm":100.0},
        {"shape":"C12X30","family":"C","aisc_type":"C","A_mm2":5680,"d_mm":305,"bf_mm":76,"tw_mm":10.0,"tf_mm":15.0,"Ix_mm4":1360e6,"Iy_mm4":77e6,"Zx_mm3":943e3,"Zy_mm3":132e3,"Sx_mm3":891e3,"Sy_mm3":101e3,"rx_mm":155.0,"ry_mm":36.8},
        {"shape":"L6X4X1/2","family":"L","aisc_type":"L","A_mm2":3760,"leg1_mm":152.4,"leg2_mm":101.6,"t_mm":12.7,"Ix_mm4":50e6,"Iy_mm4":17e6,"Zx_mm3":120e3,"Zy_mm3":60e3,"Sx_mm3":93e3,"Sy_mm3":41e3,"rx_mm":53.0,"ry_mm":31.0},
        {"shape":"WT12X38.5","family":"WT","aisc_type":"WT","d_mm":305,"bf_mm":165,"tw_mm":8.0,"tf_mm":13.0,"A_mm2":7290,"Ix_mm4":1200e6,"Iy_mm4":170e6,"Zx_mm3":1000e3,"Zy_mm3":250e3,"Sx_mm3":820e3,"Sy_mm3":190e3,"rx_mm":128.0,"ry_mm":48.0},
        {"shape":"HSS8X8X3/8","family":"HSS_RECT","aisc_type":"HSS","A_mm2":6930,"h_mm":203.2,"b_mm":203.2,"t_mm":9.5,"Ix_mm4":1740e6,"Iy_mm4":1740e6,"Zx_mm3":462e3,"Zy_mm3":462e3,"Sx_mm3":412e3,"Sy_mm3":412e3,"rx_mm":77.7,"ry_mm":77.7},
        {"shape":"HSS10.75X0.365","family":"HSS_ROUND","aisc_type":"HSS","A_mm2":7710,"D_mm":273.0,"t_mm":9.3,"Ix_mm4":2622e6,"Iy_mm4":2622e6,"Zx_mm3":529e3,"Zy_mm3":529e3,"Sx_mm3":462e3,"Sy_mm3":462e3,"rx_mm":90.4,"ry_mm":90.4},
        {"shape":"PIPE10 STD","family":"PIPE","aisc_type":"PIPE","A_mm2":7720,"D_mm":273.1,"t_mm":9.3,"Ix_mm4":2630e6,"Iy_mm4":2630e6,"Zx_mm3":532e3,"Zy_mm3":532e3,"Sx_mm3":464e3,"Sy_mm3":464e3,"rx_mm":90.5,"ry_mm":90.5},
    ])

def convert_aisc_database(df_raw):
    rows = []
    missing_dash_count = int((df_raw.astype(str) == "-").sum().sum())
    for _, r in df_raw.iterrows():
        typ = str(r.get("Type", "")).strip().upper()
        label = r.get("AISC_Manual_Label", r.get("EDI_Std_Nomenclature", typ))
        if pd.isna(label) or str(label).strip() == "":
            continue
        family = AISC_FAMILY_MAP.get(typ, typ)
        if typ == "HSS":
            family = "HSS_ROUND" if safe_float(r.get("OD")) > 0 else "HSS_RECT"

        row = {
            "shape": str(label).strip(),
            "aisc_type": typ,
            "family": family,
            "A_mm2": safe_float(r.get("A")) * IN2_TO_MM2,
            "weight_kg_m": safe_float(r.get("W")) * 1.4881639,
            "d_mm": safe_float(r.get("d")) * IN_TO_MM,
            "bf_mm": safe_float(r.get("bf")) * IN_TO_MM,
            "tw_mm": safe_float(r.get("tw")) * IN_TO_MM,
            "tf_mm": safe_float(r.get("tf")) * IN_TO_MM,
            "t_mm": safe_float(r.get("t", r.get("tdes"))) * IN_TO_MM,
            "h_mm": safe_float(r.get("h")) * IN_TO_MM,
            "b_mm": safe_float(r.get("b")) * IN_TO_MM,
            "D_mm": safe_float(r.get("OD")) * IN_TO_MM,
            "leg1_mm": safe_float(r.get("d")) * IN_TO_MM,
            "leg2_mm": safe_float(r.get("b", r.get("bf"))) * IN_TO_MM,
            "Ix_mm4": safe_float(r.get("Ix")) * IN4_TO_MM4,
            "Iy_mm4": safe_float(r.get("Iy")) * IN4_TO_MM4,
            "Zx_mm3": safe_float(r.get("Zx")) * IN3_TO_MM3,
            "Zy_mm3": safe_float(r.get("Zy")) * IN3_TO_MM3,
            "Sx_mm3": safe_float(r.get("Sx")) * IN3_TO_MM3,
            "Sy_mm3": safe_float(r.get("Sy")) * IN3_TO_MM3,
            "rx_mm": safe_float(r.get("rx")) * IN_TO_MM,
            "ry_mm": safe_float(r.get("ry")) * IN_TO_MM,
            "J_mm4": safe_float(r.get("J")) * IN4_TO_MM4,
            "Cw_mm6": safe_float(r.get("Cw")) * IN6_TO_MM6,
        }
        rows.append(row)

    out = pd.DataFrame(rows)
    out = out[out["shape"].notna()].copy()
    out = out[out["A_mm2"] > 0].copy()
    out = out.drop_duplicates(subset=["shape"]).reset_index(drop=True)
    return out, missing_dash_count

def load_shapes_from_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        xls = pd.ExcelFile(uploaded_file)
        sheet = "Database v15.0" if "Database v15.0" in xls.sheet_names else xls.sheet_names[0]
        raw = pd.read_excel(uploaded_file, sheet_name=sheet)
    else:
        raw = pd.read_csv(uploaded_file)

    cols = {c.lower(): c for c in raw.columns}
    if "shape" in cols and "family" in cols and "a_mm2" in cols:
        df = raw.copy()
        if "weight_kg_m" not in df.columns:
            df["weight_kg_m"] = 0.0
        return df, "normalized", 0

    if "type" in cols and ("aisc_manual_label" in cols or "edi_std_nomenclature" in cols):
        df, missing = convert_aisc_database(raw)
        return df, "aisc_database", missing

    raise ValueError("Unsupported file format. Upload either a normalized office CSV or the AISC shapes database file.")

def inferred_depth_mm(row):
    return max(safe_float(row.get("d_mm")), safe_float(row.get("h_mm")), safe_float(row.get("D_mm")), safe_float(row.get("leg1_mm")))

def inferred_width_mm(row):
    return max(safe_float(row.get("bf_mm")), safe_float(row.get("b_mm")), safe_float(row.get("D_mm")), safe_float(row.get("leg2_mm")))

def critical_stress(Fy, slenderness, E=E_DEFAULT):
    Fe = (math.pi**2 * E) / max(slenderness**2, 1e-9)
    lam = math.sqrt(Fy / max(Fe, 1e-9))
    Fcr = (0.658 ** (lam**2)) * Fy if lam <= 1.5 else 0.877 * Fe
    return min(Fcr, Fy), Fe, lam

def axial_tension(A, Ae, Fy, Fu, method):
    Ny = Fy * A / 1000
    Nr = Fu * Ae / 1000
    return min(phi_or_allowable(Ny, method, "tension_yield"), phi_or_allowable(Nr, method, "tension_rupture")), Ny, Nr

def axial_compression(A, Kx, Ky, Lx, Ly, rx, ry, Fy, method):
    sx = Kx * Lx / max(rx, 1e-9)
    sy = Ky * Ly / max(ry, 1e-9)
    s = max(sx, sy)
    Fcr, Fe, lam = critical_stress(Fy, s)
    Pn = Fcr * A / 1000
    return phi_or_allowable(Pn, method, "compression"), Pn, sx, sy, s, Fcr, Fe, lam

def flexure(shape, Fy, method, axis="x", Lb=0.0, Cb=1.0):
    fam = shape["family"]
    Z = safe_float(shape.get("Zx_mm3" if axis == "x" else "Zy_mm3"))
    S = safe_float(shape.get("Sx_mm3" if axis == "x" else "Sy_mm3", Z))
    ry = safe_float(shape.get("ry_mm", 1.0))
    Mp = Fy * Z / 1e6
    Mn = Mp
    note = "Plastic flexural basis."
    if fam in ["W", "C", "MC", "BUILT_UP_I"] and axis == "x" and Lb > 0:
        rts = max(1.1 * ry, 1.0)
        Lp = 1.76 * rts * math.sqrt(E_DEFAULT / Fy)
        Lr = 1.95 * rts * E_DEFAULT / (0.7 * Fy)
        if Lb <= Lp:
            note = "LTB not governing."
        elif Lb <= Lr:
            My = Fy * S / 1e6
            Mn = min(Mp, Cb * (Mp - (Mp - 0.7 * My) * (Lb - Lp) / max(Lr - Lp, 1e-9)))
            note = "Inelastic LTB screening."
        else:
            Fcr = Cb * (math.pi**2) * E_DEFAULT / max((Lb / max(rts, 1e-9))**2, 1e-9)
            Mn = min(Mp, Fcr * S / 1e6)
            note = "Elastic LTB screening."
    elif fam in ["L", "2L", "WT"]:
        note = "Simplified for unsymmetric sections; full shear-center and special-case behavior not included."
    elif fam in ["HSS_RECT", "HSS_ROUND", "PIPE"]:
        note = "Closed-section flexure basis."
    return phi_or_allowable(Mn, method, "flexure"), Mn, Mp, note

def shear(shape, Fy, method):
    fam = shape["family"]
    if fam in ["W", "C", "MC", "WT", "BUILT_UP_I"]:
        Aw = safe_float(shape.get("d_mm")) * safe_float(shape.get("tw_mm"))
    elif fam == "HSS_RECT":
        Aw = 2 * safe_float(shape.get("h_mm")) * safe_float(shape.get("t_mm"))
    elif fam in ["HSS_ROUND", "PIPE"]:
        Aw = 0.5 * safe_float(shape.get("A_mm2"))
    elif fam in ["L", "2L"]:
        Aw = 0.6 * safe_float(shape.get("A_mm2"))
    else:
        Aw = 0
    Vn = 0.6 * Fy * Aw / 1000
    return phi_or_allowable(Vn, method, "shear"), Vn, Aw

def classify(shape, Fy, seismic=False):
    fam = shape["family"]
    rootFy = math.sqrt(Fy)
    rows = []
    if fam in ["W", "C", "MC", "BUILT_UP_I", "WT"]:
        bf = safe_float(shape.get("bf_mm")); tf = safe_float(shape.get("tf_mm"))
        tw = safe_float(shape.get("tw_mm")); d = safe_float(shape.get("d_mm"))
        lam_f = (bf / 2) / max(tf, 1e-9)
        lam_w = (d - 2 * tf) / max(tw, 1e-9)
        lim_f = (0.30 if seismic else 0.38) * math.sqrt(E_DEFAULT) / rootFy
        lim_w = (2.45 if seismic else 3.76) * math.sqrt(E_DEFAULT) / rootFy
        rows += [
            {"Element":"Flange","Lambda":lam_f,"Limit":lim_f,"Status":"OK" if lam_f <= lim_f else "NG"},
            {"Element":"Web","Lambda":lam_w,"Limit":lim_w,"Status":"OK" if lam_w <= lim_w else "NG"},
        ]
    elif fam == "HSS_RECT":
        b = safe_float(shape.get("b_mm")); h = safe_float(shape.get("h_mm")); t = safe_float(shape.get("t_mm"))
        lim = (1.12 if seismic else 1.40) * math.sqrt(E_DEFAULT) / rootFy
        rows += [
            {"Element":"b/t","Lambda":(b - 3*t) / max(t, 1e-9),"Limit":lim,"Status":"OK" if (b - 3*t) / max(t, 1e-9) <= lim else "NG"},
            {"Element":"h/t","Lambda":(h - 3*t) / max(t, 1e-9),"Limit":lim,"Status":"OK" if (h - 3*t) / max(t, 1e-9) <= lim else "NG"},
        ]
    elif fam in ["HSS_ROUND", "PIPE"]:
        D = safe_float(shape.get("D_mm")); t = safe_float(shape.get("t_mm"))
        lim = 0.07 * E_DEFAULT / Fy if seismic else 0.11 * E_DEFAULT / Fy
        val = D / max(t, 1e-9)
        rows += [{"Element":"D/t","Lambda":val,"Limit":lim,"Status":"OK" if val <= lim else "NG"}]
    elif fam in ["L", "2L"]:
        leg = max(safe_float(shape.get("leg1_mm")), safe_float(shape.get("leg2_mm")))
        t = safe_float(shape.get("t_mm"))
        lim = 0.45 * math.sqrt(E_DEFAULT) / rootFy
        val = leg / max(t, 1e-9)
        rows += [{"Element":"Leg/t","Lambda":val,"Limit":lim,"Status":"OK" if val <= lim else "NG"}]
    df = pd.DataFrame(rows)
    ok = True if df.empty else bool((df["Status"] == "OK").all())
    return df, ok

def ir(demand, cap):
    return abs(demand) / cap if cap > 0 else float("inf")

def interaction(ira, irmx, irmy):
    return ira + 8/9 * (irmx + irmy) if ira >= 0.2 else ira / 2 + irmx + irmy

def export_excel(df, name):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="results")
    st.download_button("Download Excel", buf.getvalue(), file_name=name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def make_search_view(shapes):
    df = shapes.copy()
    df["depth_mm"] = df.apply(inferred_depth_mm, axis=1)
    df["width_mm"] = df.apply(inferred_width_mm, axis=1)
    if "weight_kg_m" not in df.columns:
        df["weight_kg_m"] = 0.0
    df["shape_upper"] = df["shape"].astype(str).str.upper()
    return df

st.title("AISC Steel Checker ULTRA Phase 2.5 — UI Search")
st.caption("This version adds search, filters, quick-pick tables, and favorites-like shortlist behavior for larger AISC databases.")

with st.sidebar:
    method = st.selectbox("Method", ["LRFD", "ASD"])
    seismic = st.toggle("High-seismic / Zone 4 screening", value=True)
    system = st.selectbox("Seismic system", ["SMF","IMF","OMF","SCBF","OCBF","BRBF","EBF","Other"])
    upload = st.file_uploader("Upload AISC database Excel/CSV or normalized office CSV", type=["xlsx","xls","csv"])
    st.info("Upload the AISC v15.0 Excel file and use the new search tools to narrow the section list quickly.")

try:
    if upload is not None:
        shapes, source_mode, missing_dash_count = load_shapes_from_file(upload)
    else:
        shapes = load_example_shapes()
        source_mode = "example"
        missing_dash_count = 0
except Exception as e:
    st.error(str(e))
    st.stop()

search_df = make_search_view(shapes)

st.success(f"Loaded {len(search_df):,} sections from source mode: {source_mode}")
if missing_dash_count:
    st.info(f"Handled {missing_dash_count:,} dash-style missing values from the source file automatically.")

tabs = st.tabs(["Smart Search", "Single Check", "Batch Check", "Loaded Database", "Guide"])

with tabs[0]:
    st.subheader("Smart Section Search")
    f1, f2, f3 = st.columns(3)
    fam_options = ["All"] + sorted(search_df["family"].dropna().astype(str).unique().tolist())
    family_filter = f1.selectbox("Family", fam_options)
    text_query = f2.text_input("Shape search", placeholder="Example: W14, HSS8X8, PIPE10, C12")
    sort_by = f3.selectbox("Sort by", ["shape", "depth_mm", "weight_kg_m", "A_mm2", "Zx_mm3"])

    f4, f5, f6, f7 = st.columns(4)
    min_depth = f4.number_input("Min depth (mm)", value=0.0)
    max_depth = f5.number_input("Max depth (mm)", value=float(max(search_df["depth_mm"].max(), 0)))
    min_weight = f6.number_input("Min weight (kg/m)", value=0.0)
    max_weight = f7.number_input("Max weight (kg/m)", value=float(max(search_df["weight_kg_m"].max(), 0)))

    f8, f9 = st.columns(2)
    top_n = f8.slider("Show top rows", min_value=10, max_value=200, value=30, step=10)
    ascending = f9.toggle("Ascending sort", value=True)

    filtered = search_df.copy()
    if family_filter != "All":
        filtered = filtered[filtered["family"].astype(str) == family_filter]
    if text_query.strip():
        q = text_query.strip().upper()
        filtered = filtered[filtered["shape_upper"].str.contains(re.escape(q), na=False)]
    filtered = filtered[(filtered["depth_mm"] >= min_depth) & (filtered["depth_mm"] <= max_depth)]
    filtered = filtered[(filtered["weight_kg_m"] >= min_weight) & (filtered["weight_kg_m"] <= max_weight)]
    filtered = filtered.sort_values(sort_by, ascending=ascending).head(top_n)

    st.write(f"Matches: {len(filtered):,}")
    st.dataframe(
        filtered[["shape","family","depth_mm","width_mm","weight_kg_m","A_mm2","Zx_mm3","rx_mm","ry_mm"]],
        use_container_width=True,
        hide_index=True
    )

    shortlist = filtered["shape"].astype(str).tolist()
    picked = st.selectbox("Quick-pick a section from search results", shortlist if shortlist else [""])
    if picked:
        st.session_state["selected_shape"] = picked
        st.success(f"Selected {picked}. Go to the Single Check tab to continue.")

with tabs[1]:
    st.subheader("Single Check")

    c1, c2, c3, c4 = st.columns(4)
    family = c1.selectbox("Section family", sorted(search_df["family"].dropna().astype(str).unique()), key="family_single")

    family_df = search_df[search_df["family"].astype(str) == family].copy().sort_values("shape")
    default_shape = st.session_state.get("selected_shape", "")
    family_shapes = family_df["shape"].astype(str).tolist()
    default_index = family_shapes.index(default_shape) if default_shape in family_shapes else 0
    shape_name = c2.selectbox("Section", family_shapes, index=default_index if family_shapes else 0, key="shape_single")

    role = c3.selectbox("Role", ["Beam","Column","Brace","Beam-Column"])
    axis = c4.selectbox("Primary axis", ["x","y"])

    shape = family_df[family_df["shape"].astype(str) == shape_name].iloc[0].to_dict()

    with st.expander("Selected section summary", expanded=True):
        sview = pd.DataFrame([{
            "shape": shape.get("shape"),
            "family": shape.get("family"),
            "depth_mm": inferred_depth_mm(shape),
            "width_mm": inferred_width_mm(shape),
            "weight_kg_m": safe_float(shape.get("weight_kg_m")),
            "A_mm2": safe_float(shape.get("A_mm2")),
            "Zx_mm3": safe_float(shape.get("Zx_mm3")),
            "rx_mm": safe_float(shape.get("rx_mm")),
            "ry_mm": safe_float(shape.get("ry_mm")),
        }])
        st.dataframe(sview, use_container_width=True, hide_index=True)

    m1, m2, m3, m4 = st.columns(4)
    Fy = m1.number_input("Fy (MPa)", value=345.0)
    Fu = m2.number_input("Fu (MPa)", value=450.0)
    Ae_ratio = m3.number_input("Ae / Ag", min_value=0.1, max_value=1.0, value=0.85)
    Cb = m4.number_input("Cb", value=1.0)

    g1, g2, g3, g4, g5 = st.columns(5)
    Lx = g1.number_input("Lx (mm)", value=3000.0)
    Ly = g2.number_input("Ly (mm)", value=3000.0)
    Lb = g3.number_input("Lb (mm)", value=3000.0)
    Kx = g4.number_input("Kx", value=1.0)
    Ky = g5.number_input("Ky", value=1.0)

    d1, d2, d3, d4 = st.columns(4)
    Pu = d1.number_input("Pu kN, tension(+), compression(-)", value=-400.0)
    Mux = d2.number_input("Mux kN-m", value=80.0)
    Muy = d3.number_input("Muy kN-m", value=0.0)
    Vu = d4.number_input("Vu kN", value=120.0)

    s1, s2, s3 = st.columns(3)
    clear_span = s1.number_input("Clear span (mm)", value=6000.0)
    deflection = s2.number_input("Estimated service deflection (mm)", value=8.0)
    drift_ratio = s3.number_input("Estimated elastic story drift ratio", value=0.008)

    A = safe_float(shape.get("A_mm2")); rx = safe_float(shape.get("rx_mm", 1)); ry = safe_float(shape.get("ry_mm", 1)); Ae = A * Ae_ratio
    sec_df, sec_ok = classify(shape, Fy, seismic=seismic)
    Tcap, Ny, Nr = axial_tension(A, Ae, Fy, Fu, method)
    Ccap, Pn, sx, sy, smax, Fcr, Fe, lam = axial_compression(A, Kx, Ky, Lx, Ly, rx, ry, Fy, method)
    MxCap, Mn_x, Mp_x, note_x = flexure(shape, Fy, method, "x", Lb, Cb)
    MyCap, Mn_y, Mp_y, note_y = flexure(shape, Fy, method, "y", Ly, 1.0)
    Vcap, Vn, Aw = shear(shape, Fy, method)

    Acap = Tcap if Pu >= 0 else Ccap
    ira, irmx, irmy, irv = ir(Pu, Acap), ir(Mux, MxCap), ir(Muy, MyCap), ir(Vu, Vcap)
    irint = interaction(ira, irmx, irmy)
    amplified_drift = 5.5 * drift_ratio
    L_over_d = clear_span / max(deflection, 1e-9)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Axial IR", fmt(ira, 3)); k2.metric("Mx IR", fmt(irmx, 3)); k3.metric("My IR", fmt(irmy, 3)); k4.metric("V IR", fmt(irv, 3)); k5.metric("Int. IR", fmt(irint, 3))

    left, right = st.columns([1.4, 1.0])
    with left:
        out = pd.DataFrame([
            {"Check":"Axial","Demand":abs(Pu),"Capacity":Acap,"IR":ira,"Status":"OK" if ira <= 1 else "NG"},
            {"Check":"Major Flexure","Demand":abs(Mux),"Capacity":MxCap,"IR":irmx,"Status":"OK" if irmx <= 1 else "NG"},
            {"Check":"Minor Flexure","Demand":abs(Muy),"Capacity":MyCap,"IR":irmy,"Status":"OK" if irmy <= 1 else "NG"},
            {"Check":"Shear","Demand":abs(Vu),"Capacity":Vcap,"IR":irv,"Status":"OK" if irv <= 1 else "NG"},
            {"Check":"Combined","Demand":irint,"Capacity":1.0,"IR":irint,"Status":"OK" if irint <= 1 else "NG"},
        ])
        st.dataframe(out, use_container_width=True)
        export_excel(out, f"{shape_name}_ui_search_check.xlsx")

    with right:
        st.markdown("### Section Screening")
        st.dataframe(sec_df, use_container_width=True)
        st.markdown("### Notes")
        for t in [
            f"KL/r x = {fmt(sx)}", f"KL/r y = {fmt(sy)}", f"Governing KL/r = {fmt(smax)}",
            f"Fe = {fmt(Fe)} MPa", f"λc = {fmt(lam,3)}", f"Fcr = {fmt(Fcr)} MPa",
            f"Shear area = {fmt(Aw)} mm²", f"Major-axis note: {note_x}", f"Minor-axis note: {note_y}",
            f"Estimated L/Δ = {fmt(L_over_d,1)}", f"Amplified drift prompt = {fmt(amplified_drift,4)}"
        ]:
            st.write("- " + t)
        if seismic and system in ["SMF","IMF","OMF"] and role in ["Beam","Column","Beam-Column"]:
            j1, j2 = st.columns(2)
            mpr = j1.number_input("ΣMpr beams (kN-m)", value=250.0)
            mpc = j2.number_input("ΣMpc columns (kN-m)", value=320.0)
            ratio = mpc / max(mpr, 1e-9)
            st.metric("ΣMpc / ΣMpr", fmt(ratio, 3))
            st.success("Pass" if ratio > 1.0 else "Fail")

with tabs[2]:
    st.subheader("Batch Check")
    st.code("member_id,shape,Pu_kN,Mux_kNm,Muy_kNm,Vu_kN,Lx_mm,Ly_mm,Lb_mm,Kx,Ky,Fy_MPa,Fu_MPa,Ae_ratio", language="text")
    batch = st.file_uploader("Upload batch CSV", type=["csv"], key="batch")
    if batch is not None:
        df = pd.read_csv(batch)
        merged = df.merge(search_df.drop(columns=["shape_upper"], errors="ignore"), on="shape", how="left")
        if merged["A_mm2"].isna().any():
            missing = merged.loc[merged["A_mm2"].isna(), "shape"].astype(str).unique().tolist()
            st.error("Some shapes were not found in the loaded library: " + ", ".join(missing[:20]))
        else:
            rows = []
            for _, row in merged.iterrows():
                shp = row.to_dict()
                A = safe_float(shp.get("A_mm2")); rx = safe_float(shp.get("rx_mm", 1)); ry = safe_float(shp.get("ry_mm", 1))
                Fy = safe_float(row["Fy_MPa"]); Fu = safe_float(row["Fu_MPa"]); Ae = A * safe_float(row.get("Ae_ratio", 0.85))
                Tcap, _, _ = axial_tension(A, Ae, Fy, Fu, method)
                Ccap, _, _, _, _, _, _, _ = axial_compression(A, safe_float(row["Kx"]), safe_float(row["Ky"]), safe_float(row["Lx_mm"]), safe_float(row["Ly_mm"]), rx, ry, Fy, method)
                MxCap, _, _, _ = flexure(shp, Fy, method, "x", safe_float(row.get("Lb_mm", row["Lx_mm"])), 1.0)
                MyCap, _, _, _ = flexure(shp, Fy, method, "y", safe_float(row["Ly_mm"]), 1.0)
                Vcap, _, _ = shear(shp, Fy, method)
                _, sec_ok = classify(shp, Fy, seismic=seismic)
                Pu = safe_float(row["Pu_kN"]); Mux = safe_float(row["Mux_kNm"]); Muy = safe_float(row["Muy_kNm"]); Vu = safe_float(row["Vu_kN"])
                Acap = Tcap if Pu >= 0 else Ccap
                ira, irmx, irmy, irv = ir(Pu, Acap), ir(Mux, MxCap), ir(Muy, MyCap), ir(Vu, Vcap)
                irint = interaction(ira, irmx, irmy)
                rows.append({
                    "member_id":row["member_id"], "shape":row["shape"], "family":row["family"],
                    "axial_IR":ira, "Mx_IR":irmx, "My_IR":irmy, "V_IR":irv, "Interaction_IR":irint,
                    "Seismic_slenderness_OK":sec_ok,
                    "Overall":"OK" if max(ira, irmx, irmy, irv, irint) <= 1 and sec_ok else "NG"
                })
            out = pd.DataFrame(rows)
            st.dataframe(out, use_container_width=True)
            export_excel(out, "ui_search_batch_results.xlsx")

with tabs[3]:
    st.subheader("Loaded Database")
    c1, c2, c3 = st.columns(3)
    c1.metric("Families", int(search_df["family"].nunique()))
    c2.metric("Sections", f"{len(search_df):,}")
    c3.metric("Source", source_mode)
    fam_count = search_df.groupby("family").size().reset_index(name="count").sort_values("count", ascending=False)
    st.dataframe(fam_count, use_container_width=True, hide_index=True)
    st.dataframe(
        search_df[["shape","family","weight_kg_m","depth_mm","width_mm","A_mm2","Zx_mm3","rx_mm","ry_mm"]].head(300),
        use_container_width=True,
        hide_index=True
    )
    st.download_button("Download normalized loaded library CSV", search_df.drop(columns=["shape_upper"], errors="ignore").to_csv(index=False).encode("utf-8"), "normalized_loaded_library.csv", "text/csv")

with tabs[4]:
    st.subheader("Guide")
    st.write("- Use Smart Search first when the loaded AISC file contains many sections.")
    st.write("- Filter by family, text, depth, and weight before sending the section to Single Check.")
    st.write("- The app now safely handles dash-style missing values from AISC spreadsheets.")
    st.write("- Quick-pick stores the chosen section and reuses it in Single Check.")
    st.warning("This is still a preliminary checker. Full special unsymmetric, torsional, and seismic detailing cases are not fully modeled.")
