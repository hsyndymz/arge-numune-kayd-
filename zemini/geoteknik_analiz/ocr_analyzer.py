import os
import glob

class OcrAnalyzer:
    def __init__(self, directory_path):
        self.directory_path = directory_path
        self.image_files = glob.glob(os.path.join(directory_path, '*.jpeg')) + glob.glob(os.path.join(directory_path, '*.jpg'))
        self.image_files.sort()
        
    def analyze_images(self):
        """
        Görselleri tarayarak, geoteknik parametreleri (SPT, c, phi, Df vb.) çıkarmayı simüle eder.
        Gerçek uygulamada burada google-generativeai (Gemini Vision) veya pytesseract çalışacaktır.
        """
        print(f"[{len(self.image_files)}] adet görüntü bulundu. OCR analizi başlatılıyor...")
        
        # Simülasyon: İlk birkaç görselden örnek sondaj verisi "çıkarıldığı" varsayılıyor.
        # Bu değerler, rapor oluşturmak için 'core.py' motoruna gönderilecek.
        extracted_data = [
            {
                "sayfa": self.image_files[0] if len(self.image_files) > 0 else "Sayfa 1",
                "bulunanlar": {
                    "spt_n": 8,
                    "zemin_cinsi": "Silisli Kum",
                    "c": 0,
                    "phi": 28,
                    "gama_n": 18.5,
                    "Df": 2.0,
                    "yass": 1.5,
                    "B": 2.5,
                    "tip": "sürekli" # Şerit
                }
            },
            {
                "sayfa": self.image_files[10] if len(self.image_files) > 10 else "Sayfa 10",
                "bulunanlar": {
                    "spt_n": 12,
                    "zemin_cinsi": "Yumuşak Kil",
                    "c": 25,
                    "phi": 0,
                    "gama_n": 17.0,
                    "Df": 1.5,
                    "yass": 3.0,
                    "B": 3.0,
                    "tip": "kare"
                }
            }
        ]
        
        return extracted_data
        
if __name__ == "__main__":
    analyzer = OcrAnalyzer(r"c:\Users\hsynd\OneDrive\Masaüstü\zemini")
    sonuclar = analyzer.analyze_images()
    for s in sonuclar:
        print(s)
