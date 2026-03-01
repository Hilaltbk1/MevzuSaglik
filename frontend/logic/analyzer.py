import requests

class Analyzer:
    def __init__(self):
        # Sunucunun çalıştığı adres. Eğer sunucu farklı porttaysa burayı güncelle.
        self.base_url = "http://localhost:8080"

    def create_new_session(self, user_name):
        url = f"{self.base_url}/session/create_session"
        try:
            res = requests.post(url, json={"user_name": user_name}, timeout=10)
            return res.json() if res.status_code == 200 else None
        except:
            return None

    def get_user_sessions(self, user_name):
        url = f"{self.base_url}/session/sessions/{user_name}"
        try:
            res = requests.get(url, timeout=10)
            return res.json() if res.status_code == 200 else []
        except:
            return []

    def get_session_details(self, session_uuid):
        url = f"{self.base_url}/history/{session_uuid}"
        try:
            res = requests.get(url, timeout=10)
            return res.json() if res.status_code == 200 else None
        except:
            return None

    def process(self, question, user_name, session_uuid):
        url = f"{self.base_url}/search/ask"
        payload = {"query": question, "user_name": user_name, "session_uuid": session_uuid}
        try:
            # RAG işlemleri uzun sürebileceği için timeout'u yüksek tuttuk (120 sn)
            response = requests.post(url, json=payload, timeout=120)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None