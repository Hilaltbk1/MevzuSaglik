
import socket
import subprocess
import sys
import importlib.util

# ARCELIK RS 9221 - YEREL AG ANALIZI
IP = "192.168.1.73"
PORT = 6668
MAC = "98:03:CF:37:97:56"


def baslik(metin):
    print("\n" + "=" * 55)
    print(metin)
    print("=" * 55)


def tinytuya_kontrol():
    baslik("1. TUYATUYA KUTUPHANESI")

    if importlib.util.find_spec("tinytuya"):
        import tinytuya
        print("Kurulu.")
        print("Surum:", getattr(tinytuya, "__version__", "Bilinmiyor"))
    else:
        print("Kurulu degil.")
        print("Kurmak icin:")
        print("python -m pip install tinytuya")


def cihaz_kontrol():
    baslik("2. CIHAZ BAGLANTI TESTI")

    try:
        with socket.create_connection((IP, PORT), timeout=5) as s:
            print("TCP baglantisi: BASARILI")

            s.settimeout(5)
            data = s.recv(1024)

            print("Gelen veri uzunlugu:", len(data))
            print("Gelen HEX:", data.hex(" "))

            if data.startswith(bytes.fromhex("000055aa")):
                print("Tuya benzeri paket baslangici bulundu.")

            if data.endswith(bytes.fromhex("0000aa55")):
                print("Paket bitis isareti bulundu.")

    except socket.timeout:
        print("Baglanti zaman asimina ugradi.")

    except Exception as e:
        print("Baglanti hatasi:", e)


def port_kontrol():
    baslik("3. ACIK PORTLAR")

    ports = [
        80, 443, 554, 6668, 7000,
        8000, 8080, 8443, 9000, 9999
    ]

    for port in ports:
        try:
            with socket.create_connection(
                (IP, port), timeout=2
            ):
                print(f"{port}: ACIK")
        except OSError:
            pass


def mac_bilgi():
    baslik("4. MAC ADRESI")

    print("MAC:", MAC)
    print("IP:", IP)
    print("Uretici: SHENZHEN BILIAN ELECTRONIC CO., LTD.")


def main():
    baslik("ARCELIK RS 9221 - GUVENLI ANALIZ")

    print("Hedef IP:", IP)
    print("Port:", PORT)

    mac_bilgi()
    tinytuya_kontrol()
    cihaz_kontrol()
    port_kontrol()

    baslik("ANALIZ TAMAMLANDI")

    print("Bu program cihaza kontrol komutu gondermez.")
    print("Local Key olmadan Tuya kontrolu denenmez.")
    print("Ses veya hareket komutu gonderilmemistir.")


if __name__ == "__main__":
    main()
