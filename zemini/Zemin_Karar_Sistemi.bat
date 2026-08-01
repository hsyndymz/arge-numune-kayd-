@echo off
chcp 65001 > nul
title Akilli Geoteknik Karar Destek Sistemi
color 0B

:: Bu scriptin calistigi klasoru referans alir (zemini klasoru)
set BASE_DIR=%~dp0

:MENU
cls
echo =======================================================
echo     AKILLI GEOTEKNIK KARAR DESTEK SISTEMI MENUSU
echo =======================================================
echo.
echo    [1] Yeni Geoteknik Rapor Uret (Python OCR Analizi)
echo    [2] Zemin Pro Arayuzunu Baslat (React UI)
echo    [3] Cikis
echo.
echo =======================================================
set /p secim="Lutfen bir islem secin (1/2/3): "

if "%secim%"=="1" goto PYTHON_SCRIPT
if "%secim%"=="2" goto REACT_SERVER
if "%secim%"=="3" goto EOF

echo Gecersiz secim! Lutfen 1, 2 veya 3 girin.
pause
goto MENU

:PYTHON_SCRIPT
cls
echo [Bilgi] Python OCR analiz ve Raporlama baslatiliyor...
echo.
:: Python dosyasi bu bat ile ayni klasordeki 'geoteknik_analiz' icinde
cd /d "%BASE_DIR%geoteknik_analiz"
python main.py
echo.
echo Raporlama tamamlandi. 'Geoteknik_Rapor.md' dosyasini inceleyebilirsiniz.
pause
goto MENU

:REACT_SERVER
cls
echo [Bilgi] Zemin Pro React Arayuzu baslatiliyor...
echo [Bilgi] Tarayicinizda projenin kendi portunda acilacaktir...
echo Sunucuyu durdurmak icin pencereyi kapatabilir veya CTRL+C yapabilirsiniz.
echo.
:: React projesi bu klasorun bir ustundeki 'zemin-viewer' icinde varsayilir
cd /d "%BASE_DIR%..\zemin-viewer"
npm run dev -- --host --open
pause
goto MENU

:EOF
exit
