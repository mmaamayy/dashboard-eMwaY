import pandas as pd

# Teks di Excel yang berarti "tempat/kota tidak diketahui".
# Berbeda dengan sel kosong, nilai ini SUDAH diisi (tetapi isinya "tidak diketahui").
NILAI_TIDAK_DIKETAHUI = "(TIDAK DIKETAHUI)"

# Nilai kolom LANJUT STUDI (hasil preprocessing)
STATUS_LANJUT = "LANJUT STUDI"

# Kategori jenis pekerjaan yang dikeluarkan dari perbandingan pertama vs sekarang
# (keputusan: isinya beragam, jadi "sama" belum tentu pekerjaan yang sama)
JENIS_DIKECUALIKAN = "LAINNYA"


# NOTE: semua fungsi di file ini menerima DataFrame (parameter `df`),
# tidak lagi membaca data global. Dengan begitu hasilnya mengikuti
# filter yang dipilih pengguna di dashboard.


# =========================================================
# 0. FILTER DATA
# =========================================================

def filter_data(df, periode=None, fakultas=None, program_studi=None):
    """Menyaring DataFrame berdasarkan periode, fakultas, dan program studi asal.

    Setiap parameter berupa list nilai yang dipilih.
    Jika None atau list kosong, berarti tidak ada penyaringan pada kolom itu.
    """
    hasil = df

    if periode:
        hasil = hasil[hasil["PERIODE"].isin(periode)]

    if fakultas:
        hasil = hasil[hasil["FAKULTAS"].isin(fakultas)]

    if program_studi:
        hasil = hasil[hasil["PROGRAM STUDI ASAL"].isin(program_studi)]

    return hasil


# =========================================================
# 1. KARAKTERISTIK ALUMNI
# =========================================================

def karakteristik_alumni(df):
    hasil = {
        "total_alumni": len(df),
        "berdasarkan_periode": df["PERIODE"].value_counts().sort_index(),
        "berdasarkan_fakultas": df["FAKULTAS"].value_counts(),
        "berdasarkan_program_studi": df["PROGRAM STUDI ASAL"].value_counts(),
        "berdasarkan_jenis_kelamin": df["JENIS KELAMIN"].value_counts(),
        "berdasarkan_jenjang": df["JENJANG"].value_counts()
    }

    return hasil


def distribusi_alumni(df):
    return {
        "periode_fakultas": pd.crosstab(
            df["PERIODE"],
            df["FAKULTAS"]
        ),

        "periode_prodi": pd.crosstab(
            df["PERIODE"],
            df["PROGRAM STUDI ASAL"]
        ),

        "fakultas_prodi": pd.crosstab(
            df["FAKULTAS"],
            df["PROGRAM STUDI ASAL"]
        )
    }


# =========================================================
# 2. STATUS STUDI LANJUT
# =========================================================

def studi_lanjut(df):
    jumlah = df["LANJUT STUDI"].value_counts()

    persentase = (
        df["LANJUT STUDI"]
        .value_counts(normalize=True)
        .mul(100)
        .round(2)
    )

    return {
        "jumlah": jumlah,
        "persentase": persentase
    }


def distribusi_studi_lanjut(df):
    # Detail studi lanjut hanya relevan untuk alumni yang berstatus LANJUT STUDI
    lanjut = df[df["LANJUT STUDI"] == STATUS_LANJUT]

    return {
        "berdasarkan_periode": pd.crosstab(
            df["PERIODE"],
            df["LANJUT STUDI"]
        ),

        "berdasarkan_fakultas": pd.crosstab(
            df["FAKULTAS"],
            df["LANJUT STUDI"]
        ),

        "berdasarkan_program_studi": pd.crosstab(
            df["PROGRAM STUDI ASAL"],
            df["LANJUT STUDI"]
        ),

        "jenjang_studi_lanjut": lanjut["JENJANG STUDI LANJUT"].value_counts(),

        "perguruan_tinggi": lanjut["PERGURUAN TINGGI STUDI LANJUT"].value_counts(),

        "program_studi_lanjut": lanjut["PROGRAM STUDI LANJUT"].value_counts()
    }


