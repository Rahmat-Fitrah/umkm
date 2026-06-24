import os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Denyut UMKM — Dasbor Usaha",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# THEME — palette terinspirasi denyut pasar: indigo malam + kunyit/marigold,
# dengan motif lingkaran bersusun (mengacu pada pola kawung) sebagai aksen tipis.
# ----------------------------------------------------------------------------
INK = "#1F2937"
PAPER = "#F5F6FA"
CARD = "#FFFFFF"
INDIGO = "#243B55"
INDIGO_DEEP = "#16243A"
GOLD = "#F2A93C"
TERRACOTTA = "#C2562F"
SAGE = "#5C8374"
MUTED = "#7A8699"

PALETTE = [INDIGO, GOLD, TERRACOTTA, SAGE, "#8E6C9E", "#3E7CB1", "#D4A276", "#4F6F52"]

CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
    color: {INK};
}}

.stApp {{
    background-color: {PAPER};
}}

h1, h2, h3, h4 {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    color: {INDIGO_DEEP} !important;
    font-weight: 700 !important;
}}

/* ---- Hero header ---- */
.hero {{
    background: linear-gradient(120deg, {INDIGO_DEEP} 0%, {INDIGO} 65%, {INDIGO} 100%);
    background-image:
        radial-gradient(circle at 8% 30%, rgba(242,169,60,0.16) 0px, rgba(242,169,60,0.16) 18px, transparent 19px),
        radial-gradient(circle at 92% 70%, rgba(242,169,60,0.10) 0px, rgba(242,169,60,0.10) 26px, transparent 27px),
        linear-gradient(120deg, {INDIGO_DEEP} 0%, {INDIGO} 65%, {INDIGO} 100%);
    border-radius: 18px;
    padding: 30px 36px;
    margin-bottom: 22px;
    box-shadow: 0 10px 28px rgba(22,36,58,0.25);
}}
.hero-eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 2px;
    text-transform: uppercase;
    font-size: 12px;
    color: {GOLD};
    margin-bottom: 6px;
}}
.hero h1 {{
    color: #FFFFFF !important;
    font-size: 34px !important;
    margin: 0 0 8px 0 !important;
}}
.hero p {{
    color: #D7DEE9;
    font-size: 15px;
    max-width: 720px;
    margin: 0;
}}

/* ---- KPI cards ---- */
.kpi-card {{
    background: {CARD};
    border: 1px solid #E6E8F0;
    border-radius: 14px;
    padding: 16px 18px;
    height: 100%;
    box-shadow: 0 2px 6px rgba(22,36,58,0.04);
}}
.kpi-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: {MUTED};
    margin-bottom: 6px;
}}
.kpi-value {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 800;
    font-size: 24px;
    color: {INDIGO_DEEP};
    line-height: 1.1;
}}
.kpi-sub {{
    font-size: 12px;
    color: {MUTED};
    margin-top: 4px;
}}
.accent-gold {{ color: {GOLD}; }}
.accent-terracotta {{ color: {TERRACOTTA}; }}

/* ---- Section divider ---- */
.section-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: {TERRACOTTA};
    border-left: 3px solid {GOLD};
    padding-left: 8px;
    margin: 6px 0 2px 0;
}}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {{
    background-color: {INDIGO_DEEP};
}}
section[data-testid="stSidebar"] * {{
    color: #E7EAF2 !important;
}}
section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] {{
    background-color: #243B55;
}}

/* ---- DataFrame ---- */
[data-testid="stDataFrame"] {{
    border-radius: 10px;
    overflow: hidden;
}}

footer {{visibility: hidden;}}
#MainMenu {{visibility: hidden;}}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, sans-serif", color=INK, size=13),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=10, r=10, t=40, b=10),
    title_font=dict(family="Plus Jakarta Sans, sans-serif", size=16, color=INDIGO_DEEP),
    legend=dict(font=dict(size=11)),
)


def style_fig(fig):
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


