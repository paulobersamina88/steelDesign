import io, math, pandas as pd, streamlit as st

st.set_page_config(page_title="AISC Steel Checker ULTRA Phase 2 DB-Ready", layout="wide")

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
        {"shape":"W310x39","family":"W","A_mm2":4970,"d_mm":303,"bf_mm":165,"tw_mm":6.1,"tf_mm":10.2,"Ix_mm4":821e6,"Iy_mm4":85.6e6,"Zx_mm3":596e3,"Zy_mm3":121e3,"Sx_mm3":542e3,"Sy_mm3":104e3,"rx_mm":128.0,"ry_mm":41.5},
        {"shape":"C310x40","family":"C","A_mm2":5090,"d_mm":305,"bf_mm":90,"tw_mm":9.7,"tf_mm":13.8,"Ix_mm4":78.0e6,"Iy_mm4":5.90e6,"Zx_mm3":570e3,"Zy_mm3":95e3,"Sx_mm3":512e3,"Sy_mm3":57e3,"rx_mm":123.8,"ry_mm":34.0},
        {"shape":"L152x102x12.7","family":"L","A_mm2":3040,"leg1_mm":152,"leg2_mm":102,"t_mm":12.7,"Ix_mm4":6.20e6,"Iy_mm4":2.20e6,"Zx_mm3":82e3,"Zy_mm3":43e3,"Sx_mm3":61e3,"Sy_mm3":28e3,"rx_mm":45.2,"ry_mm":26.9},
        {"shape":"WT310x39","family":"WT","d_mm":310,"bf_mm":165,"tw_mm":6.5,"tf_mm":10.0,"A_mm2":5000,"Ix_mm4":110e6,"Iy_mm4":18e6,"Zx_mm3":500e3,"Zy_mm3":150e3,"Sx_mm3":420e3,"Sy_mm3":109e3,"rx_mm":148.3,"ry_mm":60.0},
        {"shape":"HSS203x203x9.5","family":"HSS_RECT","A_mm2":6930,"h_mm":203,"b_mm":203,"t_mm":9.5,"Ix_mm4":41.8e6,"Iy_mm4":41.8e6,"Zx_mm3":462e3,"Zy_mm3":462e3,"Sx_mm3":412e3,"Sy_mm3":412e3,"rx_mm":77.7,"ry_mm":77.7},
        {"shape":"HSS273.0x9.3","family":"HSS_ROUND","A_mm2":7710,"D_mm":273.0,"t_mm":9.3,"Ix_mm4":63.0e6,"Iy_mm4":63.0e6,"Zx_mm3":529e3,"Zy_mm3":529e3,"Sx_mm3":462e3,"Sy_mm3":462e3,"rx_mm":90.4,"ry_mm":90.4},
        {"shape":"PIPE273.1x9.3","family":"PIPE","A_mm2":7720,"D_mm":273.1,"t_mm":9.3,"Ix_mm4":63.3e6,"Iy_mm4":63.3e6,"Zx_mm3":532e3,"Zy_mm3":532e3,"Sx_mm3":464e3,"Sy_mm3":464e3,"rx_mm":90.5,"ry_mm":90.5},
    ])

