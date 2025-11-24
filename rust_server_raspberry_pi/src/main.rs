use actix_cors::Cors;
use actix_files as fs;
use actix_web::{App, HttpResponse, HttpServer, Responder, post};
use rustautogui;

fn type_on_keyboard(text: String) -> String {
    println!("typing {}", text);
    let rust_auto_gui = rustautogui::RustAutoGui::new(false).unwrap();
    let _ = rust_auto_gui.keyboard_input(&text);
    return format!("typed {}", text);
}

#[post("/keyboard")]
async fn keyboard_route(req_body: String) -> impl Responder {
    let response = type_on_keyboard(req_body);
    HttpResponse::Ok().body(response)
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    pretty_env_logger::init();
    HttpServer::new(|| {
        let cors = Cors::permissive();
        App::new()
            .wrap(cors)
            .service(keyboard_route)
            .service(fs::Files::new("/", "./static").index_file("index.html"))
    })
    .bind(("127.0.0.1", 3080))?
    .run()
    .await
}
