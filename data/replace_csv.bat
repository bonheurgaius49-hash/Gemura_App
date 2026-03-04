@echo off
REM ==========================
REM Replace old CSVs with _WIDE
REM ==========================

REM Switch to the correct drive
D:

REM Navigate to the data folder
cd "D:\Solid'Africa\OneDrive - SolidAfrica\Python Backend\Dashboard\Gemura_App\data"

REM Replace Normal diet CSV
copy /Y "Gemura Program (Normal diet)_WIDE.csv" "Gemura Program (Normal diet) Database.csv"

REM Replace Special Diet CSV
copy /Y "Gemura Program (Special Diet)_WIDE.csv" "Gemura Program (Special Diet) Database.csv"

echo CSV replacement completed!
pause