# ----------------------------------------------------------------------------
# FORMATTING HELPERS (Rupiah, Indonesia-style)
# ----------------------------------------------------------------------------
def fmt_rupiah(value, compact=True):
    if pd.isna(value):
        return "—"
    sign = "-" if value < 0 else ""
    value = abs(value)
    if compact:
        if value >= 1_000_000_000:
            return f"{sign}Rp{value/1_000_000_000:,.1f} M".replace(",", "@").replace(".", ",").replace("@", ".")
        if value >= 1_000_000:
            return f"{sign}Rp{value/1_000_000:,.1f} Jt".replace(",", "@").replace(".", ",").replace("@", ".")
        if value >= 1_000:
            return f"{sign}Rp{value/1_000:,.0f} rb".replace(",", "@").replace(".", ",").replace("@", ".")
    return f"{sign}Rp{value:,.0f}".replace(",", ".")


def fmt_int(value):
    if pd.isna(value):
        return "—"
    return f"{value:,.0f}".replace(",", ".")


def fmt_pct(value):
    if pd.isna(value):
        return "—"
    return f"{value*100:,.1f}%".replace(".", ",")


# ----------------------------------------------------------------------------
# DATA LOADING & CLEANING
# ----------------------------------------------------------------------------
NUMERIC_COLS = [
    "tenaga_kerja_perempuan", "tenaga_kerja_laki_laki", "aset", "omset",
    "kapasitas_produksi", "tahun_berdiri", "laba", "biaya_karyawan", "jumlah_pelanggan",
]
CATEGORICAL_COLS = ["jenis_usaha", "marketplace", "status_legalitas"]


@st.cache_data(show_spinner=False)
def load_data(file):
    df = pd.read_csv(file)
    df.columns = [c.strip() for c in df.columns]

    # Normalisasi nilai kosong: string "unknown" diperlakukan sebagai data hilang
    df = df.replace({"unknown": np.nan, "Unknown": np.nan, "UNKNOWN": np.nan, "": np.nan})

    for c in NUMERIC_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    if "tahun_berdiri" in df.columns:
        df["tahun_berdiri"] = df["tahun_berdiri"].astype("Int64")

    for c in CATEGORICAL_COLS:
        if c in df.columns:
            df[c] = df[c].fillna("Tidak diketahui")

    df["nama_usaha"] = df["nama_usaha"].fillna("(Tanpa nama)")

    # Kolom turunan
    df["total_tenaga_kerja"] = df[["tenaga_kerja_perempuan", "tenaga_kerja_laki_laki"]].sum(
        axis=1, min_count=1
    )
    df["margin_laba"] = np.where(
        (df["omset"].notna()) & (df["omset"] != 0), df["laba"] / df["omset"], np.nan
    )
    df["umur_usaha"] = 2026 - df["tahun_berdiri"]

    return df


DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "datase_usaha.csv")

if os.path.exists(DEFAULT_PATH):
    df_raw = load_data(DEFAULT_PATH)