def ringkasan_lanjut_studi_per(df, kolom):
    """Jumlah alumni, jumlah yang lanjut studi, dan persentasenya per kelompok.

    Contoh: ringkasan_lanjut_studi_per(df, "FAKULTAS").
    Persentase pada kelompok yang alumninya sedikit kurang stabil,
    jadi total_alumni selalu ditampilkan berdampingan.
    """
    tabel = pd.crosstab(df[kolom], df["LANJUT STUDI"])

    # Jika tidak ada alumni lanjut studi pada data yang difilter,
    # kolom STATUS_LANJUT tidak terbentuk, maka dibuat bernilai 0
    if STATUS_LANJUT not in tabel.columns:
        tabel[STATUS_LANJUT] = 0

    hasil = pd.DataFrame({
        "total_alumni": tabel.sum(axis=1),
        "lanjut_studi": tabel[STATUS_LANJUT]
    })
    hasil["persen_lanjut"] = (
        hasil["lanjut_studi"] / hasil["total_alumni"] * 100
    ).round(2)

    return hasil


# =========================================================
# 3. PEKERJAAN PERTAMA
# =========================================================
# Catatan: value_counts() hanya menghitung sel yang TERISI.
# Banyaknya sel kosong dapat dilihat lewat kelengkapan_data().

def pekerjaan_pertama(df):
    return {
        "jenis_pekerjaan": df["JENIS PEKERJAAN PERTAMA"].value_counts(),
        "nama_tempat_kerja": df["NAMA TEMPAT KERJA PERTAMA"].value_counts(),
        "provinsi": df["PROVINSI TEMPAT KERJA PERTAMA"].value_counts(),
        "kabupaten_kota": df["KABUPATEN/KOTA TEMPAT KERJA PERTAMA"].value_counts(),
        "posisi": df["POSISI/JABATAN PERTAMA"].value_counts()
    }


# Kolom pekerjaan per tahap (pertama / sekarang)
KOLOM_PEKERJAAN = {
    "pertama": {
        "jenis": "JENIS PEKERJAAN PERTAMA",
        "jenis_lain": "JENIS PEKERJAAN LAIN PERTAMA",
        "tempat_kerja": "NAMA TEMPAT KERJA PERTAMA",
        "provinsi": "PROVINSI TEMPAT KERJA PERTAMA",
        "kabupaten_kota": "KABUPATEN/KOTA TEMPAT KERJA PERTAMA",
        "posisi": "POSISI/JABATAN PERTAMA"
    },
    "sekarang": {
        "jenis": "JENIS PEKERJAAN SEKARANG",
        "jenis_lain": "JENIS PEKERJAAN LAIN SEKARANG",
        "tempat_kerja": "NAMA TEMPAT KERJA SEKARANG",
        "provinsi": "PROVINSI TEMPAT KERJA SEKARANG",
        "kabupaten_kota": "KABUPATEN/KOTA TEMPAT KERJA SEKARANG",
        "posisi": "POSISI/JABATAN SEKARANG"
    }
}


def distribusi_pekerjaan_tahap(df, tahap):
    """Distribusi pekerjaan untuk satu tahap: "pertama" atau "sekarang".

    Untuk setiap aspek (jenis, tempat kerja, provinsi, kabupaten/kota, posisi)
    hasilnya berisi:
    - terisi: jumlah alumni yang sel-nya terisi
    - kosong: jumlah alumni yang sel-nya kosong (maknanya belum diketahui)
    - tidak_diketahui: yang berisi teks "(TIDAK DIKETAHUI)"
    - dapat_dianalisis: terisi dikurangi tidak_diketahui (dasar persentase)
    - distribusi: hasil value_counts() dari data yang dapat dianalisis
    """
    hasil = {}

    for aspek, kolom in KOLOM_PEKERJAAN[tahap].items():
        if aspek == "jenis_lain":
            continue

        seri = df[kolom]
        ada_isi = seri.notna()
        tidak_diketahui = seri.eq(NILAI_TIDAK_DIKETAHUI).fillna(False).astype(bool)
        dipakai = ada_isi & ~tidak_diketahui

        hasil[aspek] = {
            "total_alumni": len(df),
            "terisi": int(ada_isi.sum()),
            "kosong": int((~ada_isi).sum()),
            "tidak_diketahui": int(tidak_diketahui.sum()),
            "dapat_dianalisis": int(dipakai.sum()),
            "distribusi": seri[dipakai].value_counts()
        }

    return hasil


