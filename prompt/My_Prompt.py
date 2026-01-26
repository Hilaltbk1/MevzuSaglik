from langchain_core.prompts import ChatPromptTemplate

def create_prompt():
    # 1. Soru Cevap Promptu (QA)
    qa_ninja = """
        Görevin kullanıcı sorusunu sana "BULUNAN BİLGİLER" başlığı altında verilen metin parçalarına dayanarak yanıtlamaktır.

        KULLANICI SORUSU: {{ input }}

        BULUNAN BİLGİLER:
        {{ context }}

        TALİMATLAR:
        1. Eğer cevap bu belgelerde yoksa, "Üzgünüm, soruyu yanıtlayamıyorum" cevabını ver.
        2. Asla tahmin yürütme.
        3. Yanıtları net, profesyonel ve doğrudan ver.
        4. Yanıtı maddeler halinde alt alta yaz. 20 cümleyi geçmesin.
        """

    qa_prompt = ChatPromptTemplate.from_template(
        template=qa_ninja,
        template_format="jinja2"
    )

    # 2. Soruyu Bağlamına Göre Yeniden Düzenleme Promptu (Contextualize)
    c_ninja = """
    Sen sağlık mevzuatları konularına hakim bir yapay zeka asistanısın.
    Görevin sadece verilen sohbet geçmişini ve son kullanıcı sorusunu analiz ederek, veritabanında arama yapmak ve 
    anlamlı tek bir adet soru oluşturmaktır. Soruyu asla cevaplama sadece yeniden ifade ederek yaz.

    {% if chat_history %}
        Sohbet Geçmişi:
        {% for message in chat_history %}
            {# Veritabanı modelindeki kolon adı sender_type olduğu için ona göre güncellendi #}
            {% if message.sender_type == "human" %}
                Kullanıcı : {{ message.content }}
            {% elif message.sender_type == "ai" %}
                Asistan : {{ message.content }}
            {% endif %}
        {% endfor %}
    {% endif %}

    Son kullanıcı sorusu:
    {{ input }}
    Yukarıdaki verilenlere dayanarak oluşturulan, kendi başına anlamlı arama sorgusu
    """

    c_prompt = ChatPromptTemplate.from_template(
        template=c_ninja,
        template_format="jinja2"
    )

    return qa_prompt, c_prompt