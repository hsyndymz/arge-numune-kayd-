@echo off
TITLE AR-GE Takip + Zemin Pro Ortak Baslatici
echo ======================================================
echo    AR-GE TAKIP SISTEMI + ZEMIN PRO - ORTAK BASLATICISI
echo ======================================================
echo.

:: IP Adresini Tespit Et
for /f "tokens=4 delims= " %%i in ('route print ^| find " 0.0.0.0"') do set IPADDR=%%i

echo Bu bilgisayarin IP adresi:   %IPADDR%
echo Uygulamaya Baglanmak icin:      http://%IPADDR%:8501
echo Zemin Pro Arayuzu icin port:    :5173
echo.
echo ------------------------------------------------------
echo.

set APP_DIR=%~dp0
cd /d "%APP_DIR%"

:: Zemin-viewer klasorunu bul (Istege bagli olarak iceriye veya Masaustunde kalmis olabilir)
if exist "%APP_DIR%zemin-viewer" (
    set REACT_DIR="%APP_DIR%zemin-viewer"
    echo [OK] Zemin Klasoru program icinde bulundu!
) else (
    set REACT_DIR="%APP_DIR%..\zemin-viewer"
    echo [BILGI] Zemin Klasoru masaustunde tespit edildi.
)

:: Bagimliliklar hizlica kontrol ediliyor...
python -c "import streamlit, pandas, plotly, pdfplumber, openpyxl, fpdf" >nul 2>&1
if errorlevel 1 (
    echo [BILGI] Eksik paketler tespit edildi, yukleniyor...
    pip install -r requirements.txt --quiet
    pip install pdfplumber --quiet
) else (
    echo [OK] Tum kütüphaneler hazir.
)

echo.
echo [1/1] AR-GE Takip Sistemi başlatılıyor...
echo.
echo ======================================================
echo    BASKA BILGISAYARDAN BAGLANMAK ICIN:
echo    URL: http://%IPADDR%:8501
echo ======================================================
echo.

:: Tarayıcıyı yerel IP üzerinden aç
start "" "http://%IPADDR%:8501"

:: Streamlit'i başlat
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true --browser.gatherUsageStats false

pause
