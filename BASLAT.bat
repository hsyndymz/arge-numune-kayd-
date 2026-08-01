@echo off
TITLE Numune Takip Programi v31
echo ======================================================
echo    NUMUNE TAKIP PROGRAMI v31 - BASLATILIYOR
echo ======================================================
echo.

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
python -m streamlit run app.py --browser.gatherUsageStats false

pause
