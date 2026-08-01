import math

class GeoteknikHesaplayici:
    def __init__(self):
        # Tablo 2.1: Terzaghi Taşıma Gücü Katsayıları (Örnek değerler - daha da geliştirilebilir)
        self.terzaghi_tablo = {
            0: {"Nc": 5.70, "Nq": 1.00, "Ny": 0.00},
            1: {"Nc": 6.00, "Nq": 1.10, "Ny": 0.01},
            2: {"Nc": 6.30, "Nq": 1.22, "Ny": 0.04},
            3: {"Nc": 6.62, "Nq": 1.35, "Ny": 0.06},
            4: {"Nc": 6.97, "Nq": 1.49, "Ny": 0.10},
            5: {"Nc": 7.34, "Nq": 1.64, "Ny": 0.14},
            6: {"Nc": 7.73, "Nq": 1.81, "Ny": 0.20},
            7: {"Nc": 8.15, "Nq": 2.00, "Ny": 0.27},
            8: {"Nc": 8.60, "Nq": 2.21, "Ny": 0.35},
            9: {"Nc": 9.09, "Nq": 2.44, "Ny": 0.44},
            10: {"Nc": 9.61, "Nq": 2.69, "Ny": 0.56},
            11: {"Nc": 10.16, "Nq": 2.98, "Ny": 0.69},
            12: {"Nc": 10.76, "Nq": 3.29, "Ny": 0.85},
            13: {"Nc": 11.41, "Nq": 3.63, "Ny": 1.04},
            14: {"Nc": 12.11, "Nq": 4.02, "Ny": 1.26},
            15: {"Nc": 12.86, "Nq": 4.45, "Ny": 1.52},
            16: {"Nc": 13.68, "Nq": 4.92, "Ny": 1.82},
            17: {"Nc": 14.60, "Nq": 5.45, "Ny": 2.18},
            18: {"Nc": 15.52, "Nq": 6.04, "Ny": 2.59},
            19: {"Nc": 16.56, "Nq": 6.70, "Ny": 3.07},
            20: {"Nc": 17.69, "Nq": 7.44, "Ny": 3.64},
            21: {"Nc": 18.92, "Nq": 8.26, "Ny": 4.31},
            22: {"Nc": 20.27, "Nq": 9.19, "Ny": 5.09},
            23: {"Nc": 21.75, "Nq": 10.23, "Ny": 6.00},
            24: {"Nc": 23.36, "Nq": 11.40, "Ny": 7.08},
            25: {"Nc": 25.13, "Nq": 12.72, "Ny": 8.34},
            26: {"Nc": 27.09, "Nq": 14.21, "Ny": 9.84},
            27: {"Nc": 29.24, "Nq": 15.90, "Ny": 11.60},
            28: {"Nc": 31.61, "Nq": 17.81, "Ny": 13.70},
            29: {"Nc": 34.24, "Nq": 19.98, "Ny": 16.18},
            30: {"Nc": 37.16, "Nq": 22.46, "Ny": 19.13},
            31: {"Nc": 40.41, "Nq": 25.28, "Ny": 22.65},
            32: {"Nc": 44.04, "Nq": 28.52, "Ny": 26.87},
            33: {"Nc": 48.09, "Nq": 32.23, "Ny": 31.94},
            34: {"Nc": 52.64, "Nq": 36.50, "Ny": 38.04},
            35: {"Nc": 57.75, "Nq": 41.44, "Ny": 45.41},
            36: {"Nc": 63.53, "Nq": 47.16, "Ny": 54.36},
            37: {"Nc": 70.01, "Nq": 53.80, "Ny": 65.27},
            38: {"Nc": 77.50, "Nq": 61.55, "Ny": 78.61},
            39: {"Nc": 85.97, "Nq": 70.61, "Ny": 95.03},
            40: {"Nc": 95.66, "Nq": 81.27, "Ny": 115.31},
            41: {"Nc": 106.81, "Nq": 93.85, "Ny": 140.51},
            42: {"Nc": 119.67, "Nq": 108.75, "Ny": 171.99},
            43: {"Nc": 134.58, "Nq": 126.50, "Ny": 211.56},
            44: {"Nc": 151.95, "Nq": 147.74, "Ny": 261.60},
            45: {"Nc": 172.28, "Nq": 173.28, "Ny": 325.34},
            46: {"Nc": 196.22, "Nq": 204.19, "Ny": 407.11},
            47: {"Nc": 224.55, "Nq": 241.80, "Ny": 513.32},
            48: {"Nc": 258.28, "Nq": 287.85, "Ny": 652.73},
            49: {"Nc": 298.71, "Nq": 344.63, "Ny": 836.84},
            50: {"Nc": 347.50, "Nq": 415.14, "Ny": 1082.28}
        }

    def katsayilari_getir(self, phi):
        """En yakın phi değerine göre Terzaghi katsayılarını getirir."""
        if phi in self.terzaghi_tablo:
            return self.terzaghi_tablo[phi]
        
        # En yakın değeri bul (basit mantık, interpolasyon eklenebilir)
        closest_phi = min(self.terzaghi_tablo.keys(), key=lambda k: abs(k - phi))
        return self.terzaghi_tablo[closest_phi]

    def efektif_gama_hesapla(self, Df, B, yass, gama_n, gama_sat):
        """Yeraltı Su Seviyesi (YASS) değerine göre efektif birim hacim ağırlığı hesaplar."""
        gama_w = 10.0  # Akademik Problem çözümleri (Bayram Uzuner) için su birim hacim ağırlığı 10 alınır
        gama_batik = gama_sat - gama_w

        if yass <= 0:
            # Su seviyesi yüzeyde veya yüzeyin üstünde
            return gama_batik, gama_batik
        elif yass < Df:
            # Su seviyesi temel derinliği içinde
            # q (sürşarj) için ağırlıklı ortalama
            gama_ortalama_surşarj = (yass * gama_n + (Df - yass) * gama_batik) / Df
            return gama_ortalama_surşarj, gama_batik
        elif yass < Df + B:
            # Su seviyesi temel tabanının hemen altında, kama bölgesinde
            # 3. Terim (Birim hacim ağırlık terimi) için lineer interpolasyon
            d = yass - Df
            gama_ortalama_kama = gama_batik + (d / B) * (gama_n - gama_batik)
            return gama_n, gama_ortalama_kama
        else:
            # Su seviyesi çok derinde, etkisi yok
            return gama_n, gama_n

    def tasima_gucu_hesapla(self, tip, B, L, Df, c, phi, gama_n, gama_sat=None, yass=None, ex=0, ey=0, Gs=3.0):
        """
        Terzaghi genel taşıma gücü formülünü hesaplar.
        Meyerhof azaltılmış genişlik (eksantrisite) dikkate alınır.
        """
        # Eksantrisite kontrolü (Meyerhof)
        B_prime = B - 2 * ex if ex > 0 else B
        L_prime = L - 2 * ey if ey > 0 and L else L

        if not gama_sat:
            gama_sat = gama_n # Doygun verilmemişse doğal ile aynı kabul et

        # YASS etkisiyle gama değerleri
        if yass is not None:
            gama_sursarj, gama_kama = self.efektif_gama_hesapla(Df, B_prime, yass, gama_n, gama_sat)
        else:
            gama_sursarj, gama_kama = gama_n, gama_n

        katsayi = self.katsayilari_getir(phi)
        
        # Tablo 2.2: Şekil Katsayıları (Azaltılmış genişlik L ve B değerlerine göre)
        if tip == "şerit":
            k1, k2 = 1.0, 0.5
        elif tip == "kare":
            k1, k2 = 1.2, 0.4
        elif tip == "daire":
            k1, k2 = 1.3, 0.3
        else: # Dikdörtgen
            if L_prime:
                k1 = round(1 + 0.2 * (B_prime / L_prime), 2)
                k2 = round(0.5 - 0.1 * (B_prime / L_prime), 2)
            else:
                k1, k2 = 1.0, 0.5

        # Formül Bileşenleri
        terim1 = k1 * c * katsayi["Nc"]
        po = gama_sursarj * Df # Sürşarj
        terim2 = po * katsayi["Nq"]
        terim3 = k2 * gama_kama * B_prime * katsayi["Ny"]

        q_sinir = terim1 + terim2 + terim3
        q_emin = q_sinir / Gs
        
        alan = 0
        if tip in ["şerit", "dikdörtgen"]:
            alan = B * (L if L else 1)
        elif tip == "kare":
            alan = B * B
        elif tip == "daire":
            alan = (math.pi * B * B) / 4
            
        Q_emin = q_emin * alan
        
        return {
            "q_sinir": round(q_sinir, 2),
            "q_emin": round(q_emin, 2),
            "Q_emin": round(Q_emin, 2),
            "Alan": round(alan, 2),
            "B_prime": round(B_prime, 2),
            "L_prime": round(L_prime, 2) if L_prime else None,
            "terimler": {
                "kohezyon": round(terim1, 2),
                "sursarj": round(terim2, 2),
                "kama": round(terim3, 2)
            }
        }

    def iyilestirme_karari_ver(self, spt_n, zemin_cinsi, yass, Df):
        """
        KTŞ 2023 ve Karayolları Yayın No:266 baz alınarak kural tabanlı zemin iyileştirme kararları.
        """
        oneriler = []

        if spt_n < 10:
            oneriler.append("- Zayıf Zemin Tespiti: SPT N değeri 10'un altında. (Yayın 266: Yüzeyde zayıf tabaka). "
                            "Geosentetik / Geotekstil donatılı zemin iyileştirmesi veya zemin değişimi önerilir.")
        
        if yass is not None and yass < Df + 2:
            if "kum" in zemin_cinsi.lower() or "çakıl" in zemin_cinsi.lower():
                oneriler.append("- Sıvılaşma ve Yeraltı Suyu Riski: Su seviyesi temele yakın (< Df + 2m) ve zemin kohezyonsuz. "
                                "(KTŞ 2023: Dinamik konsolidasyon veya Jet Grout / Taş Kolon uygulanarak sıvılaşma riski azaltılmalıdır).")
            else:
                oneriler.append("- Yeraltı Suyu Etkisi: Yüksek su seviyesi, taşıma gücünü %50'ye varan oranda düşürür. "
                                "(KTŞ 2023: Temel altı drenaj sistemleri ve geçirimsiz perde/kılıf (cut-off) değerlendirilmelidir).")
                
        if "kil" in zemin_cinsi.lower() and spt_n < 15:
            oneriler.append("- Oturma Riski: Yumuşak kil tabakası mevcut. "
                            "(Yayın 266: Konsolidasyon oturmalarını hızlandırmak için Prefabrike Düşey Dren (PVD) + Sürşarj yüklemesi tavsiye edilir).")

        if not oneriler:
            oneriler.append("- Zemin parametreleri standarda uygun görünmektedir. Özel bir iyileştirme şartı tespit edilememiştir. Standart temel imalatına geçilebilir.")

        return "\n".join(oneriler)

# Test fonksiyonu
if __name__ == "__main__":
    hesaplayici = GeoteknikHesaplayici()
    print("Test Hesaplaması (Şerit Temel, Eksantrisitesiz):")
    sonuc = hesaplayici.tasima_gucu_hesapla(tip="şerit", B=2, L=None, Df=1.5, c=20, phi=30, gama_n=18, yass=1.0)
    print(sonuc)
    
    print("\nKTŞ 2023 / Yayın 266 İyileştirme Senaryosu:")
    print(hesaplayici.iyilestirme_karari_ver(spt_n=8, zemin_cinsi="Siltli Kum", yass=1.0, Df=1.5))
