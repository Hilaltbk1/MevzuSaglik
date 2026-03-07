# app.py - MevzuSağlık AI Frontend (Final Version)
import gradio as gr
import requests
import os
from typing import List

# Backend URL - Sonunda eğik çizgi (/) olmamasına dikkat edin
BACKEND_URL = "https://mevzusaglik.onrender.com"


# --- BACKEND FONKSİYONLARI ---

def create_new_session(user_name):
    try:
        res = requests.post(f"{BACKEND_URL}/session/create_session", json={"user_name": user_name}, timeout=15)
        return res.json() if res.status_code == 200 else None
    except Exception:
        return None


def get_user_sessions(user_name):
    """Kullanıcının eski oturum listesini çeker"""
    try:
        res = requests.get(f"{BACKEND_URL}/session/user_sessions/{user_name}", timeout=10)
        if res.status_code == 200:
            return res.json().get("sessions", [])
        return []
    except Exception:
        return []


def get_session_history(session_uuid):
    if not session_uuid: return []
    try:
        res = requests.get(f"{BACKEND_URL}/session/history/{session_uuid}", timeout=10)
        if res.status_code == 200:
            raw_history = res.json().get("history", [])
            formatted = []
            for item in raw_history:
                # Eğer item bir liste ise (eski format), sözlüğe çevir:
                if isinstance(item, list):
                    formatted.append({"role": "user", "content": item[0]})
                    formatted.append({"role": "assistant", "content": item[1]})
                else:
                    formatted.append(item)
            return formatted
        return []
    except:
        return []


def process_question(message, user_name, session_uuid):
    if not session_uuid:
        return "⚠️ Lütfen önce bir sohbet başlatın veya seçin."
    try:
        res = requests.post(f"{BACKEND_URL}/search/ask", json={
            "query": message,
            "user_name": user_name,
            "session_uuid": session_uuid
        }, timeout=120)
        if res.status_code == 200:
            data = res.json()
            answer = data.get("answer", "Yanıt alınamadı.")
            sources = data.get("sources", [])
            if sources:
                answer += f"\n\n---\n**📚 Kaynaklar:**\n" + "\n".join([f"• {s}" for s in sources])
            return answer
        return f"❌ Sunucu Hatası ({res.status_code})"
    except Exception as e:
        return f"📡 Bağlantı Hatası: {str(e)}"


def upload_documents(files: List):
    """Belge yükleme fonksiyonu (NamedString hatası için optimize edildi)"""
    if not files: return "❌ Dosya seçilmedi."
    try:
        prepared = []
        for f in files:
            # f.name geçici dosya yoludur.
            with open(f.name, "rb") as file_obj:
                content = file_obj.read()

            # Content-type hatası almamak için octet-stream kullanıyoruz
            file_name = os.path.basename(f.name)
            prepared.append(("files", (file_name, content, "application/octet-stream")))

        res = requests.post(f"{BACKEND_URL}/add_documents/add", files=prepared)
        return "✅ " + res.json().get("message", "Başarılı") if res.status_code == 200 else f"❌ Hata: {res.text}"
    except Exception as e:
        return f"❌ Yükleme Hatası: {str(e)}"


# --- TASARIM VE CSS ---

custom_css = """
.gradio-container { background-color: #f4f7f6; }
.login-card { 
    max-width: 500px !important; 
    margin: 100px auto !important; 
    padding: 30px; 
    border-radius: 20px; 
    background: white; 
    box-shadow: 0 10px 25px rgba(0,0,0,0.1); 
}
.sidebar { background: white; border-right: 1px solid #ddd; padding: 15px; border-radius: 15px; }
.chat-window { border-radius: 15px !important; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
footer { display: none !important; }
"""

# --- ARAYÜZ (Gradio Blocks) ---

