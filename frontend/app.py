import gradio as gr
import requests
import os
from typing import List

# Backend URL - Cloudflare Worker üzerinden domain'imizde
BACKEND_URL = os.environ.get("BACKEND_URL", "https://mevzusaglik.com.tr")

# Oturum durumu (JWT + tenant API key)
current_access_token = ""
current_api_key = ""


def auth_headers(include_json: bool = False) -> dict:
    """Backend'in beklediği Authorization Bearer + isteğe bağlı X-API-Key."""
    h = {}
    if current_access_token:
        h["Authorization"] = f"Bearer {current_access_token}"
    if current_api_key:
        h["X-API-Key"] = current_api_key
    if include_json:
        h["Content-Type"] = "application/json"
    return h


def clear_auth():
    global current_access_token, current_api_key
    current_access_token = ""
    current_api_key = ""


# --- YARDIMCI FONKSİYONLAR ---

def format_to_messages(messages_list):
    """Backend'den gelen mesaj listesini Gradio chatbot formatına çevirir"""
    formatted = []
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
                formatted.append((None, content))

    if temp_user is not None:
        formatted.append((temp_user, None))

    return formatted


def fetch_user_plan() -> str:
    """Backend'deki gerçek planı döndürür (free / pro / enterprise)."""
    try:
        res = requests.get(
            f"{BACKEND_URL}/session/user_plan",
            headers=auth_headers(),
            timeout=10,
        )
        if res.status_code == 200:
            plan = (res.json() or {}).get("plan") or "free"
            # Eski "unlimited" adı varsa enterprise'a normalize et
            if plan == "unlimited":
                return "enterprise"
            return plan
    except Exception as e:
        print(f"Plan alma hatası: {e}")
    return "free"


# --- BACKEND İSTEKLERİ ---

def create_new_session(user_name):
    try:
        res = requests.post(
            f"{BACKEND_URL}/session/create_session",
            json={"user_name": user_name},
            headers=auth_headers(include_json=True),
            timeout=15,
        )
        return res.json() if res.status_code == 200 else None
    except Exception as e:
        print(f"create_new_session hatası: {e}")
        return None


def get_user_sessions(user_name):
    try:
        res = requests.get(
            f"{BACKEND_URL}/session/sessions",
            headers=auth_headers(),
            timeout=10,
        )
        if res.status_code == 200:
            sessions = res.json()
            return [
                (f"💬 {s.get('title', 'Yeni Sohbet')}", s["session_uuid"])
                for s in sessions
            ]
        return []
    except Exception:
        return []


def start_new_session(uname):
    """Yeni bir oturum başlatır ve arayüzü hazırlar"""
    sess = create_new_session(uname)
    new_sid = sess.get("session_uuid") if sess else None
    old_sessions = get_user_sessions(uname)
    return new_sid, [], gr.update(choices=old_sessions, value=new_sid)


def get_session_history(session_uuid):
    if not session_uuid:
        return []
    try:
        res = requests.get(
            f"{BACKEND_URL}/history/{session_uuid}",
            headers=auth_headers(),
            timeout=10,
        )
        if res.status_code == 200:
            data = res.json()
            if not data or not isinstance(data, list):
                return []
            raw_history = data[0].get("messages", [])
            return format_to_messages(raw_history)
        return []
    except Exception as e:
        print(f"Geçmiş çekme hatası: {e}")
        return []


def process_question(message, user_name, session_uuid, user_code="Anonymous"):
    if not session_uuid:
        return "⚠️ Önce bir sohbet seçin."
    if not current_access_token:
        return "🔒 Oturum yok. Lütfen tekrar giriş yapın."
    try:
        res = requests.post(
            f"{BACKEND_URL}/search/chat",
            json={
                "message": message,
                "user_name": user_name,
                "session_uuid": session_uuid,
                "user_id": user_code,
            },
            headers=auth_headers(include_json=True),
            timeout=120,
        )

        if res.status_code == 200:
            return res.json().get("response", "⚠️ Cevap alınamadı.")
        if res.status_code == 401:
            return "🔒 Oturum süresi doldu. Lütfen tekrar giriş yapın."
        if res.status_code == 429:
            return "⚠️ Günlük limitinize ulaştınız. Lütfen planınızı yükseltin."
        if res.status_code == 403:
            return "🔒 Erişim reddedildi."

        return f"❌ Hata: {res.status_code} - {res.text}"
    except Exception as e:
        return f"📡 Bağlantı Hatası: {str(e)}"


