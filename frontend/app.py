import gradio as gr
import requests
import os
from typing import List

# Backend URL
BACKEND_URL = "https://mevzusaglik.onrender.com"


# --- YARDIMCI FONKSİYONLAR ---

def format_to_messages(raw_data):
    """Her türlü veriyi Gradio'nun mesaj formatına zorla dönüştürür"""
    formatted = []
    if not isinstance(raw_data, list):
        return []

    for item in raw_data:
        # Eğer veri zaten doğru formattaysa (dict): {"role": "...", "content": "..."}
        if isinstance(item, dict) and "content" in item:
            formatted.append(item)
        # Eğer veri eski formatta ise (list): ["soru", "cevap"]
        elif isinstance(item, list) and len(item) == 2:
            formatted.append({"role": "user", "content": str(item[0])})
            formatted.append({"role": "assistant", "content": str(item[1])})
    return formatted


# --- BACKEND İSTEKLERİ ---

def create_new_session(user_name):
    try:
        res = requests.post(f"{BACKEND_URL}/session/create_session", json={"user_name": user_name}, timeout=15)
        return res.json() if res.status_code == 200 else None
    except:
        return None


def get_user_sessions(user_name):
    try:
        res = requests.get(f"{BACKEND_URL}/session/user_sessions/{user_name}", timeout=10)
        return res.json().get("sessions", []) if res.status_code == 200 else []
    except:
        return []


def get_session_history(session_uuid):
    if not session_uuid: return []
    try:
        res = requests.get(f"{BACKEND_URL}/session/history/{session_uuid}", timeout=10)
        if res.status_code == 200:
            raw_history = res.json().get("history", [])
            return format_to_messages(raw_history)  # Korumalı dönüştürme
        return []
    except:
        return []


def process_question(message, user_name, session_uuid):
    if not session_uuid: return "⚠️ Önce bir sohbet seçin."
    try:
        res = requests.post(f"{BACKEND_URL}/search/ask", json={
            "query": message, "user_name": user_name, "session_uuid": session_uuid
        }, timeout=120)
        if res.status_code == 200:
            data = res.json()
            ans = data.get("answer", "Yanıt yok.")
            src = data.get("sources", [])
            if src: ans += f"\n\n**📚 Kaynaklar:**\n" + "\n".join([f"• {s}" for s in src])
            return ans
        return f"❌ Hata: {res.status_code}"
    except Exception as e:
        return f"📡 Bağlantı Hatası: {str(e)}"


def upload_documents(files: List):
    if not files: return "❌ Dosya yok."
    try:
        prepared = []
        for f in files:
            with open(f.name, "rb") as file_obj:
                content = file_obj.read()
            prepared.append(("files", (os.path.basename(f.name), content, "application/octet-stream")))
        res = requests.post(f"{BACKEND_URL}/add_documents/add", files=prepared)
        return "✅ " + res.json().get("message", "Başarılı") if res.status_code == 200 else f"❌ Hata: {res.text}"
    except Exception as e:
        return f"❌ Hata: {str(e)}"


# --- ARAYÜZ TASARIMI ---

custom_css = """
.gradio-container { background-color: #f4f7f6; font-family: 'Segoe UI', sans-serif; }
.login-card { max-width: 450px !important; margin: 80px auto !important; padding: 30px; border-radius: 20px; background: white; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
.chat-area { border-radius: 15px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.05); background: white !important; }
"""

with gr.Blocks(title="MevzuSağlık AI", theme=gr.themes.Soft(primary_hue="red"), css=custom_css) as demo:
    u_name = gr.State("Misafir")
    s_uuid = gr.State(None)

    # GİRİŞ EKRANI
    with gr.Column(visible=True, elem_classes="login-card") as login_box:
        gr.Markdown("<center><h1>⚕️ MevzuSağlık AI</h1><p>Dijital Mevzuat Asistanı</p></center>")
        name_in = gr.Textbox(label="Kullanıcı Adı", placeholder="İsminizi yazın...", lines=1)
        login_btn = gr.Button("🚀 Giriş Yap", variant="primary")

    # ANA EKRAN
    with gr.Row(visible=False) as main_box:
        # SOL PANEL
        with gr.Column(scale=1, min_width=280):
            gr.Markdown("### 👤 Menü")
            u_info = gr.Markdown("**Kullanıcı:** -")
            new_btn = gr.Button("➕ Yeni Sohbet", variant="secondary")
            gr.Markdown("---")
            gr.Markdown("### 🕒 Geçmiş")
            hist_drop = gr.Dropdown(label="Eski Oturumlar", choices=[], interactive=True)
            gr.Markdown("---")
            up_btn = gr.UploadButton("📤 Belge Yükle", file_count="multiple")
            up_status = gr.Textbox(label="Durum", interactive=False)
            logout_btn = gr.Button("🚪 Çıkış", size="sm", variant="stop")

        # SAĞ PANEL
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(height=650, type="messages", show_label=False, elem_classes="chat-area")
            with gr.Row():
                txt_in = gr.Textbox(placeholder="Mesajınızı buraya yazın...", scale=9, container=False)
                send_btn = gr.Button("✈️", scale=1, variant="primary")


    # --- ETKİLEŞİM ---

    def do_login(name):
        name = name.strip() or "Misafir"
        sess = create_new_session(name)
        old = get_user_sessions(name)
        sid = sess.get("session_uuid") if sess else None
        return {
            login_box: gr.update(visible=False),
            main_box: gr.update(visible=True),
            u_name: name,
            s_uuid: sid,
            u_info: f"**Kullanıcı:** {name}",
            hist_drop: gr.update(choices=old, value=sid),
            chatbot: []
        }


    def do_chat(msg, history, sid, uname):
        if not msg.strip(): return history, ""
        # Yeni mesajı ekle
        history.append({"role": "user", "content": msg})
        # Backend yanıtı
        ans = process_question(msg, uname, sid)
        history.append({"role": "assistant", "content": ans})
        return history, ""


    def do_session_change(sid):
        return sid, get_session_history(sid)


    login_btn.click(do_login, name_in, [login_box, main_box, u_name, s_uuid, u_info, hist_drop, chatbot])
    hist_drop.change(do_session_change, hist_drop, [s_uuid, chatbot])
    new_btn.click(lambda n: do_login(n), u_name, [login_box, main_box, u_name, s_uuid, u_info, hist_drop, chatbot])
    up_btn.upload(upload_documents, up_btn, up_status)

    send_btn.click(do_chat, [txt_in, chatbot, s_uuid, u_name], [chatbot, txt_in])
    txt_in.submit(do_chat, [txt_in, chatbot, s_uuid, u_name], [chatbot, txt_in])
    logout_btn.click(lambda: [gr.update(visible=True), gr.update(visible=False)], None, [login_box, main_box])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.queue().launch(server_name="0.0.0.0", server_port=port)