else:
    st.markdown(
        "<div class='hero'><div class='hero-eyebrow'>Denyut UMKM</div>"
        "<h1>Dasbor Usaha Mikro, Kecil & Menengah</h1>"
        "<p>Unggah berkas CSV data UMKM untuk mulai menjelajah.</p></div>",
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader("Unggah file CSV (struktur kolom sama seperti dataset UMKM)", type=["csv"])
    if uploaded is None:
        st.info("Menunggu berkas CSV diunggah untuk menampilkan dasbor.")
        st.stop()
    df_raw = load_data(uploaded)

# ----------------------------------------------------------------------------
# HERO
# ----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="hero">
        <div class="hero-eyebrow">Denyut UMKM · Dasbor Interaktif</div>
        <h1>Potret Usaha Mikro, Kecil &amp; Menengah</h1>
        <p>Jelajahi {fmt_int(len(df_raw))} catatan usaha — sebaran sektor, kinerja omset &amp; laba,
        legalitas, kanal pemasaran, hingga komposisi tenaga kerja. Gunakan panel di sisi kiri
        untuk menyaring data sesuai kebutuhan analisis Anda.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# SIDEBAR — FILTERS
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔎 Filter Data")

    search_text = st.text_input("Cari nama usaha", placeholder="mis. UD. Alif")

    jenis_opts = sorted(df_raw["jenis_usaha"].dropna().unique().tolist())
    pilih_jenis = st.multiselect("Jenis usaha", jenis_opts, default=jenis_opts)

    mp_opts = sorted(df_raw["marketplace"].dropna().unique().tolist())
    pilih_mp = st.multiselect("Kanal pemasaran", mp_opts, default=mp_opts)

    legal_opts = sorted(df_raw["status_legalitas"].dropna().unique().tolist())
    pilih_legal = st.multiselect("Status legalitas", legal_opts, default=legal_opts)

    th_min = int(df_raw["tahun_berdiri"].min(skipna=True))
    th_max = int(df_raw["tahun_berdiri"].max(skipna=True))
    rentang_tahun = st.slider("Tahun berdiri", th_min, th_max, (th_min, th_max))

    om_min = float(np.nanmin(df_raw["omset"]))
    om_max = float(np.nanmax(df_raw["omset"]))
    rentang_omset = st.slider(
        "Rentang omset (Rp)", om_min, om_max, (om_min, om_max),
        format="%.0f",
    )

    st.markdown("---")
    st.caption("Sumber data: dataset UMKM (Kaggle — dhearahmadianti/dataset-untuk-umkm). "
               "Nilai 'unknown' & kosong dibersihkan otomatis sebelum analisis.")

# Terapkan filter
df = df_raw[
    df_raw["jenis_usaha"].isin(pilih_jenis)
    & df_raw["marketplace"].isin(pilih_mp)
    & df_raw["status_legalitas"].isin(pilih_legal)
    & df_raw["tahun_berdiri"].between(rentang_tahun[0], rentang_tahun[1], inclusive="both")
    & df_raw["omset"].between(rentang_omset[0], rentang_omset[1], inclusive="both")
]
if search_text:
    df = df[df["nama_usaha"].str.contains(search_text, case=False, na=False)]

if df.empty:
    st.warning("Tidak ada data yang cocok dengan filter saat ini. Coba longgarkan filter di sisi kiri.")
    st.stop()

# ----------------------------------------------------------------------------
# KPI ROW
# ----------------------------------------------------------------------------
total_usaha = len(df)
total_omset = df["omset"].sum()
total_laba = df["laba"].sum()
rata_margin = df["margin_laba"].mean()
pct_terdaftar = (df["status_legalitas"] == "Terdaftar").mean()
rata_pelanggan = df["jumlah_pelanggan"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
kpi_data = [
    (k1, "Jumlah UMKM", fmt_int(total_usaha), f"dari {fmt_int(len(df_raw))} total catatan"),
    (k2, "Total Omset", fmt_rupiah(total_omset), "akumulasi seluruh usaha tersaring"),
    (k3, "Total Laba", fmt_rupiah(total_laba), "akumulasi seluruh usaha tersaring"),
    (k4, "Rata-rata Margin Laba", fmt_pct(rata_margin), "laba ÷ omset, dirata-ratakan"),
    (k5, "Usaha Terdaftar Legal", fmt_pct(pct_terdaftar), "berstatus 'Terdaftar'"),
]
for col, label, value, sub in kpi_data:
    with col:
        st.markdown(
            f"""<div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-sub">{sub}</div>
                </div>""",
            unsafe_allow_html=True,
        )

st.write("")

# ----------------------------------------------------------------------------
# TABS
# ----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Ringkasan", "🗂️ Sebaran Usaha", "💰 Kinerja Keuangan", "👥 Tenaga Kerja", "📋 Jelajahi Data"]
)

# ---- TAB 1: RINGKASAN ----
with tab1:
    st.markdown("<div class='section-tag'>Tren Pertumbuhan</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([1.4, 1])

    with c1:
        per_tahun = (
            df.dropna(subset=["tahun_berdiri"])
            .groupby("tahun_berdiri", as_index=False)
            .agg(jumlah=("id_umkm", "count"), total_omset=("omset", "sum"))
            .sort_values("tahun_berdiri")
        )
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=per_tahun["tahun_berdiri"], y=per_tahun["jumlah"],
            marker_color=GOLD, name="Jumlah usaha berdiri", opacity=0.85,
        ))
        fig.update_layout(
            title="Jumlah Usaha Baru per Tahun Berdiri",
            xaxis_title="Tahun", yaxis_title="Jumlah usaha",
        )
        st.plotly_chart(style_fig(fig), use_container_width=True)

    with c2:
        per_jenis = df["jenis_usaha"].value_counts().reset_index()
        per_jenis.columns = ["jenis_usaha", "jumlah"]
        fig2 = px.bar(
            per_jenis.sort_values("jumlah"), x="jumlah", y="jenis_usaha",
            orientation="h", color="jenis_usaha", color_discrete_sequence=PALETTE,
            title="Jumlah UMKM per Jenis Usaha",
        )
        fig2.update_layout(showlegend=False, yaxis_title="", xaxis_title="Jumlah usaha")
        st.plotly_chart(style_fig(fig2), use_container_width=True)

    st.markdown("<div class='section-tag'>Skala Usaha</div>", unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        fig3 = px.histogram(
            df, x="omset", nbins=40, color_discrete_sequence=[INDIGO],
            title="Distribusi Omset Usaha",
        )
        fig3.update_layout(xaxis_title="Omset (Rp)", yaxis_title="Jumlah usaha", bargap=0.05)
        st.plotly_chart(style_fig(fig3), use_container_width=True)
    with c4:
        fig4 = px.histogram(
            df, x="laba", nbins=40, color_discrete_sequence=[TERRACOTTA],
            title="Distribusi Laba Usaha",
        )
        fig4.add_vline(x=0, line_dash="dash", line_color=INK, opacity=0.5)
        fig4.update_layout(xaxis_title="Laba (Rp)", yaxis_title="Jumlah usaha", bargap=0.05)
        st.plotly_chart(style_fig(fig4), use_container_width=True)

# ---- TAB 2: SEBARAN USAHA ----
with tab2:
    c1, c2 = st.columns(2)
    with c1:
        mp_count = df["marketplace"].value_counts().reset_index()
        mp_count.columns = ["marketplace", "jumlah"]
        fig5 = px.pie(
            mp_count, names="marketplace", values="jumlah", hole=0.55,
            color_discrete_sequence=PALETTE, title="Distribusi Kanal Pemasaran",
        )
        fig5.update_traces(textinfo="percent+label")
        st.plotly_chart(style_fig(fig5), use_container_width=True)

    with c2:
        legal_count = df["status_legalitas"].value_counts().reset_index()
        legal_count.columns = ["status_legalitas", "jumlah"]
        fig6 = px.pie(
            legal_count, names="status_legalitas", values="jumlah", hole=0.55,
            color_discrete_sequence=[SAGE, TERRACOTTA, MUTED],
            title="Status Legalitas Usaha",
        )
        fig6.update_traces(textinfo="percent+label")
        st.plotly_chart(style_fig(fig6), use_container_width=True)

    st.markdown("<div class='section-tag'>Persilangan Sektor &amp; Legalitas</div>", unsafe_allow_html=True)
    cross = (
        df.groupby(["jenis_usaha", "status_legalitas"])
        .size()
        .reset_index(name="jumlah")
    )
    fig7 = px.bar(
        cross, x="jenis_usaha", y="jumlah", color="status_legalitas",
        barmode="stack", color_discrete_sequence=[SAGE, TERRACOTTA, MUTED],
        title="Jumlah Usaha per Jenis Usaha, dipecah menurut Status Legalitas",
    )
    fig7.update_layout(xaxis_title="", yaxis_title="Jumlah usaha")
    st.plotly_chart(style_fig(fig7), use_container_width=True)

# ---- TAB 3: KINERJA KEUANGAN ----
with tab3:
    st.markdown("<div class='section-tag'>Omset vs Laba</div>", unsafe_allow_html=True)
    sample_df = df.dropna(subset=["omset", "laba", "jumlah_pelanggan"])
    if len(sample_df) > 3000:
        sample_df = sample_df.sample(3000, random_state=42)
    fig8 = px.scatter(
        sample_df, x="omset", y="laba", color="jenis_usaha",
        size="jumlah_pelanggan", size_max=18, opacity=0.7,
        color_discrete_sequence=PALETTE,
        hover_data=["nama_usaha", "marketplace", "status_legalitas"],
        title="Sebaran Omset vs Laba (ukuran titik = jumlah pelanggan)",
    )
    fig8.add_hline(y=0, line_dash="dash", line_color=INK, opacity=0.4)
    fig8.update_layout(xaxis_title="Omset (Rp)", yaxis_title="Laba (Rp)")
    st.plotly_chart(style_fig(fig8), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        agg_fin = (
            df.groupby("jenis_usaha", as_index=False)
            .agg(rata_omset=("omset", "mean"), rata_laba=("laba", "mean"))
            .sort_values("rata_omset", ascending=False)
        )
        fig9 = go.Figure()
        fig9.add_trace(go.Bar(x=agg_fin["jenis_usaha"], y=agg_fin["rata_omset"],
                               name="Rata-rata Omset", marker_color=INDIGO))
        fig9.add_trace(go.Bar(x=agg_fin["jenis_usaha"], y=agg_fin["rata_laba"],
                               name="Rata-rata Laba", marker_color=GOLD))
        fig9.update_layout(barmode="group", title="Rata-rata Omset &amp; Laba per Jenis Usaha",
                            xaxis_title="", yaxis_title="Rp")
        st.plotly_chart(style_fig(fig9), use_container_width=True)

    with c2:
        agg_mp = (
            df.groupby("marketplace", as_index=False)["margin_laba"].mean()
            .sort_values("margin_laba", ascending=False)
        )
        fig10 = px.bar(
            agg_mp, x="marketplace", y="margin_laba", color="marketplace",
            color_discrete_sequence=PALETTE, title="Rata-rata Margin Laba per Kanal Pemasaran",
        )
        fig10.update_layout(showlegend=False, xaxis_title="", yaxis_title="Margin laba")
        fig10.update_yaxes(tickformat=".0%")
        st.plotly_chart(style_fig(fig10), use_container_width=True)

    st.markdown("<div class='section-tag'>10 Usaha dengan Laba Tertinggi</div>", unsafe_allow_html=True)
    top10 = df.nlargest(10, "laba")[
        ["nama_usaha", "jenis_usaha", "marketplace", "status_legalitas", "omset", "laba", "jumlah_pelanggan"]
    ].copy()
    top10["omset"] = top10["omset"].apply(lambda v: fmt_rupiah(v, compact=False))
    top10["laba"] = top10["laba"].apply(lambda v: fmt_rupiah(v, compact=False))
    st.dataframe(top10, use_container_width=True, hide_index=True)

# ---- TAB 4: TENAGA KERJA ----
with tab4:
    c1, c2 = st.columns(2)
    with c1:
        tk = (
            df.groupby("jenis_usaha", as_index=False)
            .agg(perempuan=("tenaga_kerja_perempuan", "mean"),
                 laki_laki=("tenaga_kerja_laki_laki", "mean"))
            .sort_values("jenis_usaha")
        )
        fig11 = go.Figure()
        fig11.add_trace(go.Bar(x=tk["jenis_usaha"], y=tk["perempuan"],
                                name="Tenaga kerja perempuan", marker_color=TERRACOTTA))
        fig11.add_trace(go.Bar(x=tk["jenis_usaha"], y=tk["laki_laki"],
                                name="Tenaga kerja laki-laki", marker_color=INDIGO))
        fig11.update_layout(barmode="group", title="Rata-rata Tenaga Kerja per Jenis Usaha",
                             xaxis_title="", yaxis_title="Rata-rata jumlah orang")
        st.plotly_chart(style_fig(fig11), use_container_width=True)

    with c2:
        fig12 = px.histogram(
            df, x="total_tenaga_kerja", nbins=30, color_discrete_sequence=[SAGE],
            title="Distribusi Total Tenaga Kerja per Usaha",
        )
        fig12.update_layout(xaxis_title="Total tenaga kerja", yaxis_title="Jumlah usaha", bargap=0.05)
        st.plotly_chart(style_fig(fig12), use_container_width=True)

    st.markdown("<div class='section-tag'>Efisiensi Biaya Karyawan</div>", unsafe_allow_html=True)
    eff = df.dropna(subset=["biaya_karyawan", "total_tenaga_kerja"]).copy()
    eff = eff[eff["total_tenaga_kerja"] > 0]
    eff["biaya_per_pekerja"] = eff["biaya_karyawan"] / eff["total_tenaga_kerja"]
    fig13 = px.box(
        eff, x="jenis_usaha", y="biaya_per_pekerja", color="jenis_usaha",
        color_discrete_sequence=PALETTE,
        title="Sebaran Biaya Karyawan per Pekerja, menurut Jenis Usaha",
    )
    fig13.update_layout(showlegend=False, xaxis_title="", yaxis_title="Biaya per pekerja (Rp)")
    st.plotly_chart(style_fig(fig13), use_container_width=True)

# ---- TAB 5: JELAJAHI DATA ----
with tab5:
    st.markdown("<div class='section-tag'>Tabel Data Tersaring</div>", unsafe_allow_html=True)
    st.caption(f"Menampilkan {fmt_int(len(df))} dari {fmt_int(len(df_raw))} total catatan, sesuai filter aktif.")

    kolom_tampil = st.multiselect(
        "Pilih kolom yang ditampilkan",
        options=df_raw.columns.tolist(),
        default=[
            "nama_usaha", "jenis_usaha", "marketplace", "status_legalitas",
            "tahun_berdiri", "omset", "laba", "total_tenaga_kerja", "jumlah_pelanggan",
        ],
    )
    st.dataframe(df[kolom_tampil], use_container_width=True, hide_index=True)

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Unduh data tersaring (CSV)",
        data=csv_bytes,
        file_name="umkm_data_tersaring.csv",
        mime="text/csv",
    )

    with st.expander("ℹ️ Tentang dataset & pembersihan data"):
        st.markdown(
            """
Dataset memuat catatan UMKM dengan kolom: nama usaha, jenis usaha, jumlah tenaga kerja
(perempuan/laki-laki), aset, omset, kanal pemasaran (marketplace), kapasitas produksi,
status legalitas, tahun berdiri, laba, biaya karyawan, dan jumlah pelanggan.

**Pembersihan yang diterapkan secara otomatis:**
- Nilai teks `"unknown"` diubah menjadi data hilang (missing), lalu dikategorikan sebagai
  *"Tidak diketahui"* pada kolom kategorikal.
- Kolom numerik dipaksa ke tipe angka; nilai yang tidak valid diubah menjadi kosong.
- Kolom turunan ditambahkan: **total tenaga kerja** (perempuan + laki-laki) dan
  **margin laba** (laba ÷ omset).

Gunakan filter pada sisi kiri untuk menyaring data, lalu unduh hasilnya dalam format CSV
melalui tombol di atas.
            """
        )

# ----------------------------------------------------------------------------
# FOOTER
# ----------------------------------------------------------------------------
st.markdown(
    f"<div style='text-align:center; color:{MUTED}; font-size:12px; padding: 18px 0 6px 0;'>"
    "Dibuat dengan Streamlit · Sumber data: Kaggle — dataset-untuk-umkm (dhearahmadianti)"
    "</div>",
    unsafe_allow_html=True,
)
