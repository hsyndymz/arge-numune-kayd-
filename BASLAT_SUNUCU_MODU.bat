@echo off
TITLE Numune Takip Programi v31 - SUNUCU MODU
echo ======================================================
echo    NUMUNE TAKIP PROGRAMI v31 - SUNUCU MODU
echo ======================================================
echo.

:: IP Adresini Tespit Et
for /f "tokens=4 delims= " %%i in ('route print ^| find " 0.0.0.0"') do set IPADDR=%%i

echo Bu bilgisayarin IP adresi: %IPADDR%
echo.
echo ------------------------------------------------------
echo DIGER BILGISAYARLARDAN ERISIM ICIN:
echo Tarayiciya sunu yazin: http://%IPADDR%:8501
echo ------------------------------------------------------
echo.

:: Bagimliliklari kontrol et
echo Bagimliliklar kontrol ediliyor...
pip install -r requirements.txt --quiet

:: Uygulamayi tum ag arayuzlerinde baslat
echo Uygulama ag uzerinden erisime aciliyor...
streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --browser.gatherUsageStats false

pause
