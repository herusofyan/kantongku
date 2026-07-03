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

if "user_email" not in st.session_state: st.session_state.user_email = None
if "current_page" not in st.session_state: st.session_state.current_page = "Dashboard"

# ========================================================
# 2. INJEKSI CSS - PERBAIKAN TOTAL LAYOUT HP (ANTI-BOCOR)
# ========================================================
st.markdown("""
<style>
    /* Batasi lebar form login & tengah-kan agar estetik di HP dan Desktop */
    div[data-testid="stForm"] {
        max-width: 480px !important;
        margin: 0 auto !important;
        border-radius: 20px !important;
        padding: 20px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
    }
    
    /* Mengatur tombol kantong finansial utama (Pemasukan, Pengeluaran, Sisa) */
    div[data-testid="column"] button {
        width: 100% !important;
        border-radius: 14px !important;
        padding: 12px 4px !important;
        border: none !important;
        transition: all 0.2s ease;
    }
    
    /* Warna Lembut & Teks Kontras untuk Masing-masing Tombol Kantong */
    div[data-testid="column"]:nth-child(1) button {
        background-color: #E6F4EA !important;
        color: #137333 !important;
    }
    div[data-testid="column"]:nth-child(2) button {
        background-color: #FCE8E6 !important;
        color: #C5221F !important;
    }
    div[data-testid="column"]:nth-child(3) button {
        background-color: #E8EAF6 !important;
        color: #3F51B5 !important;
    }
    
    /* Aturan Khusus Layar HP / Mobile */
    @media (max-width: 640px) {
        /* Memaksa 3 Kantong Atas Tetap Berjejer Horizontal */
        .stHorizontalBlock {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            justify-content: space-between !important;
            gap: 6px !important;
        }
        .stHorizontalBlock > div[data-testid="column"] {
            flex: 1 1 0% !important;
            min-width: 0px !important;
        }
        div[data-testid="column"] button p {
            font-size: 11px !important;
            font-weight: 800 !important;
            line-height: 1.3 !important;
        }
        .main-title { font-size: 22px !important; }
    }
</style>
""", unsafe_allow_html=True)

# ========================================================
# 3. KAMUS BILINGUAL (ID / EN)
# ========================================================
LANG = {
    "ID": {
        "login_header": "Pocket Keuangan 2026",
        "login_subheader": "Kelola finansial harian hingga tahunan dalam satu genggaman",
        "btn_login": "Masuk ke Aplikasi",
        "admin_title": "👑 KENDALI PUSAT PEMILIK",
        "pocket_in": "🟢 Masuk",
        "pocket_out": "🔴 Keluar",
        "pocket_balance": "🔵 Sisa",
        "form_title": "📝 Catat Transaksi Baru",
        "type": "Jenis",
        "income": "Pemasukan",
        "expense": "Pengeluaran",
        "desc": "Keterangan",
        "desc_placeholder": "Contoh: Makan siang, Gaji...",
        "amount": "Nominal (Rp)",
        "save": "Simpan Transaksi",
        "back": "⬅️ Dashboard Utama",
        "history": "🕒 5 Transaksi Terakhir",
        "no_data": "Belum ada catatan transaksi.",
        "download_title": "Ekspor Data",
        "btn_excel": "📊 Unduh Excel (.xlsx)",
        "btn_pdf": "📄 Unduh PDF Laporan",
        "success": "Berhasil disimpan!",
        "logout": "Keluar"
    },
    "EN": {
        "login_header": "Pocket Finance 2026",
        "login_subheader": "Manage daily to annual wealth in one grip",
        "btn_login": "Enter Application",
        "admin_title": "👑 OWNER CENTRAL PANEL",
        "pocket_in": "🟢 Income",
        "pocket_out": "🔴 Expense",
        "pocket_balance": "🔵 Balance",
        "form_title": "📝 Record New Transaction",
        "type": "Type",
        "income": "Income",
        "expense": "Expense",
        "desc": "Description",
        "desc_placeholder": "e.g. Lunch, Salary...",
        "amount": "Amount (Rp)",
        "save": "Save Transaction",
        "back": "⬅️ Main Dashboard",
        "history": "🕒 Last 5 Transactions",
        "no_data": "No transaction records yet.",
        "download_title": "Export Report",
        "btn_excel": "📊 Download Excel (.xlsx)",
        "btn_pdf": "📄 Download PDF Report",
        "success": "Successfully saved!",
        "logout": "Logout"
    }
}

