import gradio as gr
import requests
import os
from typing import List

TENANT_API_KEY = os.environ.get("TENANT_API_KEY", "")
HEADERS = {"X-API-Key": TENANT_API_KEY}
# Backend URL
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


# --- YARDIMCI FONKSİYONLAR ---

def format_to_messages(messages_list):
    """Backend'den gelen mesaj listesini Gradio chatbot formatına çevirir"""
    formatted = []
    # Mesajları sender_type'a göre eşleştir (human, ai, human, ai...)
    # Gradio [(user, bot), (user, bot)] formatı bekler
    temp_user = None
    for msg in messages_list:
        content = msg.get("content", "")
        sender = msg.get("sender", "human")
        
        if sender == "human":
            temp_user = content
        else:
            if temp_user is not None:
                formatted.append((temp_user, content))
                temp_user = None
            else:
                # Eğer AI mesajı tek başına geldse (beklenmez ama güvenlik için)
                formatted.append((None, content))
    
    # Eğer en son bir user mesajı kaldıysa ve yanıtı yoksa
    if temp_user is not None:
        formatted.append((temp_user, None))
        
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
        if res.status_code == 200:
            sessions = res.json()
            # Oturumları (Görünen İsim, UUID) formatına çevir
            return [(f"📅 {s['created_at'][:16]} - {s['session_uuid'][:8]}", s['session_uuid']) for s in sessions]
        return []
    except:
        return []


def start_new_session(uname):
    """Yeni bir oturum başlatır ve arayüzü hazırlar"""
    sess = create_new_session(uname)
    new_sid = sess.get("session_uuid") if sess else None
    old_sessions = get_user_sessions(uname)
    return new_sid, [], gr.update(choices=old_sessions, value=new_sid)


def get_session_history(session_uuid):
    if not session_uuid: return []
    try:
        res = requests.get(f"{BACKEND_URL}/history/{session_uuid}", timeout=10)
        if res.status_code == 200:
            data = res.json()
            if not data or not isinstance(data, list):
                return []
            
            # Backend'den gelen format: [{ "messages": [...] }]
            raw_history = data[0].get("messages", [])
            return format_to_messages(raw_history)
        return []
    except Exception as e:
        print(f"Geçmiş çekme hatası: {e}")
        return []


def process_question(message, user_name, session_uuid, user_code="Anonymous"):
    if not session_uuid: return "⚠️ Önce bir sohbet seçin."
    try:
        res = requests.post(f"{BACKEND_URL}/chat",
                            json={"message": message, "user_name": user_name, "session_uuid": session_uuid, "user_id": user_code},
                            headers=HEADERS, timeout=120)
        
        if res.status_code == 200:
            return res.json().get("response", "⚠️ Cevap alınamadı.")
            
        if res.status_code == 429:
            return "⚠️ Günlük limitinize ulaştınız. Lütfen planınızı yükseltin."
        if res.status_code == 403:
            return "🔒 Erişim reddedildi. API anahtarınızı kontrol edin."

        return f"❌ Hata: {res.status_code} - {res.text}"
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
/* Sol paneldeki oturum listesi için özel stil */
.session-list { background: #ffffff !important; border: none !important; }
"""

with gr.Blocks(title="MevzuSağlık AI", theme=gr.themes.Soft(primary_hue="red"), css=custom_css) as demo:
    u_name = gr.State("Misafir")
    u_code = gr.State("Anonymous")
    s_uuid = gr.State(None)

    # GİRİŞ EKRANI
    with gr.Column(visible=True, elem_classes="login-card") as login_box:
        gr.Markdown("<center><h1>⚕️ MevzuSağlık AI</h1><p>Dijital Mevzuat Asistanı</p></center>")
        name_in = gr.Textbox(label="Ad Soyad", placeholder="Adınızı yazın...", lines=1)
        code_in = gr.Textbox(label="Araştırma Kodu (Opsiyonel)", placeholder="Size verilen kodu yazın...", lines=1)
        login_btn = gr.Button("🚀 Giriş Yap", variant="primary")

    # ANA EKRAN
    with gr.Row(visible=False) as main_box:
        # SOL PANEL
        with gr.Column(scale=1, min_width=300):
            gr.Markdown("### 👤 Profil")
            u_info = gr.Markdown("**Kullanıcı:** -")
            u_code_info = gr.Markdown("**Kod:** -")
            new_btn = gr.Button("➕ Yeni Sohbet Başlat", variant="primary")
            gr.Markdown("---")
            gr.Markdown("### 🕒 Eski Sohbetleriniz")
            # Dropdown yerine Radio (List) kullanarak alt alta dizilmesini sağladık
            session_list = gr.Radio(label="Seçili Oturum", choices=[], interactive=True, elem_classes="session-list")
            gr.Markdown("---")
            up_btn = gr.UploadButton("📤 Mevzuat Yükle", file_count="multiple")
            up_status = gr.Textbox(label="Yükleme Durumu", interactive=False)
            logout_btn = gr.Button("🚪 Güvenli Çıkış", size="sm", variant="stop")

        # SAĞ PANEL
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(height=650, show_label=False, elem_classes="chat-area")
            with gr.Row():
                txt_in = gr.Textbox(placeholder="Mevzuat hakkında sorunuzu yazın...", scale=9, container=False)
                send_btn = gr.Button("✈️", scale=1, variant="primary")


    # --- ETKİLEŞİM ---

    def do_login(name, code):
        name = name.strip() or "Misafir"
        code = code.strip() or "Anonymous"
        # Giriş yapınca yeni bir temiz oturum oluştur
        sid, hist, session_update = start_new_session(name)
        return {
            login_box: gr.update(visible=False),
            main_box: gr.update(visible=True),
            u_name: name,
            u_code: code,
            s_uuid: sid,
            u_info: f"**Kullanıcı:** {name}",
            u_code_info: f"**Kod:** {code}",
            session_list: session_update,
            chatbot: hist
        }

    def do_logout():
        return {
            login_box: gr.update(visible=True),
            main_box: gr.update(visible=False),
            u_name: "Misafir",
            u_code: "Anonymous",
            s_uuid: None,
            chatbot: [],
            name_in: "",
            code_in: ""
        }

    def do_new_chat(uname):
        sid, hist, session_update = start_new_session(uname)
        return sid, hist, session_update

    def do_chat(msg, history, sid, uname, ucode):
        if not msg.strip(): return history, ""
        # Backend yanıtı
        ans = process_question(msg, uname, sid, ucode)
        history.append((msg, ans))
        return history, ""

    def do_session_change(sid):
        return sid, get_session_history(sid)


    login_btn.click(do_login, [name_in, code_in], [login_box, main_box, u_name, u_code, s_uuid, u_info, u_code_info, session_list, chatbot])
    
    # Oturum listesinden birine tıklandığında
    session_list.change(do_session_change, session_list, [s_uuid, chatbot])
    
    # Yeni sohbet butonu
    new_btn.click(do_new_chat, [u_name], [s_uuid, chatbot, session_list])
    
    up_btn.upload(upload_documents, up_btn, up_status)

    send_btn.click(do_chat, [txt_in, chatbot, s_uuid, u_name, u_code], [chatbot, txt_in])
    txt_in.submit(do_chat, [txt_in, chatbot, s_uuid, u_name, u_code], [chatbot, txt_in])
    
    logout_btn.click(do_logout, None, [login_box, main_box, u_name, u_code, s_uuid, chatbot, name_in, code_in])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.queue().launch(server_name="0.0.0.0", server_port=port)