@echo off
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

:MENU
call :SHOW_HEADER
echo 1. Xoa file tam (Temp, Prefetch)
echo 2. Xoa cache, log va file Update Windows
echo 3. Don thung rac
echo 4. Toi uu Explorer / lam moi dich vu
echo 5. Don o dia he thong (tu dong)
echo 6. Thuc hien tat ca tu 1 den 5
echo 7. Thoat
set /p choice=Chon Muc Can Don Rac - Muon Don Full Thi Bam So 6 - Roi Enter (1-7):

if "%choice%"=="1" goto CLEAN_TEMP
if "%choice%"=="2" goto CLEAN_LOG_UPDATE
if "%choice%"=="3" goto CLEAN_BIN
if "%choice%"=="4" goto OPTIMIZE
if "%choice%"=="5" goto DISKCLEAN
if "%choice%"=="6" goto ALL_TASKS
if "%choice%"=="7" exit
goto MENU

:CLEAN_TEMP
call :DO_CLEAN_TEMP
echo.
echo Da xoa file tam.
echo Nhan phim bat ky de thoat ban hien tai va quay ve MENU...
pause >nul
goto MENU

:CLEAN_LOG_UPDATE
call :DO_CLEAN_LOG_UPDATE
echo.
echo Da xoa cache, log va file cap nhat.
echo Nhan phim bat ky de thoat ban hien tai va quay ve MENU...
pause >nul
goto MENU

:CLEAN_BIN
call :DO_CLEAN_BIN
echo.
echo Da don thung rac.
echo Nhan phim bat ky de thoat ban hien tai va quay ve MENU...
pause >nul
goto MENU

:OPTIMIZE
call :DO_OPTIMIZE
echo.
echo Da lam moi Explorer.
echo Nhan phim bat ky de thoat ban hien tai va quay ve MENU...
pause >nul
goto MENU

:DISKCLEAN
call :DO_DISKCLEAN
echo.
echo Da hoan thanh don o dia.
echo Nhan phim bat ky de thoat ban hien tai va quay ve MENU...
pause >nul
goto MENU

:ALL_TASKS
echo.
echo Dang thuc hien tat ca cac buoc...
call :DO_CLEAN_TEMP
call :DO_CLEAN_LOG_UPDATE
call :DO_CLEAN_BIN
call :DO_OPTIMIZE
call :DO_DISKCLEAN
echo.
echo Tat ca cac buoc da hoan thanh!
echo Nhan phim bat ky de thoat ban hien tai va quay ve MENU...
pause >nul
goto MENU

:: ================== CAC TAC VU ===================

:DO_CLEAN_TEMP
echo.
echo Dang xoa file tam...
call :PROGRESS_BAR
del /s /f /q %temp%\*.* >nul 2>&1
rd /s /q %temp% >nul 2>&1
md %temp%
del /s /f /q C:\Windows\Prefetch\*.* >nul 2>&1
exit /b

:DO_CLEAN_LOG_UPDATE
echo.
echo Dang xoa cache, log va file cap nhat Windows...
call :PROGRESS_BAR
del /s /f /q C:\Windows\Temp\*.* >nul 2>&1
del /s /f /q C:\Windows\Logs\*.* >nul 2>&1
del /s /f /q C:\Windows\SoftwareDistribution\Download\*.* >nul 2>&1
rd /s /q C:\Windows\SoftwareDistribution\Download >nul 2>&1
md C:\Windows\SoftwareDistribution\Download >nul 2>&1
exit /b

:DO_CLEAN_BIN
echo.
echo Dang don thung rac...
call :PROGRESS_BAR
powershell -command "& {Clear-RecycleBin -Force}" >nul 2>&1
exit /b

:DO_OPTIMIZE
echo.
echo Dang lam moi dich vu Explorer...
call :PROGRESS_BAR
taskkill /f /im explorer.exe >nul 2>&1
start explorer.exe
exit /b

:DO_DISKCLEAN
echo.
echo Dang don o dia he thong (tu dong, da tich san cac muc)...
call :PROGRESS_BAR
cleanmgr /sagerun:1
exit /b

:: ================== TIEN TRINH % ===================

:PROGRESS_BAR
echo [                    ] 0%%
ping -n 1 127.0.0.1 >nul
cls
echo [####                ] 25%%
ping -n 1 127.0.0.1 >nul
cls
echo [##########          ] 50%%
ping -n 1 127.0.0.1 >nul
cls
echo [###############     ] 75%%
ping -n 1 127.0.0.1 >nul
cls
echo [####################] 100%%
ping -n 1 127.0.0.1 >nul
cls
exit /b

:SHOW_HEADER
cls
color 0A
echo ===================================================
echo            ***  TOOL TOI UU VA DON RAC PC  ***
color 0C
echo              *    NGUOI TAO: BaoTruong    *
color 07
echo ===================================================
echo.
exit /b