if "lang" not in st.session_state: st.session_state.lang = "ID"
t = LANG[st.session_state.lang]

# Switch Bahasa di Pojok Kanan Atas
col_t1, col_t2 = st.columns([0.8, 0.2])
with col_t2:
    lang_choice = st.selectbox("Lang", ["ID", "EN"], index=0 if st.session_state.lang == "ID" else 1, label_visibility="collapsed")
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()

# GERBANG LOG IN & DAFTAR (TANPA BENTROK KOLOM)
if not st.session_state.user_email:
    st.markdown(f"<h2 class='main-title' style='text-align: center; color: #3F51B5; margin-top:20px; font-weight:800;'>{t['login_header']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #666; font-size:13px; margin-bottom:20px;'>{t['login_subheader']}</p>", unsafe_allow_html=True)
    
    # Mode Pilihan Center Ringkas
    mode = st.radio("Aksi", ["Login Masuk Saku", "Daftar Akun Baru"], horizontal=True, label_visibility="collapsed")
    
    with st.form("auth_form"):
        email_input = st.text_input("Alamat Email", placeholder="nama@email.com").strip().lower()
        password_input = st.text_input("Kata Sandi (Password)", type="password", placeholder="••••••••")
        
        if st.form_submit_button("MASUK SEKARANG" if mode == "Login Masuk Saku" else "DAFTAR AKUN BARU", use_container_width=True):
            if email_input and password_input and "@" in email_input:
                if mode == "Login Masuk Saku":
                    res = supabase.table("users").select("*").eq("email", email_input).eq("password", password_input).execute()
                    if len(res.data) > 0:
                        st.session_state.user_email = email_input
                        st.rerun()
                    else: st.error("Email atau Password salah!")
                else:
                    check = supabase.table("users").select("email").eq("email", email_input).execute()
                    if len(check.data) > 0: st.error("Email ini sudah terdaftar!")
                    else:
                        supabase.table("users").insert({"email": email_input, "password": password_input}).execute()
                        st.success("Akun sukses dibuat! Silakan aktifkan opsi 'Login Masuk Saku'.")
            else: st.error("Silakan isi Email dan Password dengan benar!")
    st.stop()

# PANEL PUSAT PEMILIK (ADMIN CONTROL)
if st.session_state.user_email == EMAIL_ADMIN_PUSAT:
    st.subheader(t["admin_title"])
    if st.button("Logout Dashboard Pemilik", use_container_width=True):
        st.session_state.user_email = None
        st.rerun()
    res_u = supabase.table("users").select("*").execute()
    st.metric("Total Pengguna Terdaftar", len(res_u.data))
    st.dataframe(pd.DataFrame(res_u.data), use_container_width=True)
    st.stop()

# AMBIL DATA DARI SUPABASE CLOUD
email_active = st.session_state.user_email
res_tx = supabase.table("transactions").select("*").eq("user_email", email_active).execute()
res_bg = supabase.table("budgets").select("*").eq("user_email", email_active).execute()
res_sv = supabase.table("savings_targets").select("*").eq("user_email", email_active).execute()
res_db = supabase.table("debts").select("*").eq("user_email", email_active).execute()

df_tx = pd.DataFrame(res_tx.data)
df_budget = pd.DataFrame(res_bg.data)
df_saving = pd.DataFrame(res_sv.data)
df_debt = pd.DataFrame(res_db.data)

if not df_tx.empty: df_tx.columns = [c.lower() for c in df_tx.columns]

total_in = df_tx[df_tx["jenis"] == "Pemasukan"]["nominal"].sum() if not df_tx.empty else 0
total_out = df_tx[df_tx["jenis"] == "Pengeluaran"]["nominal"].sum() if not df_tx.empty else 0
balance = total_in - total_out

