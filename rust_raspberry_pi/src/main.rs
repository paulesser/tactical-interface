#[macro_use]
extern crate dotenv_codegen;
use eframe::egui::{self, TextureHandle};
use image::{ImageBuffer, Rgba};
use nokhwa::pixel_format::RgbAFormat;
use nokhwa::utils::{ApiBackend, RequestedFormat, RequestedFormatType};
use nokhwa::{Camera, query};
use reqwest::{Client, multipart};
use rustautogui;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};
use tokio::sync::mpsc;

#[derive(Clone)]
struct FrameData {
    image: ImageBuffer<Rgba<u8>, Vec<u8>>,
}

struct MyApp {
    current_frame: Arc<Mutex<Option<FrameData>>>,
    texture_handle: Option<TextureHandle>,
    api_sender: mpsc::UnboundedSender<FrameData>,
    api_status: Arc<Mutex<String>>,
    next_send_time: Instant,
    send_interval: Duration,
}

impl MyApp {
    fn new(cc: &eframe::CreationContext<'_>) -> Self {
        nokhwa::nokhwa_initialize(|granted| {
            println!("User said {}", granted);
        });

        let cameras = query(ApiBackend::Auto).unwrap();
        if cameras.is_empty() {
            panic!("No cameras found!");
        }

        let format =
            RequestedFormat::new::<RgbAFormat>(RequestedFormatType::AbsoluteHighestFrameRate);

        let mut camera = Camera::new(cameras[0].index().clone(), format).unwrap();
        camera.open_stream().unwrap();

        let current_frame = Arc::new(Mutex::new(None));
        let api_status = Arc::new(Mutex::new("Idle".to_string()));

        let (api_sender, mut api_receiver) = mpsc::unbounded_channel::<FrameData>();

        let runtime = tokio::runtime::Handle::current();

        let frame_clone = current_frame.clone();

        thread::spawn(move || {
            loop {
                match camera.frame() {
                    Ok(frame_buffer) => {
                        if let Ok(image) = frame_buffer.decode_image::<RgbAFormat>() {
                            let frame_data = FrameData { image };

                            if let Ok(mut frame) = frame_clone.lock() {
                                *frame = Some(frame_data.clone());
                            }
                        }
                    }
                    Err(e) => println!("Frame capture error: {}", e),
                }
                thread::sleep(Duration::from_millis(40));
            }
        });

        // Spawn API processor task
        let status_clone = api_status.clone();
        runtime.spawn(async move {
            while let Some(frame_data) = api_receiver.recv().await {
                // Update status
                if let Ok(mut status) = status_clone.lock() {
                    *status = "Processing...".to_string();
                }

                // Send frame to API
                match get_ocr(dotenv!("API_URL"), frame_data.image).await {
                    Ok(response) => {
                        if let Ok(mut status) = status_clone.lock() {
                            *status = format!("{}", response);
                        }
                    }
                    Err(e) => {
                        if let Ok(mut status) = status_clone.lock() {
                            *status = format!("{}", e);
                        }
                    }
                }
            }
        });

        let send_interval = Duration::from_secs(15);

        Self {
            current_frame,
            texture_handle: None,
            api_sender,
            api_status,
            next_send_time: Instant::now() + send_interval,
            send_interval,
        }
    }
}

impl eframe::App for MyApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        ctx.request_repaint();
        let _rustautogui = rustautogui::RustAutoGui::new(false).unwrap();
        let now = Instant::now();
        if now >= self.next_send_time {
            if let Ok(frame_guard) = self.current_frame.lock() {
                if let Some(ref frame_data) = *frame_guard {
                    let _ = self.api_sender.send(frame_data.clone());
                }
            }
            self.next_send_time = now + self.send_interval;
        }

        let remaining_secs = if now < self.next_send_time {
            (self.next_send_time - now).as_secs_f32().ceil() as u64
        } else {
            0
        };

        egui::CentralPanel::default().show(ctx, |ui| {
            if let Ok(mut status) = self.api_status.lock() {
                ui.horizontal(|ui| {
                    // ui.label("API Status:");
                    ui.colored_label(egui::Color32::GREEN, status.as_str());
                });
                if status.as_str() != "\"\""
                    && status.as_str() != "Idle"
                    && status.as_str() != "Processing..."
                {
                    let _ = _rustautogui.keyboard_input(status.as_str());
                    *status = format!("Idle")
                }
            }

            ui.add_space(2.0);

            ui.horizontal(|ui| {
                ui.label("Keyboard is ready to type in:");
                ui.colored_label(egui::Color32::BLUE, format!("{} seconds", remaining_secs));
            });

            ui.add_space(2.0);

            if let Ok(frame_guard) = self.current_frame.try_lock() {
                if let Some(ref frame_data) = *frame_guard {
                    let image = &frame_data.image;
                    let size = [image.width() as _, image.height() as _];
                    let color_image =
                        egui::ColorImage::from_rgba_unmultiplied(size, image.as_raw());

                    match &mut self.texture_handle {
                        Some(handle) => {
                            handle.set(color_image, Default::default());
                        }
                        None => {
                            self.texture_handle = Some(ui.ctx().load_texture(
                                "webcam",
                                color_image,
                                Default::default(),
                            ));
                        }
                    }

                    if let Some(ref handle) = self.texture_handle {
                        ui.add(egui::Image::new(handle).shrink_to_fit().corner_radius(10));
                    }
                } else {
                    ui.label("Waiting for camera frame...");
                }
            }
        });
    }
}

#[tokio::main]
async fn main() -> eframe::Result {
    println!("Camera initialized");
    let native_options = eframe::NativeOptions::default();
    eframe::run_native(
        "✂",
        native_options,
        Box::new(|cc| Ok(Box::new(MyApp::new(cc)))),
    )
}

async fn get_ocr(
    url: &str,
    image_buffer: ImageBuffer<Rgba<u8>, Vec<u8>>,
) -> Result<String, String> {
    let client = Client::new();
    let mut img_byte_arr = Vec::new();
    let mut cursor = std::io::Cursor::new(&mut img_byte_arr);
    image_buffer
        .write_to(&mut cursor, image::ImageFormat::Png)
        .map_err(|e| format!("Failed to encode image: {}", e))?;

    let form = multipart::Form::new().part(
        "image",
        multipart::Part::bytes(img_byte_arr)
            .file_name("image.png")
            .mime_str("image/png")
            .map_err(|e| format!("Failed to set mime type: {}", e))?,
    );
    let response = client
        .post(format!("{}/ocr", url))
        .multipart(form)
        .send()
        .await;
    let response_text = match response {
        Ok(response) => response.text().await.unwrap_or_else(|_| "".to_owned()),
        Err(_) => "".to_owned(),
    };
    Ok(response_text)
}
