import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import datetime

# 1. Konfigurasi Halaman agar Luas Maksimal
st.set_page_config(page_title="KPI Dashboard Modern", layout="wide")

# --- CSS SAKTI: Memotong space kosong TANPA menghilangkan tombol sidebar ---
st.markdown(
    """
    <style>
        /* Pangkas space atas halaman utama */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0rem !important;
            max-width: 100% !important;
        }
        /* Perkecil jarak antar elemen (Slicer ke Grafik) */
        [data-testid="stVerticalBlock"] {
            gap: 0.5rem !important;
        }
        /* Mengecilkan area header tapi TETAP memunculkan tombol panah << */
        header[data-testid="stHeader"] {
            background-color: transparent !important;
            height: 2.5rem !important;
        }
        /* Layout perbaikan posisi konten utama */
        .main .block-container {
            margin-top: -2rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📈 Dashboard KPI Dan Analisis Cluster")

# 2. Fitur Upload File di Sidebar
st.sidebar.header("📂 Sumber Data")
uploaded_file = st.sidebar.file_uploader("Pilih file CSV atau Excel:", type=["csv", "xlsx"])

if uploaded_file is not None:
    # Membaca data secara dinamis
    with st.spinner("Sedang membaca file... Mohon tunggu"):
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
    
    all_columns = df.columns.tolist()

    # ==================== CLEANING DATA ====================
    kolom_band = next((c for c in all_columns if "band" in c.lower()), None)
    if kolom_band:
        df[kolom_band] = df[kolom_band].fillna(0).astype(int).astype(str)
        
    kolom_cluster = "(4G eNodeB FDD)MSC" if "(4G eNodeB FDD)MSC" in all_columns else all_columns[0]
    kolom_moentity = next((c for c in all_columns if "moentity" in c.lower() or "cellname" in c.lower()), None)
    kolom_date = next((c for c in all_columns if "date" in c.lower() or "tanggal" in c.lower()), None)
    
    if kolom_date:
        df[kolom_date] = pd.to_datetime(df[kolom_date]).dt.date

    # ==================== LOGIKA INTERKONEKSI SLICER ====================
    if "cluster_sel" not in st.session_state: st.session_state.cluster_sel = "Select All"
    if "mo_sel" not in st.session_state: st.session_state.mo_sel = "Select All"
    if "band_sel" not in st.session_state: st.session_state.band_sel = ["Select All"]

    st.markdown("### 🎛️ Slicers (Filter Data)")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        df_for_cluster = df.copy()
        if st.session_state.mo_sel != "Select All":
            df_for_cluster = df_for_cluster[df_for_cluster[kolom_moentity] == st.session_state.mo_sel]
        if st.session_state.band_sel and "Select All" not in st.session_state.band_sel:
            df_for_cluster = df_for_cluster[df_for_cluster[kolom_band].isin(st.session_state.band_sel)]
            
        list_cluster_unik = ["Select All"] + sorted(df_for_cluster[kolom_cluster].dropna().unique().tolist())
        idx_cluster = list_cluster_unik.index(st.session_state.cluster_sel) if st.session_state.cluster_sel in list_cluster_unik else 0
        cluster_terpilih = st.selectbox("Cluster / eNodeB", options=list_cluster_unik, index=idx_cluster, key="cluster_sel")

    with col2:
        if kolom_moentity:
            df_for_mo = df.copy()
            if st.session_state.cluster_sel != "Select All":
                df_for_mo = df_for_mo[df_for_mo[kolom_cluster] == st.session_state.cluster_sel]
            if st.session_state.band_sel and "Select All" not in st.session_state.band_sel:
                df_for_mo = df_for_mo[df_for_mo[kolom_band].isin(st.session_state.band_sel)]
                
            list_mo_unik = ["Select All"] + sorted(df_for_mo[kolom_moentity].dropna().unique().tolist())
            idx_mo = list_mo_unik.index(st.session_state.mo_sel) if st.session_state.mo_sel in list_mo_unik else 0
            mo_terpilih = st.selectbox("MOEntity / Cellname", options=list_mo_unik, index=idx_mo, key="mo_sel")
        else:
            mo_terpilih = "Select All"

    with col3:
        if kolom_band:
            df_for_band = df.copy()
            if st.session_state.cluster_sel != "Select All":
                df_for_band = df_for_band[df_for_band[kolom_cluster] == st.session_state.cluster_sel]
            if st.session_state.mo_sel != "Select All":
                df_for_band = df_for_band[df_for_band[kolom_moentity] == st.session_state.mo_sel]
                
            list_band_unik = ["Select All"] + sorted([b for b in df_for_band[kolom_band].unique() if b != '0'])
            
            current_band_sel = st.session_state.band_sel
            if len(current_band_sel) > 1 and "Select All" in current_band_sel:
                if current_band_sel[0] == "Select All":
                    st.session_state.band_sel = [x for x in current_band_sel if x != "Select All"]
                else:
                    st.session_state.band_sel = ["Select All"]
                    
            band_terpilih = st.multiselect("BAND", options=list_band_unik, key="band_sel")
        else:
            band_terpilih = ["Select All"]

    with col4:
        if kolom_date:
            min_date = df[kolom_date].min()
            max_date = df[kolom_date].max()
            start_date, end_date = st.date_input(
                "Rentang Tanggal",
                value=[min_date, max_date],
                min_value=min_date,
                max_value=max_date
            )
        else:
            start_date, end_date = None, None

    # ==================== PROSES AKHIR FILTERING DATA ====================
    df_filtered = df.copy()
    if cluster_terpilih != "Select All":
        df_filtered = df_filtered[df_filtered[kolom_cluster] == cluster_terpilih]
    if mo_terpilih != "Select All":
        df_filtered = df_filtered[df_filtered[kolom_moentity] == mo_terpilih]
    if band_terpilih and "Select All" not in band_terpilih:
        df_filtered = df_filtered[df_filtered[kolom_band].isin(band_terpilih)]
    if kolom_date and start_date and end_date:
        df_filtered = df_filtered[(df_filtered[kolom_date] >= start_date) & (df_filtered[kolom_date] <= end_date)]

    # ==================== PENGATURAN GRAFIK DI SIDEBAR ====================
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Pengaturan Grafik")
    
    opsi_kpi_blank = ["-- Pilih KPI --"] + all_columns
    idx_x = all_columns.index(kolom_date) if kolom_date in all_columns else 0
    x_axis = st.sidebar.selectbox("Sumbu X (Horizontal):", all_columns, index=idx_x)
    
    st.sidebar.markdown("---")
    y_axis_1 = st.sidebar.selectbox("KPI 1 (Sumbu Kiri):", opsi_kpi_blank, index=0)
    type_chart_1 = st.sidebar.radio("Tipe Grafik KPI 1:", ["Line", "Bar", "Area"], key="chart1")
    
    st.sidebar.markdown("---")
    y_axis_2 = st.sidebar.selectbox("KPI 2 (Sumbu Kanan - Opsional):", opsi_kpi_blank, index=0)
    type_chart_2 = st.sidebar.radio("Tipe Grafik KPI 2:", ["Bar", "Line", "Area"], key="chart2")

    # ==================== RENDER CHART DYNAMICS ====================
    st.markdown("---")
    
    if df_filtered.empty:
        st.warning("⚠️ Kombinasi Slicer menghasilkan data kosong. Silakan sesuaikan kembali filter Anda di atas.")
        
    elif y_axis_1 == "-- Pilih KPI --":
        st.info("💡 **Silakan tentukan minimal pilihan metrik pada KPI 1** di sidebar menu sebelah kiri untuk memunculkan grafik.")
        
    else:
        has_kpi2 = (y_axis_2 != "-- Pilih KPI --")
        fig = make_subplots(specs=[[{"secondary_y": has_kpi2}]])
        
        is_site_level = (mo_terpilih == "Select All")

        if is_site_level:
            cols_to_group = [x_axis, kolom_cluster]
            item_aktif = sorted(df_filtered[kolom_cluster].dropna().unique().tolist())
            kolom_label = kolom_cluster
        else:
            cols_to_group = [x_axis, kolom_moentity]
            item_aktif = [mo_terpilih]
            kolom_label = kolom_moentity

        # 1. Agregasi data awal seperti biasa
        df_aggregated = df_filtered.groupby(cols_to_group, as_index=False).agg({
            y_axis_1: 'mean',
            **({y_axis_2: 'mean'} if has_kpi2 else {})
        })

        # ==================== SOLUSI JITU: REINDEX DATE SPINE ====================
        # Jika sumbu X menggunakan Tanggal, buat sequence tanggal utuh tanpa ada yang terlewat
        if kolom_date and x_axis == kolom_date and start_date and end_date:
            # Buat list semua tanggal yang seharusnya ada
            all_dates = pd.date_range(start=start_date, end=end_date).date
            
            reindexed_frames = []
            # Lakukan reindex per item (Site atau Cell) agar tidak merusak multi-line
            for item in item_aktif:
                df_item = df_aggregated[df_aggregated[kolom_label] == item].copy()
                
                # Set tanggal sebagai index temporer untuk di-reindex
                df_item = df_item.set_index(x_axis)
                df_item = df_item.reindex(all_dates)
                df_item.index.name = x_axis
                df_item = df_item.reset_index()
                
                # Isi kolom label identitas yang kosong akibat reindex tanggal baru
                df_item[kolom_label] = item
                reindexed_frames.append(df_item)
                
            if reindexed_frames:
                df_aggregated = pd.concat(reindexed_frames, ignore_index=True)

        # SEKARANG KITA PAKSA SEMUA DATA YANG KOSONG (KARENA MISSING DATE) MENJADI NO 0 MUTLAK!
        df_aggregated[y_axis_1] = df_aggregated[y_axis_1].fillna(0)
        if has_kpi2:
            df_aggregated[y_axis_2] = df_aggregated[y_axis_2].fillna(0)

        df_aggregated = df_aggregated.sort_values(by=x_axis)

        # Hitung Nilai Tertinggi Sumbu Y secara Dinamis
        max_val_1 = df_aggregated[y_axis_1].max() if not df_aggregated.empty else 100
        max_val_2 = df_aggregated[y_axis_2].max() if (has_kpi2 and not df_aggregated.empty) else 0
        global_max = max(max_val_1, max_val_2)
        limit_y_upper = 105 if global_max <= 100 else global_max * 1.05

        # Palet Warna Dinamis
        palette_kpi1_list = ["31, 119, 180", "44, 160, 44", "148, 103, 189", "214, 39, 40", "158, 218, 229"]
        palette_kpi2_list = ["255, 127, 14", "227, 119, 194", "188, 189, 34", "23, 190, 207", "255, 187, 120"]

        def add_dynamic_trace(df_c, y_col, name_legend, chart_type, is_secondary, rgb_base):
            if chart_type == "Line":
                return go.Scatter(
                    x=df_c[x_axis], y=df_c[y_col], name=name_legend, mode='lines', 
                    line=dict(color=f"rgb({rgb_base})", width=2.5),
                    connectgaps=True,
                    showlegend=True
                )
            elif chart_type == "Bar":
                opasitas = 0.50 if is_secondary else 0.80
                return go.Bar(
                    x=df_c[x_axis], y=df_c[y_col], name=name_legend, 
                    marker_color=f"rgb({rgb_base})", opacity=opasitas,
                    showlegend=True
                )
            elif chart_type == "Area":
                return go.Scatter(
                    x=df_c[x_axis], y=df_c[y_col], name=name_legend, 
                    mode='lines',
                    line=dict(color=f"rgb({rgb_base})", width=2),
                    fill='tozeroy', 
                    fillcolor=f"rgba({rgb_base}, 0.35)",
                    connectgaps=True,
                    showlegend=True
                )

        # Render KPI 1
        for i, item in enumerate(item_aktif):
            df_c = df_aggregated[df_aggregated[kolom_label] == item]
            if not df_c.empty:
                rgb_c1 = palette_kpi1_list[i % len(palette_kpi1_list)]
                trace1 = add_dynamic_trace(df_c, y_axis_1, f"{item} ({y_axis_1})", type_chart_1, is_secondary=False, rgb_base=rgb_c1)
                fig.add_trace(trace1, secondary_y=False)
        
        # Render KPI 2
        if has_kpi2:
            for i, item in enumerate(item_aktif):
                df_c = df_aggregated[df_aggregated[kolom_label] == item]
                if not df_c.empty:
                    rgb_c2 = palette_kpi2_list[i % len(palette_kpi2_list)]
                    trace2 = add_dynamic_trace(df_c, y_axis_2, f"{item} ({y_axis_2})", type_chart_2, is_secondary=True, rgb_base=rgb_c2)
                    fig.add_trace(trace2, secondary_y=True)
        
        judul_level = "Site Level" if is_site_level else "Cell Level"
        judul_chart = f"Analisis Grafik KPI ({judul_level}): {y_axis_1}" + (f" vs {y_axis_2}" if has_kpi2 else "")
        
        fig.update_layout(
            title_text=judul_chart,
            hovermode="x unified",
            height=680, 
            margin=dict(l=110, r=65, t=110, b=260), 
            showlegend=True,
            legend=dict(
                orientation="h", 
                yanchor="top", 
                y=-0.35,                        
                xanchor="center", 
                x=0.5
            ),
            bargap=0.02,
            bargroupgap=0.0,
            shapes=[
                dict(
                    type="rect",
                    xref="paper",
                    yref="paper",
                    x0=-0.06,          
                    y0=-0.56,          
                    x1=1.04,           
                    y1=1.16,           
                    line=dict(
                        color="rgba(80, 80, 80, 0.85)",  
                        width=1.8        
                    )
                )
            ]
        )
        
        fig.update_xaxes(
            title_text=f"<b>{x_axis}</b>",
            tickformat="%m/%d/%Y",
            tickangle=-45,
            type='date',
            tickmode="linear",
            dtick=7 * 86400000,                  
            showline=True,                       
            linewidth=1.2,
            linecolor='rgba(120, 120, 120, 0.6)',  
            mirror=True,                         
            showgrid=True,
            gridcolor='rgba(220, 220, 220, 0.4)' 
        )
        
        # Sumbu Y Kiri (KPI 1)
        fig.update_yaxes(
            title_text=f"<b>{y_axis_1}</b> ({type_chart_1})", 
            secondary_y=False,
            range=[0, limit_y_upper],            
            showline=True,                       
            linewidth=1.2,
            linecolor='rgba(120, 120, 120, 0.6)',  
            mirror=True if not has_kpi2 else False, 
            showgrid=True,
            gridcolor='rgba(220, 220, 220, 0.4)' 
        )
        
        # Sumbu Y Kanan (KPI 2)
        if has_kpi2:
            fig.update_yaxes(
                title_text=f"<b>{y_axis_2}</b> ({type_chart_2})", 
                secondary_y=True,
                range=[0, limit_y_upper],        
                showline=True,                   
                linewidth=1.2,
                linecolor='rgba(120, 120, 120, 0.6)' 
            )
        
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👋 Dashboard Siap! Silakan unggah file '4G DAY.csv' Anda di sidebar sebelah kiri.")