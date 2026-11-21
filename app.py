import base64
import html
import itertools
import textwrap
from pathlib import Path

import io

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from eda import (
    STATUS_LANJUT,
    alokasikan_waffle,
    alumni_dapat_dibandingkan,
    banding_jenis_pekerjaan,
    distribusi_alumni,
    distribusi_pekerjaan_tahap,
    distribusi_studi_lanjut,
    filter_data,
    kelengkapan_data,
    kelengkapan_per_kelompok,
    karakteristik_alumni,
    matriks_jenis_pekerjaan,
    perpindahan_pekerjaan,
    pola_keterisian_pekerjaan,
    rincian_jenis_pekerjaan_lainnya,
    ringkasan_per_program_studi,
    ringkasan_lanjut_studi_per,
    ringkasan_perubahan_pekerjaan,
    studi_lanjut,
)
from preprocessing import load_data

# =========================================================
# LOGO (opsional)
# =========================================================
# Letakkan file gambar di folder "assets" dengan nama logo.png
# (atau logo.jpg, logo.jpeg, logo.webp, logo.svg). Jika tidak ada,
# dashboard memakai monogram "TS".

FOLDER_ASET = Path(__file__).resolve().parent / "assets"
MIME_LOGO = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}


def cari_logo():
    for nama in ("logo.png", "logo.jpg", "logo.jpeg", "logo.webp", "logo.svg"):
        lokasi = FOLDER_ASET / nama
        if lokasi.exists():
            return lokasi
    return None


def ikon_halaman(logo):
    """Ikon tab browser: logo jika ada (selain svg), jika tidak emoji topi wisuda."""
    if logo is not None and logo.suffix.lower() != ".svg":
        try:
            from PIL import Image

            return Image.open(logo)
        except Exception:
            pass
    return "🎓"


LOGO = cari_logo()

st.set_page_config(
    page_title="Tracer Study Alumni UNSRI",
    page_icon=ikon_halaman(LOGO),
    layout="wide",
    initial_sidebar_state="auto",
)


@st.cache_data
def logo_base64(lokasi, waktu_ubah):
    # waktu_ubah ikut menjadi kunci cache: logo yang diganti langsung terbaca
    return base64.b64encode(Path(lokasi).read_bytes()).decode("ascii")


def html_brand():
    if LOGO is not None:
        data = logo_base64(str(LOGO), LOGO.stat().st_mtime)
        mime = MIME_LOGO.get(LOGO.suffix.lower(), "image/png")
        isi_logo = f'<div class="brand-logo berlogo"><img src="data:{mime};base64,{data}" alt="Logo"></div>'
    else:
        isi_logo = '<div class="brand-logo">TS</div>'
    return (
        f'<div class="brand">{isi_logo}'
        '<span class="brand-nama">eMwaY Tracer</span>'
        '<span class="brand-sub">Universitas Sriwijaya</span></div>'
    )


# =========================================================
# TAMPILAN: WARNA DAN GAYA
# =========================================================
# Gaya mengacu pada dashboard referensi: permukaan datar dengan garis tipis,
# aksen pink, netral slate, dan angka bergaya monospasi.
# Warna latar, garis, dan teks mengikuti mode terang/gelap lewat CSS light-dark()
# dan tema di .streamlit/config.toml.

PINK = "#EC4899"
TEAL = "#14B8A6"
AMBER = "#F59E0B"
SLATE = "#64748B"
SLATE_SOFT = "#94A3B8"
NETRAL = "#64748B"

PALET_UMUM = [PINK, TEAL, AMBER, SLATE, SLATE_SOFT]
PALET_STUDI = [PINK, SLATE, TEAL, AMBER]
WARNA_STATUS = {"LANJUT STUDI": PINK, "TIDAK LANJUT STUDI": NETRAL}

FONT = "Plus Jakarta Sans, Arial, sans-serif"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

