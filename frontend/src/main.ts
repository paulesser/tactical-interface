import p5 from "p5";

let result = "";
let capture: p5.MediaElement | null;
let lastMilliSeconds = 0;
let countdown = 0;

const sketch = (p: p5) => {
  p.setup = async () => {
    let font = await p.loadFont("assets/JetBrainsMono-Regular.ttf");
    p.createCanvas(640, 480);
    p.textFont(font);
    capture = p.createCapture(p.VIDEO);
    capture.size(p.width, p.height);
    capture.hide();
    p.frameRate(14);
  };
  p.draw = () => {
    p.background(100);
    countdown = (p.millis() - lastMilliSeconds) / 1000;
    if (countdown > 10.9) {
      ocr();
      lastMilliSeconds = p.millis();
      typeKeyboard(result);
    }
    if (capture) {
      p.image(capture, 0, 0);
    }
    p.textAlign(p.LEFT, p.BOTTOM);
    p.textWrap(p.CHAR);
    p.fill("#c90d00");
    p.textSize(20);
    p.text(result, 10, p.height - 10, p.width - 20);

    p.textSize(40);
    p.fill(0);
    p.textAlign(p.LEFT, p.TOP);
    p.text(11 - p.ceil(countdown), 10, 10);
  };
};
new p5(sketch);

const ocrUrl = import.meta.env.VITE_API_URL;
const keyboardUrl = import.meta.env.VITE_KEYBOARD_URL;
async function typeKeyboard(t: string) {
  try {
    const response = await fetch(`${keyboardUrl}/keyboard`, {
      method: "POST",
      body: t,
    });
    if (!response.ok) {
      throw new Error(response.statusText);
    }
    const responseText = await response.text();
    console.log(responseText);
  } catch (e) {
    console.error(e);
  }
}

async function ocr() {
  const canvas = document.querySelector("canvas");
  if (!canvas) {
    console.error("canvas not found");
    return;
  }
  canvas.toBlob(
    async (blob) => {
      try {
        const form = new FormData();
        if (!blob) throw new Error("could not get blob");
        form.append("image", blob);

        const response = await fetch(ocrUrl + "/ocr", {
          method: "POST",
          body: form,
        });
        if (response.ok) {
          let t = await response.text();
          if (t.length > 0) {
            let mapped = t
              .split('"')
              .join(" ")
              .split(",")
              .join(" ")
              .split(";")
              .join(" ");
            result = mapped;
          } else {
            result = "";
          }
        } else {
          throw new Error(response.statusText);
        }
      } catch (e) {
        console.error(e);
      }
    },

    "image/jpeg",
    0.95,
  );
}
