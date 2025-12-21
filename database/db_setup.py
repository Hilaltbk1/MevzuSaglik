from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.configuration import Settings

#Settings den nesne oluşturduk
settings=Settings()
#engıne olusturma
engine= create_engine(settings.DATABASE_URL,echo=True,pool_pre_ping=True)

#session oluşturmam lazım
SessionLocal=sessionmaker(autocommit=False,autoflush=False,bind=engine)