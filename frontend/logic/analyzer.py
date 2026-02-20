import os
import requests

class Analyzer:
    def __init__(self):
        # EĞER bu kod da Docker içinde çalışacaksa: "http://api:8000/search/ask"
        self.api_url = "http://localhost:8000/search/ask"
    def process(self, question, user_name):
        try:
            payload = {
                "query": question,
                "user_name": user_name
            }
            # self.api_url kullanarak daha esnek hale getiriyoruz
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                # Burası önemli: Hem cevabı hem kaynakları dönmelisin
                return data.get("answer", "Cevap alınamadı"), data.get("sources", [])
            else:
                return f"Hata: {response.status_code}", []
        except Exception as e:
            return f"Bağlantı Hatası: {e}", []