import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import datetime

# 1. Konfigurasi Halaman agar Luas Maksimal
st.set_page_config(page_title="KPI Dashboard XLSMART", layout="wide")

# --- CSS SAKTI V7: 1 Layar + Metric Kecil ---
st.markdown(
    """
    <style>
        html, body, [data-testid="stAppViewContainer"] {
            overflow: auto!important;
            height: auto!important;
        }
      .block-container {
            padding-top: 0.5rem!important;
            padding-bottom: 1rem!important;
            padding-left: 1rem!important;
            padding-right: 1rem!important;
            max-width: 100%!important;
        }
        [data-testid="stVerticalBlock"] {
            gap: 0.2rem!important;
        }
        h1 {
            padding-top: 0rem!important;
            padding-bottom: 0.3rem!important;
            margin-bottom: 0rem!important;
            font-size: 36px!important;
            text-align: center!important;
        }
        h3, h5 {
            font-size: 16px!important;
            margin-bottom: 0.2rem!important;
        }
        header[data-testid="stHeader"] {
            background-color: transparent!important;
            height: 0rem!important;
        }
      .main.block-container {
            margin-top: -1rem!important;
        }
        hr {
            margin-top: 0.2rem!important;
            margin-bottom: 0.2rem!important;
        }
        [data-testid="stMetricValue"] {
            font-size: 20px!important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 12px!important;
            min-height: 30px!important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📈 Dashboard Analysis KPI")

# 2. Fitur Upload File di Sidebar
st.sidebar.header("📂 Sumber Data")
uploaded_file = st.sidebar.file_uploader("Pilih file CSV atau Excel:", type=["csv", "xlsx"])

# Helper buat deteksi default agregasi
def detect_default_agg(col_name):
    col_lower = str(col_name).lower()
    sum_keywords = ['payload', 'traffic', 'volume', 'byte', 'count', 'total', 'sum']
    if any(kw in col_lower for kw in sum_keywords):
        return 'sum'
    return 'mean'

if uploaded_file is not None:
    # Membaca data secara dinamis
    with st.spinner("Sedang membaca file... Mohon tunggu"):
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

    all_columns = df.columns.tolist()

    # ==================== CLEANING DATA - FLEKSIBEL BACA HEADER ====================
    def detect_column(df_cols, keywords, exact_match=False):
        """Cari kolom berdasarkan keyword. Return nama kolom asli."""
        for col in df_cols:
            col_clean = str(col).strip().lower().replace("_", " ").replace("-", " ")
            if exact_match:
                if col_clean in keywords:
                    return col
            else:
                if any(kw in col_clean for kw in keywords):
                    return col
        return None

    # Auto-detect semua kolom penting
    kolom_band = detect_column(all_columns, ["band", "freq band", "frequency"])
    kolom_Tower_ID = detect_column(all_columns, ["(4g enodeb fdd)msc", "Tower_ID", "enodeb", "tower", "msc"])
    kolom_moentity = detect_column(all_columns, ["moentity", "cellname", "cell name", "sector"])
    kolom_date = detect_column(all_columns, ["date", "tanggal", "tgl", "timestamp", "datetime", "time"])
    kolom_operator = detect_column(all_columns, ["operator", "op", "ope", "opr", "provider", "brand"], exact_match=True)

    # Fallback kalau Tower_ID ga ketemu
    if not kolom_Tower_ID:
        kolom_Tower_ID = all_columns[0] # Pake kolom pertama

    # Cleaning nilai
    if kolom_band:
        df[kolom_band] = df[kolom_band].fillna(0).astype(str).str.extract(r'(\d+)').fillna(0).astype(int).astype(str)

    if kolom_date:
        df[kolom_date] = pd.to_datetime(df[kolom_date], errors='coerce', dayfirst=True)
        df = df.dropna(subset=[kolom_date])
        df[kolom_date] = df[kolom_date].dt.date

    if kolom_operator:
        df[kolom_operator] = df[kolom_operator].astype(str).str.strip().str.upper()

    if kolom_Tower_ID:
        df[kolom_Tower_ID] = df[kolom_Tower_ID].astype(str).str.strip()

    if kolom_moentity:
        df[kolom_moentity] = df[kolom_moentity].astype(str).str.strip()

    # ==================== LOGIKA INTERKONEKSI SLICER ====================
    if "Tower_ID_sel" not in st.session_state: st.session_state.Tower_ID_sel = ["Select All"]
    if "mo_sel" not in st.session_state: st.session_state.mo_sel = "Select All"
    if "band_sel" not in st.session_state: st.session_state.band_sel = ["Select All"]
    if "operator_sel" not in st.session_state: st.session_state.operator_sel = "Select All"

    st.markdown("### 🎛 Slicers (Filter Data)")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        df_for_Tower_ID = df.copy()
        if st.session_state.mo_sel!= "Select All":
            df_for_Tower_ID = df_for_Tower_ID[df_for_Tower_ID[kolom_moentity] == st.session_state.mo_sel]
        if st.session_state.band_sel and "Select All" not in st.session_state.band_sel:
            df_for_Tower_ID = df_for_Tower_ID[df_for_Tower_ID[kolom_band].isin(st.session_state.band_sel)]
        if kolom_operator and st.session_state.operator_sel!= "Select All":
            df_for_Tower_ID = df_for_Tower_ID[df_for_Tower_ID[kolom_operator] == st.session_state.operator_sel]

        list_Tower_ID_unik = ["Select All"] + sorted(df_for_Tower_ID[kolom_Tower_ID].dropna().unique().tolist())

        current_tower_sel = st.session_state.Tower_ID_sel
        if len(current_tower_sel) > 1 and "Select All" in current_tower_sel:
            if current_tower_sel[0] == "Select All":
                st.session_state.Tower_ID_sel = [x for x in current_tower_sel if x!= "Select All"]
            else:
                st.session_state.Tower_ID_sel = ["Select All"]

        Tower_ID_terpilih = st.multiselect("Tower_ID / eNodeB", options=list_Tower_ID_unik, key="Tower_ID_sel")

    with col2:
        if kolom_moentity:
            df_for_mo = df.copy()
            if st.session_state.Tower_ID_sel and "Select All" not in st.session_state.Tower_ID_sel:
                df_for_mo = df_for_mo[df_for_mo[kolom_Tower_ID].isin(st.session_state.Tower_ID_sel)]
            if st.session_state.band_sel and "Select All" not in st.session_state.band_sel:
                df_for_mo = df_for_mo[df_for_mo[kolom_band].isin(st.session_state.band_sel)]
            if kolom_operator and st.session_state.operator_sel!= "Select All":
                df_for_mo = df_for_mo[df_for_mo[kolom_operator] == st.session_state.operator_sel]

            list_mo_unik = ["Select All"] + sorted(df_for_mo[kolom_moentity].dropna().unique().tolist())
            idx_mo = list_mo_unik.index(st.session_state.mo_sel) if st.session_state.mo_sel in list_mo_unik else 0
            mo_terpilih = st.selectbox("MOEntity / Cellname", options=list_mo_unik, index=idx_mo, key="mo_sel")
        else:
            mo_terpilih = "Select All"

    with col3:
        if kolom_band:
            df_for_band = df.copy()
            if st.session_state.Tower_ID_sel and "Select All" not in st.session_state.Tower_ID_sel:
                df_for_band = df_for_band[df_for_band[kolom_Tower_ID].isin(st.session_state.Tower_ID_sel)]
            if st.session_state.mo_sel!= "Select All":
                df_for_band = df_for_band[df_for_band[kolom_moentity] == st.session_state.mo_sel]
            if kolom_operator and st.session_state.operator_sel!= "Select All":
                df_for_band = df_for_band[df_for_band[kolom_operator] == st.session_state.operator_sel]

            list_band_unik = ["Select All"] + sorted([b for b in df_for_band[kolom_band].unique() if b!= '0'])

            current_band_sel = st.session_state.band_sel
            if len(current_band_sel) > 1 and "Select All" in current_band_sel:
                if current_band_sel[0] == "Select All":
                    st.session_state.band_sel = [x for x in current_band_sel if x!= "Select All"]
                else:
                    st.session_state.band_sel = ["Select All"]

            band_terpilih = st.multiselect("BAND", options=list_band_unik, key="band_sel")
        else:
            band_terpilih = ["Select All"]

    with col4:
        if kolom_operator:
            df_for_op = df.copy()
            if st.session_state.Tower_ID_sel and "Select All" not in st.session_state.Tower_ID_sel:
                df_for_op = df_for_op[df_for_op[kolom_Tower_ID].isin(st.session_state.Tower_ID_sel)]
            if st.session_state.mo_sel!= "Select All":
                df_for_op = df_for_op[df_for_op[kolom_moentity] == st.session_state.mo_sel]
            if st.session_state.band_sel and "Select All" not in st.session_state.band_sel:
                df_for_op = df_for_op[df_for_op[kolom_band].isin(st.session_state.band_sel)]

            list_op_unik = ["Select All"] + sorted(df_for_op[kolom_operator].dropna().unique().tolist())
            idx_op = list_op_unik.index(st.session_state.operator_sel) if st.session_state.operator_sel in list_op_unik else 0
            operator_terpilih = st.selectbox("Operator", options=list_op_unik, index=idx_op, key="operator_sel")
        else:
            operator_terpilih = "Select All"
            st.selectbox("Operator", options=["Kolom tidak ditemukan"], disabled=True)

    with col5:
        if kolom_date:
            min_date = df[kolom_date].min()
            max_date = df[kolom_date].max()
            date_range = st.date_input(
                "Pilih Rentang Tanggal",
                value=[min_date, max_date],
                min_value=min_date,
                max_value=max_date
            )

            if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                start_date, end_date = date_range
            elif isinstance(date_range, (list, tuple)) and len(date_range) == 1:
                start_date = end_date = date_range[0]
            else:
                start_date = end_date = date_range

    # ==================== PENGATURAN GRAFIK DI SIDEBAR + AGREGASI ====================
    st.sidebar.markdown("---")
    st.sidebar.header("⚙ Pengaturan Grafik & Target")

    opsi_kpi_blank = ["-- Pilih KPI --"] + all_columns
    idx_x = all_columns.index(kolom_date) if kolom_date in all_columns else 0
    x_axis = st.sidebar.selectbox("Sumbu X (Horizontal):", all_columns, index=idx_x)

    st.sidebar.markdown("---")
    y_axis_1 = st.sidebar.selectbox("KPI 1 (Sumbu Kiri):", opsi_kpi_blank, index=0)

    agg_1 = 'mean'
    if y_axis_1!= "-- Pilih KPI --":
        default_agg1 = detect_default_agg(y_axis_1)
        agg_1 = st.sidebar.selectbox(
            "Metode Agregasi KPI 1:",
            ["mean", "sum", "max", "min"],
            index=0 if default_agg1 == 'mean' else 1,
            key="agg1"
        )

    type_chart_1 = st.sidebar.radio("Tipe Grafik KPI 1:", ["Line", "Bar", "Area"], key="chart1")

    use_threshold_1 = st.sidebar.checkbox("Aktifkan Garis Target KPI 1")
    threshold_val_1 = st.sidebar.number_input("Nilai Target KPI 1:", value=95.0 if "per" in str(y_axis_1).lower() or "%" in str(y_axis_1) else 0.0, step=1.0) if use_threshold_1 else None

    st.sidebar.markdown("---")
    y_axis_2 = st.sidebar.selectbox("KPI 2 (Sumbu Kanan - Opsional):", opsi_kpi_blank, index=0)

    agg_2 = 'mean'
    has_kpi2 = (y_axis_2!= "-- Pilih KPI --")
    if has_kpi2:
        default_agg2 = detect_default_agg(y_axis_2)
        agg_2 = st.sidebar.selectbox(
            "Metode Agregasi KPI 2:",
            ["mean", "sum", "max", "min"],
            index=0 if default_agg2 == 'mean' else 1,
            key="agg2"
        )

    type_chart_2 = st.sidebar.radio("Tipe Grafik KPI 2:", ["Bar", "Line", "Area"], key="chart2")

    split_by_operator = False
    if kolom_operator:
        split_by_operator = st.sidebar.checkbox("Split Chart by Operator", value=False)
    highlight_range = st.sidebar.checkbox("Highlight Before/After Range", value=False)
    use_threshold_2 = st.sidebar.checkbox("Aktifkan Garis Target KPI 2") if has_kpi2 else False
    threshold_val_2 = st.sidebar.number_input("Nilai Target KPI 2:", value=95.0 if "per" in str(y_axis_2).lower() or "%" in str(y_axis_2) else 0.0, step=1.0) if use_threshold_2 else None

    # ==================== PROSES AKHIR FILTERING DATA ====================
    df_filtered = df.copy()
    if Tower_ID_terpilih and "Select All" not in Tower_ID_terpilih:
        df_filtered = df_filtered[df_filtered[kolom_Tower_ID].isin(Tower_ID_terpilih)]
    if mo_terpilih!= "Select All":
        df_filtered = df_filtered[df_filtered[kolom_moentity] == mo_terpilih]
    if band_terpilih and "Select All" not in band_terpilih:
        df_filtered = df_filtered[df_filtered[kolom_band].isin(band_terpilih)]
    if kolom_operator and operator_terpilih!= "Select All":
        df_filtered = df_filtered[df_filtered[kolom_operator] == operator_terpilih]
    if kolom_date and start_date and end_date:
        df_filtered = df_filtered[(df_filtered[kolom_date] >= start_date) & (df_filtered[kolom_date] <= end_date)]

    # ==================== HEAD TO HEAD + SUMMARY KPI SEJAJAR ====================
    if kolom_date and not df_filtered.empty and y_axis_1!= "-- Pilih KPI --":
        with st.container(border=True):
            st.markdown("##### 📅 Before vs After + KPI Summary")

            if agg_1 == 'sum': val_kpi1 = df_filtered[y_axis_1].sum()
            elif agg_1 == 'max': val_kpi1 = df_filtered[y_axis_1].max()
            elif agg_1 == 'min': val_kpi1 = df_filtered[y_axis_1].min()
            else: val_kpi1 = df_filtered[y_axis_1].mean()
            label_1 = f"{agg_1.upper()} {y_axis_1}"

            val_kpi2 = None
            if has_kpi2:
                if agg_2 == 'sum': val_kpi2 = df_filtered[y_axis_2].sum()
                elif agg_2 == 'max': val_kpi2 = df_filtered[y_axis_2].max()
                elif agg_2 == 'min': val_kpi2 = df_filtered[y_axis_2].min()
                else: val_kpi2 = df_filtered[y_axis_2].mean()
                label_2 = f"{agg_2.upper()} {y_axis_2}"

            cols = st.columns([1.3, 1.3, 1, 1]) if has_kpi2 else st.columns([1.5, 1.5, 1])

            total_days = (max_date - min_date).days
            if total_days >= 14:
                default_before_start, default_before_end = min_date, min_date + datetime.timedelta(days=6)
                default_after_start, default_after_end = min_date + datetime.timedelta(days=7), min_date + datetime.timedelta(days=13)
            else:
                default_before_start = default_before_end = min_date
                default_after_start = default_after_end = max_date

            with cols[0]:
                before_range = st.date_input("BEFORE", value=[default_before_start, default_before_end], key="before_range")
                before_start, before_end = before_range if len(before_range) == 2 else (before_range[0], before_range[0])

            with cols[1]:
                after_range = st.date_input("AFTER", value=[default_after_start, default_after_end], key="after_range")
                after_start, after_end = after_range if len(after_range) == 2 else (after_range[0], after_range[0])

            with cols[2]:
                st.metric(label=label_1, value=f"{val_kpi1:,.2f}")

            if has_kpi2:
                with cols[3]:
                    st.metric(label=label_2, value=f"{val_kpi2:,.2f}")
    else:
        before_start, before_end, after_start, after_end = None, None, None, None

    # ==================== RENDER CHART DYNAMICS ====================
    st.markdown("---")

    if df_filtered.empty:
        st.warning("⚠ Kombinasi Slicer menghasilkan data kosong. Silakan sesuaikan kembali filter Anda di atas.")

    elif y_axis_1 == "-- Pilih KPI --":
        st.info("💡 **Silakan tentukan minimal pilihan metrik pada KPI 1** di sidebar menu sebelah kiri untuk memunculkan grafik.")

    else:
        fig = make_subplots(specs=[[{"secondary_y": has_kpi2}]])

        is_site_level = (mo_terpilih == "Select All")
        do_split_op = split_by_operator and kolom_operator and operator_terpilih == "Select All"

        if is_site_level:
            if do_split_op:
                cols_to_group = [x_axis, kolom_Tower_ID, kolom_operator]
                kolom_label = kolom_Tower_ID
            else:
                cols_to_group = [x_axis, kolom_Tower_ID]
                kolom_label = kolom_Tower_ID
        else:
            if do_split_op:
                cols_to_group = [x_axis, kolom_moentity, kolom_operator]
                kolom_label = kolom_moentity
            else:
                cols_to_group = [x_axis, kolom_moentity]
                kolom_label = kolom_moentity

        agg_dict = {y_axis_1: agg_1}
        if has_kpi2:
            agg_dict[y_axis_2] = agg_2

        agg_named = {k: (k, v) for k, v in agg_dict.items()}
        df_aggregated = df_filtered.groupby(cols_to_group, as_index=False, group_keys=False).agg(**agg_named)

        if kolom_date and x_axis == kolom_date and start_date and end_date:
            all_dates = pd.date_range(start=start_date, end=end_date, freq='D').date
            group_cols = [c for c in cols_to_group if c!= x_axis]
            if group_cols:
                unique_groups = df_aggregated[group_cols].drop_duplicates()
                date_df = pd.DataFrame({x_axis: all_dates})
                full_index = date_df.merge(unique_groups, how='cross')
                df_aggregated = full_index.merge(df_aggregated, on=cols_to_group, how='left').fillna({y_axis_1: 0, **({y_axis_2: 0} if has_kpi2 else {})})
            else:
                df_aggregated = df_aggregated.set_index(x_axis).reindex(all_dates).reset_index().rename(columns={'index': x_axis}).fillna(0)

        df_aggregated[y_axis_1] = df_aggregated[y_axis_1].fillna(0)
        if has_kpi2:
            df_aggregated[y_axis_2] = df_aggregated[y_axis_2].fillna(0)

        df_aggregated = df_aggregated.sort_values(by=x_axis)

        if kolom_date and x_axis == kolom_date:
            df_aggregated[x_axis] = df_aggregated[x_axis].apply(lambda x: f"{x.day}/{x.month}/{x.year}")

        palette_kpi1_list = ["31, 119, 180", "44, 160, 44", "148, 103, 189", "214, 39, 40", "158, 218, 229"]
        palette_kpi2_list = ["255, 127, 14", "227, 119, 194", "188, 189, 34", "23, 190, 207", "255, 187, 120"]
        color_map = {"xl": "0, 32, 96", "sf": "227, 6, 19"}

        def add_dynamic_trace(df_c, y_col, name_legend, chart_type, is_secondary, rgb_base, op_name=None):
            if op_name and op_name.lower() in color_map:
                rgb_base = color_map[op_name.lower()]
            if chart_type == "Line":
                return go.Scatter(x=df_c[x_axis], y=df_c[y_col], name=name_legend, mode='lines', line=dict(color=f"rgb({rgb_base})", width=2.5), connectgaps=True, showlegend=True)
            elif chart_type == "Bar":
                opasitas = 0.50 if is_secondary else 0.80
                return go.Bar(x=df_c[x_axis], y=df_c[y_col], name=name_legend, marker_color=f"rgb({rgb_base})", opacity=opasitas, showlegend=True)
            elif chart_type == "Area":
                return go.Scatter(x=df_c[x_axis], y=df_c[y_col], name=name_legend, mode='lines', line=dict(color=f"rgb({rgb_base})", width=2), fill='tozeroy', fillcolor=f"rgba({rgb_base}, 0.35)", connectgaps=True, showlegend=True)

        if do_split_op:
            item_aktif_op = sorted(df_aggregated[kolom_operator].dropna().unique().tolist())
            item_aktif_Tower_ID = sorted(df_aggregated[kolom_label].dropna().unique().tolist())
            for i, op in enumerate(item_aktif_op):
                for j, item in enumerate(item_aktif_Tower_ID):
                    df_c = df_aggregated[(df_aggregated[kolom_label] == item) & (df_aggregated[kolom_operator] == op)]
                    if not df_c.empty:
                        rgb_c1 = palette_kpi1_list[(i+j) % len(palette_kpi1_list)]
                        name_leg = f"{op}" if is_site_level else f"{item}-{op}"
                        trace1 = add_dynamic_trace(df_c, y_axis_1, name_leg, type_chart_1, is_secondary=False, rgb_base=rgb_c1, op_name=op)
                        fig.add_trace(trace1, secondary_y=False)
        else:
            item_aktif = sorted(df_aggregated[kolom_label].dropna().unique().tolist())
            for i, item in enumerate(item_aktif):
                df_c = df_aggregated[df_aggregated[kolom_label] == item]
                if not df_c.empty:
                    rgb_c1 = palette_kpi1_list[i % len(palette_kpi1_list)]
                    trace1 = add_dynamic_trace(df_c, y_axis_1, f"{item}", type_chart_1, is_secondary=False, rgb_base=rgb_c1)
                    fig.add_trace(trace1, secondary_y=False)

        if has_kpi2:
            if do_split_op:
                item_aktif_op = sorted(df_aggregated[kolom_operator].dropna().unique().tolist())
                item_aktif_Tower_ID = sorted(df_aggregated[kolom_label].dropna().unique().tolist())
                for i, op in enumerate(item_aktif_op):
                    for j, item in enumerate(item_aktif_Tower_ID):
                        df_c = df_aggregated[(df_aggregated[kolom_label] == item) & (df_aggregated[kolom_operator] == op)]
                        if not df_c.empty:
                            rgb_c2 = palette_kpi2_list[(i+j) % len(palette_kpi2_list)]
                            name_leg = f"{op} ({y_axis_2})" if is_site_level else f"{item}-{op} ({y_axis_2})"
                            trace2 = add_dynamic_trace(df_c, y_axis_2, name_leg, type_chart_2, is_secondary=True, rgb_base=rgb_c2, op_name=op)
                            fig.add_trace(trace2, secondary_y=True)
            else:
                item_aktif = sorted(df_aggregated[kolom_label].dropna().unique().tolist())
                for i, item in enumerate(item_aktif):
                    df_c = df_aggregated[df_aggregated[kolom_label] == item]
                    if not df_c.empty:
                        rgb_c2 = palette_kpi2_list[i % len(palette_kpi2_list)]
                        trace2 = add_dynamic_trace(df_c, y_axis_2, f"{item} ({y_axis_2})", type_chart_2, is_secondary=True, rgb_base=rgb_c2)
                        fig.add_trace(trace2, secondary_y=True)

        if use_threshold_1 and kolom_date and start_date and end_date:
            start_str = f"{start_date.day}/{start_date.month}/{start_date.year}"
            end_str = f"{end_date.day}/{end_date.month}/{end_date.year}"
            fig.add_trace(go.Scatter(x=[start_str, end_str], y=[threshold_val_1, threshold_val_1], name=f"Target {y_axis_1}", mode="lines", line=dict(color="red", width=2.5, dash="dash")), secondary_y=False)

        if use_threshold_2 and kolom_date and start_date and end_date:
            start_str = f"{start_date.day}/{start_date.month}/{start_date.year}"
            end_str = f"{end_date.day}/{end_date.month}/{end_date.year}"
            fig.add_trace(go.Scatter(x=[start_str, end_str], y=[threshold_val_2, threshold_val_2], name=f"Target {y_axis_2}", mode="lines", line=dict(color="purple", width=2.5, dash="dot")), secondary_y=True)

        judul_level = "Operator Level" if do_split_op else ("Site Level" if is_site_level else "Cell Level")
        judul_chart = f"Analisis Grafik KPI ({judul_level}): {y_axis_1} [{agg_1.upper()}]" + (f" vs {y_axis_2} [{agg_2.upper()}]" if has_kpi2 else "")

        if highlight_range and kolom_date and before_start and before_end and after_start and after_end:
            before_start_str = f"{before_start.day}/{before_start.month}/{before_start.year}"
            before_end_str = f"{before_end.day}/{before_end.month}/{before_end.year}"
            after_start_str = f"{after_start.day}/{after_start.month}/{after_start.year}"
            after_end_str = f"{after_end.day}/{after_end.month}/{after_end.year}"
            fig.add_shape(type="rect", xref="x", yref="paper", x0=before_start_str, x1=before_end_str, y0=0, y1=1, line=dict(color="blue", width=2, dash="dot"), fillcolor="rgba(0,0,0,0)", layer="below")
            fig.add_annotation(x=before_start_str, y=1.02, xref="x", yref="paper", text="BEFORE", showarrow=False, font=dict(color="blue", size=12, family="Arial Black"), bgcolor="rgba(255,255,0.8)")
            fig.add_shape(type="rect", xref="x", yref="paper", x0=after_start_str, x1=after_end_str, y0=0, y1=1, line=dict(color="green", width=2, dash="dot"), fillcolor="rgba(0,0,0,0)", layer="below")
            fig.add_annotation(x=after_start_str, y=1.02, xref="x", yref="paper", text="AFTER", showarrow=False, font=dict(color="green", size=12, family="Arial Black"), bgcolor="rgba(255,255,0.8)")

        fig.update_layout(
            title_text=judul_chart,
            hovermode="x unified",
            height=450,
            margin=dict(l=80, r=50, t=80, b=150),
            showlegend=True,
            legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
            xaxis=dict(type='category')
        )
        st.plotly_chart(fig, use_container_width=True)

        # ==================== TABEL PERBANDINGAN BEFORE AFTER RENTANG ====================
        if kolom_date and y_axis_1!= "-- Pilih KPI --" and before_start and before_end and after_start and after_end:
            st.markdown("---")
            st.markdown(f"### 📋 Tabel Perbandingan Before vs After")
            st.caption(f"Before: {before_start.day}/{before_start.month}/{before_start.year} s/d {before_end.day}/{before_end.month}/{before_end.year} | After: {after_start.day}/{after_start.month}/{after_start.year} s/d {after_end.day}/{after_end.month}/{after_end.year}")

            df_before = df.copy()
            df_after = df.copy()

            if Tower_ID_terpilih and "Select All" not in Tower_ID_terpilih:
                df_before = df_before[df_before[kolom_Tower_ID].isin(Tower_ID_terpilih)]
                df_after = df_after[df_after[kolom_Tower_ID].isin(Tower_ID_terpilih)]
            if mo_terpilih!= "Select All":
                df_before = df_before[df_before[kolom_moentity] == mo_terpilih]
                df_after = df_after[df_after[kolom_moentity] == mo_terpilih]
            if band_terpilih and "Select All" not in band_terpilih:
                df_before = df_before[df_before[kolom_band].isin(band_terpilih)]
                df_after = df_after[df_after[kolom_band].isin(band_terpilih)]
            if kolom_operator and operator_terpilih!= "Select All":
                df_before = df_before[df_before[kolom_operator] == operator_terpilih]
                df_after = df_after[df_after[kolom_operator] == operator_terpilih]

            df_before = df_before[(df_before[kolom_date] >= before_start) & (df_before[kolom_date] <= before_end)]
            df_after = df_after[(df_after[kolom_date] >= after_start) & (df_after[kolom_date] <= after_end)]

            if df_before.empty or df_after.empty:
                st.warning("⚠ Data kosong di salah satu rentang tanggal. Cek lagi filternya.")
            else:
                group_col = kolom_Tower_ID if is_site_level else kolom_moentity

                agg_dict = {y_axis_1: agg_1}
                if has_kpi2:
                    agg_dict[y_axis_2] = agg_2

                before_agg = df_before.groupby(group_col, as_index=False).agg(agg_dict).rename(columns={
                    y_axis_1: f'{y_axis_1}_Before',
                    **({y_axis_2: f'{y_axis_2}_Before'} if has_kpi2 else {})
                })

                after_agg = df_after.groupby(group_col, as_index=False).agg(agg_dict).rename(columns={
                    y_axis_1: f'{y_axis_1}_After',
                    **({y_axis_2: f'{y_axis_2}_After'} if has_kpi2 else {})
                })

                compare_df = pd.merge(before_agg, after_agg, on=group_col, how='outer').fillna(0)

                before_count = df_before.groupby(group_col).size().reset_index(name='Count_Before')
                after_count = df_after.groupby(group_col).size().reset_index(name='Count_After')
                compare_df = compare_df.merge(before_count, on=group_col, how='left').merge(after_count, on=group_col, how='left')

                compare_df[f'Delta_{y_axis_1}'] = compare_df[f'{y_axis_1}_After'] - compare_df[f'{y_axis_1}_Before']
                compare_df[f'Gain_{y_axis_1}'] = ((compare_df[f'{y_axis_1}_After'] - compare_df[f'{y_axis_1}_Before']) / compare_df[f'{y_axis_1}_After'].replace(0, pd.NA) * 100).fillna(0)

                if has_kpi2:
                    compare_df[f'Delta_{y_axis_2}'] = compare_df[f'{y_axis_2}_After'] - compare_df[f'{y_axis_2}_Before']
                    compare_df[f'Gain_{y_axis_2}'] = ((compare_df[f'{y_axis_2}_After'] - compare_df[f'{y_axis_2}_Before']) / compare_df[f'{y_axis_2}_After'].replace(0, pd.NA) * 100).fillna(0)

                def color_delta(val):
                    color = 'green' if val > 0 else 'red' if val < 0 else 'gray'
                    return f'color: {color}; font-weight: bold'

                format_dict = {
                    f'{y_axis_1}_Before': '{:.2f}',
                    f'{y_axis_1}_After': '{:.2f}',
                    f'Delta_{y_axis_1}': '{:+.2f}',
                    f'Gain_{y_axis_1}': '{:+.1f}%'
                }

                subset_cols = [f'Delta_{y_axis_1}', f'Gain_{y_axis_1}']

                if has_kpi2:
                    format_dict.update({
                        f'{y_axis_2}_Before': '{:.2f}',
                        f'{y_axis_2}_After': '{:.2f}',
                        f'Delta_{y_axis_2}': '{:+.2f}',
                        f'Gain_{y_axis_2}': '{:+.1f}%'
                    })
                    subset_cols.extend([f'Delta_{y_axis_2}', f'Gain_{y_axis_2}'])

                styled_df = compare_df.style.format(format_dict).map(color_delta, subset=subset_cols)

                st.dataframe(
                    styled_df,
                    use_container_width=True,
                    height=350
                )

                st.caption(f"**Metode: {agg_1.upper()} untuk {y_axis_1}" + (f", {agg_2.upper()} untuk {y_axis_2}" if has_kpi2 else "") + ". Gain = (After-Before)/After. Count = jumlah sample data. Hijau = naik, Merah = turun")

else:
    st.info("👋 Dashboard Siap! Silakan unggah file Anda di sidebar sebelah kiri.")
