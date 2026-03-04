@echo off
REM ==========================
REM Auto Commit & Push CSVs
REM ==========================

cd "D:\Solid'Africa\OneDrive - SolidAfrica\Python Backend\Dashboard\Gemura_App"

REM Add updated CSVs
git add "data\Gemura Program (Normal diet) Database.csv"
git add "data\Gemura Program (Special Diet) Database.csv"

REM Commit with current timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%
git commit -m "Auto update CSVs %timestamp%"

REM Push to remote
git push origin main

echo CSVs pushed to GitHub successfully!
pause