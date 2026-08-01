import os
import re
import sqlite3
import unicodedata
from datetime import datetime, timedelta

import pandas as pd

try:
    import requests
except Exception:
    requests = None


DB_DATA_PATH = os.path.join("data", "numune_takip.db")
DB_SETTINGS_PATH = os.path.join("data", "kesif_sistemi.db")


GUIDE_TOPICS = {
    "numune": """
### Numune kaydı nasıl yapılır?
1. Menüden **Anasayfa (Yeni Kayıt)** ekranına girin.
2. Laboratuvarı seçin.
3. Numune, proje, firma, cins, miktar ve gelen yazı bilgilerini doldurun.
4. Deneyleri tek tek seçin veya varsa **Deney Paketi** uygulayın.
5. **Kaydet ve Tutanak Oluştur** butonu ile kayıt ve PDF tutanak oluşturulur.
""",
    "paket": """
### Deney paketi nasıl yönetilir?
1. Menüden **🛠️ YÖNETİM PANELİ > 📦 Paketler** sekmesine girin.
2. Paket adı, laboratuvar, açıklama ve anahtar kelimeleri girin.
3. Pakete dahil deneyleri seçin.
4. Kaydettikten sonra paket numune kayıt ekranında kullanılabilir.
""",
    "rapor": """
### Rapor takibi nasıl yapılır?
1. Menüden **RAPOR TAKİP** ekranına girin.
2. Kayıt no, proje veya firma ile arama yapın.
3. Test başlangıç/bitiş, rapor tarihi, rapor sayısı ve deney sonucu alanlarını kontrol edin.
4. Yetkiniz varsa merkezi güncelleme alanından rapor bilgilerini düzenleyebilirsiniz.
""",
    "kesif": """
### Keşif işlemleri nerede yapılır?
1. Menüden **📑 KEŞİF** ekranına girin.
2. Proje veya kayıt no seçin.
3. Birim fiyat, akreditasyon, ek kalem ve oran ayarlarını kontrol edin.
4. Keşif kaydını oluşturun; kayıtlar keşif geçmişinde izlenir.
""",
    "protokol": """
### Protokol işlemleri nasıl yürütülür?
1. Menüden **📋 PROTOKOL İŞLEMLERİ** ekranına girin.
2. Keşif/proje bağlantılı protokol oluşturun veya mevcut protokolleri görüntüleyin.
3. Ödeme, dekont, banka bilgisi ve arşiv durumunu takip edin.
""",
    "dashboard": """
### Gösterge paneli ne işe yarar?
**Gösterge Paneli**; iş takip listesi, gecikmeler, keşif durumu, laboratuvar iş yükü, aylık trend ve duyuruları tek ekranda gösterir.
Sol menüdeki **Dashboard Ayarları** bölümünden hangi widgetların görüneceğini seçebilirsiniz.
""",
    "qr": """
### QR etiket nasıl oluşturulur?
1. Menüden **🏷️ QR ETİKET** ekranına girin.
2. Kayıt no, proje, firma veya cins bilgisiyle numuneyi bulun.
3. Numuneyi seçtiğinizde QR kod ve etiket PDF'i otomatik hazırlanır.
4. İsterseniz QR PNG dosyasını, isterseniz etiket PDF'ini indirin.
5. Toplu etiket için aynı ekrandaki **Toplu Etiket ZIP Oluştur** bölümünü kullanın.
""",
}


