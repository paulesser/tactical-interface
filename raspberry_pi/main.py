import time
from io import BytesIO

# os.environ["PYNPUT_BACKEND_KEYBOARD"] = "uinput"
import cv2 as cv
import requests
from PIL import Image
from pynput.keyboard import Controller

pressed = True

api = "https://webpage-toolbox-trembl-campbell.trycloudflare.com"


def pil2bytes(image: Image.Image) -> bytes:
    """
    converts pil image into bytes
    Args:
        image (Image.Image): the source image
    Returns:
        bytes: the bytes representation of the image
    """
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format="PNG")
    return img_byte_arr.getvalue()


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
                pil_image = Image.fromarray(frame_rgb)
                response = requests.post(
                    f"{api}/ocr",
                    files={
                        "image": pil2bytes(pil_image),
                    },
                )
                print(response.text)
                if False:
                    keyboard.press("a")
                time.sleep(1)
        except KeyboardInterrupt:
            cam.release()
            cv.destroyAllWindows()
            print("goodbye!")
            break


if __name__ == "__main__":
    main()