def rincian_jenis_pekerjaan_lainnya(df, tahap):
    """Teks bebas pada kolom "JENIS PEKERJAAN LAIN ...", dihitung per nilai.
    Hanya huruf besar-kecil yang diseragamkan; tulisan lain tidak diubah."""
    seri = df[KOLOM_PEKERJAAN[tahap]["jenis_lain"]].dropna()
    return seri.map(lambda v: v.upper()).value_counts()


# =========================================================
# 4. PEKERJAAN SEKARANG
# =========================================================

def pekerjaan_sekarang(df):
    return {
        "jenis_pekerjaan": df["JENIS PEKERJAAN SEKARANG"].value_counts(),
        "nama_tempat_kerja": df["NAMA TEMPAT KERJA SEKARANG"].value_counts(),
        "provinsi": df["PROVINSI TEMPAT KERJA SEKARANG"].value_counts(),
        "kabupaten_kota": df["KABUPATEN/KOTA TEMPAT KERJA SEKARANG"].value_counts(),
        "posisi": df["POSISI/JABATAN SEKARANG"].value_counts()
    }


def distribusi_pekerjaan(df):
    return {
        "pekerjaan_pertama": df["JENIS PEKERJAAN PERTAMA"].value_counts(),
        "pekerjaan_sekarang": df["JENIS PEKERJAAN SEKARANG"].value_counts(),
        "provinsi_pertama": df["PROVINSI TEMPAT KERJA PERTAMA"].value_counts(),
        "provinsi_sekarang": df["PROVINSI TEMPAT KERJA SEKARANG"].value_counts(),
        "kabupaten_pertama": df["KABUPATEN/KOTA TEMPAT KERJA PERTAMA"].value_counts(),
        "kabupaten_sekarang": df["KABUPATEN/KOTA TEMPAT KERJA SEKARANG"].value_counts(),
        "posisi_pertama": df["POSISI/JABATAN PERTAMA"].value_counts(),
        "posisi_sekarang": df["POSISI/JABATAN SEKARANG"].value_counts()
    }


# =========================================================
# 5. PERUBAHAN PEKERJAAN
# =========================================================

def analisis_perubahan_pekerjaan(df):
    """Tabel per alumni: pekerjaan pertama berdampingan dengan pekerjaan sekarang."""
    perubahan = pd.DataFrame({
        "NIM": df["NIM"],
        "NAMA": df["NAMA"],
        "JENIS PEKERJAAN PERTAMA": df["JENIS PEKERJAAN PERTAMA"],
        "JENIS PEKERJAAN SEKARANG": df["JENIS PEKERJAAN SEKARANG"],
        "POSISI/JABATAN PERTAMA": df["POSISI/JABATAN PERTAMA"],
        "POSISI/JABATAN SEKARANG": df["POSISI/JABATAN SEKARANG"],
        "PROVINSI PERTAMA": df["PROVINSI TEMPAT KERJA PERTAMA"],
        "PROVINSI SEKARANG": df["PROVINSI TEMPAT KERJA SEKARANG"],
        "KABUPATEN/KOTA PERTAMA": df["KABUPATEN/KOTA TEMPAT KERJA PERTAMA"],
        "KABUPATEN/KOTA SEKARANG": df["KABUPATEN/KOTA TEMPAT KERJA SEKARANG"]
    })

    return perubahan


