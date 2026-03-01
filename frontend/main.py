import sys, uuid, requests
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QFrame, QScrollArea, QListWidget,
    QStackedWidget, QListWidgetItem, QMessageBox
)

from rag_threads import RagWorker  # Aynı klasörde olduğu için doğrudan
from logic.analyzer import Analyzer  # logic klasörü altındaki dosyaya erişim
# ==========================================
# TASARIM PALETİ
# ==========================================
PALETTE = {
    "MAIN_BG": "#b5b5b5", "CARD_BG": "#dddddd", "USER_BUBBLE": "#363636",
    "AI_BUBBLE": "#800000", "INPUT_BG": "#dddddd", "ACCENT": "#800000",
    "LOGOUT": "#363636", "NEW_CHAT": "#363636", "TEXT_COLOR": "#800000"
}


class ChatBubble(QFrame):
    def __init__(self, text, time, is_user, name=""):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 10)

        bg = PALETTE["USER_BUBBLE"] if is_user else PALETTE["AI_BUBBLE"]
        self.setStyleSheet(f"background-color: {bg}; border-radius: 15px; margin: 2px;")

        n_lbl = QLabel(name)
        n_lbl.setStyleSheet("font-weight: bold; color: white; background: transparent; font-size: 11px;")
        layout.addWidget(n_lbl)

        c_lbl = QLabel(str(text))
        c_lbl.setWordWrap(True)
        c_lbl.setStyleSheet("color: white; font-size: 14px; background: transparent;")
        layout.addWidget(c_lbl)

        t_lbl = QLabel(time if time else "")
        t_lbl.setAlignment(Qt.AlignRight)
        t_lbl.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 9px; background: transparent;")
        layout.addWidget(t_lbl)
        self.setFixedWidth(450)


