from typing import Union

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, MetaData, Column, Integer, Float, String
from sqlalchemy.orm import sessionmaker
import os

base = declarative_base()


class Base(base):
    __tablename__ = 'gastos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    valor = Column(Float)
    data = Column(String)
    categoria = Column(String)
    parcelas = Column(Integer)
    descricao = Column(String)
    pagamento = Column(String)
    mes_ano = Column(String)


class Auxiliar(base):
    __tablename__ = 'auxiliar'
    id = Column(Integer, primary_key=True, autoincrement=True)
    valor = Column(Float)
    data = Column(String)
    categoria = Column(String)
    parcelas = Column(Integer)
    descricao = Column(String)
    pagamento = Column(String)
    mes_ano = Column(String)
    modo = Column(String)


# class Base(DeclarativeBase):
#     __abstract__ = True
#     id: Mapped[int] = mapped_column(primary_key=True)
#     valor: Mapped[float] = mapped_column(server_default=str(0))
#     data: Mapped[str] = mapped_column(server_default="-")
#     categoria: Mapped[str] = mapped_column(server_default="-")
#     parcelas: Mapped[int] = mapped_column(server_default=str(0))
#     descricao: Mapped[str] = mapped_column(server_default="-")
#     mes_ano: Mapped[str] = mapped_column(server_default="-")


class Banco_de_dados:
    def __init__(self):
        database_url = "sqlite:///gastos.db"
        self.engine = create_engine(database_url, echo=True, connect_args={'check_same_thread': False})
        session = sessionmaker(bind=self.engine)
        self.db = session()
        self.metadata = MetaData()
        self.base = Base

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def adicionar(self, gasto: dict, tabela: Union[type, object]):
        novo_gasto = tabela(**gasto)
        self.db.add(novo_gasto)
        self.db.commit()
        self.db.close()

    def deletar(self, id_gasto: int, tabela):
        deletar = self.db.query(tabela).filter(tabela.id == id_gasto).scalar()
        self.db.delete(deletar)
        self.db.commit()
        self.db.close()

    def alterar(self, tabela, alteracao: str, categoria: str, id_alteracao: int):
        resultado = self.db.query(tabela).filter(tabela.id == id_alteracao).scalar()
        setattr(resultado, categoria, alteracao)
        self.db.commit()
        self.db.close()

    def todos_gastos(self, tabela: object):
        todos_gastos = self.db.query(tabela).all()
        return todos_gastos

    def total_geral(self, tabela):
        todos_gastos = self.db.query(tabela.valor).all()
        total = 0
        for item in todos_gastos:
            total += item[0]
        return round(total, 2)

    def total_categoria(self, tabela, parametro: str):
        todos_gastos = self.db.query(tabela.valor).filter(tabela.categoria == parametro).all()
        total = 0
        for item in todos_gastos:
            total += item[0]
        return round(total, 2)

    def total_mes(self, tabela, mes_ano: str):
        resultado = self.db.query(tabela.valor).filter(tabela.mes_ano == mes_ano).all()
        total = 0
        for item in resultado:
            total += item[0]
        self.db.close()
        return round(total, 2)

    def linhas_mes(self, tabela, mes_ano: str):
        resultado = self.db.query(tabela).filter(tabela.mes_ano == mes_ano).all()
        return resultado

    def linhas_categoria(self, tabela, parametro: str):
        resultado = self.db.query(tabela).filter(tabela.categoria == parametro).all()
        return resultado

    def consultar_id(self, tabela, id_sinc: str):
        resultado = self.db.query(tabela).filter(tabela.id == id_sinc).all()
        return resultado
