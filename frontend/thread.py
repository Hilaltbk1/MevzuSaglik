from PyQt5.QtCore import QThread, pyqtSignal

# frontend/thread.py içinde
class RagWorker(QThread):
    finished = pyqtSignal(str, list)

    # Burası 3 parametre almalı: analyzer, question, user_name
    def __init__(self, analyzer, question, user_name):
        super().__init__()
        self.analyzer = analyzer
        self.question = question
        self.user_name = user_name

    def run(self):
        # Analyzer'a hem soruyu hem kullanıcı adını gönderiyoruz
        answer, sources = self.analyzer.process(self.question, self.user_name)
        self.finished.emit(answer, sources)