with gr.Blocks(title="MevzuSağlık AI", theme=gr.themes.Soft(primary_hue="red"), css=custom_css) as demo:
    user_name = gr.State("Misafir")
    session_uuid = gr.State(None)

    # GİRİŞ EKRANI
    with gr.Column(visible=True, elem_classes="login-card") as login_screen:
        gr.Markdown("<center><h1>⚕️ MevzuSağlık AI</h1><p>Dijital Mevzuat Asistanı</p></center>")
        name_input = gr.Textbox(label="Kullanıcı Adı", placeholder="Lütfen isminizi giriniz...", lines=1)
        login_button = gr.Button("🚀 Giriş Yap", variant="primary")

    # ANA PANEL
    with gr.Row(visible=False) as main_screen:
        # SOL MENÜ
        with gr.Column(scale=1, min_width=280, elem_classes="sidebar"):
            gr.Markdown("### 👤 Profil")
            user_info = gr.Markdown("**Kullanıcı:** Misafir")

            new_chat_btn = gr.Button("➕ Yeni Sohbet Başlat", variant="secondary")

            gr.Markdown("---")
            gr.Markdown("### 🕒 Sohbet Geçmişi")
            session_dropdown = gr.Dropdown(label="Oturum Seçin", choices=[], interactive=True)
            refresh_btn = gr.Button("🔄 Listeyi Yenile", size="sm")

            gr.Markdown("---")
            upload_btn = gr.UploadButton("📤 Belge Yükle", file_count="multiple", variant="outline")
            upload_status = gr.Textbox(label="Dosya Durumu", interactive=False, placeholder="Yükleme bekleniyor...")

            logout_btn = gr.Button("🚪 Çıkış", variant="stop", size="sm")

        # SAĞ CHAT ALANI
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(height=650, show_label=False, type="messages", bubble_full_width=False,
                                 elem_classes="chat-window")
            with gr.Row():
                msg_input = gr.Textbox(placeholder="Sormak istediğiniz mevzuatı yazın...", show_label=False, scale=9,
                                       container=False)
                send_btn = gr.Button("✈️", scale=1, variant="primary")


    # --- ETKİLEŞİM MANTIĞI ---

    def handle_login(name):
        if not name or len(name.strip()) < 2:
            return {login_screen: gr.update(visible=True)}

        # Oturum oluştur ve geçmişi çek
        name = name.strip()
        sess = create_new_session(name)
        old_sessions = get_user_sessions(name)
        sid = sess.get("session_uuid") if sess else None

        return {
            login_screen: gr.update(visible=False),
            main_screen: gr.update(visible=True),
            user_name: name,
            session_uuid: sid,
            user_info: f"**Kullanıcı:** {name}",
            session_dropdown: gr.update(choices=old_sessions, value=sid),
            chatbot: []
        }


    def handle_session_change(sid):
        history = get_session_history(sid)
        return sid, history


    def handle_new_chat(uname):
        sess = create_new_session(uname)
        sid = sess.get("session_uuid") if sess else None
        old_sessions = get_user_sessions(uname)
        return sid, [], gr.update(choices=old_sessions, value=sid)


    def handle_chat(message, history, sid, uname):
        if not message.strip(): return history, ""

        # Kullanıcı mesajını ekrana bas
        history.append({"role": "user", "content": message})
        # Backend'den cevap al
        cevap = process_question(message, uname, sid)
        # Cevabı ekrana bas
        history.append({"role": "assistant", "content": cevap})

        return history, ""


    # Event Atamaları
    login_button.click(handle_login, name_input,
                       [login_screen, main_screen, user_name, session_uuid, user_info, session_dropdown, chatbot])

    session_dropdown.change(handle_session_change, session_dropdown, [session_uuid, chatbot])

    new_chat_btn.click(handle_new_chat, user_name, [session_uuid, chatbot, session_dropdown])

    refresh_btn.click(lambda uname: gr.update(choices=get_user_sessions(uname)), user_name, session_dropdown)

    upload_btn.upload(upload_documents, upload_btn, upload_status)

    send_btn.click(handle_chat, [msg_input, chatbot, session_uuid, user_name], [chatbot, msg_input])
    msg_input.submit(handle_chat, [msg_input, chatbot, session_uuid, user_name], [chatbot, msg_input])

    logout_btn.click(lambda: [gr.update(visible=True), gr.update(visible=False), "Misafir", None, []],
                     None, [login_screen, main_screen, user_name, session_uuid, chatbot])

# Render / Hugging Face Sunucu Başlatma
if __name__ == "__main__":
    # Render PORT çevre değişkenini kullanır, yoksa 7860
    app_port = int(os.environ.get("PORT", 7860))
    demo.queue().launch(server_name="0.0.0.0", server_port=app_port)