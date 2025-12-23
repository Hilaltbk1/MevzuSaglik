from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_prompt():
    #question answer prompt
    qa_ninja = """
    Görevin kullanıcı sorusunu sana "BULUNAN BİLGİLER" başlığı altında verilen metin parçalarına dayanarak yanıtlamaktır.
    Eğer cevap bu belgelerde yoksa, "Üzgünüm, soruyu yanıtlayamıyorum" cevabını ver.
    Asla tahmin yürütme.
    Yanıtları net, profesyonel ve doğrudan ver.
    Yanıtı maddeler halinde alt alta yaz. 20 cümleyi geçmesin.

    BULUNAN BİLGİLER:
    {context}
    """


    qa_prompt = ChatPromptTemplate.from_template(
        template=qa_ninja,
        template_format = "ninja2"
    )

    #contextualize questıon prompt
    c_ninja = """
    Sen sağlık mevzuatları konularına hakim bir yapay zeka asistanısın.
    Görevin sadece verilen sohbet geçmişini ve son kullanıcı sorusunu analiz ederek ,veritabanında arama yapmak ve 
    anlamlı tek bir addet soru oluşturmaktır.Soruyu asla cevaplama sadece yeniden ifade ederek yaz.
    
    {% if chat_history %}
        Sohbet Geçmişi:
        {% for message in chat_history %}
            {% if message.type == "human" %}
                Kullanıcı : {{message.content}}
            {% elif message.type == "ai" %}
                Asistan : {{message.content}}
                {% endif %}
            {% endfor %}
        { % endif % }
        
    Son kullanıcı sorusu :
    {{input }}
    Yukarıdaki verilenlere dayanarak oluşturulan, kendi başına anlamlı arama sorgusu
    
    
    """
    c_prompt = ChatPromptTemplate.from_template(
        template=c_ninja,
        template_format = "ninja2"
    )


    return qa_prompt,c_prompt