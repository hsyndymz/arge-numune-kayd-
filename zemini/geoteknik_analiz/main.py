import os
from datetime import datetime
from core import GeoteknikHesaplayici
from ocr_analyzer import OcrAnalyzer

def ana_fonksiyon():
    kaynak_klasor = r"c:\Users\hsynd\OneDrive\Masaüstü\zemini"
    rapor_yolu = os.path.join(r"c:\Users\hsynd\OneDrive\Masaüstü\zemini\geoteknik_analiz", "Geoteknik_Rapor.md")
    
    hesaplayici = GeoteknikHesaplayici()
    analizor = OcrAnalyzer(kaynak_klasor)
    
    sondaj_verileri = analizor.analyze_images()
    
    with open(rapor_yolu, "w", encoding="utf-8") as f:
        f.write("# Akıllı Geoteknik Karar Destek Sistemi - İyileştirme Raporu\n")
        f.write(f"**Tarih:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        f.write("**Referanslar:** KTŞ 2023, Karayolları Zayıf Zemin Yayın No: 266\n")
        f.write("---\n\n")
        
        for index, veri in enumerate(sondaj_verileri, 1):
            f.write(f"## {index}. Analiz Edilen Veri: {os.path.basename(veri['sayfa'])}\n")
            b = veri['bulunanlar']
            
            f.write("### 1. Parametreler (OCR'dan Çıkarılan)\n")
            f.write(f"- **Zemin Sınıfı:** {b['zemin_cinsi']}\n")
            f.write(f"- **SPT (N):** {b['spt_n']}\n")
            f.write(f"- **Temel Derinliği (Df):** {b['Df']} m\n")
            f.write(f"- **Yeraltı Su Seviyesi (YASS):** {b['yass']} m\n")
            f.write(f"- **Temel Tipi ve Genişlik (B):** {b['tip'].title()} - {b['B']} m\n\n")
            
            # Taşıma Gücü Hesabı
            tg_sonuc = hesaplayici.tasima_gucu_hesapla(
                tip=b['tip'], B=b['B'], L=None, Df=b['Df'], 
                c=b['c'], phi=b['phi'], gama_n=b['gama_n'], yass=b['yass']
            )
            
            f.write("### 2. Terzaghi Taşıma Gücü Analizi\n")
            f.write(f"- **Sınır Taşıma Gücü ($q_{{sınır}}$):** {tg_sonuc['q_sinir']} kN/m²\n")
            f.write(f"- **Emin Taşıma Gücü ($q_{{emin}}$ - Gs:3):** {tg_sonuc['q_emin']} kN/m²\n\n")
            
            # İyileştirme Kararları
            iyilestirme = hesaplayici.iyilestirme_karari_ver(
                spt_n=b['spt_n'], zemin_cinsi=b['zemin_cinsi'], 
                yass=b['yass'], Df=b['Df']
            )
            
            f.write("### 3. Zemin İyileştirme ve Öneriler (KTŞ 2023 & Yayın 266)\n")
            f.write(iyilestirme + "\n\n")
            f.write("---\n")
            
        f.write("\n*Bu rapor yapay zeka tarafından (Akıllı Geoteknik Karar Destek Sistemi) oluşturulmuştur. Kesin proje onayı öncesi Geoteknik Mühendisi tarafından teyit edilmelidir.*\n")
    
    print(f"Rapor başarıyla oluşturuldu: {rapor_yolu}")
    print("İçeriğini inceleyebilirsiniz.")

if __name__ == "__main__":
    ana_fonksiyon()
