import sqlalchemy as sa # короткое имя sa - основная библиотека
import sqlalchemy.orm as orm # короткое имя orm - инструмент для работы с данными как с объектами
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

# служебный объект. хранение структур таблиц из tables.py
SqlAlchemyBase = dec.declarative_base()

# внутренняя переменная. хранение настроенного объекта для создания сессий
__factory = None

def global_init(db_file): 
    # физическое создание базы данных и настройка связи
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Укажите файл базы данных!")
    
    # формирование пути к файлу базы данных
    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    
    # движок. перевод команд python в команды файловой системы
    engine = sa.create_engine(conn_str, echo=False)
    
    # генератор сессий. привязывание этого генератора к конкретному движку.
    __factory = orm.sessionmaker(bind=engine)

    from . import tables
    
    # команда на выполнение. создание таблиц в файле на диске
    SqlAlchemyBase.metadata.create_all(engine)

def create_session() -> Session:
    # создание нового окна связи (сессии) для работы с данными
    global __factory
    return __factory()
