UNIFIED_LAB_MENU = "🔬 LABORATUVAR İŞLEMLERİ"
MANAGEMENT_MENU = "🛠️ YÖNETİM PANELİ"

CORE_MENU = ["Gösterge Paneli", "🔎 GLOBAL ARAMA", "🔔 BİLDİRİMLER", "🏷️ QR ETİKET"]

LAB_MENU_ITEMS = ["Beton ve Çimento Lab.", "Bitüm ve Bitümlü Karışımlar Lab.", "Toprak ve Stabilizasyon Lab."]

MENU_GROUPS = {
    "Ana Panel": ["Gösterge Paneli", "🔔 BİLDİRİMLER"],
    "Numune İşlemleri": ["Anasayfa (Yeni Kayıt)", "Numune Bilgileri", UNIFIED_LAB_MENU, "🏷️ QR ETİKET"],
    "Rapor ve Süreçler": ["RAPOR TAKİP", "📑 KEŞİF", "📋 PROTOKOL İŞLEMLERİ", "📦 ARŞİV"],
    "Akıllı Araçlar": ["🔎 GLOBAL ARAMA", "🤖 SİSTEM ASİSTANI"],
    "Yönetim": [MANAGEMENT_MENU],
}


def normalize_user_permissions(raw_permissions):
    permissions = list(raw_permissions or [])
    if "🤖 AKILLI SORGULAMA" in permissions and "🤖 SİSTEM ASİSTANI" not in permissions:
        permissions.append("🤖 SİSTEM ASİSTANI")
    if "AYARLAR" in permissions and MANAGEMENT_MENU not in permissions:
        permissions.append(MANAGEMENT_MENU)
    has_lab_permission = any(lab_menu in permissions for lab_menu in LAB_MENU_ITEMS)
    has_lab_permission = has_lab_permission or any("Lab." in str(permission) for permission in permissions)
    if UNIFIED_LAB_MENU in permissions:
        permissions.extend([item for item in LAB_MENU_ITEMS if item not in permissions])
    if has_lab_permission and UNIFIED_LAB_MENU not in permissions:
        permissions.append(UNIFIED_LAB_MENU)
    return permissions


def build_visible_menu_groups(raw_permissions, all_menu):
    permissions = normalize_user_permissions(raw_permissions)
    accessible_pages = set(CORE_MENU)
    accessible_pages.update([menu_item for menu_item in all_menu if menu_item in permissions])
    if UNIFIED_LAB_MENU in permissions or any("Lab." in str(permission) for permission in raw_permissions or []):
        accessible_pages.add(UNIFIED_LAB_MENU)
    if MANAGEMENT_MENU in permissions or "AYARLAR" in (raw_permissions or []):
        accessible_pages.add(MANAGEMENT_MENU)

    visible_groups = {
        group: [page for page in pages if page in accessible_pages]
        for group, pages in MENU_GROUPS.items()
    }
    return {group: pages for group, pages in visible_groups.items() if pages}, permissions
