import json
import urllib.request
import urllib.error
import os

# LM Studio varsayılan yerel API adresi
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

# React projesindeki veritabanı dosyasının yolu
DB_YOLU = r"c:\Users\hsynd\OneDrive\Masaüstü\zemin-viewer\src\utils\ai_tecrube.json"

def ai_ile_analiz_et(rapor_metni):
    print("LM Studio'ya bağlanılıyor (Lütfen uygulamanın açık ve modelin yüklü olduğundan emin olun)...")
    
    sistem_promptu = """
    Sen uzman bir geoteknik mühendisisin. Kullanıcının sana verdiği eski bir 'Zemin Analiz Raporu/Yorumu' metnini okuyacaksın.
    Bu metinden şu bilgileri çıkarıp SADECE, YALNIZCA aşağıdaki JSON formatında cevap vereceksin (başka hiçbir kelime ekleme):
    {
      "zemin_cinsi_anahtar": "kum veya kil veya silt",
      "spt_min": 0,
      "spt_max": 99,
      "yass_durumu": "var veya yok veya farketmez",
      "yorum": "Geçmiş Rapordaki mühendislik tavsiyesini/yorumunu profesyonel bir dille buraya yaz"
    }
    """
    
    veri = {
        "model": "local-model", # LM studio modeli ne if you use "local-model" it routes to loaded model.
        "messages": [
            {"role": "system", "content": sistem_promptu},
            {"role": "user", "content": rapor_metni}
        ],
        "temperature": 0.3
    }
    
    req = urllib.request.Request(LM_STUDIO_URL, json.dumps(veri).encode('utf-8'))
    req.add_header('Content-Type', 'application/json')
    
    try:
        response = urllib.request.urlopen(req)
        sonucText = response.read().decode('utf-8')
        sonuc_json = json.loads(sonucText)
        
        # Yapay zekanın ürettiği JSON metnini çıkaralım
        ai_mesaj = sonuc_json['choices'][0]['message']['content']
        # Markdown kod bloklarını (```json ... ```) temizle
        if "```" in ai_mesaj:
            ai_mesaj = ai_mesaj.split("```")[1]
            if ai_mesaj.startswith("json"):
                ai_mesaj = ai_mesaj[4:]
                
        cikartilan_veri = json.loads(ai_mesaj.strip())
        return cikartilan_veri

    except Exception as e:
        print(f"Hata: Yapay Gecikmesi veya LM Studio kapalı olabilir. Detay: {e}")
        return None

def veritabanina_ekle(yeni_tecrube):
    if not yeni_tecrube:
        return
        
    try:
        # Eski veritabanını oku
        if os.path.exists(DB_YOLU):
            with open(DB_YOLU, "r", encoding="utf-8") as f:
                mevcut_veri = json.load(f)
        else:
            mevcut_veri = []
            
        # Benzersiz ID ekle
        yeni_tecrube["id"] = f"exp_{len(mevcut_veri) + 1:03d}"
        
        # Listeye ekle ve kaydet
        mevcut_veri.append(yeni_tecrube)
        
        with open(DB_YOLU, "w", encoding="utf-8") as f:
            json.dump(mevcut_veri, f, ensure_ascii=False, indent=2)
            
        print(f"🚀 Yeni tecrübe kuralları başarıyla React veritabanına eklendi! ({DB_YOLU})")
        print("\nÇIKARILAN KURAL:")
        for k, v in yeni_tecrube.items():
            print(f"- {k}: {v}")
            
    except Exception as e:
        print(f"Veritabanı kaydetme hatası: {e}")

if __name__ == "__main__":
    print("===================================================")
    print("  YEREL YAPAY ZEKA (LM STUDIO) RAPOR ÖĞRETİCİSİ")
    print("===================================================\n")
    
    print("Yeni öğrenilecek Eski Onaylı Raporun Metnini girin (İşiniz bitince Enter'a iki kez basın):")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
        
    rapor_metni = "\n".join(lines)
    
    if len(rapor_metni.strip()) > 10:
        tecrube = ai_ile_analiz_et(rapor_metni)
        veritabanina_ekle(tecrube)
    else:
        print("Çok kısa veya boş metin girdiniz. Çıkılıyor.")
