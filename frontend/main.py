import sys
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QFrame, QScrollArea, QStackedWidget, QLineEdit
)

# ==========================================
# MANTIK KATMANI (Thread Yönetimi)
# ==========================================
try:
    from logic.analyzer import Analyzer
    from thread import RagWorker
except ImportError:
    class Analyzer:
        def process(self, q, u): return "Sistem Yanıtı: Analiz modülü aktif.", []


    class RagWorker(QThread):
        finished = pyqtSignal(str, list)

        def __init__(self, a, m, u): super().__init__()

        def run(self):
            self.finished.emit("Sistem hazır: Yanıtınız hazırlanıyor...", [])

# ==========================================
# MODERN GRİ TONLARI & ŞEFFAF MAVİ PALETİ
# ==========================================
PALETTE = {
    "MAIN_BG": "#D1D1D1",
    "PANEL_BG": "#BDBDBD",
    "USER_BUBBLE": "rgba(0, 102, 204, 0.45)",
    "AI_BUBBLE": "rgba(45, 55, 75, 0.75)",
    "BUBBLE_TEXT": "#FDFCF0",
    "OUTSIDE_TEXT": "#2B2B2B",
    "INPUT_BG": "#E8E8E8",
    "ACCENT": "#00509D"
}


# ==========================================
# ŞEFFAF ELİPS SOHBET BALONU
# ==========================================
class ChatBubble(QFrame):
    def __init__(self, text, time, is_user, name=""):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 6)
        layout.setSpacing(2)

        bg_color = PALETTE["USER_BUBBLE"] if is_user else PALETTE["AI_BUBBLE"]
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border-radius: 18px;
                padding: 4px 10px;
                margin: 2px;
                border: 1px solid rgba(255, 255, 255, 0.12);
            }}
        """)

        if name:
            name_label = QLabel(name)
            name_label.setStyleSheet(
                f"color: {PALETTE['BUBBLE_TEXT']}; font-weight: bold; font-size: 14px; background: transparent;")
            layout.addWidget(name_label)

        content_label = QLabel(text)
        content_label.setWordWrap(True)
        content_label.setStyleSheet(
            f"color: {PALETTE['BUBBLE_TEXT']}; font-size: 21px; background: transparent; border: none;")
        layout.addWidget(content_label)

        time_label = QLabel(time)
        time_label.setAlignment(Qt.AlignRight)
        time_label.setStyleSheet(
            f"color: {PALETTE['BUBBLE_TEXT']}; font-size: 10px; background: transparent; opacity: 0.6;")
        layout.addWidget(time_label)
        self.setFixedWidth(400)


# ==========================================
# GİRİŞ EKRANI (Login Page)
# ==========================================
class LoginPage(QWidget):
    login_successful = pyqtSignal(str)  # Giriş başarılı olduğunda ismi gönderir

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Giriş Kartı
        card = QFrame()
        card.setFixedWidth(400)
        card.setStyleSheet(f"background-color: {PALETTE['PANEL_BG']}; border-radius: 30px;")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(15)

        title = QLabel("MevzuSağlık AI")
        title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {PALETTE['ACCENT']};")
        title.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title)

        subtitle = QLabel("Lütfen giriş yapın")
        subtitle.setStyleSheet(f"color: {PALETTE['OUTSIDE_TEXT']}; font-size: 14px;")
        subtitle.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(subtitle)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Kullanıcı Adı")
        self.style_input(self.username)
        card_layout.addWidget(self.username)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Şifre")
        self.password.setEchoMode(QLineEdit.Password)
        self.style_input(self.password)
        card_layout.addWidget(self.password)

        self.login_btn = QPushButton("Giriş Yap")
        self.login_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.login_btn.setFixedHeight(50)
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PALETTE['ACCENT']};
                color: white;
                border-radius: 15px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #003D7A; }}
        """)
        self.login_btn.clicked.connect(self.handle_login)
        card_layout.addWidget(self.login_btn)

        layout.addWidget(card)

    def style_input(self, widget):
        widget.setFixedHeight(45)
        widget.setStyleSheet(f"""
            background-color: {PALETTE['INPUT_BG']};
            border-radius: 10px;
            padding: 5px 15px;
            font-size: 16px;
            color: black;
            border: 1px solid rgba(0,0,0,0.1);
        """)

    def handle_login(self):
        user = self.username.text().strip()
        pw = self.password.text().strip()
        if user and pw:  # Gerçek bir sistemde burada şifre kontrolü yapılır
            self.login_successful.emit(user)


