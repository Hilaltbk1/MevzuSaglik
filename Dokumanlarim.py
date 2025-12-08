import os
from docx import Document
import logging

logging.basicConfig(level=logging.DEBUG)

PATH_FOLDER=r"C:\Users\hilal\MevzuSaglik\DOCX"

files=os.listdir(PATH_FOLDER) #list döndürür.

for index,file in enumerate(files):
    try:
        file_path=os.path.join(PATH_FOLDER,file)
        doc=Document(file_path)
        for paragraph in doc.paragraphs:
            prg=paragraph.text
            print(prg)

        print("Sıra No:",index+1)

    except Exception:
        print("Error")
        logging.exception("Error")
    print("*****************************************************************************")