def convert_aisc_database(df_raw):
    df = df_raw.copy()

    def family_from_type(t):
        t = "" if pd.isna(t) else str(t).strip().upper()
        if t == "HSS":
            B = pd.notna
            return None
        return AISC_FAMILY_MAP.get(t, t)

    rows = []
    for _, r in df.iterrows():
        typ = "" if pd.isna(r.get("Type")) else str(r.get("Type")).strip().upper()
        label = r.get("AISC_Manual_Label", r.get("EDI_Std_Nomenclature", typ))
        if pd.isna(label):
            continue
        family = AISC_FAMILY_MAP.get(typ, typ)
        # split HSS family into rect vs round based on OD
        if typ == "HSS":
            if pd.notna(r.get("OD")) and float(r.get("OD") or 0) > 0:
                family = "HSS_ROUND"
            else:
                family = "HSS_RECT"

        row = {
            "shape": str(label).strip(),
            "aisc_type": typ,
            "family": family,
            "A_mm2": float(r.get("A", 0) or 0) * IN2_TO_MM2,
            "d_mm": float(r.get("d", 0) or 0) * IN_TO_MM,
            "bf_mm": float(r.get("bf", 0) or 0) * IN_TO_MM,
            "tw_mm": float(r.get("tw", 0) or 0) * IN_TO_MM,
            "tf_mm": float(r.get("tf", 0) or 0) * IN_TO_MM,
            "t_mm": float(r.get("t", r.get("tdes", 0)) or 0) * IN_TO_MM,
            "h_mm": float(r.get("h", 0) or 0) * IN_TO_MM,
            "b_mm": float(r.get("b", 0) or 0) * IN_TO_MM,
            "D_mm": float(r.get("OD", 0) or 0) * IN_TO_MM,
            "leg1_mm": float(r.get("d", 0) or 0) * IN_TO_MM,
            "leg2_mm": float(r.get("b", r.get("bf", 0)) or 0) * IN_TO_MM,
            "Ix_mm4": float(r.get("Ix", 0) or 0) * IN4_TO_MM4,
            "Iy_mm4": float(r.get("Iy", 0) or 0) * IN4_TO_MM4,
            "Zx_mm3": float(r.get("Zx", 0) or 0) * IN3_TO_MM3,
            "Zy_mm3": float(r.get("Zy", 0) or 0) * IN3_TO_MM3,
            "Sx_mm3": float(r.get("Sx", 0) or 0) * IN3_TO_MM3,
            "Sy_mm3": float(r.get("Sy", 0) or 0) * IN3_TO_MM3,
            "rx_mm": float(r.get("rx", 0) or 0) * IN_TO_MM,
            "ry_mm": float(r.get("ry", 0) or 0) * IN_TO_MM,
            "J_mm4": float(r.get("J", 0) or 0) * IN4_TO_MM4,
            "Cw_mm6": float(r.get("Cw", 0) or 0) * IN6_TO_MM6,
        }
        rows.append(row)

    out = pd.DataFrame(rows)
    out = out[out["shape"].notna()].copy()
    out = out[out["A_mm2"] > 0].copy()
    out = out.drop_duplicates(subset=["shape"]).reset_index(drop=True)
    return out