def matriks_jenis_pekerjaan(df):
    """Baris = jenis pekerjaan pertama, kolom = jenis pekerjaan sekarang.
    Hanya alumni yang KEDUA datanya terisi yang dihitung.
    Kategori LAINNYA (JENIS_DIKECUALIKAN) tidak ikut dihitung."""
    dapat = _dapat_dibandingkan(df, "jenis")
    return pd.crosstab(
        df.loc[dapat, "JENIS PEKERJAAN PERTAMA"],
        df.loc[dapat, "JENIS PEKERJAAN SEKARANG"]
    )


def ringkasan_perubahan_pekerjaan(df):
    """Membandingkan pekerjaan pertama dan sekarang untuk tiap aspek.

    Hanya alumni yang kedua datanya terisi (dan bukan "(TIDAK DIKETAHUI)")
    yang dibandingkan. Sisanya TIDAK dianggap sama maupun berbeda.
    Untuk jenis pekerjaan, kategori LAINNYA dikeluarkan dari perbandingan
    dan jumlahnya dicatat pada kolom "dikecualikan".
    Untuk posisi/jabatan, "berbeda" artinya tulisannya tidak persis sama,
    belum tentu jabatannya benar-benar berbeda.
    """
    aspek = {
        "Jenis pekerjaan": "jenis",
        "Provinsi": "provinsi",
        "Kabupaten/Kota": "kabupaten_kota",
        "Posisi/Jabatan": "posisi"
    }

    baris = {}
    for nama, kunci in aspek.items():
        kolom_pertama, kolom_sekarang = PASANGAN_ASPEK[kunci]
        pertama = df[kolom_pertama]
        sekarang = df[kolom_sekarang]

        salah_satu_kosong = pertama.isna() | sekarang.isna()
        tidak_diketahui = ~salah_satu_kosong & (
            pertama.eq(NILAI_TIDAK_DIKETAHUI).fillna(False).astype(bool)
            | sekarang.eq(NILAI_TIDAK_DIKETAHUI).fillna(False).astype(bool)
        )
        dapat_dibandingkan = _dapat_dibandingkan(df, kunci)
        dikecualikan = ~salah_satu_kosong & ~tidak_diketahui & ~dapat_dibandingkan

        sama = (pertama == sekarang).fillna(False).astype(bool)

        baris[nama] = {
            "total_alumni": len(df),
            "dapat_dibandingkan": int(dapat_dibandingkan.sum()),
            "sama": int((dapat_dibandingkan & sama).sum()),
            "berbeda": int((dapat_dibandingkan & ~sama).sum()),
            "salah_satu_kosong": int(salah_satu_kosong.sum()),
            "tidak_diketahui": int(tidak_diketahui.sum()),
            "dikecualikan": int(dikecualikan.sum())
        }

    return pd.DataFrame(baris).T


# Pasangan kolom (pertama, sekarang) untuk setiap aspek yang dibandingkan
PASANGAN_ASPEK = {
    "jenis": ("JENIS PEKERJAAN PERTAMA", "JENIS PEKERJAAN SEKARANG"),
    "provinsi": ("PROVINSI TEMPAT KERJA PERTAMA", "PROVINSI TEMPAT KERJA SEKARANG"),
    "kabupaten_kota": (
        "KABUPATEN/KOTA TEMPAT KERJA PERTAMA",
        "KABUPATEN/KOTA TEMPAT KERJA SEKARANG"
    ),
    "posisi": ("POSISI/JABATAN PERTAMA", "POSISI/JABATAN SEKARANG")
}


def _dapat_dibandingkan(df, aspek):
    """True untuk alumni yang data pertama dan sekarangnya terisi
    dan bukan "(TIDAK DIKETAHUI)". Khusus aspek "jenis", alumni yang jenis
    pekerjaannya LAINNYA (pada salah satu tahap) juga dikeluarkan."""
    kolom_pertama, kolom_sekarang = PASANGAN_ASPEK[aspek]
    pertama = df[kolom_pertama]
    sekarang = df[kolom_sekarang]

    pertama_diketahui = pertama.notna() & ~pertama.eq(NILAI_TIDAK_DIKETAHUI).fillna(False).astype(bool)
    sekarang_diketahui = sekarang.notna() & ~sekarang.eq(NILAI_TIDAK_DIKETAHUI).fillna(False).astype(bool)

    dapat = pertama_diketahui & sekarang_diketahui

    if aspek == "jenis":
        lainnya = (
            pertama.eq(JENIS_DIKECUALIKAN).fillna(False).astype(bool)
            | sekarang.eq(JENIS_DIKECUALIKAN).fillna(False).astype(bool)
        )
        dapat = dapat & ~lainnya

    return dapat