# ========================================================
# UI ATAS: 3 TOMBOL KANTONG BERJEJER HORIZONTAL (HP-OPTIMIZED)
# ========================================================
st.write("")
k1, k2, k3 = st.columns(3)
with k1:
    if st.button(f"{t['pocket_in']}\nRp {total_in:,.0f}", use_container_width=True):
        st.session_state.current_page = "pemasukan_page"
with k2:
    if st.button(f"{t['pocket_out']}\nRp {total_out:,.0f}", use_container_width=True):
        st.session_state.current_page = "pengeluaran_page"
with k3:
    if st.button(f"{t['pocket_balance']}\nRp {balance:,.0f}", use_container_width=True):
        st.session_state.current_page = "Dashboard"

# TAB NAVIGASI UTAMA SIDEBAR UNTUK SMARTPHONE
with st.sidebar:
    st.write(f"👤 Akun: **{email_active}**")
    menu = st.radio("FITUR UTAMA", [
        "🏠 Dashboard & Input",
        "💼 Dompet & Anggaran",
        "🎯 Target Tabungan",
        "🤝 Hutang & Piutang",
        "📊 Grafik Analisis"
    ])
    if st.button(t["logout"], use_container_width=True, type="secondary"):
        st.session_state.user_email = None
        st.rerun()

# EXPORTER LAPORAN
def get_excel(df_target):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='openpyxl') as w: df_target.to_excel(w, index=False)
    return out.getvalue()

def get_html_pdf(df_data, title, total):
    rows = "".join([f"<tr><td style='border:1px solid #ddd;padding:6px;text-align:center;'>{i+1}</td><td style='border:1px solid #ddd;padding:6px;text-align:center;'>{r['tanggal']}</td><td style='border:1px solid #ddd;padding:6px;'>{r['keterangan']}</td><td style='border:1px solid #ddd;padding:6px;text-align:right;'>Rp {r['nominal']:,.0f}</td></tr>" for i, r in df_data.iterrows()])
    return f"<html><body onload='window.print()'><h3 style='text-align:center;'>{title.upper()}</h3><table style='width:100%;border-collapse:collapse;'><thead><tr style='background:#f2f2f2;'><th>No</th><th>Tanggal</th><th>Keterangan</th><th>Nominal</th></tr></thead><tbody>{rows}</tbody></table><h4 style='text-align:right;'>Total: Rp {total:,.0f}</h4></body></html>"

# LOGIKA ROUTING HALAMAN SUB-KANTONG
if st.session_state.current_page != "Dashboard":
    st.write(f"### 🗂️ Detail {st.session_state.current_page.replace('_page', '').upper()}")
    if st.button(t["back"], use_container_width=True):
        st.session_state.current_page = "Dashboard"
        st.rerun()
        
    f_jenis = "Pemasukan" if "pemasukan" in st.session_state.current_page else "Pengeluaran"
    if df_tx.empty: st.info(t["no_data"])
    else:
        df_f = df_tx[df_tx["jenis"] == f_jenis].reset_index(drop=True)
        if df_f.empty: st.info(t["no_data"])
        else:
            st.dataframe(df_f[["tanggal", "kategori", "dompet", "keterangan", "nominal"]], use_container_width=True)
            st.download_button(t["btn_excel"], get_excel(df_f), "laporan.xlsx", use_container_width=True)
            st.download_button(t["btn_pdf"], get_html_pdf(df_f, f_jenis, total_in if f_jenis=="Pemasukan" else total_out), "laporan.html", use_container_width=True)

