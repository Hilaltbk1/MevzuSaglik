---
title: MevzuSaglik
emoji: ⚕️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# ⚕️ MevzuSağlık - Dijital Mevzuat Asistanı

Bu proje, FastAPI ve HTML kullanılarak geliştirilmiş, sağlık çalışanlarının mevzuat karmaşasını çözmeyi hedefleyen yapay zeka destekli bir asistandır. Hugging Face Spaces üzerinde Docker altyapısı ile çalışmaktadır.

---

## 📊 Proje Sunum Slaytları

### 1. Giriş ve Vizyon
<img width="994" height="533" alt="Slayt 1" src="https://github.com/user-attachments/assets/d9798039-dbd2-4dc9-87be-0fda979a3910" />

<br>
<br>

### 2. Problem Tanımı
<img width="1004" height="525" alt="Slayt 2" src="https://github.com/user-attachments/assets/12b49a8d-bd00-40b6-9d45-8c7cd4b1e29b" />

<br>
<br>

### 3. Mevzuat Karmaşası ve Riskler
<img width="1003" height="530" alt="Slayt 3" src="https://github.com/user-attachments/assets/9009ac5e-85b9-4fec-b62c-e8340b35fa89" />

<br>
<br>

### 4. Çözüm: MevzuSağlık AI
<img width="1003" height="539" alt="Slayt 4" src="https://github.com/user-attachments/assets/7acd761f-0335-40be-a098-032e8a65c44d" />

<br>
<br>

### 5. Teknik Mimari (RAG Yapısı)
<img width="996" height="529" alt="Slayt 5" src="https://github.com/user-attachments/assets/b696ecb7-e31e-43c3-92a5-874e1d632b10" />

<br>
<br>

### 6. Performans ve Doğruluk Metrikleri
<img width="976" height="540" alt="Slayt 6" src="https://github.com/user-attachments/assets/0f274272-da6d-4594-a298-f61beaf63416" />

<br>
<br>

### 7. Sistem Özellikleri ve Ayrıcalıklar
<img width="999" height="495" alt="Slayt 7" src="https://github.com/user-attachments/assets/a0ffb735-2182-4410-a091-65101f29567f" />

<br>
<br>

### 8. Canlı Senaryo ve Örnek Kullanım
<img width="1004" height="548" alt="Slayt 8" src="https://github.com/user-attachments/assets/079b72af-34ae-427d-a7d3-7c39c3d219f3" />

<br>
<br>

### 9. İş Modeli ve Abonelik Yapısı
<img width="1004" height="532" alt="Slayt 9" src="https://github.com/user-attachments/assets/6f5da7b4-6f6c-41c8-a199-8221a25a303a" />

<br>
<br>

### 10. Gelecek Planları ve Yol Haritası
<img width="1002" height="505" alt="Slayt 10" src="https://github.com/user-attachments/assets/e56269b9-be2f-499b-9bd1-3e6a06bb4081" />

<br>
<br>

### 11. Kapanış ve İletişim
<img width="992" height="534" alt="Slayt 11" src="https://github.com/user-attachments/assets/0223faba-b787-4915-a2c8-5a03ab73d895" />

---

## 🛠️ Kurulum ve Çalıştırma

Bu proje Dockerize edilmiştir. Yerelde çalıştırmak için:

```bash
docker build -t mevzusaglik .
docker run -p 7860:7860 mevzusaglik
