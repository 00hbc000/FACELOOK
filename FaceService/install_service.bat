@echo off
cd /d C:\FACELOOK\FaceService
python face_service.py install
sc config FACELOOKService start= auto
net start FACELOOKService
echo FACELOOK Service installed and started.
pause