def normalize_text(value):
    text = str(value or "").strip().lower()
    if not text:
        return ""
    replacements = str.maketrans({
        "ı": "i", "İ": "i", "ğ": "g", "Ğ": "g", "ü": "u", "Ü": "u",
        "ş": "s", "Ş": "s", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c",
    })
    text = text.translate(replacements)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_date(value):
    if not value or str(value).strip() in ["-", "None", "nan"]:
        return None
    for fmt in ("%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value).strip(), fmt)
        except Exception:
            pass
    return None


def is_completed(value):
    return normalize_text(value).startswith("tamam")


def read_data(query, params=()):
    if not os.path.exists(DB_DATA_PATH):
        return pd.DataFrame()
    with sqlite3.connect(DB_DATA_PATH) as conn:
        return pd.read_sql(query, conn, params=params)


def read_settings(query, params=()):
    if not os.path.exists(DB_SETTINGS_PATH):
        return pd.DataFrame()
    with sqlite3.connect(DB_SETTINGS_PATH) as conn:
        return pd.read_sql(query, conn, params=params)


def search_samples(term, limit=80):
    if str(term).strip().isdigit():
        exact = read_data("""
            SELECT kayit_no, gelis_tarihi, lab_type, proje, firma, cins, deney_adi,
                   test_durumu, test_baslangic, test_bitis, deney_sonuc, deney_sorumlusu
            FROM samples
            WHERE kayit_no = ?
            ORDER BY id DESC
            LIMIT ?
        """, (str(term).strip(), int(limit)))
        if not exact.empty:
            return exact
    search = f"%{term}%"
    return read_data("""
        SELECT kayit_no, gelis_tarihi, lab_type, proje, firma, cins, deney_adi,
               test_durumu, test_baslangic, test_bitis, deney_sonuc, deney_sorumlusu
        FROM samples
        WHERE kayit_no LIKE ?
           OR proje LIKE ?
           OR firma LIKE ?
           OR cins LIKE ?
           OR deney_adi LIKE ?
        ORDER BY CAST(kayit_no AS INTEGER) DESC, id DESC
        LIMIT ?
    """, (search, search, search, search, search, int(limit)))


def classify_samples(df):
    if df.empty:
        return df
    tests = read_settings("SELECT test_name, duration_days FROM test_durations")
    durations = dict(zip(tests.get("test_name", []), tests.get("duration_days", [])))
    today = datetime.now()
    result = df.copy()
    takip = []
    gecikme = []
    for _, row in result.iterrows():
        status = row.get("test_durumu")
        start = parse_date(row.get("test_baslangic")) or parse_date(row.get("gelis_tarihi"))
        duration = int(durations.get(row.get("deney_adi"), 7) or 7)
        late = bool(start and not is_completed(status) and today > start + timedelta(days=duration))
        gecikme.append("Var" if late else "Yok")
        if late:
            takip.append("Geciken")
        elif is_completed(status):
            takip.append("Tamamlanan")
        else:
            takip.append("Beklemede")
    result["takip_durumu"] = takip
    result["gecikme"] = gecikme
    return result


def dataframe_to_markdown(df, max_rows=20):
    if df.empty:
        return "Kayıt bulunamadı."
    visible = df.head(max_rows).fillna("-")
    columns = [str(c) for c in visible.columns]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for _, row in visible.iterrows():
        values = []
        for col in visible.columns:
            text = str(row[col]).replace("\n", " ").replace("|", "/")
            if len(text) > 90:
                text = text[:87] + "..."
            values.append(text)
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def answer_sample_search(question):
    term = extract_search_term(question)
    if not term:
        return None
    df = classify_samples(search_samples(term))
    if df.empty:
        return {
            "status": "warning",
            "report": f"**{term}** için numune kaydı bulunamadı.",
            "data": pd.DataFrame(),
        }
    summary = df.groupby(["kayit_no", "proje", "firma"], dropna=False).size().reset_index(name="Deney Sayısı")
    report = [f"### Arama Sonucu: {term}", dataframe_to_markdown(summary, max_rows=15)]
    detail_cols = ["kayit_no", "deney_adi", "test_durumu", "takip_durumu", "gecikme", "test_bitis", "deney_sonuc"]
    report.append("\n### Deney Detayları")
    report.append(dataframe_to_markdown(df[[c for c in detail_cols if c in df.columns]], max_rows=30))
    return {"status": "success", "report": "\n\n".join(report), "data": df}


def extract_search_term(question):
    q = question.strip()
    match = re.search(r"\b(?:kayıt|kayit|no|numara)\s*[:#-]?\s*(\d+)\b", q, re.IGNORECASE)
    if match:
        return match.group(1)
    number = re.search(r"\b\d{1,8}\b", q)
    if number and any(word in normalize_text(q) for word in ["kayit", "numune", "durum", "deney"]):
        return number.group(0)
    quoted = re.search(r"['\"]([^'\"]{3,})['\"]", q)
    if quoted:
        return quoted.group(1)
    for marker in ["proje", "firma", "numune", "kayıt", "kayit"]:
        norm = normalize_text(q)
        if marker in norm and len(q) > 8:
            return q
    return None


def answer_counts(question):
    q = normalize_text(question)
    df = classify_samples(read_data("SELECT * FROM samples"))
    if df.empty:
        return {"status": "warning", "report": "Numune veritabanında kayıt bulunamadı.", "data": df}

    if "bugun" in q:
        today = datetime.now().strftime("%d/%m/%Y")
        df = df[df["gelis_tarihi"].astype(str).isin([today, today.replace("/", ".")])]

    if "bekleyen" in q:
        out = df[~df["test_durumu"].apply(is_completed)]
        title = "Bekleyen / devam eden deneyler"
    elif "geciken" in q or "gecik" in q:
        out = df[df["gecikme"] == "Var"]
        title = "Geciken deneyler"
    elif "tamam" in q:
        out = df[df["test_durumu"].apply(is_completed)]
        title = "Tamamlanan deneyler"
    else:
        out = df
        title = "Genel numune/deney özeti"

    lab_summary = out.groupby("lab_type").size().reset_index(name="Sayı") if not out.empty else pd.DataFrame()
    status_summary = out.groupby("test_durumu").size().reset_index(name="Sayı") if not out.empty else pd.DataFrame()
    report = [
        f"### {title}",
        f"Toplam kayıt/deney satırı: **{len(out)}**",
        "\n#### Laboratuvar Dağılımı",
        dataframe_to_markdown(lab_summary),
        "\n#### Durum Dağılımı",
        dataframe_to_markdown(status_summary),
    ]
    detail_cols = ["kayit_no", "gelis_tarihi", "lab_type", "proje", "deney_adi", "test_durumu", "gecikme"]
    if "liste" in q or "hangileri" in q or len(out) <= 30:
        report.extend(["\n#### İlk Kayıtlar", dataframe_to_markdown(out[[c for c in detail_cols if c in out.columns]], 30)])
    return {"status": "success", "report": "\n\n".join(report), "data": out}


def answer_most_common(question):
    q = normalize_text(question)
    df = read_data("SELECT deney_adi, lab_type, gelis_tarihi FROM samples")
    if df.empty:
        return {"status": "warning", "report": "Deney kaydı bulunamadı.", "data": df}
    if "son 1 ay" in q or "son bir ay" in q or "ayda" in q:
        dates = df["gelis_tarihi"].apply(parse_date)
        cutoff = datetime.now() - timedelta(days=31)
        df = df[pd.to_datetime(dates, errors="coerce") >= cutoff]
    summary = df.groupby(["deney_adi", "lab_type"]).size().reset_index(name="Sayı").sort_values("Sayı", ascending=False)
    return {
        "status": "success",
        "report": "### En Çok Yapılan Deneyler\n\n" + dataframe_to_markdown(summary, 20),
        "data": summary,
    }


def answer_protocol_discovery(question):
    protocols = read_settings("SELECT * FROM protocols WHERE is_archived=0")
    discoveries = read_settings("SELECT * FROM kesif_kayitlari")
    waiting = discoveries[discoveries["status"].fillna("").str.upper().str.contains("BEK", na=False)] if not discoveries.empty else pd.DataFrame()
    report = [
        "### Keşif ve Protokol Özeti",
        f"Aktif protokol sayısı: **{len(protocols)}**",
        f"Keşif kaydı sayısı: **{len(discoveries)}**",
        f"Bekleyen keşif sayısı: **{len(waiting)}**",
    ]
    if not waiting.empty:
        report.extend(["\n#### Bekleyen Keşifler", dataframe_to_markdown(waiting[["project_name", "total_amount", "created_at", "status"]], 20)])
    return {"status": "success", "report": "\n\n".join(report), "data": discoveries}


def answer_help(question):
    q = normalize_text(question)
    matched = []
    for key, text in GUIDE_TOPICS.items():
        if key in q:
            matched.append(text)
    if not matched:
        matched = ["""
### AR-GE Takip Sistemi Asistanı
Sorabileceğiniz örnekler:
- `99 kayıt no durumunu göster`
- `Geciken deneyler hangileri?`
- `Bekleyen deneyleri listele`
- `Son 1 ayda en çok hangi deney yapılmış?`
- `Keşif ve protokol özeti`
- `Deney paketi nasıl oluşturulur?`
- `Rapor takibi nasıl yapılır?`
- `QR etiket nasıl oluşturulur?`
"""]
    return {"status": "success", "report": "\n\n".join(matched), "data": pd.DataFrame()}


def ask_local_llm(prompt, provider="ollama", model="qwen2.5:3b", timeout=20):
    if requests is None:
        return None
    try:
        if provider == "lmstudio":
            payload = {
                "model": model or "local-model",
                "messages": [
                    {"role": "system", "content": "Kısa, teknik ve Türkçe cevap ver."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            }
            response = requests.post("http://localhost:1234/v1/chat/completions", json=payload, timeout=timeout)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        payload = {
            "model": model or "qwen2.5:3b",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception:
        return None


def query_system_assistant(question, use_local_llm=False, llm_provider="ollama", llm_model="qwen2.5:3b"):
    question = (question or "").strip()
    if not question:
        return answer_help(question)

    q = normalize_text(question)
    guide_intent = any(word in q for word in ["nasil", "nas l", "nerede", "yardim", "rehber", "kullanim", "paket", "dashboard", "qr", "etiket"])
    guide_intent = guide_intent or ("numune" in q and any(word in q for word in ["kayd", "kayit", "olu", "ekle", "yap"]))
    guide_intent = guide_intent or ("rapor" in q and any(word in q for word in ["takip", "nasil", "nas l", "nerede", "yap"]))
    guide_intent = guide_intent or ("protokol" in q and any(word in q for word in ["nasil", "nas l", "nerede", "olu", "yap"]))

    if guide_intent:
        result = answer_help(question)
    elif any(word in q for word in ["protokol", "kesif"]):
        result = answer_protocol_discovery(question)
    elif any(word in q for word in ["en cok", "en fazla", "hangi deney"]):
        result = answer_most_common(question)
    elif any(word in q for word in ["kac", "sayisi", "bekleyen", "geciken", "tamamlanan", "liste", "hangileri", "bugun"]):
        result = answer_counts(question)
    else:
        result = answer_sample_search(question) or answer_help(question)

    if use_local_llm and result.get("report"):
        prompt = (
            "Aşağıdaki sistem cevabını kullanıcıya daha anlaşılır, kısa ve teknik Türkçe ile özetle. "
            "Verileri değiştirme, sayı uydurma.\n\n"
            f"Kullanıcı sorusu: {question}\n\nSistem cevabı:\n{result['report'][:4000]}"
        )
        llm_text = ask_local_llm(prompt, provider=llm_provider, model=llm_model)
        if llm_text:
            result["report"] = f"{llm_text}\n\n---\n\n{result['report']}"
            result["llm_used"] = True
        else:
            result["llm_used"] = False
    return result


def query_sample_status(query_term: str):
    """Backward-compatible wrapper for the old smart query screen."""
    result = answer_sample_search(query_term)
    if not result:
        return {"status": "error", "message": "Arama terimi anlaşılamadı."}
    if result["status"] != "success":
        return {"status": "error", "message": result["report"]}
    return {"status": "success", "report": result["report"]}
