import os
import time

os.environ["QT_QPA_PLATFORM"] = "xcb"

import easyocr
from cv2 import CAP_V4L2, COLOR_BGR2RGB, VideoCapture, cvtColor, imshow
from pynput.keyboard import Controller


def main():
    keyboard = Controller()
    cam = VideoCapture(0, CAP_V4L2)
    reader = easyocr.Reader(["de", "en"])
    while True:
        try:
            ret, frame = cam.read()
            if ret:
                imshow("Captured", frame)
                frame_rgb = cvtColor(frame, COLOR_BGR2RGB)
                result = reader.readtext(image=frame_rgb)
                if len(result) > 0:
                    for r in result:
                        if isinstance(r, tuple):
                            for key in r[1]:
                                keyboard.press(key)
                                print(key)
                        else:
                            print("no keys found")
                else:
                    print("no letters found")
            else:
                print("no image")
            time.sleep(1)
        except KeyboardInterrupt:
            cam.release()
            print("goodbye!")
            break


if __name__ == "__main__":
    main()