def perpindahan_pekerjaan(df, aspek):
    """Perpindahan dari pekerjaan pertama ke sekarang untuk satu aspek
    ("jenis", "provinsi", "kabupaten_kota", atau "posisi").

    Hanya alumni yang kedua datanya terisi yang dibandingkan.
    Hasil berisi:
    - dapat_dibandingkan: jumlah alumni yang dibandingkan
    - berbeda: jumlah alumni yang nilainya berbeda
    - perpindahan: tabel (dari, ke, jumlah) khusus yang berbeda, terbanyak dulu
    """
    kolom_pertama, kolom_sekarang = PASANGAN_ASPEK[aspek]
    dapat = _dapat_dibandingkan(df, aspek)

    pasangan = pd.DataFrame({
        "dari": df.loc[dapat, kolom_pertama],
        "ke": df.loc[dapat, kolom_sekarang]
    })
    berbeda = pasangan[pasangan["dari"] != pasangan["ke"]]

    tabel = (
        berbeda.groupby(["dari", "ke"])
        .size()
        .reset_index(name="jumlah")
        .sort_values(["jumlah", "dari", "ke"], ascending=[False, True, True])
        .reset_index(drop=True)
    )

    return {
        "dapat_dibandingkan": int(dapat.sum()),
        "berbeda": len(berbeda),
        "perpindahan": tabel
    }


def alumni_dapat_dibandingkan(df):
    """Alumni yang minimal satu aspeknya dapat dibandingkan."""
    mask = pd.Series(False, index=df.index)
    for aspek in PASANGAN_ASPEK:
        mask = mask | _dapat_dibandingkan(df, aspek)
    return df[mask]


def banding_jenis_pekerjaan(df):
    """Jumlah alumni per jenis pekerjaan pada tahap pertama dan sekarang,
    hanya dari alumni yang dapat dibandingkan (lihat matriks_jenis_pekerjaan).
    selisih = sekarang - pertama."""
    matriks = matriks_jenis_pekerjaan(df)
    kategori = sorted(set(matriks.index) | set(matriks.columns))
    pertama = matriks.sum(axis=1).reindex(kategori, fill_value=0)
    sekarang = matriks.sum(axis=0).reindex(kategori, fill_value=0)

    return pd.DataFrame({
        "pertama": pertama,
        "sekarang": sekarang,
        "selisih": sekarang - pertama
    })


def ringkasan_per_program_studi(df):
    """Satu baris per program studi asal (per fakultas dan jenjang):
    jumlah alumni, jumlah dan persen lanjut studi, serta persen alumni
    yang data jenis pekerjaan pertamanya terisi."""
    bantu = df.assign(
        _lanjut=(df["LANJUT STUDI"] == STATUS_LANJUT),
        _kerja1=df["JENIS PEKERJAAN PERTAMA"].notna()
    )

    hasil = (
        bantu.groupby(["PROGRAM STUDI ASAL", "FAKULTAS", "JENJANG"])
        .agg(
            alumni=("PERIODE", "size"),
            lanjut=("_lanjut", "sum"),
            kerja1=("_kerja1", "sum")
        )
        .reset_index()
    )
    hasil["persen_lanjut"] = (hasil["lanjut"] / hasil["alumni"] * 100).round(2)
    hasil["persen_kerja1"] = (hasil["kerja1"] / hasil["alumni"] * 100).round(2)

    return hasil.sort_values(
        ["alumni", "PROGRAM STUDI ASAL"], ascending=[False, True]
    ).reset_index(drop=True)


