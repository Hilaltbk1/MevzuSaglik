from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def create_prompt():
    c_ninja = """
    Görevin kullanıcı sorusunu sana "BULUNAN BİLGİLER" başlığı altında verilen metin parçalarına dayanarak yanıtlamaktır.
    Eğer cevap bu belgelerde yoksa, "Üzgünüm, soruyu yanıtlayamıyorum" cevabını ver.
    Asla tahmin yürütme.
    Yanıtları net, profesyonel ve doğrudan ver.
    Yanıtı maddeler halinde alt alta yaz. 20 cümleyi geçmesin.

    BULUNAN BİLGİLER:
    {context}
    """

    c_prompt = ChatPromptTemplate.from_messages([
        ("system", c_ninja),
        # Hafıza (Memory) eklendiğinde geçmiş buraya dolacak:
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
    ])

    return c_prompt