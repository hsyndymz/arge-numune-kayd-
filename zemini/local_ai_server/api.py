import os
import json
import urllib.request
import urllib.error
from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # React uygulamasının (localhost:5173) istek atabilmesi için gerekli

# Konfigürasyonlar
LM_STUDIO_URL = "http://localhost:1234/v1"
DB_YOLU = r"c:\Users\hsynd\OneDrive\Masaüstü\zemin-viewer\src\utils\ai_tecrube.json"

@app.route('/api/models', methods=['GET'])
def get_models():
    """LM Studio'daki mevcut yapay zeka modellerini listeler."""
    try:
        req = urllib.request.Request(f"{LM_STUDIO_URL}/models")
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": f"LM Studio bağlantı hatası: {str(e)}"}), 500

@app.route('/api/upload_report', methods=['POST'])
def upload_report():
    """PDF dosyasını alır, metnini ayıklar, LM Studio'ya gönderir ve veritabanını günceller."""
    if 'file' not in request.files:
        return jsonify({"error": "Dosya bulunamadı"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Seçili dosya yok"}), 400
        
    model_name = request.form.get('model', 'local-model')
        
    try:
        # 1. PDF Metnini Çıkar
        pdf_reader = PyPDF2.PdfReader(file)
        full_text = ""
        # Sadece son 5 sayfayı veya varsa "Sonuç ve Öneriler" kısmını almak için bir filitrasyon yapılabilir.
        # Basitlik için tüm metni veya ilk birkaç sayfayı alıyoruz (çok uzunsa LM Studio token limiti aşılabilir)
        page_count = len(pdf_reader.pages)
        # Raporların genelde sonunda yorumlar olur, son 3 sayfaya odaklanalım
        start_page = max(0, page_count - 5)
        for i in range(start_page, page_count):
            page = pdf_reader.pages[i]
            full_text += page.extract_text() + "\n"
            
        if len(full_text.strip()) < 50:
            # Belki ilk sayfalardadır
            full_text = ""
            for i in range(min(page_count, 3)):
                full_text += pdf_reader.pages[i].extract_text() + "\n"
                
        # 2. LM Studio'ya (Seçili Modele) Gönder
        sistem_promptu = """
        Sen uzman bir geoteknik mühendisisin. Aşağıdaki geçmiş "Zemin İyileştirme/Zemin Etüd" raporunun sonuç bölümünü oku.
        Bu raporun içeriğinden şu bilgileri çıkarıp SADECE ve YALNIZCA aşağıdaki JSON formatında cevap vereceksin:
        {
          "zemin_cinsi_anahtar": "kum veya kil veya silt",
          "spt_min": 0,
          "spt_max": 99,
          "yass_durumu": "var veya yok veya farketmez",
          "yorum": "Rapordaki mühendislik tavsiyesini profesyonel bir dille buraya yaz"
        }
        Dikkat: Herhangi bir markdown işareti (```json) eklemeksizin direkt saf {} verisi döneceksin.
        """
        
        veri = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": sistem_promptu},
                {"role": "user", "content": full_text[:4000]} # LM Studio limite takılmaması için ilk/son 4000 karakter
            ],
            "temperature": 0.2
        }
        
        req = urllib.request.Request(f"{LM_STUDIO_URL}/chat/completions", json.dumps(veri).encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        
        response = urllib.request.urlopen(req)
        sonuc_json = json.loads(response.read().decode('utf-8'))
        ai_mesaj = sonuc_json['choices'][0]['message']['content'].strip()
        
        # Markdown blok temizlemesi
        if ai_mesaj.startswith("```json"):
            ai_mesaj = ai_mesaj[7:]
        if ai_mesaj.startswith("```"):
            ai_mesaj = ai_mesaj[3:]
        if ai_mesaj.endswith("```"):
            ai_mesaj = ai_mesaj[:-3]
            
        tecrube = json.loads(ai_mesaj.strip())
        
        # 3. Veritabanını Güncelle
        if os.path.exists(DB_YOLU):
            with open(DB_YOLU, "r", encoding="utf-8") as f:
                mevcut_veri = json.load(f)
        else:
            mevcut_veri = []
            
        tecrube["id"] = f"exp_{len(mevcut_veri) + 1:03d}"
        mevcut_veri.append(tecrube)
        
        with open(DB_YOLU, "w", encoding="utf-8") as f:
            json.dump(mevcut_veri, f, ensure_ascii=False, indent=2)
            
        return jsonify({
            "success": True,
            "message": "Model başarıyla öğrendi ve kural eklendi!",
            "data": tecrube
        })
        
    except Exception as e:
        import traceback
        return jsonify({"error": f"İşlem sırasında hata oluştu: {str(e)}", "trace": traceback.format_exc()}), 500

if __name__ == '__main__':
    print("🚀 Zemin Pro AI Sunucusu başlatılıyor... (Port: 5000)")
    # Ağdaki diğer bilgisayarların erişebilmesi için 0.0.0.0 olarak değiştirildi
    app.run(host='0.0.0.0', port=5000, debug=True)
