# app.py - MevzuSağlık Gradio Frontend (Güncel Versiyon)
import gradio as gr
import requests
from typing import List

BACKEND_URL = "https://mevzusaglik.onrender.com"


# --- BACKEND FONKSİYONLARI ---

def create_new_session(user_name):
    try:
        res = requests.post(f"{BACKEND_URL}/session/create_session", json={"user_name": user_name}, timeout=10)
        return res.json() if res.status_code == 200 else None
    except:
        return None


def get_user_sessions(user_name):
    """Kullanıcının eski oturumlarını listeler"""
    try:
        res = requests.get(f"{BACKEND_URL}/session/user_sessions/{user_name}", timeout=10)
        if res.status_code == 200:
            # Backend'in bir liste döndüğünü varsayıyoruz: ["uuid1", "uuid2"]
            return res.json().get("sessions", [])
        return []
    except:
        return []


def get_session_history(session_uuid):
    """Seçilen oturumun mesaj geçmişini getirir"""
    try:
        res = requests.get(f"{BACKEND_URL}/session/history/{session_uuid}", timeout=10)
        if res.status_code == 200:
            # Backend'den gelen veriyi Gradio formatına (role/content) çeviriyoruz
            return res.json().get("history", [])
        return []
    except:
        return []


def process_question(message, user_name, session_uuid):
    if not session_uuid:
        return "Önce yeni sohbet başlatın veya geçmişten bir sohbet seçin."
    try:
        res = requests.post(f"{BACKEND_URL}/search/ask", json={
            "query": message,
            "user_name": user_name,
            "session_uuid": session_uuid
        }, timeout=120)
        if res.status_code == 200:
            data = res.json()
            answer = data.get("answer", "Cevap yok")
            sources = "\n".join(data.get("sources", []))
            if sources:
                answer += f"\n\nKaynaklar:\n{sources}"
            return answer
        return f"Sunucu hatası ({res.status_code})"
    except Exception as e:
        return f"Bağlantı hatası: {str(e)}"


def upload_documents(files: List):
    if not files:
        return "Dosya seçilmedi."
    try:
        prepared = []
        for f in files:
            file_content = open(f.name, "rb").read()
            prepared.append(("files", (f.name, file_content, "application/octet-stream")))
        res = requests.post(f"{BACKEND_URL}/add_documents/add", files=prepared)
        return res.json().get("message", "Yükleme başarılı") if res.status_code == 200 else f"Hata: {res.text}"
    except Exception as e:
        return f"Yükleme hatası: {str(e)}"


# --- GRADIO ARAYÜZÜ ---

with gr.Blocks(title="MevzuSağlık AI", theme=gr.themes.Soft(primary_hue="red")) as demo:
    gr.Markdown("# MevzuSağlık AI\nSağlık Çalışanları İçin Mevzuat Sorgulama")

    user_name = gr.State("Misafir")
    session_uuid = gr.State(None)

    with gr.Row(visible=True) as login_screen:
        with gr.Column():
            gr.Markdown("### Giriş Yap")
            name_input = gr.Textbox(label="Kullanıcı Adı", placeholder="Adınızı yazın...")
            login_button = gr.Button("Sisteme Gir", variant="primary")

    with gr.Row(visible=False) as main_screen:
        # SOL MENÜ
        with gr.Column(scale=1, min_width=250):
            gr.Markdown("### İşlemler")
            new_chat_btn = gr.Button("➕ Yeni Sohbet", variant="secondary")

            gr.Markdown("---")
            gr.Markdown("### Geçmiş Sohbetler")
            session_dropdown = gr.Dropdown(label="Oturum Seçin", choices=[], interactive=True)
            refresh_btn = gr.Button("🔄 Listeyi Yenile", size="sm")

            gr.Markdown("---")
            upload_files = gr.UploadButton("📁 Belge Yükle", file_count="multiple", file_types=[".pdf", ".docx", ".txt"])
            upload_result = gr.Textbox(label="Durum", interactive=False)
            logout_btn = gr.Button("Çıkış Yap")

        # SAĞ CHAT ALANI
        with gr.Column(scale=4):
            chat = gr.Chatbot(height=550, show_label=False, type="messages")
            with gr.Row():
                msg = gr.Textbox(placeholder="Mevzuat hakkında sorunuzu yazın...", show_label=False, scale=9)
                send = gr.Button("Gönder", scale=1)


    # --- ETKİLEŞİM MANTIĞI ---

    def login(name):
        if not name: return [gr.update()] * 5
        sess = create_new_session(name)
        old_sess = get_user_sessions(name)
        sid = sess.get("session_uuid") if sess else None
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            name,
            sid,
            gr.update(choices=old_sess, value=sid)
        )


    def change_session(sid):
        history = get_session_history(sid)
        return sid, history


    def start_new_chat(uname):
        sess = create_new_session(uname)
        sid = sess.get("session_uuid") if sess else None
        old_sess = get_user_sessions(uname)
        return sid, [], gr.update(choices=old_sess, value=sid)


    def handle_response(message, history, sid, uname):
        if not message: return history, ""
        # Kullanıcı mesajını ekle
        history.append({"role": "user", "content": message})
        # Yanıtı al
        cevap = process_question(message, uname, sid)
        # Asistan yanıtını ekle
        history.append({"role": "assistant", "content": cevap})
        return history, ""


    def refresh_list(uname):
        old_sess = get_user_sessions(uname)
        return gr.update(choices=old_sess)


    # Buton Tıklamaları
    login_button.click(login, name_input, [login_screen, main_screen, user_name, session_uuid, session_dropdown])

    session_dropdown.change(change_session, session_dropdown, [session_uuid, chat])

    new_chat_btn.click(start_new_chat, user_name, [session_uuid, chat, session_dropdown])

    refresh_btn.click(refresh_list, user_name, session_dropdown)

    upload_files.upload(upload_documents, upload_files, upload_result)

    send.click(handle_response, [msg, chat, session_uuid, user_name], [chat, msg])
    msg.submit(handle_response, [msg, chat, session_uuid, user_name], [chat, msg])

    logout_btn.click(lambda: [gr.update(visible=True), gr.update(visible=False), "Misafir", None, []],
                     None, [login_screen, main_screen, user_name, session_uuid, chat])

demo.queue(max_size=20).launch(server_name="0.0.0.0", server_port=7860)