# LOGIKA FITUR UTAMA KEUANGAN
elif menu == "🏠 Dashboard & Input":
    st.write(f"#### {t['form_title']}")
    with st.form("tx_form", clear_on_submit=True):
        in_j = st.selectbox(t["type"], ["Pengeluaran", "Pemasukan"])
        in_k = st.selectbox("Kategori", ["Gaji Utama", "Investasi", "Makanan & Minuman", "Transportasi", "Belanja", "Tagihan", "Lainnya"])
        in_d = st.selectbox("Dompet / Rekening", ["Cash/Tunai", "Bank Mandiri", "Bank BCA", "E-Wallet"])
        in_n = st.number_input(t["amount"], min_value=0, step=1000)
        in_kt = st.text_input(t["desc"], placeholder=t["desc_placeholder"])
        
        if st.form_submit_button(t["save"], use_container_width=True) and in_n > 0:
            supabase.table("transactions").insert({
                "user_email": email_active, "tanggal": datetime.now().strftime("%Y-%m-%d"),
                "jenis": in_j, "kategori": in_k, "dompet": in_d, "keterangan": in_kt, "nominal": in_n
            }).execute()
            st.success(t["success"])
            st.rerun()

    st.write(f"#### {t['history']}")
    if not df_tx.empty:
        st.dataframe(df_tx.sort_values(by="id", ascending=False).head(5)[["tanggal", "jenis", "keterangan", "nominal"]], use_container_width=True)
    else: st.caption(t["no_data"])

elif menu == "💼 Dompet & Anggaran":
    st.subheader("💼 Batas Anggaran Bulanan")
    c_month = datetime.now().strftime("%Y-%m")
    with st.form("b_form"):
        set_b = st.number_input("Set Limit Anggaran Bulan Ini (Rp)", min_value=0, step=50000)
        if st.form_submit_button("Simpan Batas", use_container_width=True):
            supabase.table("budgets").upsert({"user_email": email_active, "bulan_tahun": c_month, "nominal": set_b}, on_conflict="user_email,bulan_tahun").execute()
            st.success("Anggaran diperbarui!")
            st.rerun()
    b_val = df_budget[df_budget["bulan_tahun"] == c_month]["nominal"].values[0] if not df_budget.empty else 0
    st.progress(min(float(total_out / b_val) if b_val > 0 else 0.0, 1.0), text=f"Terpakai: Rp {total_out:,.0f} / Rp {b_val:,.0f}")

elif menu == "🎯 Target Tabungan":
    st.subheader("🎯 Target Tabungan Impian")
    with st.form("s_form", clear_on_submit=True):
        s_n = st.text_input("Nama Barang / Impian")
        s_t = st.number_input("Nominal Target Capaian (Rp)", min_value=0)
        if st.form_submit_button("Tambah Celengan", use_container_width=True) and s_n:
            supabase.table("savings_targets").insert({"user_email": email_active, "nama_target": s_n, "nominal_target": s_t}).execute()
            st.rerun()
    if not df_saving.empty: st.dataframe(df_saving[["nama_target", "nominal_target", "terkumpul"]], use_container_width=True)

elif menu == "🤝 Hutang & Piutang":
    st.subheader("🤝 Buku Catatan Hutang & Piutang")
    with st.form("d_form", clear_on_submit=True):
        d_tp = st.selectbox("Tipe Transaksi", ["Hutang", "Piutang"])
        d_nm = st.text_input("Nama Orang Terkait")
        d_nm_val = st.number_input("Nominal Transaksi (Rp)", min_value=0)
        if st.form_submit_button("Simpan Buku Catatan", use_container_width=True) and d_nm:
            supabase.table("debts").insert({"user_email": email_active, "tipe": d_tp, "nama_orang": d_nm, "nominal": d_nm_val}).execute()
            st.rerun()
    if not df_debt.empty: st.dataframe(df_debt[["tipe", "nama_orang", "nominal", "status"]], use_container_width=True)

elif menu == "📊 Grafik Analisis":
    st.subheader("📈 Ringkasan Grafik Keuangan Berkala")
    if df_tx.empty: st.info(t["no_data"])
    else:
        df_tx["tanggal"] = pd.to_datetime(df_tx["tanggal"])
        
        st.write("📆 **Tren Pengeluaran 7 Hari Terakhir (Mingguan)**")
        w_ago = datetime.now() - timedelta(days=7)
        df_w = df_tx[(df_tx["tanggal"] >= w_ago) & (df_tx["jenis"] == "Pengeluaran")]
        if not df_w.empty: st.bar_chart(df_w.groupby(df_w["tanggal"].dt.strftime('%m-%d'))["nominal"].sum())
        
        st.write("📅 **Arus Kas Akumulasi Keseluruhan (Pemasukan vs Pengeluaran)**")
        st.bar_chart(df_tx.groupby("jenis")["nominal"].sum())