def load_shapes_from_file(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        xls = pd.ExcelFile(uploaded_file)
        if "Database v15.0" in xls.sheet_names:
            raw = pd.read_excel(uploaded_file, sheet_name="Database v15.0")
        else:
            raw = pd.read_excel(uploaded_file, sheet_name=xls.sheet_names[0])
    else:
        raw = pd.read_csv(uploaded_file)

    cols = {c.lower(): c for c in raw.columns}

    # if already normalized office CSV
    if "shape" in cols and "family" in cols and "a_mm2" in cols:
        return raw.copy(), "normalized"

    # if this looks like AISC database
    if "type" in cols and ("aisc_manual_label" in cols or "edi_std_nomenclature" in cols):
        return convert_aisc_database(raw), "aisc_database"

    raise ValueError("Unsupported file format. Upload either a normalized office CSV or the AISC shapes database file.")

def critical_stress(Fy, slenderness, E=E_DEFAULT):
    Fe = (math.pi**2 * E) / max(slenderness**2, 1e-9)
    lam = math.sqrt(Fy / max(Fe, 1e-9))
    Fcr = (0.658 ** (lam**2)) * Fy if lam <= 1.5 else 0.877 * Fe
    return min(Fcr, Fy), Fe, lam

def axial_tension(A, Ae, Fy, Fu, method):
    Ny = Fy * A / 1000
    Nr = Fu * Ae / 1000
    return min(phi_or_allowable(Ny, method, "tension_yield"),
               phi_or_allowable(Nr, method, "tension_rupture")), Ny, Nr

def axial_compression(A, Kx, Ky, Lx, Ly, rx, ry, Fy, method):
    sx = Kx * Lx / max(rx, 1e-9)
    sy = Ky * Ly / max(ry, 1e-9)
    s = max(sx, sy)
    Fcr, Fe, lam = critical_stress(Fy, s)
    Pn = Fcr * A / 1000
    return phi_or_allowable(Pn, method, "compression"), Pn, sx, sy, s, Fcr, Fe, lam

def flexure(shape, Fy, method, axis="x", Lb=0.0, Cb=1.0):
    fam = shape["family"]
    Z = float(shape.get("Zx_mm3" if axis == "x" else "Zy_mm3", 0))
    S = float(shape.get("Sx_mm3" if axis == "x" else "Sy_mm3", Z))
    ry = float(shape.get("ry_mm", 1.0))
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
        Aw = float(shape.get("d_mm", 0)) * float(shape.get("tw_mm", 0))
    elif fam == "HSS_RECT":
        Aw = 2 * float(shape.get("h_mm", 0)) * float(shape.get("t_mm", 0))
    elif fam in ["HSS_ROUND", "PIPE"]:
        Aw = 0.5 * float(shape.get("A_mm2", 0))
    elif fam in ["L", "2L"]:
        Aw = 0.6 * float(shape.get("A_mm2", 0))
    else:
        Aw = 0
    Vn = 0.6 * Fy * Aw / 1000
    return phi_or_allowable(Vn, method, "shear"), Vn, Aw

def classify(shape, Fy, seismic=False):
    fam = shape["family"]
    rootFy = math.sqrt(Fy)
    rows = []
    if fam in ["W", "C", "MC", "BUILT_UP_I", "WT"]:
        bf = float(shape.get("bf_mm", 0)); tf = float(shape.get("tf_mm", 0))
        tw = float(shape.get("tw_mm", 0)); d = float(shape.get("d_mm", 0))
        lam_f = (bf / 2) / max(tf, 1e-9)
        lam_w = (d - 2 * tf) / max(tw, 1e-9)
        lim_f = (0.30 if seismic else 0.38) * math.sqrt(E_DEFAULT) / rootFy
        lim_w = (2.45 if seismic else 3.76) * math.sqrt(E_DEFAULT) / rootFy
        rows += [
            {"Element":"Flange","Lambda":lam_f,"Limit":lim_f,"Status":"OK" if lam_f <= lim_f else "NG"},
            {"Element":"Web","Lambda":lam_w,"Limit":lim_w,"Status":"OK" if lam_w <= lim_w else "NG"},
        ]
    elif fam == "HSS_RECT":
        b = float(shape.get("b_mm", 0)); h = float(shape.get("h_mm", 0)); t = float(shape.get("t_mm", 0))
        lim = (1.12 if seismic else 1.40) * math.sqrt(E_DEFAULT) / rootFy
        rows += [
            {"Element":"b/t","Lambda":(b - 3*t) / max(t, 1e-9),"Limit":lim,"Status":"OK" if (b - 3*t) / max(t, 1e-9) <= lim else "NG"},
            {"Element":"h/t","Lambda":(h - 3*t) / max(t, 1e-9),"Limit":lim,"Status":"OK" if (h - 3*t) / max(t, 1e-9) <= lim else "NG"},
        ]
    elif fam in ["HSS_ROUND", "PIPE"]:
        D = float(shape.get("D_mm", 0)); t = float(shape.get("t_mm", 0))
        lim = 0.07 * E_DEFAULT / Fy if seismic else 0.11 * E_DEFAULT / Fy
        val = D / max(t, 1e-9)
        rows += [{"Element":"D/t","Lambda":val,"Limit":lim,"Status":"OK" if val <= lim else "NG"}]
    elif fam in ["L", "2L"]:
        leg = max(float(shape.get("leg1_mm", 0)), float(shape.get("leg2_mm", 0)))
        t = float(shape.get("t_mm", 0))
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

st.title("AISC Steel Checker ULTRA Phase 2 — DB Ready")
st.caption("This version can read the AISC shapes database file directly and convert it into usable section properties for the checker.")

with st.sidebar:
    method = st.selectbox("Method", ["LRFD", "ASD"])
    seismic = st.toggle("High-seismic / Zone 4 screening", value=True)
    system = st.selectbox("Seismic system", ["SMF","IMF","OMF","SCBF","OCBF","BRBF","EBF","Other"])
    upload = st.file_uploader("Upload AISC database Excel/CSV or normalized office CSV", type=["xlsx","xls","csv"])
    st.info("Tip: you can upload the AISC v15.0 Excel file directly. The app will auto-map and convert inch-based properties to metric.")

try:
    if upload is not None:
        shapes, source_mode = load_shapes_from_file(upload)
    else:
        shapes = load_example_shapes()
        source_mode = "example"
except Exception as e:
    st.error(str(e))
    st.stop()

st.success(f"Loaded {len(shapes):,} sections from source mode: {source_mode}")

tabs = st.tabs(["Single Check","Batch Check","Loaded Database","Mapping Notes"])

with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    family = c1.selectbox("Section family", sorted(shapes["family"].dropna().astype(str).unique()))
    family_df = shapes[shapes["family"].astype(str) == family].copy()
    shape_name = c2.selectbox("Section", family_df["shape"].astype(str).tolist())
    role = c3.selectbox("Role", ["Beam","Column","Brace","Beam-Column"])
    axis = c4.selectbox("Primary axis", ["x","y"])
    shape = family_df[family_df["shape"].astype(str) == shape_name].iloc[0].to_dict()

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

    A = float(shape.get("A_mm2", 0)); rx = float(shape.get("rx_mm", 1)); ry = float(shape.get("ry_mm", 1)); Ae = A * Ae_ratio
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
        export_excel(out, f"{shape_name}_dbready_check.xlsx")

        cap_df = pd.DataFrame([
            {"Item":"Tension nominal yield","Value":Ny},
            {"Item":"Tension nominal rupture","Value":Nr},
            {"Item":"Compression nominal","Value":Pn},
            {"Item":"Major nominal flexure","Value":Mn_x},
            {"Item":"Minor nominal flexure","Value":Mn_y},
            {"Item":"Nominal shear","Value":Vn},
        ])
        st.dataframe(cap_df, use_container_width=True)

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

with tabs[1]:
    st.subheader("Batch Check")
    st.code("member_id,shape,Pu_kN,Mux_kNm,Muy_kNm,Vu_kN,Lx_mm,Ly_mm,Lb_mm,Kx,Ky,Fy_MPa,Fu_MPa,Ae_ratio", language="text")
    batch = st.file_uploader("Upload batch CSV", type=["csv"], key="batch")
    if batch is not None:
        df = pd.read_csv(batch)
        merged = df.merge(shapes, on="shape", how="left")
        if merged["A_mm2"].isna().any():
            missing = merged.loc[merged["A_mm2"].isna(), "shape"].astype(str).unique().tolist()
            st.error("Some shapes were not found in the loaded library: " + ", ".join(missing[:20]))
        else:
            rows = []
            for _, row in merged.iterrows():
                shp = row.to_dict()
                A = float(shp.get("A_mm2", 0)); rx = float(shp.get("rx_mm", 1)); ry = float(shp.get("ry_mm", 1))
                Fy = float(row["Fy_MPa"]); Fu = float(row["Fu_MPa"]); Ae = A * float(row.get("Ae_ratio", 0.85))
                Tcap, _, _ = axial_tension(A, Ae, Fy, Fu, method)
                Ccap, _, _, _, _, _, _, _ = axial_compression(A, float(row["Kx"]), float(row["Ky"]), float(row["Lx_mm"]), float(row["Ly_mm"]), rx, ry, Fy, method)
                MxCap, _, _, _ = flexure(shp, Fy, method, "x", float(row.get("Lb_mm", row["Lx_mm"])), 1.0)
                MyCap, _, _, _ = flexure(shp, Fy, method, "y", float(row["Ly_mm"]), 1.0)
                Vcap, _, _ = shear(shp, Fy, method)
                _, sec_ok = classify(shp, Fy, seismic=seismic)
                Pu = float(row["Pu_kN"]); Mux = float(row["Mux_kNm"]); Muy = float(row["Muy_kNm"]); Vu = float(row["Vu_kN"])
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
            export_excel(out, "dbready_batch_results.xlsx")

with tabs[2]:
    st.subheader("Loaded Database")
    st.write(f"Families loaded: {shapes['family'].nunique()} | Sections loaded: {len(shapes):,}")
    fam_count = shapes.groupby("family").size().reset_index(name="count")
    st.dataframe(fam_count, use_container_width=True)
    st.dataframe(shapes.head(200), use_container_width=True)
    st.download_button("Download normalized loaded library CSV", shapes.to_csv(index=False).encode("utf-8"), "normalized_loaded_library.csv", "text/csv")

with tabs[3]:
    st.subheader("Mapping Notes")
    st.write("- AISC database inch-based properties are converted internally to mm, mm², mm³, mm⁴, and mm⁶.")
    st.write("- The app auto-detects AISC database files using columns such as Type and AISC_Manual_Label.")
    st.write("- HSS entries are auto-classified into HSS_RECT or HSS_ROUND depending on whether OD exists.")
    st.write("- This keeps the checker light while still letting you use a much larger real section library.")
    st.warning("This is still a preliminary checker. Full final-design equations for all special unsymmetric and seismic cases are not fully modeled.")
