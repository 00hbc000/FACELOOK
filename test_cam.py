import cv2

backends = [
    ('DSHOW',  cv2.CAP_DSHOW),
    ('MSMF',   cv2.CAP_MSMF),
    ('ANY',    cv2.CAP_ANY),
    ('V4L2',   cv2.CAP_V4L2),
]

for name, backend in backends:
    for idx in range(3):
        try:
            cap = cv2.VideoCapture(idx, backend)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f'SUCCESS: backend={name} index={idx} shape={frame.shape}')
                else:
                    print(f'OPENED but no frame: backend={name} index={idx}')
                cap.release()
            else:
                print(f'FAIL: backend={name} index={idx}')
        except Exception as e:
            print(f'ERROR: backend={name} index={idx} error={e}')
