import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
import io

# ========================================================
# 1. KONEKSI & DATABASE SETUP
# ========================================================
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

EMAIL_ADMIN_PUSAT = "admin@apps.com"

# Inisialisasi State Aplikasi
if "user_email" not in st.session_state: st.session_state.user_email = None
if "current_page" not in st.session_state: st.session_state.current_page = "Dashboard"
if "auth_mode" not in st.session_state: st.session_state.auth_mode = "Login"

# ========================================================
# 2. OPTIMASI UI MOBILE (CSS INJECTION)
# ========================================================
st.markdown("""
<style>
    /* Mengatur tombol kantong atas agar tetap berjejer horizontal di layar HP */
    @media (max-width: 640px) {
        div[data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            justify-content: space-between !important;
            gap: 4px !important;
        }
        div[data-testid="column"] {
            width: 33.33% !important;
            min-width: 0px !important;
            padding: 0px !important;
        }
        div[data-testid="column"] button {
            padding: 6px 2px !important;
            font-size: 10px !important;
        }
    }
    /* Mempercantik tampilan card keuangan */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 12px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ========================================================
# 3. SISTEM AUTENTIKASI: LOGIN & DAFTAR AKUN
# ========================================================
if not st.session_state.user_email:
    st.markdown("<h2 style='text-align: center; color: #4F46E5;'>Pocket Keuangan 2026</h2>", unsafe_allow_html=True)
    
    col_auth1, col_auth2, col_auth3 = st.columns([0.2, 0.6, 0.2])
    with col_auth2:
        # Pilihan Mode: Login atau Daftar
        mode = st.radio("Aksi Sistem", ["Login Masuk Akun", "Daftar Akun Baru"], horizontal=True, label_visibility="collapsed")
        
        with st.form("auth_form"):
            email_input = st.text_input("Alamat Email", placeholder="contoh@email.com").strip().lower()
            password_input = st.text_input("Kata Sandi / Password", type="password", placeholder="••••••••")
            submit_auth = st.form_submit_button("Eksekusi" if mode == "Login Masuk Akun" else "Buat Akun Baru", use_container_width=True)
            
            if submit_auth:
                if not email_input or not password_input or "@" not in email_input:
                    st.error("Format Email atau Password tidak valid!")
                else:
                    if mode == "Login Masuk Akun":
                        # Proses Login
                        res = supabase.table("users").select("*").eq("email", email_input).eq("password", password_input).execute()
                        if len(res.data) > 0:
                            st.session_state.user_email = email_input
                            st.rerun()
                        else:
                            st.error("Email atau Kata Sandi Anda salah!")
                    else:
                        # Proses Pendaftaran
                        check_user = supabase.table("users").select("email").eq("email", email_input).execute()
                        if len(check_user.data) > 0:
                            st.error("Email ini sudah terdaftar! Silakan Login.")
                        else:
                            supabase.table("users").insert({"email": email_input, "password": password_input}).execute()
                            st.success("Akun berhasil dibuat! Silakan pindah ke opsi 'Login Masuk Akun'.")
    st.stop()

# ========================================================
# 4. HALAMAN KHUSUS PEMILIK (ADMIN CONTROL PUSAT)
# ========================================================
if st.session_state.user_email == EMAIL_ADMIN_PUSAT:
    st.title("👑 PANEL UTAMA PEMILIK APLIKASI")
    if st.button("Keluar Sistem / Logout"):
        st.session_state.user_email = None
        st.rerun()
    st.write("---")
    
    res_u = supabase.table("users").select("*").execute()
    res_t = supabase.table("transactions").select("*").execute()
    
    st.metric("Total Pengguna Aktif", len(res_u.data))
    st.write("### Daftar Akun Pengguna Terdaftar:")
    st.dataframe(pd.DataFrame(res_u.data), use_container_width=True)
    st.stop()

# ========================================================
# 5. INTEGRASI NAVIGASI & PENARIKAN DATA USER PERSONAL
# ========================================================
email_active = st.session_state.user_email

# Tarik semua data pelengkap dari database cloud
tx_res = supabase.table("transactions").select("*").eq("user_email", email_active).execute()
budget_res = supabase.table("budgets").select("*").eq("user_email", email_active).execute()
saving_res = supabase.table("savings_targets").select("*").eq("user_email", email_active).execute()
debt_res = supabase.table("debts").select("*").eq("user_email", email_active).execute()

df_tx = pd.DataFrame(tx_res.data)
df_budget = pd.DataFrame(budget_res.data)
df_saving = pd.DataFrame(saving_res.data)
df_debt = pd.DataFrame(debt_res.data)

# Hitung Akumulasi Nominal Kantong Utama
total_in = df_tx[df_tx["jenis"] == "Pemasukan"]["nominal"].sum() if not df_tx.empty else 0
total_out = df_tx[df_tx["jenis"] == "Pengeluaran"]["nominal"].sum() if not df_tx.empty else 0
net_balance = total_in - total_out

# ========================================================
# UI ATAS: 3 TOMBOL KANTONG BERJEJER HORIZONTAL (HP OPTIMIZED)
# ========================================================
c_in, c_out, c_bal = st.columns(3)
with c_in:
    if st.button(f"🟢 Masuk\nRp {total_in:,.0f}", use_container_width=True):
        st.session_state.current_page = "Kantong Pemasukan"
with c_out:
    if st.button(f"🔴 Keluar\nRp {total_out:,.0f}", use_container_width=True):
        st.session_state.current_page = "Kantong Pengeluaran"
with c_bal:
    if st.button(f"🔵 Sisa\nRp {net_balance:,.0f}", use_container_width=True):
        st.session_state.current_page = "Dashboard"

# Sidebar untuk menu fitur pelengkap harian - tahunan
with st.sidebar:
    st.write(f"👤 **{email_active}**")
    menu_fitur = st.radio("MENU FITUR KEUANGAN", [
        "🏠 Dashboard & Input",
        "💼 Dompet & Anggaran Bulanan",
        "🎯 Target Tabungan",
        "🤝 Catatan Hutang & Piutang",
        "📊 Grafik Mingguan/Bulanan/Tahunan"
    ])
    if st.button("🚪 Keluar Akun (Logout)", use_container_width=True):
        st.session_state.user_email = None
        st.rerun()

# HELPER: Generator Dokumen
def get_excel_bytes(df_target):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as w: df_target.to_excel(w, index=False)
    return out.getvalue()

# ========================================================
# LOGIKA ROUTING HALAMAN FITUR KEUANGAN LENGKAP
# ========================================================
st.write("---")

# A. HALAMAN SUB-KANTONG DETAIL (PEMASUKAN / PENGELUARAN)
if st.session_state.current_page != "Dashboard":
    st.subheader(f"🗂️ Detail {st.session_state.current_page}")
    if st.button("⬅️ Kembali ke Dashboard Utama"):
        st.session_state.current_page = "Dashboard"
        st.rerun()
        
    filter_jenis = "Pemasukan" if "Pemasukan" in st.session_state.current_page else "Pengeluaran"
    if df_tx.empty:
        st.info("Belum ada riwayat transaksi.")
    else:
        df_filtered = df_tx[df_tx["jenis"] == filter_jenis].reset_index(drop=True)
        if df_filtered.empty:
            st.info("Belum ada data di kantong ini.")
        else:
            st.dataframe(df_filtered[["tanggal", "kategori", "dompet", "keterangan", "nominal"]], use_container_width=True)
            st.download_button("📊 Ekspor ke Excel (.xlsx)", get_excel_bytes(df_filtered), f"laporan_{filter_jenis}.xlsx")

# B. DASHBOARD UTAMA & PENCATATAN HARIAN
elif menu_fitur == "🏠 Dashboard & Input":
    st.subheader("📊 Dashboard Saldo & Pencatatan Transaksi")
    
    # Form Input Transaksi Hari Ini (Bagian Bawah Tiga Kantong)
    with st.form("tx_form", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            in_jenis = st.selectbox("Jenis Transaksi", ["Pengeluaran", "Pemasukan"])
            in_kategori = st.selectbox("Kategori", ["Gaji Utama", "Investasi", "Makanan & Minuman", "Transportasi", "Belanja", "Tagihan", "Hiburan", "Lainnya"])
        with col_f2:
            in_dompet = st.selectbox("Dompet / Rekening Sumber", ["Cash/Tunai", "Bank Mandiri", "Bank BCA", "E-Wallet (Gopay/OVO)"])
            in_nominal = st.number_input("Nominal Transaksi (Rp)", min_value=0, step=1000)
            
        in_ket = st.text_input("Keterangan Transaksi", placeholder="Contoh: Beli bensin motor, makan bakso")
        submit_tx = st.form_submit_button("Simpan Transaksi Hari Ini")
        
        if submit_tx and in_nominal > 0:
            supabase.table("transactions").insert({
                "user_email": email_active, "tanggal": datetime.now().strftime("%Y-%m-%d"),
                "jenis": in_jenis, "kategori": in_kategori, "dompet": in_dompet,
                "keterangan": in_ket, "nominal": in_nominal
            }).execute()
            st.success("Transaksi berhasil masuk ke dalam database kantong!")
            st.invalidate()
            st.rerun()

    # Tabel Riwayat Transaksi Ringkas
    st.write("#### 🕒 10 Riwayat Transaksi Terakhir")
    if not df_tx.empty:
        st.dataframe(df_tx.sort_values(by="id", ascending=False).head(10)[["tanggal", "jenis", "kategori", "dompet", "keterangan", "nominal"]], use_container_width=True)
    else:
        st.caption("Belum ada riwayat pencatatan.")

# C. FITUR DOMPET & ANGGARAN BULANAN
elif menu_fitur == "💼 Dompet & Anggaran Bulanan":
    st.subheader("Anggaran Bulanan & Pos Rekening")
    current_month = datetime.now().strftime("%Y-%m")
    
    with st.form("budget_form"):
        set_budget = st.number_input(f"Set Batas Anggaran Bulanan Bulan Ini ({current_month})", min_value=0, step=50000)
        if st.form_submit_button("Simpan Anggaran"):
            supabase.table("budgets").upsert({"user_email": email_active, "bulan_tahun": current_month, "nominal": set_budget}, on_conflict="user_email,bulan_tahun").execute()
            st.success("Anggaran bulanan berhasil diperbarui!")
            st.rerun()
            
    # Tampilkan progres sisa anggaran bulanan rill
    budget_val = df_budget[df_budget["bulan_tahun"] == current_month]["nominal"].values[0] if not df_budget.empty else 0
    st.metric("Alokasi Anggaran Bulanan Anda", f"Rp {budget_val:,.0f}")
    st.progress(min(float(total_out / budget_val) if budget_val > 0 else 0.0, 1.0), text=f"Pengeluaran Terpakai: Rp {total_out:,.0f} dari Rp {budget_val:,.0f}")

# D. FITUR TARGET TABUNGAN
elif menu_fitur == "🎯 Target Tabungan":
    st.subheader("🎯 Impian & Target Celengan Tabungan")
    with st.form("saving_form", clear_on_submit=True):
        s_nama = st.text_input("Nama Impian / Barang", placeholder="Contoh: Beli Laptop Baru, Liburan Akhir Tahun")
        s_target = st.number_input("Target Dana Terkumpul (Rp)", min_value=0, step=100000)
        if st.form_submit_button("Tambah Target"):
            if s_nama:
                supabase.table("savings_targets").insert({"user_email": email_active, "nama_target": s_nama, "nominal_target": s_target, "terkumpul": 0}).execute()
                st.success("Target tabungan baru berhasil ditambahkan!")
                st.rerun()
                
    if not df_saving.empty:
        st.write("#### Daftar Target Celengan Anda:")
        st.dataframe(df_saving[["nama_target", "nominal_target", "terkumpul"]], use_container_width=True)

# E. FITUR CATATAN HUTANG & PIUTANG
elif menu_fitur == "🤝 Catatan Hutang & Piutang":
    st.subheader("🤝 Buku Pencatatan Hutang dan Piutang")
    with st.form("debt_form", clear_on_submit=True):
        d_tipe = st.selectbox("Tipe Catatan", ["Hutang", "Piutang"])
        d_nama = st.text_input("Nama Orang Terkait")
        d_nominal = st.number_input("Nominal (Rp)", min_value=0, step=10000)
        if st.form_submit_button("Simpan Catatan"):
            if d_nama and d_nominal > 0:
                supabase.table("debts").insert({"user_email": email_active, "tipe": d_tipe, "nama_orang": d_nama, "nominal": d_nominal, "status": "Belum Lunas"}).execute()
                st.success("Catatan saldo piutang/hutang disimpan!")
                st.rerun()
                
    if not df_debt.empty:
        st.write("#### Daftar Tanggungan Aktif:")
        st.dataframe(df_debt[["tipe", "nama_orang", "nominal", "status"]], use_container_width=True)

# F. LAPORAN & GRAFIK BERKALA (MINGGUAN, BULANAN, TAHUNAN)
elif menu_fitur == "📊 Grafik Mingguan/Bulanan/Tahunan":
    st.subheader("📉 Laporan & Analisis Grafik Keuangan Berkala")
    if df_tx.empty:
        st.info("Masukkan data transaksi terlebih dahulu untuk memunculkan visualisasi grafik.")
    else:
        df_tx["tanggal"] = pd.to_datetime(df_tx["tanggal"])
        
        # 1. Grafik Mingguan (7 Hari Terakhir)
        st.write("#### 📆 Tren Pengeluaran Mingguan (7 Hari Terakhir)")
        one_week_ago = datetime.now() - timedelta(days=7)
        df_week = df_tx[(df_tx["tanggal"] >= one_week_ago) & (df_tx["jenis"] == "Pengeluaran")]
        if not df_week.empty:
            df_week_group = df_week.groupby(df_week["tanggal"].dt.strftime('%Y-%m-%d'))["nominal"].sum()
            st.bar_chart(df_week_group)
        else: st.caption("Tidak ada pengeluaran dalam 7 hari terakhir.")
        
        # 2. Grafik Bulanan (Bulan Berjalan)
        st.write("#### 📅 Perbandingan Pemasukan vs Pengeluaran Bulan Ini")
        df_tx["bulan"] = df_tx["tanggal"].dt.strftime('%Y-%m')
        this_month = datetime.now().strftime('%Y-%m')
        df_month = df_tx[df_tx["bulan"] == this_month]
        if not df_month.empty:
            df_month_group = df_month.groupby("jenis")["nominal"].sum()
            st.bar_chart(df_month_group)
        else: st.caption("Belum ada data transaksi di bulan ini.")
        
        # 3. Grafik Tahunan (Tahun Berjalan)
        st.write("#### 🏛️ Akumulasi Total Berjalan Sepanjang Tahun 2026")
        df_year_group = df_tx.groupby("jenis")["nominal"].sum()
        st.bar_chart(df_year_group)
