import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QTextCursor
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QFrame, QScrollArea,
    QMessageBox
)

# Mevcut mantık dosyaların
try:
    from logic.analyzer import Analyzer
    from thread import RagWorker
except ImportError:
    class Analyzer:
        pass


    class RagWorker:
        pass

# ==========================================
# GÜNCELLENMİŞ SOFT-DARK & HIGH-RADIUS TEMA
# ==========================================
GLASS_THEME_QSS = """
QMainWindow {
    background-color: #0F0F12;
}

QWidget {
    font-family: 'Segoe UI Semibold', sans-serif;
    font-size: 18px;
    color: #FFFFFF;
}

/* Yan Paneller - Yüksek Radius ve Soft Geçiş */
#sidePanel {
    background-color: rgba(30, 30, 45, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 40px; /* Radius artırıldı */
    margin: 10px;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

/* Kaynaklar Bölümü - Beyaz Yerine Açık Gri */
#sourcesContainer {
    background-color: rgba(255, 255, 255, 0.04); /* Soft gri tonu */
    border-radius: 30px;
}

#chatDisplay {
    background-color: transparent;
    border: none;
}

/* Input Alanı */
QTextEdit#inputArea {
    background-color: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 30px; /* Radius artırıldı */
    padding: 15px;
    color: #FFFFFF;
}

/* Gönder Butonu */
QPushButton#sendButton {
    background-color: rgba(0, 188, 255, 0.7);
    color: #FFFFFF;
    border: none;
    border-radius: 40px; /* Tam yuvarlak */
    font-weight: bold;
    font-size: 28px;
}

QPushButton#sendButton:hover {
    background-color: rgba(0, 188, 255, 0.9);
}

QLabel#headerLabel {
    font-size: 26px;
    font-weight: 800;
    color: #FFFFFF;
    padding: 10px;
}
"""


class SourceCard(QFrame):
    def __init__(self, title, full_text, parent=None):
        super().__init__(parent)
        self.full_text = full_text
        self.setCursor(QCursor(Qt.PointingHandCursor))

        # Kartların radiusu artırıldı ve rengi yumuşatıldı
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 25px;
                padding: 18px;
                margin: 8px;
            }
            QFrame:hover {
                border-color: #00BCFF;
                background-color: rgba(255, 255, 255, 0.12);
            }
        """)

        layout = QVBoxLayout(self)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #00BCFF; font-weight: bold; font-size: 16px; border:none;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)


class MevzuSaglik(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MevzuSağlık AI")
        self.resize(1300, 900)
        self.setStyleSheet(GLASS_THEME_QSS)
        self.analyzer = Analyzer()
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # ========= SOL PANEL =========
        left_panel = QFrame()
        left_panel.setObjectName("sidePanel")
        left_panel.setFixedWidth(280)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(25, 40, 25, 40)

        logo = QLabel("MevzuSağlık")
        logo.setObjectName("headerLabel")
        left_layout.addWidget(logo)

        self.user_name_input = QTextEdit()
        self.user_name_input.setObjectName("inputArea")
        self.user_name_input.setFixedHeight(55)
        self.user_name_input.setPlaceholderText("İsim...")
        left_layout.addWidget(self.user_name_input)
        left_layout.addStretch()

        # ========= ORTA PANEL =========
        center_container = QVBoxLayout()
        chat_frame = QFrame()
        chat_frame.setStyleSheet("background-color: rgba(20, 20, 30, 0.4); border-radius: 45px;")
        chat_v_layout = QVBoxLayout(chat_frame)

        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("chatDisplay")
        self.chat_display.setReadOnly(True)
        chat_v_layout.addWidget(self.chat_display)
        center_container.addWidget(chat_frame)

        input_row = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setObjectName("inputArea")
        self.message_input.setFixedHeight(85)
        self.message_input.setPlaceholderText("Mesajınızı buraya yazın...")
        input_row.addWidget(self.message_input)

        self.send_button = QPushButton("→")
        self.send_button.setObjectName("sendButton")
        self.send_button.setFixedSize(85, 85)
        self.send_button.clicked.connect(self.handle_send)
        input_row.addWidget(self.send_button)
        center_container.addLayout(input_row)

        # ========= SAĞ PANEL =========
        right_panel = QFrame()
        right_panel.setObjectName("sidePanel")
        right_panel.setFixedWidth(350)
        right_layout = QVBoxLayout(right_panel)

        header = QLabel("Alıntılanan Kaynaklar")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: rgba(255,255,255,0.7); margin-left: 10px;")
        right_layout.addWidget(header)

        self.sources_scroll = QScrollArea()
        self.sources_scroll.setWidgetResizable(True)
        self.sources_container = QWidget()
        self.sources_container.setObjectName("sourcesContainer")
        self.sources_layout = QVBoxLayout(self.sources_container)
        self.sources_layout.setAlignment(Qt.AlignTop)
        self.sources_scroll.setWidget(self.sources_container)
        right_layout.addWidget(self.sources_scroll)

        main_layout.addWidget(left_panel)
        main_layout.addLayout(center_container, stretch=1)
        main_layout.addWidget(right_panel)

    def handle_send(self):
        message = self.message_input.toPlainText().strip()
        username = self.user_name_input.toPlainText().strip()
        if not message or not username: return

        # KULLANICI MESAJI (Sağda - Boşluk Artırıldı)
        user_html = f"""
        <div style="text-align:right; margin-bottom:45px;">
            <div style="display:inline-block;
                        background: rgba(255, 255, 255, 0.1);
                        color:white;
                        padding:20px 28px;
                        border-radius:35px 35px 5px 35px;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        font-size:18px;
                        max-width: 75%;">
                <small style="color:#AAAAAA; font-weight:bold; font-size:13px;">{username}</small><br>{message}
            </div>
        </div>
        """
        self.chat_display.append(user_html)
        self.message_input.clear()
        self.chat_display.moveCursor(QTextCursor.End)

        # Worker'ı sınıf üyesi yaparak çökme sorununu çözdük
        self.worker = RagWorker(self.analyzer, message, username)
        self.worker.finished.connect(self.display_answer)
        self.worker.start()

    def display_answer(self, answer, sources):
        # BOT YANITI (Solda - Boşluk Artırıldı)
        bot_html = f"""
        <div style="text-align:left; margin-bottom:50px;">
            <div style="display:inline-block;
                        background: rgba(0, 188, 255, 0.12);
                        color:#FFFFFF;
                        padding:25px 30px;
                        border-radius:35px 35px 35px 5px;
                        border: 1px solid rgba(0, 188, 255, 0.4);
                        line-height:1.6;
                        font-size:18px;
                        max-width: 85%;">
                <b style="color:#00BCFF; font-size:20px;">MevzuSağlık</b><br><br>
                {answer}
            </div>
        </div>
        """
        self.chat_display.append(bot_html)
        self.chat_display.moveCursor(QTextCursor.End)

        for i in reversed(range(self.sources_layout.count())):
            w = self.sources_layout.itemAt(i).widget()
            if w: w.setParent(None)

        if sources:
            for i, src in enumerate(sources, 1):
                title = f"Referans {i}: {src.splitlines()[0][:35]}"
                card = SourceCard(title, src)
                self.sources_layout.addWidget(card)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MevzuSaglik()
    window.show()
    sys.exit(app.exec_())