def upload_documents(files: List):
    if not files:
        return "❌ Dosya yok."
    if not current_access_token:
        return "🔒 Oturum yok. Lütfen tekrar giriş yapın."
    try:
        prepared = []
        for f in files:
            with open(f.name, "rb") as file_obj:
                content = file_obj.read()
            prepared.append(
                ("files", (os.path.basename(f.name), content, "application/octet-stream"))
            )
        # Multipart için Content-Type elle set edilmez
        res = requests.post(
            f"{BACKEND_URL}/add_documents/add",
            files=prepared,
            headers=auth_headers(),
            timeout=120,
        )
        if res.status_code == 200:
            return "✅ " + res.json().get("message", "Başarılı")
        if res.status_code == 403:
            return "❌ Ücretsiz planda belge yükleyemezsiniz veya yetkiniz yok."
        return f"❌ Hata: {res.text}"
    except Exception as e:
        return f"❌ Hata: {str(e)}"


# --- ARAYÜZ TASARIMI ---

custom_css = """
.gradio-container { background-color: #f4f7f6; font-family: 'Segoe UI', sans-serif; }
.login-card { max-width: 450px !important; margin: 80px auto !important; padding: 30px; border-radius: 20px; background: white; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
.chat-area { border-radius: 15px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.05); background: white !important; }
.session-list { background: #ffffff !important; border: none !important; }
"""

