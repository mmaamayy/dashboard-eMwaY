import re
import warnings
from pathlib import Path

import pandas as pd

# Lokasi file Excel dihitung dari lokasi preprocessing.py,
# jadi aplikasi tetap jalan walaupun dijalankan dari folder lain.
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "alumni.xlsx"

# Daftar kolom SESUAI URUTAN di Excel terbaru (27 kolom, tanpa kolom pendapatan).
# Setiap item: (nama baru, kata kunci yang harus ada di header asli).
# Kata kunci dipakai untuk memeriksa bahwa urutan kolom Excel belum berubah.
KOLOM = [
    ("NO", "no."),
    ("NIM", "nim"),
    ("FAKULTAS", "fakultas"),
    ("PROGRAM STUDI ASAL", "unnamed"),          # header Excel kosong
    ("JENJANG", "jenjang"),
    ("NAMA", "nama"),
    ("JENIS KELAMIN", "jenis kelamin"),
    ("PERIODE", "periode"),
    ("TANGGAL LAHIR", "tanggal lahir"),
    ("LANJUT STUDI", "lanjut studi"),
    ("JENJANG STUDI LANJUT", "jenjang"),
    ("PERGURUAN TINGGI STUDI LANJUT", "perguruan tinggi"),
    ("PROGRAM STUDI LANJUT", "program studi"),
    ("TANGGAL MASUK STUDI LANJUT", "tanggal masuk"),
    ("JENIS PEKERJAAN PERTAMA", "jenis pekerjaan"),
    ("JENIS PEKERJAAN LAIN PERTAMA", "selain"),
    ("NAMA TEMPAT KERJA PERTAMA", "nama tempat kerja"),
    ("PROVINSI TEMPAT KERJA PERTAMA", "provinsi"),
    ("KABUPATEN/KOTA TEMPAT KERJA PERTAMA", "kabupaten"),
    ("POSISI/JABATAN PERTAMA", "posisi"),
    ("JENIS PEKERJAAN SEKARANG", "jenis pekerjaan"),
    ("JENIS PEKERJAAN LAIN SEKARANG", "selain"),
    ("NAMA TEMPAT KERJA SEKARANG", "nama tempat kerja"),
    ("PROVINSI TEMPAT KERJA SEKARANG", "provinsi"),
    ("KABUPATEN/KOTA TEMPAT KERJA SEKARANG", "kabupaten"),
    ("POSISI/JABATAN SEKARANG", "posisi"),
    ("LINK LINKEDIN", "linkedin"),
]


# Kolom kategori yang ditulis dengan huruf besar/kecil tidak konsisten di Excel
# (mis. "EKONOMI" dan "Ekonomi"). Isinya diseragamkan menjadi HURUF BESAR
# agar tidak terhitung sebagai dua kategori berbeda. Tulisan lain tidak diubah.
KOLOM_HURUF_BESAR = [
    "FAKULTAS",
    "PROGRAM STUDI ASAL",
    "JENJANG",
    "JENJANG STUDI LANJUT",
    "PERGURUAN TINGGI STUDI LANJUT",
    "PROGRAM STUDI LANJUT",
    "JENIS PEKERJAAN PERTAMA",
    "NAMA TEMPAT KERJA PERTAMA",
    "PROVINSI TEMPAT KERJA PERTAMA",
    "KABUPATEN/KOTA TEMPAT KERJA PERTAMA",
    "POSISI/JABATAN PERTAMA",
    "JENIS PEKERJAAN SEKARANG",
    "NAMA TEMPAT KERJA SEKARANG",
    "PROVINSI TEMPAT KERJA SEKARANG",
    "KABUPATEN/KOTA TEMPAT KERJA SEKARANG",
    "POSISI/JABATAN SEKARANG",
]

# Penulisan berbeda untuk hal yang sama (sudah dikonfirmasi: D3 = DIII)
PENYERAGAMAN_JENJANG = {"D3": "DIII"}


def _normalisasi_header(teks):
    """Huruf kecil, spasi/enter berlebih dirapikan, agar mudah dibandingkan."""
    return re.sub(r"\s+", " ", str(teks)).strip().lower()


