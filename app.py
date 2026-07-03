import streamlit as st
import pandas as pd
from datetime import datetime
import sqlite3
import io

# ========================================================
# 1. INNER DATABASE SYSTEM (SQLite Setup)
# ========================================================
DB_NAME = "database_kantong.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            tanggal_daftar TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            tanggal TEXT,
            jenis TEXT,
            keterangan TEXT,
            nominal REAL,
            FOREIGN KEY (user_email) REFERENCES users(email)
        )
    """)
    conn.commit()
    conn.close()

init_db()
EMAIL_ADMIN_PUSAT = "admin@apps.com"

# ========================================================
# 2. KAMUS MULTI-BAHASA (ID / EN)
# ========================================================
LANG = {
    "ID": {
        "login_header": "Selamat Datang di Kantong Keuangan",
        "login_subheader": "Silakan masukkan email Anda untuk masuk ke kantong personal",
        "btn_login": "Masuk ke Aplikasi",
        "admin_title": "👑 KENDALI PUSAT (Halaman Pemilik)",
        "admin_subtitle": "Daftar pengguna aktif yang menggunakan aplikasi Anda saat ini",
        "total_users": "Total Pengguna Terdaftar",
        "user_list": "Daftar Email Pengguna",
        "pocket_in": "Kantong Pemasukan",
        "pocket_out": "Kantong Pengeluaran",
        "pocket_balance": "Kantong Sisa Uang",
        "form_title": "Input Transaksi Hari Ini",
        "type": "Jenis Transaksi",
        "income": "Pemasukan",
        "expense": "Pengeluaran",
        "desc": "Keterangan / Kategori",
        "desc_placeholder": "Contoh: Gaji bulanan, Makan siang...",
        "amount": "Nominal (Rupiah)",
        "save": "Simpan ke Kantong",
        "back": "⬅️ Kembali ke Dashboard",
        "history": "Riwayat Transaksi",
        "no_data": "Belum ada transaksi di kantong ini.",
        "download_title": "Pilih Format Unduhan Laporan",
        "btn_excel": "📊 Unduh format Excel (.xlsx)",
        "btn_pdf": "📄 Unduh format PDF Laporan",
        "success": "Transaksi berhasil disimpan!",
        "logout": "Keluar Akun"
    },
    "EN": {
        "login_header": "Welcome to Pocket Finance",
        "login_subheader": "Please enter your email to access your personal pocket",
        "btn_login": "Enter Application",
        "admin_title": "👑 CENTRAL PANEL (Owner View)",
        "admin_subtitle": "List of active users currently using your application",
        "total_users": "Total Registered Users",
        "user_list": "User Email Registry",
        "pocket_in": "Income Pocket",
        "pocket_out": "Expense Pocket",
        "pocket_balance": "Balance Pocket",
        "form_title": "Input Today's Transaction",
        "type": "Transaction Type",
        "income": "Income",
        "expense": "Expense",
        "desc": "Description / Category",
        "desc_placeholder": "e.g. Monthly salary, Lunch...",
        "amount": "Amount (Rupiah)",
        "save": "Save to Pocket",
        "back": "⬅️ Back to Dashboard",
        "history": "Transaction History",
        "no_data": "No transactions in this pocket yet.",
        "download_title": "Select Report Download Format",
        "btn_excel": "📊 Download Excel Format (.xlsx)",
        "btn_pdf": "📄 Download PDF Report",
        "success": "Transaction saved successfully!",
        "logout": "Logout Account"
    }
}

st.set_page_config(page_title="Financial Pockets Database", layout="wide")

if "lang" not in st.session_state:
    st.session_state.lang = "ID"
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "dashboard"

t = LANG[st.session_state.lang]

col_top1, col_top2 = st.columns([0.8, 0.2])
with col_top2:
    lang_choice = st.selectbox("Language", ["ID", "EN"], index=0 if st.session_state.lang == "ID" else 1, label_visibility="collapsed")
    if lang_choice != st.session_state.lang:
        st.session_state.lang = lang_choice
        st.rerun()
    if st.session_state.user_email:
        if st.button(t["logout"], type="secondary", use_container_width=True):
            st.session_state.user_email = None
            st.session_state.current_page = "dashboard"
            st.rerun()

# GERBANG LOGIN
if not st.session_state.user_email:
    st.write("---")
    st.markdown(f"<h2 style='text-align: center;'>{t['login_header']}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: gray;'>{t['login_subheader']}</p>", unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([0.3, 0.4, 0.3])
    with col_l2:
        with st.form("login_form"):
            input_email = st.text_input("Email Address", placeholder="nama@email.com").strip().lower()
            submit_login = st.form_submit_button(t["btn_login"], use_container_width=True)
            
            if submit_login:
                if input_email == "" or "@" not in input_email:
                    st.error("Masukkan format email yang valid!")
                else:
                    conn = sqlite3.connect(DB_NAME)
                    cursor = conn.cursor()
                    cursor.execute("INSERT OR IGNORE INTO users (email, tanggal_daftar) VALUES (?, ?)", 
                                   (input_email, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    conn.commit()
                    conn.close()
                    
                    st.session_state.user_email = input_email
                    st.rerun()
    st.stop()

# KENDALI PUSAT ADMIN
if st.session_state.user_email == EMAIL_ADMIN_PUSAT:
    st.title(t["admin_title"])
    st.caption(t["admin_subtitle"])
    st.write("---")
    
    conn = sqlite3.connect(DB_NAME)
    df_users = pd.read_sql_query("SELECT * FROM users", conn)
    df_total_tx = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    
    col_adm1, col_adm2 = st.columns(2)
    with col_adm1:
        st.metric(label=t["total_users"], value=len(df_users))
    with col_adm2:
        st.metric(label="Total Seluruh Log Transaksi Sistem", value=len(df_total_tx))
        
    st.write(f"### 👥 {t['user_list']}")
    st.dataframe(df_users, use_container_width=True)
    st.stop()

# HALAMAN USER PERSONAL
email_user = st.session_state.user_email
st.caption(f"👤 Login as: **{email_user}**")

conn = sqlite3.connect(DB_NAME)
df_user_tx = pd.read_sql_query("SELECT * FROM transactions WHERE user_email = ?", conn, params=(email_user,))
conn.close()

total_masuk = df_user_tx[df_user_tx["jenis"] == "Pemasukan"]["nominal"].sum() if not df_user_tx.empty else 0
total_keluar = df_user_tx[df_user_tx["jenis"] == "Pengeluaran"]["nominal"].sum() if not df_user_tx.empty else 0
sisa_uang = total_masuk - total_keluar

st.write("---")
k_in, k_out, k_bal = st.columns(3)
with k_in:
    st.metric(label=t["pocket_in"], value=f"Rp {total_masuk:,.0f}")
    if st.button("📂 " + t["pocket_in"] + " →", use_container_width=True, key="btn_in"):
        st.session_state.current_page = "income_page"
with k_out:
    st.metric(label=t["pocket_out"], value=f"Rp {total_keluar:,.0f}")
    if st.button("📂 " + t["pocket_out"] + " →", use_container_width=True, key="btn_out"):
        st.session_state.current_page = "expense_page"
with k_bal:
    st.metric(label=t["pocket_balance"], value=f"Rp {sisa_uang:,.0f}")
    if st.button("📂 " + t["pocket_balance"] + " →", use_container_width=True, key="btn_bal"):
        st.session_state.current_page = "balance_page"

# LOGIKA GENERATOR LAPORAN YANG SUDAH DIPERBAIKI (generate_excel)
def generate_excel(df_data, title):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_data.to_excel(writer, index=False, sheet_name=title[:30])
    return output.getvalue()

def get_html_pdf_download(df_data, title, total_val):
    show_jenis = "jenis" in df_data.columns
    th_jenis = "<th>Jenis</th>" if show_jenis else ""
    
    rows = ""
    for idx, row in df_data.iterrows():
        td_jenis = f"<td style='border:1px solid #ddd;padding:8px;text-align:center;'>{row['jenis']}</td>" if show_jenis else ""
        rows += f"""<tr>
            <td style='border:1px solid #ddd;padding:8px;text-align:center;'>{idx+1}</td>
            <td style='border:1px solid #ddd;padding:8px;text-align:center;'>{row['tanggal']}</td>
            <td style='border:1px solid #ddd;padding:8px;'>{row['keterangan']}</td>
            {td_jenis}
            <td style='border:1px solid #ddd;padding:8px;text-align:right;'>Rp {row['nominal']:,.0f}</td>
        </tr>"""
        
    return f"""<html><body onload='window.print()'>
        <h2 style='text-align:center;'>{title.upper()}</h2>
        <p style='text-align:center;'>User Email: {email_user}</p>
        <table style='width:100%;border-collapse:collapse;'>
            <thead>
                <tr style='background:#f2f2f2;'>
                    <th>No</th>
                    <th>Tanggal</th>
                    <th>Keterangan</th>
                    {th_jenis}
                    <th>Nominal</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        <h3 style='text-align:right;margin-top:20px;'>Total: Rp {total_val:,.0f}</h3>
    </body></html>"""

st.write("---")

if st.session_state.current_page == "dashboard":
    st.write(f"### 📥 {t['form_title']}")
    with st.form("user_input_form", clear_on_submit=True):
        jenis_tx = st.selectbox(t["type"], [t["income"], t["expense"]])
        keterangan_tx = st.text_input(t["desc"], placeholder=t["desc_placeholder"])
        nominal_tx = st.number_input(t["amount"], min_value=0, step=1000, value=0)
        
        if st.form_submit_button(t["save"]):
            if keterangan_tx.strip() == "" or nominal_tx <= 0:
                st.error("Data tidak valid!")
            else:
                real_type = "Pemasukan" if jenis_tx == t["income"] else "Pengeluaran"
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO transactions (user_email, tanggal, jenis, keterangan, nominal) VALUES (?, ?, ?, ?, ?)",
                               (email_user, datetime.now().strftime("%Y-%m-%d"), real_type, keterangan_tx, nominal_tx))
                conn.commit()
                conn.close()
                st.success(t["success"])
                st.rerun()

elif st.session_state.current_page == "income_page":
    if st.button(t["back"]): st.session_state.current_page = "dashboard"; st.rerun()
    st.subheader(t["pocket_in"])
    df_inc = df_user_tx[df_user_tx["jenis"] == "Pemasukan"].reset_index(drop=True)
    if df_inc.empty: st.warning(t["no_data"])
    else:
        st.dataframe(df_inc[["tanggal", "keterangan", "nominal"]], use_container_width=True)
        col_d1, col_d2 = st.columns(2)
        col_d1.download_button(t["btn_excel"], generate_excel(df_inc[["tanggal", "keterangan", "nominal"]], "Pemasukan"), "pemasukan.xlsx")
        col_d2.download_button(t["btn_pdf"], get_html_pdf_download(df_inc[["tanggal", "keterangan", "nominal"]], t["pocket_in"], total_masuk), "pemasukan.html")

elif st.session_state.current_page == "expense_page":
    if st.button(t["back"]): st.session_state.current_page = "dashboard"; st.rerun()
    st.subheader(t["pocket_out"])
    df_exp = df_user_tx[df_user_tx["jenis"] == "Pengeluaran"].reset_index(drop=True)
    if df_exp.empty: st.warning(t["no_data"])
    else:
        st.dataframe(df_exp[["tanggal", "keterangan", "nominal"]], use_container_width=True)
        col_d1, col_d2 = st.columns(2)
        col_d1.download_button(t["btn_excel"], generate_excel(df_exp[["tanggal", "keterangan", "nominal"]], "Pengeluaran"), "pengeluaran.xlsx")
        col_d2.download_button(t["btn_pdf"], get_html_pdf_download(df_exp[["tanggal", "keterangan", "nominal"]], t["pocket_out"], total_keluar), "pengeluaran.html")

elif st.session_state.current_page == "balance_page":
    if st.button(t["back"]): st.session_state.current_page = "dashboard"; st.rerun()
    st.subheader(t["pocket_balance"])
    if df_user_tx.empty: st.warning(t["no_data"])
    else:
        st.dataframe(df_user_tx[["tanggal", "jenis", "keterangan", "nominal"]], use_container_width=True)
        col_d1, col_d2 = st.columns(2)
        col_d1.download_button(t["btn_excel"], generate_excel(df_user_tx[["tanggal", "jenis", "keterangan", "nominal"]], "Sisa Uang"), "neraca_total.xlsx")
        col_d2.download_button(t["btn_pdf"], get_html_pdf_download(df_user_tx[["tanggal", "jenis", "keterangan", "nominal"]], t["pocket_balance"], sisa_uang), "neraca_total.html")
