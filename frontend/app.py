# app.py - MevzuSağlık web arayüzü (Gradio ile, tek dosya)
import gradio as gr
import requests

# Backend'in Render URL'si (değiştirmene gerek yok)
BACKEND_URL = "https://mevzusaglik.onrender.com"

# Backend'e bağlanan basit fonksiyonlar
def create_new_session(user_name):
    try:
        res = requests.post(f"{BACKEND_URL}/session/create_session", json={"user_name": user_name})
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
        return "Sunucu hatası"
    except:
        return "Bağlantı hatası"

def upload_documents(files):
    if not files:
        return "Dosya seçilmedi"
    try:
        prepared = [("files", (f.name, f.read(), f.content_type)) for f in files]
        res = requests.post(f"{BACKEND_URL}/add_documents/add", files=prepared)
        if res.status_code == 200:
            return res.json().get("message", "Yükleme başarılı")
        return "Hata oluştu"
    except Exception as e:
        return f"Hata: {str(e)}"

# Gradio arayüzü (senin istediğin tasarım)
with gr.Blocks(title="MevzuSağlık", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# MevzuSağlık AI")

    user_name = gr.State("Misafir")
    session_uuid = gr.State(None)
    chat_history = gr.State([])

    # 1. Login ekranı
    with gr.Row(visible=True) as login_screen:
        with gr.Column():
            gr.Markdown("### Giriş Yap")
            name_input = gr.Textbox(label="Kullanıcı Adı")
            login_button = gr.Button("Giriş Yap")

    # 2. Ana ekran (giriş sonrası)
    with gr.Row(visible=False) as main_screen:
        # Sol menü
        with gr.Column(scale=1, min_width=220):
            gr.Markdown("**Menü**")
            new_chat = gr.Button("Yeni Sohbet")
            upload_files = gr.UploadButton("Belge Yükle 📎", file_count="multiple")
            upload_result = gr.Textbox(label="Yükleme Sonucu")
            logout = gr.Button("Çıkış")

        # Chat alanı
        with gr.Column(scale=4):
            chat = gr.Chatbot(height=500)
            msg = gr.Textbox(placeholder="Mesaj yaz...")
            send = gr.Button("Gönder")

    # Giriş yapınca ekran değiştir
    def login(name):
        sess = create_new_session(name)
        if sess:
            return gr.update(visible=False), gr.update(visible=True), name, sess.get("session_uuid"), []
        return gr.update(), gr.update(), "", None, []

    login_button.click(login, name_input, [login_screen, main_screen, user_name, session_uuid, chat_history])

    # Yeni sohbet
    def yeni_sohbet(uname):
        sess = create_new_session(uname)
        return sess.get("session_uuid") if sess else None, "Yeni sohbet başladı"

    new_chat.click(yeni_sohbet, user_name, [session_uuid, upload_result])

    # Dosya yükleme
    upload_files.upload(upload_documents, upload_files, upload_result)

    # Mesaj gönderme
    def gonder(mesaj, tarihce, sid, uname):
        if not mesaj:
            return tarihce
        cevap = process_question(mesaj, uname, sid)
        return tarihce + [[mesaj, cevap]]

    msg.submit(gonder, [msg, chat_history, session_uuid, user_name], chat)
    send.click(gonder, [msg, chat_history, session_uuid, user_name], chat).then(lambda: "", None, msg)

    # Çıkış
    def cikis():
        return gr.update(visible=True), gr.update(visible=False), "Misafir", None, []

    logout.click(cikis, None, [login_screen, main_screen, user_name, session_uuid, chat_history])

demo.launch(server_name="0.0.0.0", server_port=7860)