# ==========================================
# CHAT EKRANI (Senin Hazırladığın Yapı)
# ==========================================
class ChatPage(QWidget):
    def __init__(self, analyzer):
        super().__init__()
        self.analyzer = analyzer
        self.active_threads = []
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # ========= SOL PANEL =========
        left_panel = QFrame()
        left_panel.setFixedWidth(240)
        left_panel.setStyleSheet(f"background-color: {PALETTE['PANEL_BG']}; border-radius: 20px; margin: 5px;")
        left_layout = QVBoxLayout(left_panel)

        logo = QLabel("MevzuSağlık")
        logo.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {PALETTE['ACCENT']}; margin: 5px;")
        left_layout.addWidget(logo)

        self.user_name_input = QTextEdit()
        self.user_name_input.setPlaceholderText("İsim...")
        self.user_name_input.setFixedHeight(45)
        self.user_name_input.setStyleSheet(
            f"background-color: {PALETTE['INPUT_BG']}; border-radius: 12px; padding: 8px; font-size: 16px; color: black;")
        left_layout.addWidget(self.user_name_input)
        left_layout.addStretch()

        # ========= ORTA PANEL =========
        center_container = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")
        self.scroll_area.verticalScrollBar().setStyleSheet(
            f"QScrollBar:vertical {{ border: none; background: transparent; width: 8px; }} QScrollBar::handle:vertical {{ background: {PALETTE['PANEL_BG']}; border-radius: 4px; }}")

        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(10)

        self.scroll_area.setWidget(self.chat_content)
        center_container.addWidget(self.scroll_area)

        input_row = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setFixedHeight(65)
        self.message_input.setPlaceholderText("Mesajınızı yazın...")
        self.message_input.setStyleSheet(
            f"background-color: {PALETTE['INPUT_BG']}; border-radius: 20px; padding: 12px; font-size: 18px; color: black;")
        input_row.addWidget(self.message_input)

        self.send_button = QPushButton("→")
        self.send_button.setFixedSize(65, 65)
        self.send_button.setStyleSheet(
            f"background-color: {PALETTE['ACCENT']}; color: white; border-radius: 32px; font-size: 26px;")
        self.send_button.clicked.connect(self.handle_send)
        input_row.addWidget(self.send_button)

        center_container.addLayout(input_row)
        main_layout.addWidget(left_panel)
        main_layout.addLayout(center_container, stretch=1)

    def set_user(self, name):
        self.user_name_input.setPlainText(name)

    def handle_send(self):
        msg = self.message_input.toPlainText().strip()
        user = self.user_name_input.toPlainText().strip()
        if not msg or not user: return
        self.add_message_bubble(msg, user, True)
        self.message_input.clear()

        worker = RagWorker(self.analyzer, msg, user)
        self.active_threads.append(worker)
        worker.finished.connect(lambda ans, src: self.add_message_bubble(ans, "MevzuSağlık AI", False))
        worker.finished.connect(lambda: self.active_threads.remove(worker) if worker in self.active_threads else None)
        worker.start()

    def add_message_bubble(self, text, name, is_user):
        time_str = datetime.now().strftime("%H:%M")
        bubble = ChatBubble(text, time_str, is_user, name)
        row = QHBoxLayout()
        if is_user:
            row.addStretch();
            row.addWidget(bubble)
        else:
            row.addWidget(bubble);
            row.addStretch()
        self.chat_layout.addLayout(row)
        QTimer.singleShot(100, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())


# ==========================================
# ANA PENCERE (Kontrolcü)
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MevzuSağlık AI")
        self.resize(1150, 850)
        self.analyzer = Analyzer()

        self.setStyleSheet(f"QMainWindow {{ background-color: {PALETTE['MAIN_BG']}; }}")

        # Stacked Widget ile sayfaları yönetiyoruz
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.login_page = LoginPage()
        self.chat_page = ChatPage(self.analyzer)

        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.chat_page)

        # Sinyal Bağlantısı
        self.login_page.login_successful.connect(self.switch_to_chat)

    def switch_to_chat(self, username):
        self.chat_page.set_user(username)
        self.stacked_widget.setCurrentIndex(1)  # Chat sayfasına geç


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())