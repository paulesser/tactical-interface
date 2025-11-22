import time

# os.environ["PYNPUT_BACKEND_KEYBOARD"] = "uinput"
import cv2 as cv
from pynput.keyboard import Controller

pressed = True


def main():
    cam = cv.VideoCapture(0)
    # cam.set(CAP_PROP_FRAME_WIDTH, 1920)
    # cam.set(CAP_PROP_FRAME_HEIGHT, 1080)
    time.sleep(2)

    keyboard = Controller()

    while True:
        try:
            ret, frame = cam.read()
            if ret:
                cv.imshow("Captured", frame)
                cv.waitKey(1)

                frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                if False:
                    keyboard.press("a")

        except KeyboardInterrupt:
            cam.release()
            cv.destroyAllWindows()
            print("goodbye!")
            break


if __name__ == "__main__":
    main()
