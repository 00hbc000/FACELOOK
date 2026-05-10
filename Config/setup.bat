@echo off
echo Installing FACELOOK...
mkdir C:\FACELOOK\Database
mkdir C:\FACELOOK\Logs
copy /Y FacelookProvider.dll C:\FACELOOK\CredentialProvider\
reg import C:\FACELOOK\Config\registry.reg
pip install -r C:\FACELOOK\FaceService\requirements.txt
call C:\FACELOOK\FaceService\install_service.bat
echo Done.
pause