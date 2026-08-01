@echo off
TITLE Protokol Takip Programi - SUNUCU MODU
echo ======================================================
echo    PROTOKOL TAKIP PROGRAMI - SUNUCU MODU
echo ======================================================
echo.

:: IP Adresini Goster
echo Bu bilgisayarin IP adresi asagidadir.
echo Diger bilgisayarlardan erismek icin tarayiciya:
echo http://[IP_ADRESI]:8001 yaziniz.
echo.
ipconfig | findstr "IPv4"
echo.
echo ======================================================

:: Python kontrolü
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python yuklu degil! 
    echo Lutfen Python'i yukleyin veya tasinabilir surumu kullanin.
    pause
    exit
)

:: Bagimliliklari kontrol et ve yukle
echo Bagimliliklar kontrol ediliyor...
pip install -r requirements.txt --quiet

:: Uygulamayi baslat
echo Uygulama aciliyor...
python app.py

pause