def alokasikan_waffle(seri, dasar, maks_irisan=6, nama_gabungan="Kategori kecil (gabungan)"):
    """Membagi 100 petak waffle ke kategori menurut proporsinya.

    seri: hasil value_counts() (terbesar dulu). Kategori di luar (maks_irisan - 1)
    teratas digabung. Setiap kategori mendapat minimal 1 petak; sisa petak dibagi
    dengan metode sisa terbesar. persen dihitung terhadap `dasar`.
    Mengembalikan list dict: label, jumlah, persen, petak.
    """
    positif = seri[seri > 0]
    if len(positif) == 0 or dasar <= 0:
        return []

    if len(positif) > maks_irisan:
        atas = positif.iloc[:maks_irisan - 1]
        sisa_jumlah = int(positif.iloc[maks_irisan - 1:].sum())
        kelompok = [(k, int(v)) for k, v in atas.items()] + [(nama_gabungan, sisa_jumlah)]
    else:
        kelompok = [(k, int(v)) for k, v in positif.items()]

    total = sum(jumlah for _, jumlah in kelompok) or dasar
    pasti = [jumlah / total * 100 for _, jumlah in kelompok]
    petak = [max(1, int(p)) for p in pasti]
    pecahan = [p - int(p) for p in pasti]
    banyak = len(kelompok)

    kurang = 100 - sum(petak)
    if kurang > 0:
        urutan = sorted(range(banyak), key=lambda i: -pecahan[i])
        i = 0
        while kurang > 0:
            petak[urutan[i % banyak]] += 1
            kurang -= 1
            i += 1
    elif kurang < 0:
        urutan = sorted(range(banyak), key=lambda i: -petak[i])
        i = 0
        while kurang < 0:
            sasaran = urutan[i % banyak]
            if petak[sasaran] > 1:
                petak[sasaran] -= 1
                kurang += 1
            i += 1

    return [
        {"label": label, "jumlah": jumlah, "persen": jumlah / dasar * 100, "petak": petak[i]}
        for i, (label, jumlah) in enumerate(kelompok)
    ]


# =========================================================
# 6. KELENGKAPAN DATA
# =========================================================

def _tabel_kelengkapan(data, daftar_kolom):
    tabel = pd.DataFrame({
        "terisi": data[daftar_kolom].notna().sum(),
        "kosong": data[daftar_kolom].isna().sum(),
        "tidak_diketahui": (data[daftar_kolom] == NILAI_TIDAK_DIKETAHUI).sum()
    })

    total = len(data)
    if total > 0:
        tabel["persen_terisi"] = (tabel["terisi"] / total * 100).round(2)
    else:
        tabel["persen_terisi"] = 0.0

    return tabel


def kelengkapan_data(df):
    """Jumlah data terisi dan kosong per kolom.

    Fungsi ini hanya MENGHITUNG, tidak menafsirkan arti sel kosong
    (belum tercatat, belum ditemukan, tidak bekerja, dan seterusnya
    belum bisa dibedakan dari data yang ada).
    - "pekerjaan": dasar perhitungan = semua alumni pada data yang difilter.
    - "studi_lanjut": dasar perhitungan = hanya alumni berstatus LANJUT STUDI.
    """
    kolom_pekerjaan = [
        "JENIS PEKERJAAN PERTAMA",
        "NAMA TEMPAT KERJA PERTAMA",
        "PROVINSI TEMPAT KERJA PERTAMA",
        "KABUPATEN/KOTA TEMPAT KERJA PERTAMA",
        "POSISI/JABATAN PERTAMA",
        "JENIS PEKERJAAN SEKARANG",
        "NAMA TEMPAT KERJA SEKARANG",
        "PROVINSI TEMPAT KERJA SEKARANG",
        "KABUPATEN/KOTA TEMPAT KERJA SEKARANG",
        "POSISI/JABATAN SEKARANG"
    ]

    kolom_studi_lanjut = [
        "JENJANG STUDI LANJUT",
        "PERGURUAN TINGGI STUDI LANJUT",
        "PROGRAM STUDI LANJUT"
    ]

    lanjut = df[df["LANJUT STUDI"] == STATUS_LANJUT]

    return {
        "total_alumni": len(df),
        "total_lanjut_studi": len(lanjut),
        "pekerjaan": _tabel_kelengkapan(df, kolom_pekerjaan),
        "studi_lanjut": _tabel_kelengkapan(lanjut, kolom_studi_lanjut)
    }


