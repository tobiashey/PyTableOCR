@DEL _version.py

git describe --tags HEAD>VERSION.txt
set /P version= < VERSION.txt
echo version = "%version%" >>_version.py
@DEL VERSION.txt

set PYTHONOPTIMIZE=1 && PyInstaller --clean ^
	--distpath="./" ^
	--name="TableOCR" ^
	--icon="icon.ico" ^
	--noconfirm ^
	--noconsole ^
	--add-data "icon.ico;." ^
	--onedir main.py

@RD /S /Q dist
@RD /S /Q build
@DEL TableOCR.spec
echo ###Finished###
pause