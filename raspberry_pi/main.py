import os
import sys

from dotenv import find_dotenv, load_dotenv
from pydantic_settings import BaseSettings

# change input managment for pynput if i am on the raspberry pi
if sys.platform == "linux":
    os.environ["PYNPUT_BACKEND_KEYBOARD"] = "uinput"

import cv2 as cv
import requests
from pynput.keyboard import Controller

pressed = True

load_dotenv(find_dotenv(".env"))


class Settings(BaseSettings):
    api_url: str


def main():
    cam = cv.VideoCapture(1)

    url = Settings().api_url
    keyboard = Controller()

    while True:
        try:
            ret, frame = cam.read()
            if ret:
                cv.imshow("Captured", frame)
                cv.waitKey(1)

                frame_rgb = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
                ret2, encoded_image = cv.imencode(".png", frame_rgb)
                if ret2:
                    img_byte_arr = encoded_image.tobytes()
                    response = requests.post(
                        f"{url}/ocr",
                        files={
                            "image": img_byte_arr,
                        },
                    )
                    for char in response.text:
                        keyboard.press(char)
                else:
                    print("error encoding image into bytes")
            else:
                print("error opening webcam")

        except KeyboardInterrupt:
            cam.release()
            cv.destroyAllWindows()
            print("goodbye!")
            break


if __name__ == "__main__":
    main()
