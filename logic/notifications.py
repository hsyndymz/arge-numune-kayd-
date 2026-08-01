from datetime import datetime, timedelta
import re

import pandas as pd
import streamlit as st

from logic.db_utils import get_settings_connection


@st.cache_resource
def ensure_dashboard_tables():
    conn = get_settings_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT,
            target_lab TEXT DEFAULT 'ALL',
            is_active INTEGER DEFAULT 1,
            created_by TEXT,
            created_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dashboard_preferences (
            username TEXT PRIMARY KEY,
            widget_order TEXT,
            hidden_widgets TEXT,
            updated_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT DEFAULT 'ALL',
            category TEXT,
            title TEXT NOT NULL,
            message TEXT,
            related_type TEXT,
            related_key TEXT,
            priority TEXT DEFAULT 'normal',
            is_read INTEGER DEFAULT 0,
            is_archived INTEGER DEFAULT 0,
            unique_key TEXT UNIQUE,
            created_at TEXT,
            read_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_dashboard_announcement(title, body, target_lab, username):
    ensure_dashboard_tables()
    conn = get_settings_connection()
    conn.execute("""
        INSERT INTO dashboard_announcements (title, body, target_lab, is_active, created_by, created_at)
        VALUES (?,?,?,?,?,?)
    """, (title, body, target_lab, 1, username, datetime.now().strftime("%d/%m/%Y %H:%M")))
    conn.commit()
    conn.close()


def get_dashboard_announcements(lab_scope):
    ensure_dashboard_tables()
    conn = get_settings_connection()
    df = pd.read_sql("SELECT * FROM dashboard_announcements WHERE is_active=1 ORDER BY id DESC", conn)
    conn.close()
    if df.empty:
        return df
    allowed = ["ALL"] + lab_scope
    return df[df["target_lab"].isin(allowed)]


def normalize_dashboard_match_text(value):
    text = str(value or "").strip().lower()
    if not text:
        return ""
    replacements = str.maketrans({
        "ı": "i", "İ": "i", "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u",
        "ş": "s", "Ş": "s", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"
    })
    text = text.translate(replacements)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def get_discovery_done_records():
    conn = get_settings_connection()
    try:
        df = pd.read_sql("SELECT project_name FROM kesif_kayitlari", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    if df.empty or "project_name" not in df.columns:
        return []
    records = []
    for value in df["project_name"].dropna().tolist():
        raw = str(value).strip()
        normalized = normalize_dashboard_match_text(raw)
        if raw and normalized:
            records.append({"raw": raw, "normalized": normalized})
    return records


def has_discovery_record(project_name, kayit_no, discovery_records):
    project_norm = normalize_dashboard_match_text(project_name)
    kayit_norm = normalize_dashboard_match_text(kayit_no)
    for record in discovery_records:
        discovery_norm = record["normalized"]
        if kayit_norm and discovery_norm == kayit_norm:
            return True
        if project_norm and discovery_norm == project_norm:
            return True
        if project_norm and discovery_norm and len(discovery_norm) >= 8:
            if discovery_norm in project_norm or project_norm in discovery_norm:
                return True
            project_tokens = set(project_norm.split())
            discovery_tokens = set(discovery_norm.split())
            if discovery_tokens:
                overlap = len(project_tokens & discovery_tokens) / len(discovery_tokens)
                if overlap >= 0.70:
                    return True
    return False


def build_dashboard_worklist(samples_df, today, get_all_tests, parse_any_date, is_completed_status, dashboard_lab_label):
    if samples_df.empty:
        return pd.DataFrame()
    tests_info = get_all_tests()
    durations = dict(zip(tests_info["test_name"], tests_info["duration_days"]))
    discovery_records = get_discovery_done_records()
    rows = []

    for _, row in samples_df.sort_values(by="id", ascending=False).iterrows():
        status = str(row.get("test_durumu") or "Beklemede")
        start = parse_any_date(row.get("test_baslangic")) or parse_any_date(row.get("gelis_tarihi"))
        duration = int(durations.get(row.get("deney_adi"), 7) or 7)
        is_late = bool(start and not is_completed_status(status) and today > start + timedelta(days=duration))
        has_discovery = has_discovery_record(row.get("proje"), row.get("kayit_no"), discovery_records)

        if is_late:
            takip = "Geciken"
            sira = 1
        elif is_completed_status(status):
            takip = "Tamamlanan"
            sira = 3
        else:
            takip = "Beklemede"
            sira = 2

        rows.append({
            "Öncelik": sira,
            "Takip Durumu": takip,
            "Gecikme": "Var" if is_late else "Yok",
            "Keşif": "Yapıldı" if has_discovery else "Yapılmadı",
            "Kayıt No": row.get("kayit_no"),
            "Geliş Tarihi": row.get("gelis_tarihi"),
            "Lab": dashboard_lab_label(row.get("lab_type")),
            "Proje": row.get("proje"),
            "Firma": row.get("firma"),
            "Cins": row.get("cins"),
            "Deney": row.get("deney_adi"),
            "Test Durumu": status,
            "Sorumlu": row.get("deney_sorumlusu"),
        })

    worklist = pd.DataFrame(rows)
    if worklist.empty:
        return worklist
    return worklist.sort_values(by=["Öncelik", "Kayıt No"], ascending=[True, False]).drop(columns=["Öncelik"])


def style_dashboard_worklist(row):
    takip = row.get("Takip Durumu", "")
    kesif = row.get("Keşif", "")
    if kesif == "Yapıldı":
        return ["background-color: #f3e8ff; color: #581c87; text-decoration: line-through; font-weight: 650"] * len(row)
    if takip == "Geciken":
        return ["background-color: #fee2e2; color: #991b1b; font-weight: 650"] * len(row)
    if takip == "Tamamlanan":
        return ["background-color: #dcfce7; color: #166534"] * len(row)
    if takip == "Beklemede":
        return ["background-color: #ffedd5; color: #9a3412"] * len(row)
    return [""] * len(row)


def add_notification(username, category, title, message, related_type="", related_key="", priority="normal", unique_key=None):
    ensure_dashboard_tables()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    unique_key = unique_key or f"{username}|{category}|{related_type}|{related_key}|{title}"
    conn = get_settings_connection()
    try:
        conn.execute("""
            INSERT OR IGNORE INTO notifications
            (username, category, title, message, related_type, related_key, priority, is_read, is_archived, unique_key, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (username, category, title, message, related_type, related_key, priority, 0, 0, unique_key, now))
        conn.commit()
    finally:
        conn.close()


def get_notifications(username=None, unread_only=False, include_archived=False):
    ensure_dashboard_tables()
    conn = get_settings_connection()
    query = "SELECT * FROM notifications WHERE 1=1"
    params = []
    if username:
        query += " AND (username='ALL' OR username=?)"
        params.append(username)
    if unread_only:
        query += " AND is_read=0"
    if not include_archived:
        query += " AND is_archived=0"
    query += " ORDER BY is_read ASC, id DESC"
    try:
        df = pd.read_sql(query, conn, params=params)
    finally:
        conn.close()
    return df


def mark_notifications_read(notification_ids=None, username=None):
    ensure_dashboard_tables()
    conn = get_settings_connection()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    try:
        if notification_ids:
            placeholders = ",".join(["?"] * len(notification_ids))
            conn.execute(f"UPDATE notifications SET is_read=1, read_at=? WHERE id IN ({placeholders})", [now] + list(notification_ids))
        elif username:
            conn.execute("UPDATE notifications SET is_read=1, read_at=? WHERE username='ALL' OR username=?", (now, username))
        conn.commit()
    finally:
        conn.close()


def archive_notification(notification_id):
    ensure_dashboard_tables()
    conn = get_settings_connection()
    try:
        conn.execute("UPDATE notifications SET is_archived=1 WHERE id=?", (int(notification_id),))
        conn.commit()
    finally:
        conn.close()


def generate_auto_notifications(load_dashboard_samples, build_dashboard_worklist):
    ensure_dashboard_tables()
    samples = load_dashboard_samples([])
    if not samples.empty:
        worklist = build_dashboard_worklist(samples, datetime.now())
        for _, row in worklist.iterrows():
            kayit_no = str(row.get("Kayıt No") or "")
            deney = str(row.get("Deney") or "")
            lab = str(row.get("Lab") or "")
            key_base = f"{kayit_no}|{deney}"
            if row.get("Gecikme") == "Var":
                add_notification(
                    "ALL", "Geciken Deney", f"Geciken deney: {kayit_no}",
                    f"{lab} laboratuvarında '{deney}' deneyi süresini aşmış görünüyor.",
                    "sample", kayit_no, "high", f"late|{key_base}"
                )
            elif row.get("Takip Durumu") == "Beklemede":
                add_notification(
                    "ALL", "Bekleyen Deney", f"Bekleyen deney: {kayit_no}",
                    f"{lab} laboratuvarında '{deney}' deneyi beklemede/devam ediyor.",
                    "sample", kayit_no, "normal", f"pending|{key_base}"
                )

    try:
        discoveries = pd.read_sql("SELECT id, project_name, status, total_amount FROM kesif_kayitlari", get_settings_connection())
        waiting = discoveries[discoveries["status"].fillna("").str.upper().str.contains("BEK", na=False)] if not discoveries.empty else pd.DataFrame()
        for _, row in waiting.iterrows():
            add_notification(
                "ALL", "Keşif", f"Bekleyen keşif: {row.get('project_name')}",
                f"Toplam tutar: {row.get('total_amount')}",
                "kesif", str(row.get("id")), "normal", f"kesif_waiting|{row.get('id')}"
            )
    except Exception:
        pass


def render_notification_center(username):
    st.title("🔔 Bildirim Merkezi")
    st.caption("Sistem içi uyarılar, geciken işler ve bekleyen süreçler.")
    notifications = get_notifications(username=username, include_archived=False)
    unread_count = int((notifications["is_read"] == 0).sum()) if not notifications.empty else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Bildirim", len(notifications))
    c2.metric("Okunmamış", unread_count)
    c3.metric("Yüksek Öncelik", len(notifications[notifications["priority"] == "high"]) if not notifications.empty else 0)

    b1, b2 = st.columns(2)
    if b1.button("Tümünü Okundu İşaretle", use_container_width=True):
        mark_notifications_read(username=username)
        st.rerun()
    if b2.button("Bildirimleri Yenile", use_container_width=True):
        st.rerun()

    if notifications.empty:
        st.info("Aktif bildirim yok.")
        return

    filters = st.columns(3)
    with filters[0]:
        category_filter = st.multiselect("Kategori", sorted(notifications["category"].dropna().unique().tolist()), default=sorted(notifications["category"].dropna().unique().tolist()))
    with filters[1]:
        priority_filter = st.multiselect("Öncelik", sorted(notifications["priority"].dropna().unique().tolist()), default=sorted(notifications["priority"].dropna().unique().tolist()))
    with filters[2]:
        read_filter = st.selectbox("Okunma", ["Tümü", "Okunmamış", "Okunmuş"])

    filtered = notifications[
        notifications["category"].isin(category_filter)
        & notifications["priority"].isin(priority_filter)
    ].copy()
    if read_filter == "Okunmamış":
        filtered = filtered[filtered["is_read"] == 0]
    elif read_filter == "Okunmuş":
        filtered = filtered[filtered["is_read"] == 1]

    for _, row in filtered.iterrows():
        border = "#dc2626" if row["priority"] == "high" else ("#f97316" if row["priority"] == "normal" else "#64748b")
        opacity = "0.65" if row["is_read"] else "1"
        st.markdown(f"""
            <div style="border:1px solid #e5e7eb;border-left:6px solid {border};border-radius:8px;padding:12px 14px;margin:8px 0;background:#fff;opacity:{opacity};">
                <div style="font-weight:800;color:#0f172a;">{row['title']}</div>
                <div style="font-size:13px;color:#475569;margin-top:4px;">{row['message'] or ''}</div>
                <div style="font-size:12px;color:#64748b;margin-top:8px;">{row['category']} | {row['priority']} | {row['created_at']} | {row['related_type']}:{row['related_key']}</div>
            </div>
        """, unsafe_allow_html=True)
        rb1, rb2 = st.columns([1, 1])
        if row["is_read"] == 0 and rb1.button("Okundu", key=f"notif_read_{row['id']}"):
            mark_notifications_read([int(row["id"])])
            st.rerun()
        if rb2.button("Arşivle", key=f"notif_archive_{row['id']}"):
            archive_notification(int(row["id"]))
            st.rerun()
