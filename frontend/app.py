# app.py - MevzuSağlık Gradio frontend (ayrı servis, tek dosya)
import gradio as gr
import requests
from typing import List

BACKEND_URL = "https://mevzusaglik.onrender.com"  # backend URL'in

def create_new_session(user_name):
    try:
        res = requests.post(f"{BACKEND_URL}/session/create_session", json={"user_name": user_name}, timeout=10)
        return res.json() if res.status_code == 200 else None
    except:
        return None

def process_question(message, user_name, session_uuid):
    if not session_uuid:
        return "Önce yeni sohbet başlatın."
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
            with open(f.name, "rb") as file_obj:
                prepared.append(("files", (f.name, file_obj.read(), f.content_type or "application/octet-stream")))
        res = requests.post(f"{BACKEND_URL}/add_documents/add", files=prepared)
        if res.status_code == 200:
            return res.json().get("message", "Yükleme başarılı")
        return f"Hata ({res.status_code}): {res.text}"
    except Exception as e:
        return f"Yükleme hatası: {str(e)}"

with gr.Blocks(title="MevzuSağlık AI", theme=gr.themes.Soft(primary_hue="red")) as demo:
    gr.Markdown("# MevzuSağlık AI\nSağlık Çalışanları İçin Mevzuat Sorgulama")

    user_name = gr.State("Misafir")
    session_uuid = gr.State(None)
    chat_history = gr.State([])

    with gr.Row(visible=True) as login_screen:
        with gr.Column():
            gr.Markdown("### Giriş Yap")
            name_input = gr.Textbox(label="Kullanıcı Adı")
            login_button = gr.Button("Giriş Yap")

    with gr.Row(visible=False) as main_screen:
        with gr.Column(scale=1, min_width=250):
            gr.Markdown("**Menü**")
            new_chat = gr.Button("Yeni Sohbet")
            upload_files = gr.UploadButton("Belge Yükle 📤", file_count="multiple", file_types=[".pdf", ".docx", ".txt"])
            upload_result = gr.Textbox(label="Yükleme Sonucu", interactive=False, lines=3)
            logout = gr.Button("Çıkış")

        with gr.Column(scale=4):
            chat = gr.Chatbot(height=500, show_label=False)
            with gr.Row():
                msg = gr.Textbox(placeholder="Mesaj yaz...")
                send = gr.Button("Gönder")

    def login(name):
        sess = create_new_session(name)
        return gr.update(visible=False), gr.update(visible=True), name, sess.get("session_uuid") if sess else None, []

    login_button.click(login, name_input, [login_screen, main_screen, user_name, session_uuid, chat_history])

    def yeni_sohbet(uname):
        sess = create_new_session(uname)
        return sess.get("session_uuid") if sess else None, "Yeni sohbet başladı"

    new_chat.click(yeni_sohbet, user_name, [session_uuid, upload_result])

    upload_files.upload(upload_documents, upload_files, upload_result)

    def gonder(mesaj, tarihce, sid, uname):
        if not mesaj:
            return tarihce
        cevap = process_question(mesaj, uname, sid)
        return tarihce + [[mesaj, cevap]]

    msg.submit(gonder, [msg, chat_history, session_uuid, user_name], chat)
    send.click(gonder, [msg, chat_history, session_uuid, user_name], chat).then(lambda: "", None, msg)

    def cikis():
        return gr.update(visible=True), gr.update(visible=False), "Misafir", None, []

    logout.click(cikis, None, [login_screen, main_screen, user_name, session_uuid, chat_history])

demo.queue(max_size=20).launch(server_name="0.0.0.0", server_port=7860)