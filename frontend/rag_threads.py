from PyQt5.QtCore import QThread, pyqtSignal

class RagWorker(QThread):
    finished = pyqtSignal(str, list)

    def __init__(self, analyzer, question, user_name, session_uuid):
        super().__init__()
        self.analyzer = analyzer
        self.question = question
        self.user_name = user_name
        self.session_uuid = session_uuid

    def run(self):
        result = self.analyzer.process(self.question, self.user_name, self.session_uuid)
        if result:
            answer = result.get("answer", "Cevap üretilemedi.")
            sources = result.get("sources", [])
            self.finished.emit(answer, sources)
        else:
            self.finished.emit("Sunucuya ulaşılamıyor. Lütfen backend bağlantısını kontrol edin.", [])