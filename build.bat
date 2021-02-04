@DEL _version.py

git describe --tags HEAD>VERSION.txt
set /P version= < VERSION.txt
echo version = "%version%" >>_version.py
@DEL VERSION.txt

pyinstaller --clean --distpath="./" --name="TableOCR" --onefile main.py 

@RD /S /Q dist
@RD /S /Q build
@DEL TableOCR.spec
echo ###Finished###
pause