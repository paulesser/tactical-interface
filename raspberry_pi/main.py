import time

# os.environ["PYNPUT_BACKEND_KEYBOARD"] = "uinput"
import easyocr
from cv2 import (
    COLOR_BGR2RGB,
    VideoCapture,
    cvtColor,
    destroyAllWindows,
    imshow,
    waitKey,
)
from pynput.keyboard import Controller

pressed = True


def main():
    cam = VideoCapture(0)
    # cam.set(CAP_PROP_FRAME_WIDTH, 1920)
    # cam.set(CAP_PROP_FRAME_HEIGHT, 1080)
    time.sleep(2)
    reader = easyocr.Reader(["de", "en"])
    keyboard = Controller()

    while True:
        try:
            ret, frame = cam.read()
            if ret:
                imshow("Captured", frame)
                waitKey(1)

                frame_rgb = cvtColor(frame, COLOR_BGR2RGB)
                if True:
                    result = reader.readtext(image=frame_rgb)
                    print(result)
                    if len(result) > 0:
                        for r in result:
                            if isinstance(r, tuple):
                                for key in r[1]:
                                    if type(key) is str and (
                                        key.encode("ascii", errors="ignore").decode(
                                            "ascii"
                                        )
                                    ):
                                        if False and key != " ":
                                            keyboard.press(key)

                            else:
                                print("no keys found")
                    else:
                        print("no letters found")
            else:
                print("no image")
        except KeyboardInterrupt:
            cam.release()
            destroyAllWindows()
            print("goodbye!")
            break


if __name__ == "__main__":
    main()
