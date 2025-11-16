# import logging
import time

import easyocr
from cv2 import COLOR_BGR2RGB, VideoCapture, cvtColor, imshow
from pynput.keyboard import Controller

# logging.basicConfig(
#     filename="/var/log/my-pynput-tool.log",
#     level=logging.INFO,
#     format="%(asctime)s - %(message)s",
# )


def main():
    keyboard = Controller()
    cam = VideoCapture(1)
    pressed: bool = True
    reader = easyocr.Reader(["de", "en"])
    while True:
        try:
            if pressed:
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
            time.sleep(10)
        except KeyboardInterrupt:
            cam.release()
            print("goodbye!")
            break


if __name__ == "__main__":
    main()