def _validasi_struktur(df):
    """Memeriksa struktur kolom Excel sebelum nama kolom diganti.

    Kalau jumlah atau urutan kolom tidak sesuai, program berhenti dengan
    pesan yang jelas (bukan menebak dan menghasilkan data yang tertukar).
    """
    header = [_normalisasi_header(c) for c in df.columns]

    # Kolom pendapatan seharusnya sudah tidak ada
    ada_pendapatan = [h for h in header if "pendapatan" in h or "gaji" in h]
    if ada_pendapatan:
        raise ValueError(
            f"Masih ada kolom pendapatan/gaji di Excel: {ada_pendapatan}. "
            "Proyek ini tidak memakai kolom tersebut."
        )

    if len(header) != len(KOLOM):
        raise ValueError(
            f"Jumlah kolom Excel = {len(header)}, tetapi preprocessing.py "
            f"mengharapkan {len(KOLOM)} kolom. Header yang terbaca: "
            f"{list(df.columns)}"
        )

    tidak_cocok = []
    for posisi, (nama_baru, kata_kunci) in enumerate(KOLOM):
        if kata_kunci not in header[posisi]:
            tidak_cocok.append(
                f"kolom ke-{posisi + 1}: diharapkan '{nama_baru}' "
                f"(mengandung '{kata_kunci}'), tetapi header Excel = "
                f"'{df.columns[posisi]}'"
            )
    if tidak_cocok:
        raise ValueError(
            "Urutan kolom Excel tidak sesuai dengan preprocessing.py:\n"
            + "\n".join(tidak_cocok)
        )


def _rapikan_teks(df):
    """Menghapus spasi di awal/akhir teks. Sel yang hanya berisi spasi
    dianggap kosong. Nilai asli lainnya tidak diubah."""
    for kolom in df.columns:
        seri = df[kolom]
        if pd.api.types.is_object_dtype(seri) or pd.api.types.is_string_dtype(seri):
            df[kolom] = seri.map(
                lambda v: v.strip() if isinstance(v, str) else v
            ).replace("", pd.NA)
    return df


def _seragamkan_kategori(df):
    """Huruf besar untuk kolom kategori, dan menyamakan D3 menjadi DIII."""
    for kolom in KOLOM_HURUF_BESAR:
        df[kolom] = df[kolom].map(
            lambda v: v.upper() if isinstance(v, str) else v
        )
    df["JENJANG"] = df["JENJANG"].replace(PENYERAGAMAN_JENJANG)
    return df


def load_data():
    # Pesan peringatan openpyxl tentang "Data Validation" tidak berbahaya
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Data Validation extension")
        # header=0: header ada di baris pertama Excel (baris Maharani sudah
        # dipindah ke bawah header, jadi tidak ada lagi baris di atasnya)
        df = pd.read_excel(DATA_PATH, sheet_name=0, header=0)

    # 1. Pastikan struktur kolom sesuai, lalu ganti nama kolom berdasarkan
    #    POSISI. Cara ini aman untuk header duplikat (mis. dua kolom
    #    "PROGRAM STUDI": satu program studi asal, satu program studi lanjut).
    _validasi_struktur(df)
    df.columns = [nama for nama, _ in KOLOM]

    # 2. Rapikan spasi di semua kolom teks
    df = _rapikan_teks(df)

    # 3. Seragamkan huruf besar/kecil pada kolom kategori
    df = _seragamkan_kategori(df)

    # 4. Nilai kosong pada LANJUT STUDI = tidak tercatat lanjut studi
    df["LANJUT STUDI"] = (
        df["LANJUT STUDI"].astype("string").fillna("TIDAK LANJUT STUDI")
    )

    return df


# Pengujian preprocessing
if __name__ == "__main__":
    df = load_data()

    print("Ukuran data:", df.shape)

    print("\nNama kolom:")
    print(df.columns.tolist())

    print("\n5 data pertama:")
    print(df.head())

    print("\nDistribusi LANJUT STUDI:")
    print(df["LANJUT STUDI"].value_counts())

    print("\nJumlah data kosong setiap kolom:")
    print(df.isna().sum())