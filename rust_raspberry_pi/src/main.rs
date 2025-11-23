use image::{ImageBuffer, Rgba};
use nokhwa::{
    CallbackCamera, nokhwa_initialize,
    pixel_format::{RgbAFormat, RgbFormat},
    query,
    utils::{ApiBackend, RequestedFormat, RequestedFormatType},
};

#[macro_use]
extern crate dotenv_codegen;
use rustautogui;

use reqwest::Client;
use reqwest::multipart;
use std::sync::{Arc, Mutex};
use tokio::runtime::Runtime;

#[tokio::main]
async fn main() {
    let _rustautogui = rustautogui::RustAutoGui::new(false).unwrap();

    nokhwa_initialize(|granted| {
        println!("User said {}", granted);
    });
    let _url = dotenv!("API_URL");

    let cameras = query(ApiBackend::Auto).unwrap();
    cameras.iter().for_each(|cam| println!("{:?}", cam));
    let format = RequestedFormat::new::<RgbFormat>(RequestedFormatType::AbsoluteHighestFrameRate);
    let first_camera = cameras.first().unwrap();
    let mut threaded = CallbackCamera::new(first_camera.index().clone(), format, |buffer| {
        let image = buffer.decode_image::<RgbAFormat>().unwrap();
        println!("{}x{} {}", image.width(), image.height(), image.len());
    })
    .unwrap();
    threaded.open_stream().unwrap();
    println!("Camera initialized");

    loop {
        if let Ok(frame) = threaded.poll_frame() {
            if let Ok(image) = frame.decode_image::<RgbAFormat>() {
                let ocr = get_ocr(_url, image).await;
                println!("OCR: {:#?}", ocr);
                match ocr {
                    Ok(ocr) => _rustautogui.keyboard_input(&ocr).unwrap(),
                    Err(_) => {}
                }
            }
        }

        //
    }
}

async fn get_ocr(
    url: &str,
    image_buffer: ImageBuffer<Rgba<u8>, Vec<u8>>,
) -> Result<String, String> {
    let client = Client::new();
    // Encode the image to PNG format in memory
    let mut img_byte_arr = Vec::new();
    let mut cursor = std::io::Cursor::new(&mut img_byte_arr);
    image_buffer
        .write_to(&mut cursor, image::ImageFormat::Png)
        .map_err(|e| format!("Failed to encode image: {}", e))?;

    // Create multipart form with the image file
    let form = multipart::Form::new().part(
        "image",
        multipart::Part::bytes(img_byte_arr)
            .file_name("image.png")
            .mime_str("image/png")
            .map_err(|e| format!("Failed to set mime type: {}", e))?,
    );

    // Send POST request
    let response = client
        .post(format!("{}/ocr", url))
        .multipart(form)
        .send()
        .await;
    let response_text = match response {
        Ok(response) => response.text().await.unwrap_or_else(|_| "".to_owned()),
        Err(_) => "".to_owned(),
    };
    // Get response text

    Ok(response_text)
}