with gr.Blocks(title="MevzuSağlık AI", theme=gr.themes.Soft(primary_hue="red"), css=custom_css) as demo:
    u_name = gr.State("Misafir")
    u_code = gr.State("")
    u_plan = gr.State("free")
    s_uuid = gr.State(None)

    # GİRİŞ EKRANI — gerçek auth (username + password)
    with gr.Column(visible=True, elem_classes="login-card") as login_box:
        gr.Markdown("<center><h1>⚕️ MevzuSağlık AI</h1><p>Dijital Mevzuat Asistanı</p></center>")
        name_in = gr.Textbox(label="Kullanıcı Adı", placeholder="Kullanıcı adınız...", lines=1)
        code_in = gr.Textbox(label="Parola", placeholder="Parolanız...", type="password", lines=1)
        login_status = gr.Markdown("")
        login_btn = gr.Button("🚀 Giriş Yap", variant="primary")

    # ANA EKRAN
    with gr.Row(visible=False) as main_box:
        with gr.Column(scale=1, min_width=300):
            gr.Markdown("### 👤 Profil")
            u_info = gr.Markdown("**Kullanıcı:** -")
            u_code_info = gr.Markdown("**Plan:** -")
            new_btn = gr.Button("➕ Yeni Sohbet Başlat", variant="primary")
            gr.Markdown("---")
            gr.Markdown("### 🕒 Eski Sohbetleriniz")
            session_list = gr.Radio(
                label="Seçili Oturum",
                choices=[],
                interactive=True,
                elem_classes="session-list",
            )
            gr.Markdown("---")

            with gr.Column() as upload_section:
                up_btn = gr.UploadButton("📤 Mevzuat Yükle", file_count="multiple", visible=True)
                upgrade_msg = gr.Markdown("", visible=False)
                up_status = gr.Textbox(label="Yükleme Durumu", interactive=False)
            gr.Markdown("---")
            logout_btn = gr.Button("🚪 Güvenli Çıkış", size="sm", variant="stop")

        with gr.Column(scale=4):
            chatbot = gr.Chatbot(height=650, show_label=False, elem_classes="chat-area")
            with gr.Row():
                txt_in = gr.Textbox(
                    placeholder="Mevzuat hakkında sorunuzu yazın...",
                    scale=9,
                    container=False,
                )
                send_btn = gr.Button("✈️", scale=1, variant="primary")

    # --- ETKİLEŞİM ---

    def do_login(name, password):
        global current_access_token, current_api_key

        name = (name or "").strip()
        password = password or ""

        if not name or not password:
            return {
                login_status: "❌ Kullanıcı adı ve parola zorunludur.",
                login_box: gr.update(visible=True),
                main_box: gr.update(visible=False),
            }

        try:
            res = requests.post(
                f"{BACKEND_URL}/auth/login",
                json={"user_name": name, "password": password},
                timeout=15,
            )
        except Exception as e:
            return {
                login_status: f"📡 Bağlantı hatası: {e}",
                login_box: gr.update(visible=True),
                main_box: gr.update(visible=False),
            }

        if res.status_code != 200:
            detail = ""
            try:
                detail = res.json().get("detail", res.text)
            except Exception:
                detail = res.text
            return {
                login_status: f"❌ Giriş başarısız: {detail}",
                login_box: gr.update(visible=True),
                main_box: gr.update(visible=False),
            }

        data = res.json()
        current_access_token = data.get("access_token") or ""
        current_api_key = data.get("api_key") or ""
        sid = data.get("session_uuid")
        display_name = data.get("user_name") or name

        if not current_access_token:
            clear_auth()
            return {
                login_status: "❌ Sunucu access_token döndürmedi.",
                login_box: gr.update(visible=True),
                main_box: gr.update(visible=False),
            }

        plan = fetch_user_plan()
        old_sessions = get_user_sessions(display_name)
        hist = get_session_history(sid) if sid else []

        upload_visible = plan != "free"
        upgrade_text = (
            "⚠️ **Ücretsiz planda belge yükleyemezsiniz.**\n\n"
            "[Pro plana yükselt](https://mevzusaglik.com.tr/billing/checkout?plan=pro)"
            if plan == "free"
            else ""
        )

        return {
            login_status: "",
            login_box: gr.update(visible=False),
            main_box: gr.update(visible=True),
            u_name: display_name,
            u_code: display_name,
            u_plan: plan,
            s_uuid: sid,
            u_info: f"**Kullanıcı:** {display_name}",
            u_code_info: f"**Plan:** {plan}",
            session_list: gr.update(choices=old_sessions, value=sid),
            chatbot: hist,
            up_btn: gr.update(visible=upload_visible),
            upgrade_msg: gr.update(value=upgrade_text, visible=plan == "free"),
        }

    def do_logout():
        # Sunucuda token'ı revoke et
        if current_access_token:
            try:
                requests.post(
                    f"{BACKEND_URL}/auth/logout",
                    headers=auth_headers(),
                    timeout=10,
                )
            except Exception as e:
                print(f"Logout hatası: {e}")

        clear_auth()
        return {
            login_box: gr.update(visible=True),
            main_box: gr.update(visible=False),
            u_name: "Misafir",
            u_code: "",
            u_plan: "free",
            s_uuid: None,
            chatbot: [],
            name_in: "",
            code_in: "",
            login_status: "",
            session_list: gr.update(choices=[], value=None),
            up_btn: gr.update(visible=True),
            upgrade_msg: gr.update(value="", visible=False),
        }

    def do_new_chat(uname):
        if not current_access_token:
            return None, [], gr.update(choices=[])
        sid, hist, session_update = start_new_session(uname)
        return sid, hist, session_update

    def do_chat(msg, history, sid, uname, ucode):
        if not msg.strip():
            return history, ""
        ans = process_question(msg, uname, sid, ucode)
        history.append((msg, ans))
        return history, ""

    def do_session_change(sid):
        return sid, get_session_history(sid)

    login_btn.click(
        do_login,
        [name_in, code_in],
        [
            login_status,
            login_box,
            main_box,
            u_name,
            u_code,
            u_plan,
            s_uuid,
            u_info,
            u_code_info,
            session_list,
            chatbot,
            up_btn,
            upgrade_msg,
        ],
    )

    session_list.change(do_session_change, session_list, [s_uuid, chatbot])
    new_btn.click(do_new_chat, [u_name], [s_uuid, chatbot, session_list])
    up_btn.upload(upload_documents, up_btn, up_status)
    send_btn.click(do_chat, [txt_in, chatbot, s_uuid, u_name, u_code], [chatbot, txt_in])
    txt_in.submit(do_chat, [txt_in, chatbot, s_uuid, u_name, u_code], [chatbot, txt_in])
    logout_btn.click(
        do_logout,
        None,
        [
            login_box,
            main_box,
            u_name,
            u_code,
            u_plan,
            s_uuid,
            chatbot,
            name_in,
            code_in,
            login_status,
            session_list,
            up_btn,
            upgrade_msg,
        ],
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.queue().launch(server_name="0.0.0.0", server_port=port)