.stApp {
    --canvas: light-dark(#F8FAFC, #0B0F14);
    --surface: light-dark(#FFFFFF, #11171F);
    --subtle: light-dark(#F1F5F9, #161E29);
    --hairline: light-dark(#E2E8F0, #1E2733);
    --strong: light-dark(#CBD5E1, #2C394B);
    --heading: light-dark(#0F172A, #F1F5F9);
    --body: light-dark(#334155, #CBD5E1);
    --muted: light-dark(#64748B, #8B9BB4);
    --pink: light-dark(#DB2777, #EC4899);
    --pink-soft: light-dark(rgba(219,39,119,.10), rgba(236,72,153,.12));
    --pink-border: light-dark(rgba(219,39,119,.28), rgba(236,72,153,.32));
    --up: light-dark(#059669, #10B981);
    --down: light-dark(#DC2626, #EF4444);
    font-family: 'Plus Jakarta Sans', Arial, sans-serif;
}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp label,
.stApp button, .stApp input, .stApp textarea {
    font-family: 'Plus Jakarta Sans', Arial, sans-serif;
}
header[data-testid="stHeader"] {
    background: var(--surface); border-bottom: 1px solid var(--hairline);
}
[data-testid="stWidgetLabel"] p {
    font-size: .72rem; font-weight: 600; color: var(--muted); letter-spacing: .02em;
}
.st-key-ekspor button { background: var(--pink); border-color: transparent; }
.st-key-ekspor button, .st-key-ekspor button p, .st-key-ekspor button span { color: #FFFFFF !important; }
.block-container { max-width: 1400px; padding: 4.6rem 2.5rem 3rem; }

/* ---------- Teks dan angka ---------- */
.mono, .kpi-nilai, .kpi-delta, .ph-stat span, .strip b, .pk-baris b, .pk-label b {
    font-family: 'JetBrains Mono', ui-monospace, monospace; font-variant-numeric: tabular-nums;
}

/* ---------- Brand dan aksi atas ---------- */
.brand { display: flex; align-items: center; gap: .7rem; min-height: 40px; }
.brand-logo {
    width: 34px; height: 34px; flex: none; border-radius: 10px; background: var(--pink);
    color: #fff; display: grid; place-items: center; font-weight: 700; font-size: .78rem;
}
.brand-logo.berlogo { background: #FFFFFF; border: 1px solid var(--hairline); padding: 2px; overflow: hidden; }
.brand-logo img { width: 100%; height: 100%; object-fit: contain; }
.brand-nama { font-weight: 600; color: var(--heading); font-size: .92rem; letter-spacing: -.005em; }
.brand-sub { color: var(--muted); font-size: .78rem; }
.brand-sub::before { content: "/"; margin: 0 .55rem; color: var(--strong); }

/* ---------- Judul halaman ---------- */
.ph { border-bottom: 1px solid var(--hairline); padding: 1.1rem 0 1.2rem; margin-bottom: .9rem; }
.ph h1 {
    font-size: 1.65rem; font-weight: 600; color: var(--heading); letter-spacing: -.012em;
    margin: 0 0 .45rem; padding: 0;
}
.ph p { color: var(--muted); font-size: .9rem; max-width: 760px; margin: 0 0 .7rem; line-height: 1.7; }
.ph-stat { font-size: .76rem; color: var(--muted); display: flex; gap: .65rem; flex-wrap: wrap; }

/* ---------- Strip cakupan ---------- */
.strip {
    display: flex; flex-wrap: wrap; justify-content: space-between; gap: .35rem 1.6rem;
    font-size: .78rem; color: var(--muted); margin: .1rem 0 1.2rem;
}
.strip b { color: var(--heading); font-weight: 600; }

/* ---------- Kartu ---------- */
[class*="st-key-kartu"] {
    background: var(--surface); border: 1px solid var(--hairline); border-radius: 12px;
    padding: 1.4rem 1.5rem; transition: border-color .15s;
}
[class*="st-key-kartu"]:hover { border-color: var(--strong); }
.kt {
    font-size: .75rem; font-weight: 600; letter-spacing: .04em; text-transform: uppercase;
    color: var(--heading);
}
.ks { color: var(--muted); font-size: .76rem; line-height: 1.65; margin: .35rem 0 .75rem; }
.sec {
    color: var(--heading); font-weight: 600; font-size: .78rem; letter-spacing: .04em;
    text-transform: uppercase; margin: 1.3rem 0 .2rem;
}

/* ---------- Kartu KPI ---------- */
.kpi {
    background: var(--surface); border: 1px solid var(--hairline); border-radius: 12px;
    padding: 1.15rem 1.3rem; display: flex; flex-direction: column; justify-content: space-between;
    gap: 1rem; min-height: 128px; transition: border-color .15s;
}
.kpi:hover { border-color: var(--strong); }
.kpi-top { display: flex; justify-content: space-between; align-items: flex-start; gap: .5rem; }
.kpi-label {
    font-size: .68rem; font-weight: 600; text-transform: uppercase; letter-spacing: .05em;
    color: var(--muted);
}
.kpi-delta { font-size: .72rem; font-weight: 500; white-space: nowrap; color: var(--muted); }
.kpi-delta.up { color: var(--up); }
.kpi-delta.down { color: var(--down); }
.kpi-body { display: flex; justify-content: space-between; align-items: flex-end; gap: .8rem; }
.kpi-nilai { font-size: 1.85rem; font-weight: 600; color: var(--heading); line-height: 1; }
.kpi-nilai.kecil { font-size: 1.02rem; line-height: 1.3; }
.kpi-ket { margin-top: .55rem; font-size: .72rem; color: var(--muted); }

/* ---------- Chip ---------- */
.chip {
    display: inline-flex; align-items: center; padding: .2rem .7rem; border-radius: 8px;
    font-size: .75rem; font-weight: 500; background: var(--pink-soft);
    border: 1px solid var(--pink-border); color: var(--heading); margin: 0 .35rem .3rem 0;
}

/* ---------- Isi dialog catatan ----------
   Dialog dirender di luar .stApp, jadi tidak memakai variabel warna tema:
   teks mewarisi warna dialog dan garis memakai abu-abu transparan. */
.pk-baris {
    display: flex; justify-content: space-between; gap: .6rem; font-size: .82rem;
    padding: .5rem 0; border-bottom: 1px solid rgba(148,163,184,.28);
}
.pk-baris span { opacity: .75; }
.pk-baris b { font-weight: 600; text-align: right; font-family: 'JetBrains Mono', ui-monospace, monospace; }
.pk-judul {
    font-size: .72rem; font-weight: 600; text-transform: uppercase; letter-spacing: .05em;
    margin: 1.2rem 0 .5rem;
}
.pk-bar { height: 6px; border-radius: 99px; background: rgba(148,163,184,.28); margin: .3rem 0 .8rem; overflow: hidden; }
.pk-bar span { display: block; height: 100%; background: #EC4899; border-radius: 99px; }
.pk-label { font-size: .8rem; display: flex; justify-content: space-between; gap: .6rem; }
.pk-label span { opacity: .8; }
.pk-label b { font-family: 'JetBrains Mono', ui-monospace, monospace; }
.pk ul { margin: 0; padding-left: 1.1rem; font-size: .8rem; line-height: 1.7; }
.pk ul li { margin-bottom: .35rem; }
.pk-kecil { font-size: .76rem; opacity: .7; }

/* ---------- Waffle ---------- */
.wf { display: flex; gap: 1.8rem; align-items: center; flex-wrap: wrap; }
.wf-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 4px; width: 230px; flex: none; }
.wf-kotak { aspect-ratio: 1 / 1; border-radius: 3px; }
.wf-legenda { flex: 1; min-width: 200px; }
.wf-baris {
    display: flex; align-items: center; gap: .55rem; font-size: .78rem; padding: .38rem 0;
    border-bottom: 1px dashed var(--hairline);
}
.wf-titik { width: 9px; height: 9px; border-radius: 3px; flex: none; }
.wf-label { flex: 1; color: var(--body); }
.wf-nilai { color: var(--heading); font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: .74rem; }

@media (max-width: 760px) {
    .block-container { padding: 4.2rem 1rem 2rem; }
    .ph h1 { font-size: 1.3rem; }
    .kpi-nilai { font-size: 1.5rem; }
    .brand-sub { display: none; }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# Penomoran kunci kartu: dibuat ulang setiap script dijalankan
_hitung_kartu = itertools.count()


def kartu():
    """Wadah bergaya kartu (gaya diatur lewat CSS kelas st-key-kartu...)."""
    return st.container(key=f"kartu-{next(_hitung_kartu)}")


# =========================================================
# KOMPONEN: KARTU KPI DAN SPARKLINE
# =========================================================

_hitung_spark = itertools.count()


def sparkline_svg(nilai, nada="pink"):
    """Grafik mini (garis + area) untuk kartu KPI, dibuat sebagai SVG."""
    if len(nilai) < 2:
        return ""
    lebar, tinggi, pad = 88, 32, 3
    kecil, besar = min(nilai), max(nilai)
    rentang = (besar - kecil) or 1
    titik = [
        (pad + i / (len(nilai) - 1) * (lebar - 2 * pad),
         tinggi - pad - (v - kecil) / rentang * (tinggi - 2 * pad))
        for i, v in enumerate(nilai)
    ]
    garis = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(titik))
    area = f"{garis} L{titik[-1][0]:.1f},{tinggi} L{titik[0][0]:.1f},{tinggi} Z"
    warna = {"naik": "var(--up)", "turun": "var(--down)"}.get(nada, "var(--pink)")
    gid = f"sp{next(_hitung_spark)}"
    return (
        f'<svg width="{lebar}" height="{tinggi}" viewBox="0 0 {lebar} {tinggi}" '
        'style="overflow:visible;flex:none" aria-hidden="true">'
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" style="stop-color:{warna};stop-opacity:.22"/>'
        f'<stop offset="100%" style="stop-color:{warna};stop-opacity:0"/></linearGradient></defs>'
        f'<path d="{area}" fill="url(#{gid})"/>'
        f'<path d="{garis}" fill="none" style="stroke:{warna}" stroke-width="1.75" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="{titik[-1][0]:.1f}" cy="{titik[-1][1]:.1f}" r="2.5" style="fill:{warna}"/></svg>'
    )


def delta_periode(label, nilai, jenis="jumlah"):
    """Perubahan periode terakhir dibanding periode sebelumnya.

    jenis "jumlah": perubahan relatif dalam persen.
    jenis "persen": selisih dalam poin persentase.
    Mengembalikan dict (teks, nada, tip) atau None bila datanya belum cukup.
    """
    if len(nilai) < 2:
        return None
    sebelum, terakhir = nilai[-2], nilai[-1]
    if jenis == "persen":
        selisih = terakhir - sebelum
        besar = format_desimal(abs(selisih), 1) + " poin"
    else:
        if sebelum == 0:
            return None
        selisih = (terakhir - sebelum) / sebelum * 100
        besar = format_desimal(abs(selisih), 1) + "%"

    if selisih > 0:
        nada, panah, tanda = "up", "▲ ", "+"
    elif selisih < 0:
        nada, panah, tanda = "down", "▼ ", "-"
    else:
        nada, panah, tanda = "neutral", "", ""

    return {
        "teks": f"{panah}{tanda}{besar}",
        "nada": nada,
        "tip": f"Periode {label[-1]} dibandingkan periode {label[-2]}",
    }


def kartu_metrik(ikon, label, nilai, keterangan="", pink=False, kecil=False,
                 delta=None, spark=None, nada_spark="pink"):
    """Kartu KPI. Parameter `ikon` dan `pink` dipertahankan agar pemanggilan lama
    tetap berjalan, tetapi gaya referensi tidak memakai ikon."""
    delta_html = ""
    if delta:
        delta_html = (
            f'<span class="kpi-delta {delta["nada"]}" title="{html.escape(delta.get("tip", ""))}">'
            f'{html.escape(delta["teks"])}</span>'
        )
    ket = f'<div class="kpi-ket">{html.escape(keterangan)}</div>' if keterangan else ""
    kelas_nilai = "kpi-nilai kecil" if kecil else "kpi-nilai"
    grafik_mini = sparkline_svg(spark, nada_spark) if spark else ""
    return (
        f'<div class="kpi"><div class="kpi-top"><span class="kpi-label">{html.escape(label)}</span>'
        f"{delta_html}</div>"
        f'<div class="kpi-body"><div style="min-width:0"><div class="{kelas_nilai}">'
        f'{html.escape(str(nilai))}</div>{ket}</div>{grafik_mini}</div></div>'
    )


def kepala(judul, keterangan=""):
    """Judul kartu (HTML, mengikuti warna tema)."""
    ket = f'<div class="ks">{html.escape(keterangan)}</div>' if keterangan else ""
    st.markdown(f'<div class="kt">{html.escape(judul)}</div>{ket}', unsafe_allow_html=True)


# =========================================================
# DATA
# =========================================================

@st.cache_data
def muat_data():
    # cache_data: Excel hanya dibaca sekali, bukan setiap pengguna mengubah filter
    return load_data()


df = muat_data()


# =========================================================
# FUNGSI BANTU: FORMAT ANGKA
# =========================================================

def format_angka(angka):
    """12345 -> '12.345' (pemisah ribuan titik, gaya Indonesia)."""
    return f"{int(angka):,}".replace(",", ".")


def format_desimal(angka, digit=2):
    """7.3 -> '7,30' (pemisah desimal koma, gaya Indonesia)."""
    return f"{angka:.{digit}f}".replace(".", ",")


def catatan_terisi(seri, jumlah_dasar):
    """Teks kecil: berapa data yang terisi dibandingkan dasar perhitungannya."""
    return (
        f"Data terisi: {format_angka(seri.sum())} dari "
        f"{format_angka(jumlah_dasar)} alumni lanjut studi."
    )


# =========================================================
# FUNGSI BANTU: GRAFIK
# =========================================================
# Warna teks grafik mengikuti tema Streamlit (terang/gelap),
# jadi tidak diatur di sini. Latar dibuat transparan agar warna kartu terlihat.

def rapikan(gambar, sembunyikan=None, tinggi=None, legenda=True, margin_kanan=10):
    gambar.update_layout(
        title={"text": ""},
        font={"family": FONT, "size": 12.5},
        margin={"l": 0, "r": margin_kanan, "t": 10, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=legenda,
        legend={"title": {"text": ""}, "orientation": "h", "y": -0.05, "x": 0.5, "xanchor": "center"},
        height=tinggi,
    )
    gambar.update_xaxes(showgrid=False, title_text="")
    gambar.update_yaxes(showgrid=False, title_text="")

    if sembunyikan == "x":
        gambar.update_xaxes(visible=False)
    elif sembunyikan == "y":
        gambar.update_yaxes(visible=False)

    return gambar


def tampilkan_grafik(gambar, nama_file="grafik-tracer-study"):
    # Hanya tombol kamera (unduh PNG) yang ditampilkan saat kursor di atas grafik
    st.plotly_chart(
        gambar,
        width="stretch",
        config={
            "displayModeBar": "hover",
            "displaylogo": False,
            "modeBarButtons": [["toImage"]],
            "toImageButtonOptions": {"format": "png", "scale": 2, "filename": nama_file},
        },
    )


def bungkus(teks, lebar=30):
    """Label panjang dipecah menjadi beberapa baris agar tidak terpotong.
    Kata tidak dipotong di tengah; garis miring boleh menjadi tempat pemisah baris."""
    baris = textwrap.wrap(
        str(teks).replace("/", "/ "), width=lebar,
        break_long_words=False, break_on_hyphens=False,
    )
    return "<br>".join(b.replace("/ ", "/") for b in baris) or str(teks)


def tinggi_batang(label_batang):
    """Tinggi grafik batang horizontal menyesuaikan banyaknya batang
    dan banyaknya baris label."""
    baris = sum(str(label).count("<br>") + 1 for label in label_batang)
    return max(280, 26 * baris + 14 * len(label_batang) + 30)


def grafik_batang_horizontal(seri, label, gradien=True, warna=PINK, dasar=None):
    """Batang horizontal dari hasil value_counts(); terbesar di atas.

    Jika `dasar` diisi, teks batang menjadi "jumlah (persen%)" dengan persen
    dihitung terhadap dasar tersebut (mis. jumlah alumni yang datanya terisi).
    """
    data = seri.rename_axis(label).reset_index(name="Jumlah")
    data[label] = data[label].map(bungkus)
    if dasar:
        data["Teks"] = [
            f"{format_angka(n)} ({format_desimal(n / dasar * 100, 1)}%)" for n in data["Jumlah"]
        ]
    else:
        data["Teks"] = data["Jumlah"].map(format_angka)

    gambar = px.bar(data, x="Jumlah", y=label, orientation="h", text="Teks")
    gambar.update_traces(marker_color=warna)
    gambar.update_traces(textposition="outside", cliponaxis=False, marker_cornerradius=5)
    gambar.update_layout(yaxis={"categoryorder": "total ascending"})
    gambar.update_xaxes(range=[0, max(data["Jumlah"].max() * (1.3 if dasar else 1.15), 1)])
    return rapikan(
        gambar, sembunyikan="x", tinggi=tinggi_batang(data[label]), legenda=False,
        margin_kanan=60 if dasar else 45,
    )


def grafik_batang_vertikal(seri, label):
    """Batang vertikal untuk deret yang berurutan (periode wisuda)."""
    data = seri.rename_axis(label).reset_index(name="Jumlah")
    data[label] = data[label].astype(str)
    gambar = px.bar(data, x=label, y="Jumlah", text="Jumlah")
    gambar.update_traces(
        marker_color=PINK, textposition="outside", cliponaxis=False, marker_cornerradius=5
    )
    gambar.update_xaxes(type="category")
    gambar.update_yaxes(range=[0, max(data["Jumlah"].max() * 1.18, 1)])
    return rapikan(gambar, sembunyikan="y", tinggi=340, legenda=False)


def grafik_area_periode(seri, kumulatif=False):
    """Garis beraera: jumlah alumni per periode wisuda.
    kumulatif=True menampilkan jumlah berjalan; jika tidak, ada garis rata-rata."""
    x = [str(p) for p in seri.index]
    y = seri.cumsum().tolist() if kumulatif else seri.values.tolist()
    judul_hover = "Kumulatif s.d. periode" if kumulatif else "Periode"

    gambar = go.Figure(
        go.Scatter(
            x=x, y=y, mode="lines+markers",
            line={"color": PINK, "width": 2},
            marker={"size": 8, "color": PINK, "line": {"color": "rgba(0,0,0,0)", "width": 0}},
            fill="tozeroy", fillcolor="rgba(236,72,153,0.10)",
            hovertemplate=judul_hover + " %{x}<br>%{y:,} alumni<extra></extra>",
        )
    )

    if not kumulatif and len(y) > 1:
        rata = sum(y) / len(y)
        gambar.add_hline(
            y=rata, line={"color": SLATE_SOFT, "width": 1, "dash": "dot"},
            annotation_text=f"Rata-rata {format_angka(round(rata))}",
            annotation_position="top left", annotation_font={"size": 11},
        )

    # Jumlah alumni ditulis di bawah nomor periode agar tidak menimpa garis
    gambar.update_xaxes(
        type="category", range=[-0.3, len(x) - 0.7], tickmode="array", tickvals=x,
        ticktext=[f"{p}<br><b>{format_angka(v)}</b>" for p, v in zip(x, y)],
    )
    gambar.update_yaxes(range=[0, max(max(y) * 1.12, 1)])
    return rapikan(gambar, sembunyikan="y", tinggi=330, legenda=False)


def grafik_donat(seri, label, palet, peta_warna=None, tengah=None, warna_tengah=PINK):
    data = seri.rename_axis(label).reset_index(name="Jumlah")
    gambar = px.pie(
        data, names=label, values="Jumlah", hole=0.64, color=label,
        color_discrete_map=peta_warna, color_discrete_sequence=palet,
    )
    bagian = data["Jumlah"] / data["Jumlah"].sum()
    teks_irisan = [format_desimal(b * 100, 1) + "%" if b >= 0.03 else "" for b in bagian]

    # Teks irisan gelap pada warna terang (amber, slate muda), putih pada warna lain
    warna_irisan = [
        (peta_warna or {}).get(nama, palet[i % len(palet)]) for i, nama in enumerate(data[label])
    ]
    warna_teks = ["#0F172A" if w in (AMBER, SLATE_SOFT) else "#FFFFFF" for w in warna_irisan]
    gambar.update_traces(
        text=teks_irisan, textinfo="text", textfont={"color": warna_teks, "size": 12},
        sort=False, domain={"x": [0, 1], "y": [0.14, 1]},
        marker={"line": {"color": "rgba(0,0,0,0)", "width": 0}},
    )
    if tengah:
        gambar.add_annotation(
            text=f"<b>{tengah}</b>", x=0.5, y=0.57, xref="paper", yref="paper",
            showarrow=False, font={"size": 26, "color": warna_tengah},
        )
    return rapikan(gambar, tinggi=330)


def grafik_persen_lanjut(ringkasan, kolom, horizontal):
    """Persentase alumni lanjut studi per kelompok (periode atau fakultas).
    Jumlah mentah dan total alumni muncul saat kursor diarahkan ke batang."""
    data = ringkasan.reset_index()
    data[kolom] = data[kolom].astype(str).map(bungkus)
    data["label"] = data["persen_lanjut"].map(lambda v: format_desimal(v, 1) + "%")
    maks = max(data["persen_lanjut"].max() * 1.2, 1)

    if horizontal:
        gambar = px.bar(
            data, x="persen_lanjut", y=kolom, orientation="h", text="label",
            custom_data=["lanjut_studi", "total_alumni"],
        )
        gambar.update_layout(yaxis={"categoryorder": "total ascending"})
        gambar.update_xaxes(range=[0, maks])
        nama = "%{y}"
        sembunyikan = "x"
        tinggi = tinggi_batang(data[kolom])
    else:
        gambar = px.bar(
            data, x=kolom, y="persen_lanjut", text="label",
            custom_data=["lanjut_studi", "total_alumni"],
        )
        gambar.update_xaxes(type="category")
        gambar.update_yaxes(range=[0, maks])
        nama = "%{x}"
        sembunyikan = "y"
        tinggi = 340

    gambar.update_traces(
        marker_color=PINK, marker_cornerradius=8, textposition="outside", cliponaxis=False,
        hovertemplate=(
            f"<b>{nama}</b><br>"
            "Lanjut studi: %{customdata[0]} dari %{customdata[1]} alumni<br>"
            "Persentase: %{text}<extra></extra>"
        ),
    )
    return rapikan(
        gambar, sembunyikan=sembunyikan, tinggi=tinggi, legenda=False,
        margin_kanan=45 if horizontal else 10,
    )


def grafik_sama_berbeda(ringkasan):
    """Batang bertumpuk 100%: bagian yang sama dan berbeda untuk tiap aspek."""
    data = ringkasan[ringkasan["dapat_dibandingkan"] > 0]
    kategori = [
        f"{nama} (n={format_angka(baris['dapat_dibandingkan'])})"
        for nama, baris in data.iterrows()
    ]
    persen_sama = (data["sama"] / data["dapat_dibandingkan"] * 100).tolist()
    persen_beda = (data["berbeda"] / data["dapat_dibandingkan"] * 100).tolist()

    gambar = go.Figure()
    gambar.add_bar(
        y=kategori, x=persen_sama, orientation="h", name="Sama", marker_color=SLATE_SOFT,
        text=[format_desimal(p, 1) + "%" for p in persen_sama], textposition="inside",
        textfont={"color": "#0F172A"},
        customdata=data["sama"].tolist(),
        hovertemplate="%{y}<br>Sama: %{customdata} alumni (%{x:.1f}%)<extra></extra>",
    )
    gambar.add_bar(
        y=kategori, x=persen_beda, orientation="h", name="Berbeda", marker_color=PINK,
        text=[format_desimal(p, 1) + "%" for p in persen_beda], textposition="inside",
        textfont={"color": "#FFFFFF"},
        customdata=data["berbeda"].tolist(),
        hovertemplate="%{y}<br>Berbeda: %{customdata} alumni (%{x:.1f}%)<extra></extra>",
    )
    gambar.update_layout(barmode="stack", yaxis={"autorange": "reversed"})
    gambar.update_xaxes(range=[0, 100])
    rapikan(gambar, sembunyikan="x", tinggi=110 + 55 * len(kategori), margin_kanan=10)
    # Legenda di atas grafik, urutan Sama lalu Berbeda
    gambar.update_layout(
        legend={"orientation": "h", "y": 1.0, "yanchor": "bottom", "x": 0, "xanchor": "left",
                "traceorder": "normal"},
        margin={"t": 36},
    )
    return gambar


def grafik_sankey_jenis(matriks):
    """Aliran jenis pekerjaan: kiri = pertama, kanan = sekarang."""
    kiri = list(matriks.index)
    kanan = list(matriks.columns)
    jumlah_kiri = matriks.sum(axis=1)
    jumlah_kanan = matriks.sum(axis=0)

    label = (
        [f"{k} ({format_angka(jumlah_kiri[k])})" for k in kiri]
        + [f"{k} ({format_angka(jumlah_kanan[k])})" for k in kanan]
    )

    sumber, target, nilai, warna = [], [], [], []
    for i, nama_kiri in enumerate(kiri):
        for j, nama_kanan in enumerate(kanan):
            v = int(matriks.iloc[i, j])
            if v > 0:
                sumber.append(i)
                target.append(len(kiri) + j)
                nilai.append(v)
                warna.append(
                    "rgba(148,163,184,0.30)" if nama_kiri == nama_kanan else "rgba(236,72,153,0.42)"
                )

    gambar = go.Figure(
        go.Sankey(
            node={"label": label, "pad": 22, "thickness": 18, "color": [SLATE] * len(label)},
            link={
                "source": sumber, "target": target, "value": nilai, "color": warna,
                "hovertemplate": "%{source.label} → %{target.label}<br>%{value} alumni<extra></extra>",
            },
        )
    )
    gambar.update_layout(
        title={"text": ""}, font={"family": FONT, "size": 12},
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=620,
    )
    return gambar


def nama_kolom_ramah(kolom):
    """JENIS PEKERJAAN PERTAMA -> Jenis pekerjaan pertama."""
    return kolom.capitalize()


def grafik_keterisian(tabel, dasar):
    """Batang bertumpuk 100% per kolom: terisi, (TIDAK DIKETAHUI), dan kosong.

    tabel: hasil kelengkapan_data (kolom terisi, kosong, tidak_diketahui).
    dasar: jumlah alumni yang menjadi pembagi (semua alumni, atau alumni lanjut studi).
    """
    nama = [bungkus(nama_kolom_ramah(k), 30) for k in tabel.index]
    bagian = [
        ("Terisi", tabel["terisi"] - tabel["tidak_diketahui"], PINK, "#FFFFFF"),
        ("Tidak diketahui", tabel["tidak_diketahui"], AMBER, "#0F172A"),
        ("Kosong", tabel["kosong"], SLATE, "#FFFFFF"),
    ]

    gambar = go.Figure()
    for label, jumlah, warna, warna_teks in bagian:
        persen = jumlah / dasar * 100
        gambar.add_bar(
            y=nama, x=persen.tolist(), orientation="h", name=label, marker_color=warna,
            text=[format_desimal(p, 1) + "%" if p >= 16 else "" for p in persen],
            textposition="inside", textangle=0,
            textfont={"color": warna_teks} if warna_teks else None,
            customdata=jumlah.tolist(),
            hovertemplate=f"%{{y}}<br>{label}: %{{customdata}} alumni (%{{x:.1f}}%)<extra></extra>",
        )

    gambar.update_layout(barmode="stack", yaxis={"autorange": "reversed"})
    gambar.update_xaxes(range=[0, 100])
    rapikan(gambar, sembunyikan="x", tinggi=100 + 42 * len(nama), margin_kanan=10)
    gambar.update_layout(
        legend={"orientation": "h", "y": 1.0, "yanchor": "bottom", "x": 0, "xanchor": "left",
                "traceorder": "normal", "font": {"size": 12}},
        margin={"t": 36},
    )
    return gambar


def grafik_keterisian_kelompok(pertama, sekarang, horizontal):
    """Persentase jenis pekerjaan terisi per kelompok: pertama vs sekarang."""
    kelompok = list(pertama.index)
    kategori = [bungkus(str(k), 26) if horizontal else str(k) for k in kelompok]
    maks = max(pertama["persen_terisi"].max(), sekarang["persen_terisi"].max(), 1) * 1.2

    gambar = go.Figure()
    for nama, tabel, warna in [
        ("Pekerjaan pertama", pertama, PINK),
        ("Pekerjaan sekarang", sekarang, TEAL),
    ]:
        tabel = tabel.reindex(kelompok)
        persen = tabel["persen_terisi"].tolist()
        teks = [format_desimal(p, 1) + "%" for p in persen]
        data_hover = tabel[["terisi", "total_alumni"]].values.tolist()
        sumbu = "%{y}" if horizontal else "%{x}"
        gambar.add_bar(
            x=persen if horizontal else kategori,
            y=kategori if horizontal else persen,
            orientation="h" if horizontal else "v",
            name=nama, marker_color=warna, marker_cornerradius=6,
            text=teks, textposition="outside", cliponaxis=False, customdata=data_hover,
            hovertemplate=(
                f"<b>{sumbu}</b><br>{nama}: %{{customdata[0]}} dari "
                "%{customdata[1]} alumni (%{text})<extra></extra>"
            ),
        )

    gambar.update_layout(barmode="group")
    if horizontal:
        gambar.update_layout(yaxis={"autorange": "reversed"})
        gambar.update_xaxes(range=[0, maks])
        rapikan(gambar, sembunyikan="x", tinggi=max(320, 70 * len(kategori) + 60), margin_kanan=50)
    else:
        gambar.update_xaxes(type="category")
        gambar.update_yaxes(range=[0, maks])
        rapikan(gambar, sembunyikan="y", tinggi=380)
    gambar.update_layout(
        legend={"orientation": "h", "y": 1.0, "yanchor": "bottom", "x": 0, "xanchor": "left"},
        margin={"t": 36},
    )
    return gambar


WARNA_WAFFLE = [PINK, TEAL, AMBER, "#38BDF8", SLATE, SLATE_SOFT]


def html_waffle(irisan):
    """Waffle 10 x 10 (100 petak) sebagai HTML, dengan legenda jumlah dan persen."""
    petak = []
    for i, ir in enumerate(irisan):
        warna = WARNA_WAFFLE[i % len(WARNA_WAFFLE)]
        judul = html.escape(f"{ir['label']}: {format_angka(ir['jumlah'])} alumni")
        petak += [f'<span class="wf-kotak" style="background:{warna}" title="{judul}"></span>'] * ir["petak"]

    legenda = ""
    for i, ir in enumerate(irisan):
        warna = WARNA_WAFFLE[i % len(WARNA_WAFFLE)]
        legenda += (
            f'<div class="wf-baris"><span class="wf-titik" style="background:{warna}"></span>'
            f'<span class="wf-label">{html.escape(ir["label"])}</span>'
            f'<span class="wf-nilai">{format_angka(ir["jumlah"])} · {format_desimal(ir["persen"], 1)}%</span></div>'
        )
    return (
        f'<div class="wf"><div class="wf-grid">{"".join(petak)}</div>'
        f'<div class="wf-legenda">{legenda}</div></div>'
    )


def grafik_banding_jenis(banding):
    """Jumlah alumni per jenis pekerjaan: pertama vs sekarang."""
    data = banding.assign(maks=banding[["pertama", "sekarang"]].max(axis=1))
    data = data.sort_values(["maks"], ascending=True, kind="stable")
    label = [bungkus(k, 24) for k in data.index]
    selisih = [("+" if d > 0 else "") + format_angka(d) for d in data["selisih"]]
    maks = max(data["maks"].max() * 1.24, 1)

    gambar = go.Figure()
    # Pada batang horizontal berkelompok, trace pertama tampil paling bawah,
    # jadi urutannya dibalik agar "pertama" berada di atas "sekarang".
    for nama, kolom, warna in [("Pekerjaan sekarang", "sekarang", PINK), ("Pekerjaan pertama", "pertama", SLATE)]:
        gambar.add_bar(
            y=label, x=data[kolom].tolist(), orientation="h", name=nama, marker_color=warna,
            marker_cornerradius=4, text=[format_angka(v) for v in data[kolom]],
            textposition="outside", cliponaxis=False, customdata=selisih,
            hovertemplate=(
                f"<b>%{{y}}</b><br>{nama}: %{{x:,}} alumni<br>"
                "Perubahan ke sekarang: %{customdata} alumni<extra></extra>"
            ),
        )
    gambar.update_layout(barmode="group")
    gambar.update_xaxes(range=[0, maks])
    rapikan(gambar, sembunyikan="x", tinggi=max(320, 70 * len(label) + 60), margin_kanan=45)
    gambar.update_layout(
        legend={"orientation": "h", "y": 1.0, "yanchor": "bottom", "x": 0, "xanchor": "left",
                "traceorder": "reversed"},
        margin={"t": 36},
    )
    return gambar


def grafik_heatmap_jenis(matriks):
    """Matriks perpindahan jenis pekerjaan. Baris = pertama, kolom = sekarang.
    Warna memakai akar jumlah agar sel kecil tetap terlihat."""
    baris = [bungkus(k, 20) for k in matriks.index]
    kolom = [bungkus(k, 12) for k in matriks.columns]
    jumlah = matriks.values
    teks = [["" if v == 0 else format_angka(v) for v in r] for r in jumlah]

    gambar = go.Figure(
        go.Heatmap(
            z=jumlah ** 0.5, x=kolom, y=baris, customdata=jumlah, text=teks,
            texttemplate="%{text}", textfont={"color": "#FFFFFF", "size": 12},
            colorscale=[[0, "rgba(148,163,184,0.14)"], [0.0001, SLATE], [1, PINK]],
            showscale=False, xgap=3, ygap=3,
            hovertemplate="Pertama: %{y}<br>Sekarang: %{x}<br>%{customdata} alumni<extra></extra>",
        )
    )
    gambar.update_yaxes(autorange="reversed")
    rapikan(gambar, tinggi=max(360, 56 * len(baris) + 130), legenda=False, margin_kanan=10)
    gambar.update_xaxes(title_text="Pekerjaan sekarang", side="top")
    gambar.update_yaxes(title_text="Pekerjaan pertama")
    gambar.update_layout(margin={"t": 70})
    return gambar


def batang_top_n(seri, judul, label, kunci, gradien=True, bawaan=10, keterangan="", dasar=None):
    """Kartu berisi batang horizontal N teratas, dengan slider untuk mengatur N."""
    with kartu():
        jumlah_kategori = len(seri)

        if jumlah_kategori == 0:
            kepala(judul)
            st.info("Belum ada data terisi.")
            return

        kepala(judul, keterangan)

        if jumlah_kategori > 1:
            n = st.slider(
                f"Tampilkan N teratas ({label.lower()})",
                min_value=1,
                max_value=jumlah_kategori,
                value=min(bawaan, jumlah_kategori),
                key=kunci,
            )
        else:
            n = 1

        tampilkan_grafik(grafik_batang_horizontal(seri.head(n), label, gradien=gradien, dasar=dasar))


# =========================================================
# FILTER, PENCARIAN, EKSPOR, DAN CATATAN
# =========================================================

KUNCI_FILTER = ["filter_periode", "filter_fakultas", "filter_prodi"]

# Kolom yang dicari oleh kotak pencarian global
KOLOM_CARI = [
    "FAKULTAS",
    "PROGRAM STUDI ASAL",
    "PERGURUAN TINGGI STUDI LANJUT",
    "NAMA TEMPAT KERJA PERTAMA",
    "NAMA TEMPAT KERJA SEKARANG",
    "POSISI/JABATAN PERTAMA",
    "POSISI/JABATAN SEKARANG",
]

# Kolom yang ikut diekspor (tanpa NIM, nama, tanggal lahir, dan tautan LinkedIn)
KOLOM_EKSPOR = [
    "PERIODE", "FAKULTAS", "PROGRAM STUDI ASAL", "JENJANG", "JENIS KELAMIN",
    "LANJUT STUDI", "JENJANG STUDI LANJUT", "PERGURUAN TINGGI STUDI LANJUT",
    "PROGRAM STUDI LANJUT",
    "JENIS PEKERJAAN PERTAMA", "NAMA TEMPAT KERJA PERTAMA", "PROVINSI TEMPAT KERJA PERTAMA",
    "KABUPATEN/KOTA TEMPAT KERJA PERTAMA", "POSISI/JABATAN PERTAMA",
    "JENIS PEKERJAAN SEKARANG", "NAMA TEMPAT KERJA SEKARANG", "PROVINSI TEMPAT KERJA SEKARANG",
    "KABUPATEN/KOTA TEMPAT KERJA SEKARANG", "POSISI/JABATAN SEKARANG",
]


def reset_filter():
    for kunci in KUNCI_FILTER:
        st.session_state[kunci] = []
    st.session_state["pencarian"] = ""


def terapkan_pencarian(data, kata):
    """Menyaring baris yang memuat kata pencarian pada salah satu KOLOM_CARI."""
    kata = kata.strip().lower()
    if not kata:
        return data
    cocok = pd.Series(False, index=data.index)
    for kolom in KOLOM_CARI:
        cocok = cocok | data[kolom].astype("string").str.lower().str.contains(
            kata, regex=False, na=False
        )
    return data[cocok]


def csv_bytes(tabel):
    # utf-8-sig: Excel membaca huruf Indonesia dengan benar
    return tabel.to_csv(index=False).encode("utf-8-sig")


@st.cache_data(show_spinner=False)
def xlsx_bytes(tabel):
    penyangga = io.BytesIO()
    tabel.to_excel(penyangga, index=False, sheet_name="Alumni", engine="openpyxl")
    return penyangga.getvalue()


def judul_kasus(teks):
    return str(teks).title()


@st.dialog("Cakupan dan catatan metodologi", width="medium")
def dialog_catatan(nama_halaman, data_semua, data_filter, filter_aktif, catatan):
    st.caption(nama_halaman)

    daftar = " · ".join(filter_aktif) if filter_aktif else "Semua data"
    st.markdown(
        f'<div class="pk-judul">Cakupan data</div><div style="font-size:.82rem">'
        f"{html.escape(daftar)}</div>"
        f'<div style="margin-top:.7rem"><div class="pk-baris"><span>Alumni ditampilkan</span>'
        f"<b>{format_angka(len(data_filter))}</b></div>"
        f'<div class="pk-baris"><span>Total alumni</span><b>{format_angka(len(data_semua))}</b></div></div>',
        unsafe_allow_html=True,
    )

    if len(data_filter) > 0:
        tabel = kelengkapan_data(data_filter)["pekerjaan"]
        baris = ""
        for nama, kolom in [
            ("Pekerjaan pertama terisi", "JENIS PEKERJAAN PERTAMA"),
            ("Pekerjaan sekarang terisi", "JENIS PEKERJAAN SEKARANG"),
        ]:
            persen = float(tabel.loc[kolom, "persen_terisi"])
            baris += (
                f'<div class="pk-label"><span>{nama}</span><b>{format_desimal(persen, 1)}%</b></div>'
                f'<div class="pk-bar"><span style="width:{persen:.1f}%"></span></div>'
            )
        st.markdown(
            '<div class="pk-judul">Kelengkapan data pekerjaan</div>' + baris +
            '<div class="pk-kecil">Sel kosong belum dapat '
            "ditafsirkan sebagai kondisi tertentu.</div>",
            unsafe_allow_html=True,
        )

    butir = "".join(f"<li>{html.escape(c)}</li>" for c in catatan)
    st.markdown(
        f'<div class="pk"><div class="pk-judul">Catatan halaman</div><ul>{butir}</ul></div>',
        unsafe_allow_html=True,
    )


# =========================================================
# HALAMAN 1: RINGKASAN
# =========================================================

def deret_per_periode(data):
    """Deret per periode wisuda untuk sparkline dan delta kartu KPI."""
    periode = data.groupby("PERIODE").size().sort_index()
    lanjut = ringkasan_lanjut_studi_per(data, "PERIODE").sort_index()
    kerja1 = kelengkapan_per_kelompok(data, "PERIODE", "JENIS PEKERJAAN PERTAMA").sort_index()
    kerja2 = kelengkapan_per_kelompok(data, "PERIODE", "JENIS PEKERJAAN SEKARANG").sort_index()
    return {
        "label": [str(p) for p in periode.index],
        "alumni": periode.tolist(),
        "lanjut": lanjut["lanjut_studi"].tolist(),
        "persen_lanjut": lanjut["persen_lanjut"].tolist(),
        "kerja1": kerja1["persen_terisi"].tolist(),
        "kerja2": kerja2["persen_terisi"].tolist(),
    }


def halaman_ringkasan(data):
    hasil = karakteristik_alumni(data)
    status = studi_lanjut(data)
    jumlah_ya = int(status["jumlah"].get(STATUS_LANJUT, 0))
    persen_ya = jumlah_ya / len(data) * 100

    deret = deret_per_periode(data)
    jumlah_fakultas = data["FAKULTAS"].nunique()
    kerja1_terisi = int(data["JENIS PEKERJAAN PERTAMA"].notna().sum())

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(
        kartu_metrik(
            "", "Total alumni", format_angka(len(data)),
            f"{len(deret['label'])} periode · {jumlah_fakultas} fakultas",
            delta=delta_periode(deret["label"], deret["alumni"]), spark=deret["alumni"],
        ),
        unsafe_allow_html=True,
    )
    m2.markdown(
        kartu_metrik(
            "", "Lanjut studi", format_angka(jumlah_ya),
            f"{format_desimal(persen_ya, 1)}% dari total alumni",
            delta=delta_periode(deret["label"], deret["persen_lanjut"], "persen"),
            spark=deret["persen_lanjut"],
        ),
        unsafe_allow_html=True,
    )
    m3.markdown(
        kartu_metrik(
            "", "Data kerja 1 terisi", format_desimal(kerja1_terisi / len(data) * 100, 1) + "%",
            f"{format_angka(kerja1_terisi)} alumni tercatat",
            delta=delta_periode(deret["label"], deret["kerja1"], "persen"), spark=deret["kerja1"],
        ),
        unsafe_allow_html=True,
    )
    m4.markdown(
        kartu_metrik(
            "", "Program studi asal", data["PROGRAM STUDI ASAL"].nunique(),
            f"Tersebar di {jumlah_fakultas} fakultas",
            delta={"teks": f"{data['JENJANG'].nunique()} jenjang", "nada": "neutral", "tip": ""},
        ),
        unsafe_allow_html=True,
    )

    st.write("")
    kiri, kanan = st.columns([3, 2])

    with kiri:
        with kartu():
            kepala("Alumni per periode wisuda", "Jumlah alumni pada setiap periode")
            mode_periode = st.segmented_control(
                "Tampilan tren periode", ["Per periode", "Kumulatif"], default="Per periode",
                key="mode_periode", label_visibility="collapsed",
            )
            tampilkan_grafik(grafik_area_periode(
                hasil["berdasarkan_periode"], kumulatif=(mode_periode == "Kumulatif")
            ))

    with kanan:
        with kartu():
            kepala("Status studi lanjut", "Seluruh alumni pada filter ini")
            tampilkan_grafik(grafik_donat(
                status["jumlah"], "Status", PALET_STUDI,
                peta_warna=WARNA_STATUS, tengah=format_desimal(persen_ya, 1) + "%", warna_tengah=PINK,
            ))

    kiri, kanan = st.columns([3, 2])

    with kiri:
        with kartu():
            kepala("Alumni per fakultas")
            tampilkan_grafik(grafik_batang_horizontal(hasil["berdasarkan_fakultas"], "Fakultas"))

    with kanan:
        with kartu():
            kepala("Jenis kelamin")
            tampilkan_grafik(grafik_donat(
                hasil["berdasarkan_jenis_kelamin"], "Jenis kelamin", PALET_UMUM
            ))

    # ---- Tabel ringkasan per program studi ----
    with kartu():
        kepala(
            "Ringkasan alumni per program studi",
            "Mengikuti filter di atas. Klik judul kolom untuk mengurutkan, "
            "arahkan kursor ke tabel untuk mencari.",
        )
        ringkasan_prodi = ringkasan_per_program_studi(data)
        pilihan_fak = st.selectbox(
            "Tampilkan fakultas",
            ["Semua fakultas"] + sorted(ringkasan_prodi["FAKULTAS"].unique().tolist()),
            key="tabel_prodi_fakultas",
        )
        if pilihan_fak != "Semua fakultas":
            ringkasan_prodi = ringkasan_prodi[ringkasan_prodi["FAKULTAS"] == pilihan_fak]

        st.dataframe(
            ringkasan_prodi.rename(columns={
                "PROGRAM STUDI ASAL": "Program studi", "FAKULTAS": "Fakultas", "JENJANG": "Jenjang",
                "alumni": "Alumni", "lanjut": "Lanjut studi",
                "persen_lanjut": "% Lanjut", "persen_kerja1": "% Data kerja 1",
            })[["Program studi", "Fakultas", "Jenjang", "Alumni", "Lanjut studi", "% Lanjut", "% Data kerja 1"]],
            width="stretch", hide_index=True,
            column_config={
                "Alumni": st.column_config.NumberColumn(format="%d"),
                "Lanjut studi": st.column_config.NumberColumn(format="%d"),
                "% Lanjut": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
                "% Data kerja 1": st.column_config.ProgressColumn(format="%.1f%%", min_value=0, max_value=100),
            },
        )
        st.caption(
            "% Lanjut = alumni lanjut studi dari seluruh alumni program studi itu. "
            "% Data kerja 1 = alumni yang jenis pekerjaan pertamanya terisi. "
            "Persentase pada program studi kecil kurang stabil."
        )


# =========================================================
# HALAMAN 2: KARAKTERISTIK ALUMNI
# =========================================================

def halaman_karakteristik(data):
    hasil = karakteristik_alumni(data)

    kiri, kanan = st.columns(2)

    with kiri:
        with kartu():
            kepala("Alumni per periode wisuda")
            tampilkan_grafik(grafik_batang_vertikal(hasil["berdasarkan_periode"], "Periode"))

    with kanan:
        with kartu():
            kepala("Jenis kelamin")
            tampilkan_grafik(grafik_donat(
                hasil["berdasarkan_jenis_kelamin"], "Jenis kelamin", PALET_UMUM
            ))

    kiri, kanan = st.columns(2)

    with kiri:
        with kartu():
            kepala("Alumni per fakultas")
            tampilkan_grafik(grafik_batang_horizontal(hasil["berdasarkan_fakultas"], "Fakultas"))

    with kanan:
        with kartu():
            kepala("Jenjang")
            tampilkan_grafik(grafik_donat(hasil["berdasarkan_jenjang"], "Jenjang", PALET_UMUM))

    batang_top_n(
        hasil["berdasarkan_program_studi"],
        "Alumni per program studi asal",
        "Program studi asal",
        kunci="slider_prodi_asal",
        bawaan=15,
        keterangan="Diurutkan dari jumlah alumni terbanyak",
    )

    with st.expander("Lihat tabel: periode × fakultas"):
        st.dataframe(distribusi_alumni(data)["periode_fakultas"], width="stretch")


# =========================================================
# HALAMAN 3: STUDI LANJUT
# =========================================================

def halaman_studi_lanjut(data):
    total = len(data)
    status = studi_lanjut(data)
    jumlah_ya = int(status["jumlah"].get(STATUS_LANJUT, 0))
    jumlah_tidak = total - jumlah_ya
    persen_ya = jumlah_ya / total * 100

    deret = deret_per_periode(data)
    kampus_unik = data.loc[
        data["LANJUT STUDI"] == STATUS_LANJUT, "PERGURUAN TINGGI STUDI LANJUT"
    ].nunique()

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(
        kartu_metrik(
            "", "Lanjut studi", format_angka(jumlah_ya), "Alumni melanjutkan pendidikan",
            delta=delta_periode(deret["label"], deret["lanjut"]), spark=deret["lanjut"],
        ),
        unsafe_allow_html=True,
    )
    m2.markdown(
        kartu_metrik(
            "", "Persentase lanjut studi", format_desimal(persen_ya, 1) + "%",
            f"Dari {format_angka(total)} alumni",
            delta=delta_periode(deret["label"], deret["persen_lanjut"], "persen"),
            spark=deret["persen_lanjut"],
        ),
        unsafe_allow_html=True,
    )
    m3.markdown(
        kartu_metrik(
            "", "Tidak tercatat lanjut studi", format_angka(jumlah_tidak),
            f"{format_desimal(jumlah_tidak / total * 100, 1)}% dari total",
        ),
        unsafe_allow_html=True,
    )
    m4.markdown(
        kartu_metrik("", "Kampus tujuan unik", format_angka(kampus_unik),
                     "Perguruan tinggi tujuan tercatat"),
        unsafe_allow_html=True,
    )

    st.write("")
    kiri, kanan = st.columns([2, 3])

    with kiri:
        with kartu():
            kepala("Status studi lanjut")
            tampilkan_grafik(grafik_donat(
                status["jumlah"], "Status", PALET_STUDI,
                peta_warna=WARNA_STATUS, tengah=format_desimal(persen_ya, 1) + "%", warna_tengah=PINK,
            ))

    with kanan:
        with kartu():
            kepala("Persentase lanjut studi per periode wisuda", "Arahkan kursor untuk melihat jumlah alumni")
            per_periode = ringkasan_lanjut_studi_per(data, "PERIODE").sort_index()
            tampilkan_grafik(grafik_persen_lanjut(per_periode, "PERIODE", horizontal=False))

    kiri, kanan = st.columns(2)

    per_prodi = ringkasan_lanjut_studi_per(data, "PROGRAM STUDI ASAL")
    prodi_lanjut = (
        per_prodi[per_prodi["lanjut_studi"] > 0]
        .sort_values("lanjut_studi", ascending=False)["lanjut_studi"]
    )

    with kiri:
        with kartu():
            kepala("Persentase lanjut studi per fakultas", "Arahkan kursor untuk melihat jumlah alumni")
            per_fakultas = ringkasan_lanjut_studi_per(data, "FAKULTAS")
            tampilkan_grafik(grafik_persen_lanjut(per_fakultas, "FAKULTAS", horizontal=True))

    with kanan:
        batang_top_n(
            prodi_lanjut,
            "Alumni lanjut studi per program studi asal",
            "Program studi asal",
            kunci="slider_prodi_lanjut_asal",
            gradien=False,
            bawaan=10,
            keterangan="Jumlah alumni, bukan persentase",
        )

    with st.expander("Lihat tabel: studi lanjut per program studi asal"):
        tabel = per_prodi.sort_values(
            ["lanjut_studi", "total_alumni"], ascending=False
        ).rename(columns={
            "total_alumni": "Total alumni",
            "lanjut_studi": "Lanjut studi",
            "persen_lanjut": "% lanjut studi",
        })
        st.dataframe(tabel, width="stretch")
        st.caption(
            "Persentase pada program studi dengan alumni sedikit kurang stabil. "
            "Baca bersama kolom Total alumni."
        )

    # ---- Detail alumni yang melanjutkan studi ----
    st.markdown('<div class="sec">Alumni yang melanjutkan studi</div>', unsafe_allow_html=True)

    if jumlah_ya == 0:
        st.info("Tidak ada alumni lanjut studi pada filter yang dipilih.")
        return

    detail = distribusi_studi_lanjut(data)

    kiri, kanan = st.columns([2, 3])

    with kiri:
        with kartu():
            jenjang = detail["jenjang_studi_lanjut"]
            kepala("Jenjang studi lanjut", catatan_terisi(jenjang, jumlah_ya))
            if jenjang.empty:
                st.info("Belum ada data jenjang studi lanjut yang terisi.")
            else:
                tampilkan_grafik(grafik_donat(jenjang, "Jenjang", PALET_STUDI))

    with kanan:
        perguruan_tinggi = detail["perguruan_tinggi"]
        batang_top_n(
            perguruan_tinggi,
            "Perguruan tinggi tujuan",
            "Perguruan tinggi",
            kunci="slider_perguruan_tinggi",
            gradien=False,
            bawaan=10,
            keterangan=catatan_terisi(perguruan_tinggi, jumlah_ya),
        )

    program_lanjut = detail["program_studi_lanjut"]
    batang_top_n(
        program_lanjut,
        "Program studi lanjut",
        "Program studi lanjut",
        kunci="slider_program_lanjut",
        gradien=False,
        bawaan=10,
        keterangan=catatan_terisi(program_lanjut, jumlah_ya),
    )

    with st.expander("Lihat tabel: alumni yang melanjutkan studi"):
        lanjut = data[data["LANJUT STUDI"] == STATUS_LANJUT]
        kolom_tabel = [
            "PERIODE",
            "FAKULTAS",
            "PROGRAM STUDI ASAL",
            "JENJANG STUDI LANJUT",
            "PERGURUAN TINGGI STUDI LANJUT",
            "PROGRAM STUDI LANJUT",
        ]
        st.dataframe(lanjut[kolom_tabel], width="stretch", hide_index=True)
        st.caption("Tabel ini tidak memuat nama maupun NIM alumni.")


# =========================================================
# HALAMAN 4: PEKERJAAN PERTAMA DAN SEKARANG
# =========================================================

def keterangan_dasar(info):
    """Teks dasar perhitungan untuk judul kartu pekerjaan."""
    persen = info["dapat_dianalisis"] / info["total_alumni"] * 100
    teks = (
        f"Dasar: {format_angka(info['dapat_dianalisis'])} alumni dengan data terisi "
        f"({format_desimal(persen, 1)}% dari {format_angka(info['total_alumni'])} alumni)"
    )
    if info["tidak_diketahui"] > 0:
        teks += (
            f". {format_angka(info['tidak_diketahui'])} data bertuliskan "
            "(TIDAK DIKETAHUI) tidak ditampilkan"
        )
    return teks


def halaman_pekerjaan(data):
    pilihan = st.segmented_control(
        "Tahap pekerjaan",
        ["Pekerjaan pertama", "Pekerjaan sekarang"],
        default="Pekerjaan pertama",
        key="tahap_pekerjaan",
        label_visibility="collapsed",
    )
    # segmented_control bisa bernilai None bila pilihan dibatalkan
    tahap = "sekarang" if pilihan == "Pekerjaan sekarang" else "pertama"

    hasil = distribusi_pekerjaan_tahap(data, tahap)
    total = len(data)
    jenis = hasil["jenis"]
    provinsi = hasil["provinsi"]

    if jenis["terisi"] == 0:
        st.info(f"Belum ada data jenis pekerjaan ({tahap}) yang terisi pada filter ini.")
        return

    # ---- Metrik ----
    deret = deret_per_periode(data)
    seri_kerja = deret["kerja1"] if tahap == "pertama" else deret["kerja2"]
    persen_terisi = jenis["terisi"] / total * 100
    tempat = hasil["tempat_kerja"]

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(
        kartu_metrik(
            "", "Data jenis pekerjaan terisi", format_angka(jenis["terisi"]),
            f"{format_desimal(persen_terisi, 1)}% dari {format_angka(total)} alumni",
            delta=delta_periode(deret["label"], seri_kerja, "persen"), spark=seri_kerja,
        ),
        unsafe_allow_html=True,
    )

    teratas_jenis = jenis["distribusi"]
    if len(teratas_jenis) > 0:
        n = int(teratas_jenis.iloc[0])
        m2.markdown(
            kartu_metrik(
                "", "Jenis pekerjaan terbanyak", teratas_jenis.index[0],
                f"{format_angka(n)} alumni ({format_desimal(n / jenis['dapat_dianalisis'] * 100, 1)}% dari data terisi)",
                kecil=True,
            ),
            unsafe_allow_html=True,
        )

    teratas_prov = provinsi["distribusi"]
    if len(teratas_prov) > 0:
        n = int(teratas_prov.iloc[0])
        m3.markdown(
            kartu_metrik(
                "", "Provinsi terbanyak", teratas_prov.index[0],
                f"{format_angka(n)} alumni ({format_desimal(n / provinsi['dapat_dianalisis'] * 100, 1)}% dari data terisi)",
                kecil=True,
            ),
            unsafe_allow_html=True,
        )

    m4.markdown(
        kartu_metrik(
            "", "Perusahaan / instansi unik", format_angka(len(tempat["distribusi"])),
            f"Dari {format_angka(tempat['dapat_dianalisis'])} data terisi",
        ),
        unsafe_allow_html=True,
    )

    st.write("")

    # ---- Waffle dan jenis pekerjaan ----
    kiri, kanan = st.columns(2)

    with kiri:
        with kartu():
            kepala("Proporsi jenis pekerjaan (waffle 10×10)", keterangan_dasar(jenis))
            irisan = alokasikan_waffle(jenis["distribusi"], jenis["dapat_dianalisis"])
            if irisan:
                st.markdown(html_waffle(irisan), unsafe_allow_html=True)
                st.caption(
                    "Satu petak = sekitar 1% dari data terisi. Kategori kecil digabung "
                    "bila lebih dari 6 kategori."
                )
            else:
                st.info("Belum ada data jenis pekerjaan yang dapat ditampilkan.")

    with kanan:
        with kartu():
            kepala("Jenis pekerjaan (jumlah dan persen)", keterangan_dasar(jenis))
            tampilkan_grafik(grafik_batang_horizontal(
                jenis["distribusi"], "Jenis pekerjaan", dasar=jenis["dapat_dianalisis"]
            ))

    # ---- Provinsi dan kabupaten/kota ----
    kiri, kanan = st.columns(2)
    kabupaten = hasil["kabupaten_kota"]

    with kiri:
        batang_top_n(
            provinsi["distribusi"], "Provinsi tempat kerja", "Provinsi",
            kunci=f"slider_provinsi_{tahap}", bawaan=10, dasar=provinsi["dapat_dianalisis"],
            keterangan=keterangan_dasar(provinsi),
        )

    with kanan:
        batang_top_n(
            kabupaten["distribusi"], "Kabupaten/kota tempat kerja", "Kabupaten/kota",
            kunci=f"slider_kabupaten_{tahap}", bawaan=10, dasar=kabupaten["dapat_dianalisis"],
            keterangan=keterangan_dasar(kabupaten),
        )

    # ---- Nama tempat kerja dan posisi/jabatan ----
    kiri, kanan = st.columns(2)
    posisi = hasil["posisi"]

    with kiri:
        batang_top_n(
            tempat["distribusi"], "Nama tempat kerja", "Tempat kerja",
            kunci=f"slider_tempat_{tahap}", bawaan=10, dasar=tempat["dapat_dianalisis"],
            keterangan=keterangan_dasar(tempat),
        )

    with kanan:
        batang_top_n(
            posisi["distribusi"], "Posisi/jabatan", "Posisi/jabatan",
            kunci=f"slider_posisi_{tahap}", bawaan=10, dasar=posisi["dapat_dianalisis"],
            keterangan=keterangan_dasar(posisi),
        )

    with st.expander("Lihat tabel: rincian jenis pekerjaan \"Lainnya\" (teks bebas)"):
        rincian = rincian_jenis_pekerjaan_lainnya(data, tahap)
        if rincian.empty:
            st.info("Tidak ada rincian yang terisi pada filter ini.")
        else:
            st.dataframe(
                rincian.rename_axis("Rincian (teks bebas)").reset_index(name="Jumlah"),
                width="stretch",
                hide_index=True,
            )
            st.caption(
                "Teks ditulis bebas pada data asli. Hanya huruf besar-kecil yang diseragamkan, "
                "penulisan lain (mis. FREELANCE dan FREELANCER) belum digabung."
            )


# =========================================================
# HALAMAN 5: PERBANDINGAN PEKERJAAN PERTAMA DAN SEKARANG
# =========================================================

def deret_perpindahan(tabel):
    """Tabel (dari, ke, jumlah) menjadi Series berlabel 'dari → ke'."""
    return (
        tabel.assign(label=tabel["dari"] + " → " + tabel["ke"])
        .set_index("label")["jumlah"]
    )


def halaman_perbandingan(data):
    total = len(data)
    ringkasan = ringkasan_perubahan_pekerjaan(data)
    jenis = ringkasan.loc["Jenis pekerjaan"]
    provinsi = ringkasan.loc["Provinsi"]
    kabupaten = ringkasan.loc["Kabupaten/Kota"]

    if ringkasan["dapat_dibandingkan"].sum() == 0:
        st.info(
            "Tidak ada alumni dengan data pekerjaan pertama dan sekarang yang sama-sama terisi "
            "pada filter ini."
        )
        return

    def persen_berbeda(baris):
        if baris["dapat_dibandingkan"] == 0:
            return "belum ada data yang dapat dibandingkan"
        return (
            f"{format_desimal(baris['berbeda'] / baris['dapat_dibandingkan'] * 100, 1)}% dari "
            f"{format_angka(baris['dapat_dibandingkan'])} alumni"
        )

    # ---- Metrik ----
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(
        kartu_metrik(
            "kerja", "Dapat dibandingkan", format_angka(jenis["dapat_dibandingkan"]),
            f"jenis pekerjaan, tanpa LAINNYA ({format_angka(jenis['dikecualikan'])} dikeluarkan)",
        ),
        unsafe_allow_html=True,
    )
    m2.markdown(
        kartu_metrik("topi", "Jenis berbeda", format_angka(jenis["berbeda"]),
                     persen_berbeda(jenis), pink=True),
        unsafe_allow_html=True,
    )
    m3.markdown(
        kartu_metrik("lokasi", "Provinsi berbeda", format_angka(provinsi["berbeda"]),
                     persen_berbeda(provinsi), pink=True),
        unsafe_allow_html=True,
    )
    m4.markdown(
        kartu_metrik("lokasi", "Kab./kota berbeda", format_angka(kabupaten["berbeda"]),
                     persen_berbeda(kabupaten), pink=True),
        unsafe_allow_html=True,
    )

    st.write("")

    # ---- Sama atau berbeda ----
    with kartu():
        kepala(
            "Pekerjaan pertama dibandingkan dengan pekerjaan sekarang",
            "Persentase dari alumni yang kedua datanya terisi. Alumni lainnya tidak dihitung sama maupun berbeda.",
        )
        tampilkan_grafik(grafik_sama_berbeda(ringkasan))
        st.caption(
            f"Jenis pekerjaan LAINNYA dikeluarkan dari perbandingan jenis "
            f"({format_angka(jenis['dikecualikan'])} alumni). "
            "Posisi/jabatan: \"berbeda\" berarti tulisannya tidak persis sama, "
            "belum tentu jabatannya benar-benar berbeda."
        )

    # ---- Perpindahan lokasi ----
    kiri, kanan = st.columns(2)

    for kolom_halaman, aspek, judul, label in [
        (kiri, "provinsi", "Perpindahan provinsi terbanyak", "Perpindahan provinsi"),
        (kanan, "kabupaten_kota", "Perpindahan kabupaten/kota terbanyak", "Perpindahan kabupaten/kota"),
    ]:
        hasil = perpindahan_pekerjaan(data, aspek)
        with kolom_halaman:
            if hasil["berbeda"] == 0:
                with kartu():
                    kepala(judul)
                    st.info("Tidak ada alumni dengan lokasi berbeda pada filter ini.")
            else:
                batang_top_n(
                    deret_perpindahan(hasil["perpindahan"]), judul, label,
                    kunci=f"slider_pindah_{aspek}", bawaan=10, dasar=hasil["berbeda"],
                    keterangan=(
                        f"Dasar: {format_angka(hasil['berbeda'])} alumni yang berbeda, dari "
                        f"{format_angka(hasil['dapat_dibandingkan'])} yang dapat dibandingkan"
                    ),
                )

    # ---- Jenis pekerjaan: pertama vs sekarang ----
    matriks = matriks_jenis_pekerjaan(data)
    kiri, kanan = st.columns(2)

    with kiri:
        with kartu():
            kepala(
                "Sebaran jenis pekerjaan: pertama vs sekarang",
                "Jumlah alumni di tiap jenis pekerjaan pada pekerjaan pertama dan sekarang "
                "(tanpa LAINNYA)",
            )
            if matriks.empty:
                st.info("Belum ada alumni dengan jenis pekerjaan pertama dan sekarang yang dapat dibandingkan.")
            else:
                tampilkan_grafik(grafik_banding_jenis(banding_jenis_pekerjaan(data)))

    with kanan:
        hasil_jenis = perpindahan_pekerjaan(data, "jenis")
        if hasil_jenis["berbeda"] == 0:
            with kartu():
                kepala("Perpindahan jenis pekerjaan terbanyak")
                st.info("Tidak ada alumni dengan jenis pekerjaan berbeda pada filter ini.")
        else:
            batang_top_n(
                deret_perpindahan(hasil_jenis["perpindahan"]),
                "Perpindahan jenis pekerjaan terbanyak", "Perpindahan jenis",
                kunci="slider_pindah_jenis", bawaan=10, dasar=hasil_jenis["berbeda"],
                keterangan=(
                    f"Dasar: {format_angka(hasil_jenis['berbeda'])} alumni yang berbeda, dari "
                    f"{format_angka(hasil_jenis['dapat_dibandingkan'])} yang dapat dibandingkan"
                ),
            )

    # ---- Peta lengkap perpindahan jenis pekerjaan ----
    with kartu():
        tampilan_peta = st.segmented_control(
            "Tampilan peta perpindahan", ["Matriks Heatmap", "Diagram Sankey"],
            default="Matriks Heatmap", key="tampilan_peta", label_visibility="collapsed",
        )
        if tampilan_peta == "Diagram Sankey":
            kepala(
                "Peta lengkap perpindahan jenis pekerjaan",
                "Kiri: pekerjaan pertama. Kanan: pekerjaan sekarang. Pita abu = jenis sama, "
                "pink = berubah. Arahkan kursor untuk melihat jumlah alumni.",
            )
        else:
            kepala(
                "Peta lengkap perpindahan jenis pekerjaan",
                "Baris = pekerjaan pertama, kolom = pekerjaan sekarang. Diagonal menunjukkan "
                "alumni yang bertahan di jenis pekerjaan yang sama.",
            )

        if matriks.empty:
            st.info("Belum ada alumni dengan jenis pekerjaan pertama dan sekarang yang dapat dibandingkan.")
        else:
            if tampilan_peta == "Diagram Sankey":
                tampilkan_grafik(grafik_sankey_jenis(matriks))
            else:
                tampilkan_grafik(grafik_heatmap_jenis(matriks))
            st.caption(
                f"Jenis LAINNYA dikeluarkan dari perbandingan ({format_angka(jenis['dikecualikan'])} "
                "alumni). Rincian LAINNYA ada di halaman Pekerjaan."
            )

    with st.expander("Lihat tabel: perbandingan per alumni (tanpa nama dan NIM)"):
        kolom_tabel = [
            "PERIODE", "FAKULTAS", "PROGRAM STUDI ASAL",
            "JENIS PEKERJAAN PERTAMA", "JENIS PEKERJAAN SEKARANG",
            "PROVINSI TEMPAT KERJA PERTAMA", "PROVINSI TEMPAT KERJA SEKARANG",
            "KABUPATEN/KOTA TEMPAT KERJA PERTAMA", "KABUPATEN/KOTA TEMPAT KERJA SEKARANG",
            "POSISI/JABATAN PERTAMA", "POSISI/JABATAN SEKARANG",
        ]
        st.dataframe(alumni_dapat_dibandingkan(data)[kolom_tabel], width="stretch", hide_index=True)
        st.caption("Hanya alumni yang minimal satu aspeknya dapat dibandingkan.")


# =========================================================
# HALAMAN 6: KELENGKAPAN DATA
# =========================================================

POLA_WARNA = {
    "Keduanya terisi": PINK,
    "Hanya pekerjaan pertama terisi": TEAL,
    "Hanya pekerjaan sekarang terisi": AMBER,
    "Keduanya kosong": NETRAL,
}


def tabel_tampil(tabel, dasar):
    """Tabel kelengkapan dengan nama kolom yang mudah dibaca."""
    hasil = tabel[["terisi", "kosong", "tidak_diketahui"]].copy()
    hasil["% terisi"] = (hasil["terisi"] / dasar * 100).round(2)
    hasil.index = [nama_kolom_ramah(k) for k in hasil.index]
    return hasil.rename(columns={
        "terisi": "Terisi", "kosong": "Kosong", "tidak_diketahui": "(TIDAK DIKETAHUI)",
    }).rename_axis("Kolom")


def halaman_kelengkapan(data):
    total = len(data)
    kelengkapan = kelengkapan_data(data)
    tabel_kerja = kelengkapan["pekerjaan"]
    pola = pola_keterisian_pekerjaan(data)

    terisi_pertama = int(tabel_kerja.loc["JENIS PEKERJAAN PERTAMA", "terisi"])
    terisi_sekarang = int(tabel_kerja.loc["JENIS PEKERJAAN SEKARANG", "terisi"])
    keduanya = int(pola["Keduanya terisi"])

    # ---- Metrik ----
    deret = deret_per_periode(data)

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(kartu_metrik("", "Total alumni", format_angka(total)), unsafe_allow_html=True)
    m2.markdown(
        kartu_metrik(
            "", "Pekerjaan pertama terisi", format_desimal(terisi_pertama / total * 100, 1) + "%",
            f"{format_angka(terisi_pertama)} alumni",
            delta=delta_periode(deret["label"], deret["kerja1"], "persen"), spark=deret["kerja1"],
        ),
        unsafe_allow_html=True,
    )
    m3.markdown(
        kartu_metrik(
            "", "Pekerjaan sekarang terisi", format_desimal(terisi_sekarang / total * 100, 1) + "%",
            f"{format_angka(terisi_sekarang)} alumni",
            delta=delta_periode(deret["label"], deret["kerja2"], "persen"), spark=deret["kerja2"],
        ),
        unsafe_allow_html=True,
    )
    m4.markdown(
        kartu_metrik("", "Keduanya terisi", format_desimal(keduanya / total * 100, 1) + "%",
                     f"{format_angka(keduanya)} alumni"),
        unsafe_allow_html=True,
    )

    st.write("")

    # ---- Keterisian per kolom dan pola ----
    kiri, kanan = st.columns([3, 2])

    with kiri:
        with kartu():
            kepala(
                "Keterisian kolom pekerjaan",
                f"Dasar: {format_angka(total)} alumni pada filter ini",
            )
            tampilkan_grafik(grafik_keterisian(tabel_kerja, total))

    with kanan:
        with kartu():
            kepala("Pola keterisian jenis pekerjaan", "Pertama dan sekarang")
            tampilkan_grafik(grafik_donat(
                pola, "Pola", PALET_UMUM, peta_warna=POLA_WARNA,
                tengah=format_desimal(keduanya / total * 100, 1) + "%",
            ))
            st.caption("Angka di tengah = persentase alumni yang kedua datanya terisi.")

    # ---- Keterisian per kelompok ----
    with kartu():
        kepala(
            "Keterisian jenis pekerjaan per kelompok",
            "Persentase alumni pada kelompok yang data jenis pekerjaannya terisi",
        )
        pilihan = st.segmented_control(
            "Kelompokkan berdasarkan",
            ["Fakultas", "Periode wisuda"],
            default="Fakultas",
            key="kelompok_keterisian",
        )
        kolom_kelompok = "PERIODE" if pilihan == "Periode wisuda" else "FAKULTAS"

        pertama = kelengkapan_per_kelompok(data, kolom_kelompok, "JENIS PEKERJAAN PERTAMA")
        sekarang = kelengkapan_per_kelompok(data, kolom_kelompok, "JENIS PEKERJAAN SEKARANG")
        if kolom_kelompok == "PERIODE":
            pertama = pertama.sort_index()
        else:
            pertama = pertama.sort_values("persen_terisi", ascending=False)

        tampilkan_grafik(grafik_keterisian_kelompok(
            pertama, sekarang, horizontal=(kolom_kelompok == "FAKULTAS")
        ))
        st.caption(
            "Arahkan kursor untuk melihat jumlah alumni. Persentase pada kelompok kecil "
            "kurang stabil, jadi baca bersama jumlah alumninya."
        )

    # ---- Studi lanjut ----
    jumlah_lanjut = kelengkapan["total_lanjut_studi"]
    with kartu():
        kepala(
            "Keterisian data studi lanjut",
            f"Dasar: {format_angka(jumlah_lanjut)} alumni berstatus LANJUT STUDI",
        )
        if jumlah_lanjut == 0:
            st.info("Tidak ada alumni lanjut studi pada filter yang dipilih.")
        else:
            tampilkan_grafik(grafik_keterisian(kelengkapan["studi_lanjut"], jumlah_lanjut))

    with st.expander("Lihat tabel: keterisian setiap kolom"):
        st.markdown("**Pekerjaan** (dasar: semua alumni pada filter)")
        st.dataframe(tabel_tampil(tabel_kerja, total), width="stretch")
        if jumlah_lanjut > 0:
            st.markdown("**Studi lanjut** (dasar: alumni LANJUT STUDI)")
            st.dataframe(
                tabel_tampil(kelengkapan["studi_lanjut"], jumlah_lanjut), width="stretch"
            )


# =========================================================
# TEKS HALAMAN
# =========================================================

HERO_HALAMAN = {
    "Ringkasan": (
        "Ringkasan Alumni",
        "Gambaran umum jumlah alumni, sebaran periode wisuda dan fakultas, "
        "serta status studi lanjut.",
    ),
    "Karakteristik Alumni": (
        "Karakteristik Alumni",
        "Sebaran alumni berdasarkan periode wisuda, fakultas, program studi asal, "
        "jenis kelamin, dan jenjang.",
    ),
    "Studi Lanjut": (
        "Studi Lanjut",
        "Status studi lanjut alumni, serta jenjang, perguruan tinggi tujuan, "
        "dan program studi lanjut.",
    ),
    "Pekerjaan": (
        "Pekerjaan Pertama dan Sekarang",
        "Distribusi jenis pekerjaan, provinsi, kabupaten/kota, tempat kerja, "
        "dan posisi/jabatan alumni.",
    ),
    "Perbandingan": (
        "Perubahan Pekerjaan",
        "Perbandingan pekerjaan pertama dan sekarang: jenis pekerjaan, posisi, "
        "dan lokasi kerja.",
    ),
    "Kelengkapan Data": (
        "Kelengkapan Data",
        "Seberapa banyak data pekerjaan dan studi lanjut yang terisi, "
        "agar angka di halaman lain dibaca dengan konteks yang tepat.",
    ),
}

CATATAN_HALAMAN = {
    "Ringkasan": [
        "TIDAK LANJUT STUDI berarti tidak tercatat melanjutkan studi pada data tracer study.",
        "Periode wisuda ditampilkan sebagai nomor periode sesuai data.",
    ],
    "Karakteristik Alumni": [
        "Program studi ditampilkan N teratas. Atur dengan slider untuk melihat lebih banyak.",
        "Tabel periode × fakultas tersedia di bagian bawah halaman.",
    ],
    "Studi Lanjut": [
        "Persentase pada kelompok kecil kurang stabil. Baca bersama jumlah alumni.",
        "Jenjang, perguruan tinggi, dan program studi lanjut hanya dari alumni berstatus LANJUT STUDI.",
    ],
    "Pekerjaan": [
        "Persentase dihitung dari alumni yang datanya terisi, bukan dari seluruh alumni.",
        "Sebagian data pekerjaan diperoleh dari penelusuran LinkedIn secara manual.",
        "Data kosong tidak ditafsirkan sebagai belum bekerja atau kondisi tertentu.",
    ],
    "Perbandingan": [
        "Hanya alumni yang kedua datanya terisi yang dibandingkan.",
        "Jenis pekerjaan LAINNYA dikeluarkan dari perbandingan jenis pekerjaan.",
        "Data kosong dan (TIDAK DIKETAHUI) tidak dihitung sebagai sama maupun berbeda.",
        "Hasil tidak menunjukkan sebab perubahan atau urutan waktunya.",
    ],
    "Kelengkapan Data": [
        "Halaman ini hanya menghitung data terisi dan kosong, tanpa menafsirkan artinya.",
        "Sel kosong dapat berarti belum ditemukan, belum dicatat, atau hal lain. Data belum menjelaskannya.",
        "TIDAK LANJUT STUDI berasal dari sel kosong pada kolom LANJUT STUDI di Excel, sesuai keputusan pengolahan data.",
    ],
}

# =========================================================
# NAVIGASI ATAS DAN TATA LETAK
# =========================================================

def page_ringkasan():
    halaman_ringkasan(df_filter)


def page_karakteristik():
    halaman_karakteristik(df_filter)


def page_studi_lanjut():
    halaman_studi_lanjut(df_filter)


def page_pekerjaan():
    halaman_pekerjaan(df_filter)


def page_perbandingan():
    halaman_perbandingan(df_filter)


def page_kelengkapan():
    halaman_kelengkapan(df_filter)


halaman = st.navigation(
    [
        st.Page(page_ringkasan, title="Ringkasan", icon=":material/dashboard:",
                url_path="ringkasan", default=True),
        st.Page(page_karakteristik, title="Karakteristik Alumni", icon=":material/groups:",
                url_path="karakteristik"),
        st.Page(page_studi_lanjut, title="Studi Lanjut", icon=":material/school:",
                url_path="studi-lanjut"),
        st.Page(page_pekerjaan, title="Pekerjaan", icon=":material/work:",
                url_path="pekerjaan"),
        st.Page(page_perbandingan, title="Perbandingan", icon=":material/compare_arrows:",
                url_path="perbandingan"),
        st.Page(page_kelengkapan, title="Kelengkapan Data", icon=":material/fact_check:",
                url_path="kelengkapan"),
    ],
    position="top",
)

# ---- Baris atas: brand, pencarian, catatan, ekspor ----
kolom_brand, kolom_cari, kolom_catatan, kolom_ekspor = st.columns(
    [4, 3.2, 1.1, 1.2], vertical_alignment="center"
)

with kolom_brand:
    st.markdown(html_brand(), unsafe_allow_html=True)

with kolom_cari:
    pencarian = st.text_input(
        "Cari",
        key="pencarian",
        placeholder="Cari prodi, kampus, instansi, jabatan...",
        label_visibility="collapsed",
    )

# Tempat judul halaman: diisi setelah jumlah alumni pada filter diketahui
wadah_judul = st.container()

# ---- Baris filter ----
kolom_periode, kolom_fakultas, kolom_prodi, kolom_reset = st.columns(
    [1, 1, 1.3, 0.45], vertical_alignment="bottom"
)

with kolom_periode:
    pilihan_periode = st.multiselect(
        "Periode",
        options=sorted(df["PERIODE"].unique()),
        key="filter_periode",
        placeholder="Semua periode",
    )

with kolom_fakultas:
    pilihan_fakultas = st.multiselect(
        "Fakultas",
        options=sorted(df["FAKULTAS"].unique()),
        key="filter_fakultas",
        placeholder="Semua fakultas",
    )

# Pilihan program studi menyesuaikan fakultas yang dipilih
if pilihan_fakultas:
    data_untuk_prodi = df[df["FAKULTAS"].isin(pilihan_fakultas)]
else:
    data_untuk_prodi = df

opsi_prodi = sorted(data_untuk_prodi["PROGRAM STUDI ASAL"].unique())

# Buang pilihan program studi yang sudah tidak termasuk fakultas terpilih
st.session_state["filter_prodi"] = [
    p for p in st.session_state.get("filter_prodi", []) if p in opsi_prodi
]

with kolom_prodi:
    pilihan_prodi = st.multiselect(
        "Program studi",
        options=opsi_prodi,
        key="filter_prodi",
        placeholder="Semua program studi",
    )

with kolom_reset:
    st.button("Reset", key="tombol_reset", icon=":material/restart_alt:", on_click=reset_filter)

df_filter = filter_data(
    df,
    periode=pilihan_periode,
    fakultas=pilihan_fakultas,
    program_studi=pilihan_prodi,
)
df_filter = terapkan_pencarian(df_filter, pencarian)

# ---- Judul halaman ----
judul_hero, deskripsi_hero = HERO_HALAMAN[halaman.title]
jumlah_periode = df_filter["PERIODE"].nunique() if len(df_filter) else 0
jumlah_fakultas = df_filter["FAKULTAS"].nunique() if len(df_filter) else 0

with wadah_judul:
    st.markdown(
        f'<div class="ph"><h1>{html.escape(judul_hero)}</h1><p>{html.escape(deskripsi_hero)}</p>'
        f'<div class="ph-stat"><span>{format_angka(len(df_filter))} alumni</span><span>·</span>'
        f"<span>{jumlah_periode} periode wisuda</span><span>·</span>"
        f"<span>{jumlah_fakultas} fakultas</span></div></div>",
        unsafe_allow_html=True,
    )

# ---- Strip cakupan dan kelengkapan ----
if len(df_filter) > 0:
    kelengkapan_ringkas = kelengkapan_data(df_filter)["pekerjaan"]
    persen_pertama = float(kelengkapan_ringkas.loc["JENIS PEKERJAAN PERTAMA", "persen_terisi"])
    persen_sekarang = float(kelengkapan_ringkas.loc["JENIS PEKERJAAN SEKARANG", "persen_terisi"])
    bagian_kelengkapan = (
        f'<span>Pekerjaan pertama terisi: <b>{format_desimal(persen_pertama, 1)}%</b></span>'
        f'<span>Pekerjaan sekarang terisi: <b>{format_desimal(persen_sekarang, 1)}%</b></span>'
    )
else:
    bagian_kelengkapan = ""

st.markdown(
    f'<div class="strip"><span>Cakupan: <b>{format_angka(len(df_filter))}</b> dari '
    f"<b>{format_angka(len(df))}</b> alumni</span>"
    f'<span style="display:flex;gap:1.4rem;flex-wrap:wrap">{bagian_kelengkapan}</span></div>',
    unsafe_allow_html=True,
)

# ---- Catatan dan ekspor (butuh df_filter) ----
filter_aktif = []
if pilihan_periode:
    filter_aktif.append("Periode " + ", ".join(str(p) for p in sorted(pilihan_periode)))
filter_aktif += [judul_kasus(f) for f in pilihan_fakultas]
filter_aktif += [judul_kasus(p) for p in pilihan_prodi]
if pencarian.strip():
    filter_aktif.append(f'Cari: "{pencarian.strip()}"')

with kolom_catatan:
    if st.button("Catatan", key="tombol_catatan", icon=":material/info:"):
        dialog_catatan(halaman.title, df, df_filter, filter_aktif, CATATAN_HALAMAN[halaman.title])

with kolom_ekspor:
    with st.container(key="ekspor"):
        with st.popover("Ekspor", icon=":material/download:", disabled=df_filter.empty):
            tabel_ekspor = df_filter[KOLOM_EKSPOR]
            nama_berkas = f"tracer-study-alumni-{len(df_filter)}"
            st.download_button(
                f"Unduh CSV ({format_angka(len(df_filter))} baris)",
                data=lambda: csv_bytes(tabel_ekspor),
                file_name=f"{nama_berkas}.csv",
                mime="text/csv",
                key="unduh_csv",
                icon=":material/description:",
            )
            st.download_button(
                "Unduh Excel (.xlsx)",
                data=lambda: xlsx_bytes(tabel_ekspor),
                file_name=f"{nama_berkas}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="unduh_xlsx",
                icon=":material/table_view:",
            )
            st.caption("File tidak memuat nama, NIM, tanggal lahir, maupun tautan LinkedIn.")

# ---- Isi halaman ----
if df_filter.empty:
    st.warning(
        "Tidak ada alumni yang sesuai dengan kombinasi filter atau pencarian ini. "
        "Ubah pilihan atau klik Reset."
    )
else:
    halaman.run()