class MevzuSaglik(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MevzuSağlık AI - 2026")
        self.resize(1200, 800)
        self.setStyleSheet(f"background-color: {PALETTE['MAIN_BG']};")

        self.analyzer = Analyzer()
        self.current_session_uuid = None
        self.active_workers = []

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # BU FONKSİYONLAR AŞAĞIDA TANIMLI
        self.init_login_page()
        self.init_main_page()

    def init_login_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)

        card = QFrame()
        card.setFixedSize(400, 350)
        card.setStyleSheet("background: white; border-radius: 20px; border: 1px solid #E5E7EB;")
        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(30, 30, 30, 30)

        title = QLabel("MevzuSağlık AI")
        title.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {PALETTE['ACCENT']}; border: none;")
        vbox.addWidget(title, alignment=Qt.AlignCenter)

        self.login_input = QTextEdit()
        self.login_input.setPlaceholderText("Kullanıcı adınızı yazın...")
        self.login_input.setFixedHeight(45)
        self.login_input.setStyleSheet("border: 1px solid #D1D5DB; border-radius: 8px; padding: 10px; font-size: 14px;")
        vbox.addWidget(self.login_input)

        btn = QPushButton("Giriş Yap")
        btn.setFixedHeight(45)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"background: {PALETTE['ACCENT']}; color: white; border-radius: 8px; font-weight: bold;")
        btn.clicked.connect(self.login_action)
        vbox.addWidget(btn)

        layout.addWidget(card)
        self.stack.addWidget(page)

    def init_main_page(self):
        page = QWidget()
        main_layout = QHBoxLayout(page)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 1. SOL PANEL
        left_panel = QFrame()
        left_panel.setFixedWidth(260)
        left_panel.setStyleSheet("background: #800000; border-right: 1px solid #363636; border-radius: 0px;")
        l_lay = QVBoxLayout(left_panel)
        l_lay.setContentsMargins(15, 20, 15, 20)

        self.user_lbl = QLabel("Kullanıcı")
        self.user_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-bottom: 20px;")
        l_lay.addWidget(self.user_lbl)

        n_btn = QPushButton("➕ Yeni Sohbet")
        n_btn.setFixedHeight(40)
        n_btn.setCursor(Qt.PointingHandCursor)
        n_btn.clicked.connect(self.new_chat_action)
        n_btn.setStyleSheet(f"background: {PALETTE['NEW_CHAT']}; color: white; border-radius: 8px; font-weight: bold;")
        l_lay.addWidget(n_btn)

        h_btn = QPushButton("📜 Sohbet Geçmişi")
        h_btn.setFixedHeight(40)
        h_btn.setCursor(Qt.PointingHandCursor)
        h_btn.clicked.connect(self.view_history_action)
        h_btn.setStyleSheet("background: #363636; color: white; border-radius: 8px; margin-top: 10px;")
        l_lay.addWidget(h_btn)

        l_lay.addStretch()

        o_btn = QPushButton("🚪 Güvenli Çıkış")
        o_btn.setFixedHeight(40)
        o_btn.setCursor(Qt.PointingHandCursor)
        o_btn.clicked.connect(self.logout_action)
        o_btn.setStyleSheet(f"background: {PALETTE['LOGOUT']}; color: white; border-radius: 8px;")
        l_lay.addWidget(o_btn)

        # 2. ORTA PANEL (Chat)
        chat_area = QWidget()
        self.chat_container = QVBoxLayout(chat_area)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background: transparent;")

        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.chat_widget)

        self.input_widget = QFrame()
        self.input_widget.setFixedHeight(100)
        self.input_widget.setStyleSheet("background: white; border-top: 1px solid #E5E7EB;")
        i_row = QHBoxLayout(self.input_widget)

        self.msg_input = QTextEdit()
        self.msg_input.setPlaceholderText("Mesajınızı buraya yazın...")
        self.msg_input.setStyleSheet("border: 1px solid #D1D5DB; border-radius: 10px; padding: 10px;")

        self.send_btn = QPushButton("GÖNDER")
        self.send_btn.setFixedSize(100, 50)
        self.send_btn.setStyleSheet(
            f"background: {PALETTE['ACCENT']}; color: white; border-radius: 10px; font-weight: bold;")
        self.send_btn.clicked.connect(self.handle_send)

        i_row.addWidget(self.msg_input)
        i_row.addWidget(self.send_btn)

        self.chat_container.addWidget(self.scroll_area, 1)
        self.chat_container.addWidget(self.input_widget, 0)

        # 3. SAĞ PANEL (Geçmiş)
        self.hist_panel = QFrame()
        self.hist_panel.setFixedWidth(280)
        self.hist_panel.setStyleSheet("background: white; border-left: 1px solid #E5E7EB;")
        r_lay = QVBoxLayout(self.hist_panel)
        self.hist_list = QListWidget()
        self.hist_list.itemClicked.connect(self.load_history_session)
        r_lay.addWidget(QLabel("📜 Önceki Sohbetler", styleSheet="font-weight: bold; font-size: 15px; margin: 10px;"))
        r_lay.addWidget(self.hist_list)
        self.hist_panel.setVisible(False)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(chat_area, stretch=1)
        main_layout.addWidget(self.hist_panel)
        self.stack.addWidget(page)

    def login_action(self):
        user = self.login_input.toPlainText().strip()
        if user:
            self.user_lbl.setText(user)
            self.stack.setCurrentIndex(1)
            self.new_chat_action()

    def logout_action(self):
        self.nuke_chat_widget()
        self.stack.setCurrentIndex(0)

    def new_chat_action(self):
        self.nuke_chat_widget()
        try:
            new_sess = self.analyzer.create_new_session(self.user_lbl.text())
            if new_sess and "session_uuid" in new_sess:
                self.current_session_uuid = new_sess.get("session_uuid")
                self.add_bubble("Yeni bir sohbet başladı.", "Sistem", False)
            else:
                raise Exception("Sunucu yanıt vermedi.")
        except Exception as e:
            self.current_session_uuid = str(uuid.uuid4())
            self.add_bubble(f"Sunucuya bağlanılamadı. (Hata: {e})", "Sistem", False)

    def handle_send(self):
        msg = self.msg_input.toPlainText().strip()
        if not msg: return
        self.add_bubble(msg, self.user_lbl.text(), True)
        self.msg_input.clear()

        worker = RagWorker(self.analyzer, msg, self.user_lbl.text(), self.current_session_uuid)
        worker.finished.connect(lambda ans, src: self.add_bubble(ans, "MevzuSağlık AI", False))
        worker.start()
        self.active_workers.append(worker)

    def add_bubble(self, text, name, is_user):
        bubble = ChatBubble(text, datetime.now().strftime("%H:%M"), is_user, name)
        row = QHBoxLayout()
        if is_user:
            row.addStretch(); row.addWidget(bubble)
        else:
            row.addWidget(bubble); row.addStretch()
        self.chat_layout.addLayout(row)
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()))

    def nuke_chat_widget(self):
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def view_history_action(self):
        self.hist_panel.setVisible(not self.hist_panel.isVisible())
        if self.hist_panel.isVisible():
            self.hist_list.clear()
            sessions = self.analyzer.get_user_sessions(self.user_lbl.text())
            for s in sessions:
                item = QListWidgetItem(f"📅 {s['created_at'][11:16]} - {s['session_uuid'][:8]}")
                item.setData(Qt.UserRole, s['session_uuid'])
                self.hist_list.addItem(item)

    def load_history_session(self, item):
        s_uuid = item.data(Qt.UserRole)
        data = self.analyzer.get_session_details(s_uuid)
        if data:
            session_info = data[0] if isinstance(data, list) else data
            self.current_session_uuid = session_info["session_uuid"]
            self.nuke_chat_widget()
            self.hist_panel.setVisible(False)
            for m in session_info.get("messages", []):
                self.add_bubble(m["content"], m["sender"].upper(), m["is_user"])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MevzuSaglik()
    win.show()
    sys.exit(app.exec_())