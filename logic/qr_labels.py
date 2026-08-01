import io
import os
import re
import zipfile
from datetime import datetime

import pandas as pd
import streamlit as st
from fpdf import FPDF

from logic.db_utils import get_connection


def tr_fix(text):
    if not text:
        return ""
    cleaned_text = str(text)
    replacements = [
        ("İ", "I"), ("ı", "i"), ("Ş", "S"), ("ş", "s"), ("Ğ", "G"), ("ğ", "g"),
        ("Ç", "C"), ("ç", "c"), ("Ö", "O"), ("ö", "o"), ("Ü", "U"), ("ü", "u"),
        ("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'),
        ("–", "-"), ("—", "-"), ("…", "..."), ("•", "*"),
    ]
    for src, dst in replacements:
        cleaned_text = cleaned_text.replace(src, dst)
    return cleaned_text.encode("latin-1", "replace").decode("latin-1")


def safe_filename(value):
    text = tr_fix(str(value or "")).strip()
    text = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    return text.strip("_") or "kayit"


def compact_text(value, limit=32):
    text = re.sub(r"\s+", " ", tr_fix(str(value or "")).strip())
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3].rstrip() + "..."


def get_sample_groups():
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT
                kayit_no,
                COALESCE(proje, '') AS proje,
                COALESCE(firma, '') AS firma,
                COALESCE(lab_type, '') AS lab_type,
                COALESCE(gelis_tarihi, '') AS gelis_tarihi,
                COALESCE(cins, '') AS cins,
                COALESCE(miktar, '') AS miktar,
                COALESCE(yer, '') AS yer,
                COALESCE(teslim_alan, '') AS teslim_alan,
                COALESCE(teslim_eden, '') AS teslim_eden,
                COALESCE(lifecycle_status, 'Kayit') AS lifecycle_status,
                GROUP_CONCAT(deney_adi, ' | ') AS deneyler,
                COUNT(*) AS deney_sayisi
            FROM samples
            GROUP BY kayit_no, COALESCE(proje, ''), COALESCE(firma, '')
            ORDER BY CAST(kayit_no AS INTEGER) DESC
            """,
            conn,
        )
    finally:
        conn.close()
    return df


def build_qr_payload(sample_row):
    fields = [
        ("KAYIT_NO", sample_row.get("kayit_no", "")),
        ("LAB", sample_row.get("lab_type", "")),
        ("CINS", sample_row.get("cins", "")),
        ("KAYIT_TARIHI", sample_row.get("gelis_tarihi", "")),
    ]
    return "\n".join([f"{key}: {value}" for key, value in fields if str(value).strip()])


def create_sample_qr_png(sample_row):
    try:
        import qrcode
    except Exception as exc:
        raise RuntimeError(
            "QR kod üretimi için qrcode paketi gerekli. Kurulum: python -m pip install qrcode[pil]"
        ) from exc

    payload = build_qr_payload(sample_row)
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=12, border=4)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    file_key = f"{sample_row.get('kayit_no', '')}_{sample_row.get('lab_type', '')}_{sample_row.get('cins', '')}"
    path = os.path.join("qr_codes", f"QR_{safe_filename(file_key)}.png")
    img.save(path)
    return path, payload


def create_sample_label_pdf(sample_row, qr_path):
    pdf = FPDF(orientation="P", unit="mm", format="A5")
    pdf.add_page()
    pdf.set_auto_page_break(False)
    pdf.set_draw_color(30, 41, 59)
    pdf.set_line_width(0.4)
    pdf.rect(8, 8, 132, 184)

    pdf.set_font("Arial", "B", 16)
    pdf.set_xy(12, 14)
    pdf.cell(110, 8, tr_fix("KGM AR-GE NUMUNE ETIKETI"), ln=1)

    pdf.set_font("Arial", "B", 26)
    pdf.set_xy(12, 28)
    pdf.cell(110, 12, tr_fix(f"Lab No: {sample_row.get('kayit_no', '')}"), ln=1)

    label_x = 12
    label_w = 34
    value_x = 46
    value_w = 76
    row_h = 13

    pdf.set_font("Arial", "B", 11)
    pdf.set_xy(label_x, 56)
    pdf.cell(label_w, row_h, tr_fix("Lab. Adi:"), border=1)
    pdf.set_font("Arial", "", 11)
    pdf.set_xy(value_x, 56)
    pdf.cell(value_w, row_h, compact_text(sample_row.get("lab_type", ""), 48), border=1)

    pdf.set_font("Arial", "B", 11)
    pdf.set_xy(label_x, 71)
    pdf.cell(label_w, row_h, tr_fix("Cinsi:"), border=1)
    pdf.set_font("Arial", "", 11)
    pdf.set_xy(value_x, 71)
    pdf.cell(value_w, row_h, compact_text(sample_row.get("cins", ""), 48), border=1)

    pdf.set_font("Arial", "B", 11)
    pdf.set_xy(label_x, 86)
    pdf.cell(label_w, row_h, tr_fix("Kayıt Tarihi:"), border=1)
    pdf.set_font("Arial", "", 11)
    pdf.set_xy(value_x, 86)
    pdf.cell(value_w, row_h, compact_text(sample_row.get("gelis_tarihi", ""), 48), border=1)

    if os.path.exists(qr_path):
        qr_box_x = 36
        qr_box_y = 106
        qr_box_size = 82
        pdf.rect(qr_box_x, qr_box_y, qr_box_size, qr_box_size)
        pdf.image(qr_path, x=qr_box_x + 4, y=qr_box_y + 4, w=qr_box_size - 8, h=qr_box_size - 8)
        pdf.set_font("Arial", "B", 11)
        pdf.set_xy(qr_box_x, qr_box_y + qr_box_size + 2)
        pdf.cell(qr_box_size, 6, tr_fix("QR KOD"), align="C")

    pdf.set_xy(12, 190)
    pdf.set_font("Arial", "", 7)
    pdf.cell(120, 5, tr_fix(f"Oluşturma: {datetime.now().strftime('%d/%m/%Y %H:%M')}"), align="R")

    file_key = f"{sample_row.get('kayit_no', '')}_{sample_row.get('lab_type', '')}_{sample_row.get('cins', '')}"
    path = os.path.join("qr_codes", f"Etiket_{safe_filename(file_key)}.pdf")
    pdf.output(path)
    return path


def render_qr_label_center():
    st.title("🏷️ QR Kod ve Numune Etiketleri")
    st.caption("Numuneler için sade QR etiketleri ve toplu etiket arşivi oluşturur.")

    samples = get_sample_groups()
    if samples.empty:
        st.info("Etiket oluşturulacak aktif numune kaydı yok.")
        return

    search = st.text_input("🔍 Kayıt no, lab adı veya cins ara", key="qr_label_search")
    filtered = samples.copy()
    if search:
        filtered = filtered[filtered.apply(lambda row: row.astype(str).str.contains(search, case=False, na=False).any(), axis=1)]

    if filtered.empty:
        st.warning("Arama kriterine uygun numune bulunamadı.")
        return

    display_df = filtered[["kayit_no", "lab_type", "cins"]].rename(columns={
        "kayit_no": "Lab No",
        "lab_type": "Lab Adı",
        "cins": "Cins",
    })
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    selected_index = st.selectbox(
        "Etiket oluşturulacak numune",
        filtered.index.tolist(),
        format_func=lambda idx: f"{filtered.loc[idx, 'kayit_no']} | {filtered.loc[idx, 'lab_type']} | {filtered.loc[idx, 'cins']}",
        key="qr_label_sample_select",
    )
    selected = filtered.loc[selected_index].to_dict()

    qr_path, payload = create_sample_qr_png(selected)
    pdf_path = create_sample_label_pdf(selected, qr_path)

    c1, c2 = st.columns([1, 2])
    with c1:
        st.image(qr_path, caption=f"QR - Kayıt No {selected.get('kayit_no')}", width=220)
        with open(qr_path, "rb") as qr_file:
            st.download_button("📥 QR PNG İndir", qr_file, file_name=os.path.basename(qr_path), mime="image/png", use_container_width=True)
        with open(pdf_path, "rb") as pdf_file:
            st.download_button("📄 Etiket PDF İndir", pdf_file, file_name=os.path.basename(pdf_path), mime="application/pdf", use_container_width=True)
    with c2:
        st.markdown("#### QR İçeriği")
        st.code(payload, language="text")

    with st.expander("📦 Toplu Etiket ZIP Oluştur"):
        max_count = min(len(filtered), 200)
        bulk_count = st.number_input(
            "İlk kaç kayıt için etiket oluşturulsun?",
            min_value=1,
            max_value=max_count,
            value=min(20, max_count),
        )
        if st.button("Toplu ZIP Hazırla", type="primary"):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for _, row in filtered.head(int(bulk_count)).iterrows():
                    row_dict = row.to_dict()
                    qr_file_path, _ = create_sample_qr_png(row_dict)
                    label_file_path = create_sample_label_pdf(row_dict, qr_file_path)
                    zf.write(qr_file_path, arcname=os.path.basename(qr_file_path))
                    zf.write(label_file_path, arcname=os.path.basename(label_file_path))
            st.download_button(
                "📥 Toplu Etiket ZIP İndir",
                zip_buffer.getvalue(),
                file_name=f"Numune_QR_Etiketleri_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip",
                use_container_width=True,
            )