def kelengkapan_per_kelompok(df, kolom_kelompok, kolom_data):
    """Persentase alumni yang kolom_data-nya terisi, untuk tiap kelompok.

    Contoh: kelengkapan_per_kelompok(df, "FAKULTAS", "JENIS PEKERJAAN PERTAMA").
    Dasar persentase = seluruh alumni pada kelompok tersebut.
    """
    terisi = df[kolom_data].notna()

    hasil = pd.DataFrame({
        "total_alumni": df.groupby(kolom_kelompok).size(),
        "terisi": terisi.groupby(df[kolom_kelompok]).sum().astype(int)
    })
    hasil["persen_terisi"] = (hasil["terisi"] / hasil["total_alumni"] * 100).round(2)

    return hasil


def pola_keterisian_pekerjaan(df):
    """Jumlah alumni menurut kombinasi terisi/kosong pada jenis pekerjaan
    pertama dan sekarang. Hanya menghitung, tidak menafsirkan sel kosong."""
    pertama = df["JENIS PEKERJAAN PERTAMA"].notna()
    sekarang = df["JENIS PEKERJAAN SEKARANG"].notna()

    return pd.Series({
        "Keduanya terisi": int((pertama & sekarang).sum()),
        "Hanya pekerjaan pertama terisi": int((pertama & ~sekarang).sum()),
        "Hanya pekerjaan sekarang terisi": int((~pertama & sekarang).sum()),
        "Keduanya kosong": int((~pertama & ~sekarang).sum())
    })


# =========================================================
# PENGUJIAN (hanya jalan jika file ini dijalankan langsung)
# =========================================================

if __name__ == "__main__":
    from preprocessing import load_data

    df = load_data()

    print("=== KARAKTERISTIK ALUMNI ===")
    hasil = karakteristik_alumni(df)
    print("\nTotal alumni:", hasil["total_alumni"])
    print("\nBerdasarkan periode:")
    print(hasil["berdasarkan_periode"])
    print("\nBerdasarkan fakultas:")
    print(hasil["berdasarkan_fakultas"])
    print("\nBerdasarkan jenis kelamin:")
    print(hasil["berdasarkan_jenis_kelamin"])
    print("\nBerdasarkan jenjang:")
    print(hasil["berdasarkan_jenjang"])

    print("\n=== STUDI LANJUT ===")
    hasil_studi = studi_lanjut(df)
    print(hasil_studi["jumlah"])
    print(hasil_studi["persentase"])

    print("\n=== DISTRIBUSI STUDI LANJUT ===")
    hasil_distribusi = distribusi_studi_lanjut(df)
    print("\nJenjang studi lanjut:")
    print(hasil_distribusi["jenjang_studi_lanjut"])
    print("\n5 perguruan tinggi tujuan terbanyak:")
    print(hasil_distribusi["perguruan_tinggi"].head())

    print("\n=== PEKERJAAN PERTAMA ===")
    print(pekerjaan_pertama(df)["jenis_pekerjaan"])

    print("\n=== PEKERJAAN SEKARANG ===")
    print(pekerjaan_sekarang(df)["jenis_pekerjaan"])

    print("\n=== RINGKASAN PERUBAHAN PEKERJAAN ===")
    print(ringkasan_perubahan_pekerjaan(df))

    print("\n=== KELENGKAPAN DATA ===")
    kelengkapan = kelengkapan_data(df)
    print("\nPekerjaan (dasar: semua alumni):")
    print(kelengkapan["pekerjaan"])
    print("\nStudi lanjut (dasar: alumni LANJUT STUDI):")
    print(kelengkapan["studi_lanjut"])

    print("\n=== UJI FILTER ===")
    contoh = filter_data(df, fakultas=["ILMU KOMPUTER"])
    print("Alumni Fakultas Ilmu Komputer:", len(contoh))
    print(studi_lanjut(contoh)["jumlah"])