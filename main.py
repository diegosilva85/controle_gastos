from datetime import datetime
from functools import partial
from concurrent.futures import ThreadPoolExecutor
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.behaviors import CommonElevationBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.screen import MDScreen
# from kivymd.uix.textfield import MDTextField
# from kivy.uix.popup import Popup
# from kivymd.uix.button import MDRaisedButton
# from kivy.metrics import dp
import re
from sqlalchemy import Column, String

from Base import Banco_de_dados, Base, Auxiliar
import requests

banco_dados = Banco_de_dados()
__version__ = "0.1"
base, altura = Window.size
print(base, altura)

Builder.load_file("tela.kv")
meses = {'01': 'Janeiro', '02': 'Fevereiro', '03': 'Março', '04': 'Abril', '05': 'Maio', '06': 'Junho', '07': 'Julho',
         '08': 'Agosto', '09': 'Setembro', '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'}
url = "https://diego-matematica-bbe5cdd19f71.herokuapp.com/controle_gastos"
mes_ano = ['05/2024', '06/2024', '07/2024']

class Gastos(Base):
    __tablename__ = "gastos"


class GastosAuxiliar(Auxiliar):
    __tablename__ = "auxiliar"


class Tela(MDScreen):
    hoje = datetime.now().strftime('%d/%m/%Y')
    mes_atual = meses[datetime.now().strftime('%m')]
    categorias = ["mercado", "alimentação", "eletrônicos", "combustível", "despesa médica", "lazer", "livros", "impostos", "despesa doméstica",
                  "outros"]
    pagamento = ["Pix", "Crédito", "Débito", "Dinheiro"]
    distancia_icones = base * 0.05
    
    def open_menu(self, item, tela):
        if tela == "pagamento":
            items_categoria = Tela.pagamento
        elif tela == "add":
            items_categoria = Tela.categorias
        else:
            items_categoria = Tela.categorias
        menu_items = [
            {
                "text": f"{categoria}",
                "on_release": lambda x=f"{categoria}": self.set_item(x, tela),
            } for categoria in items_categoria]
        self.ids.menu = MDDropdownMenu(
            caller=item,
            items=menu_items,
            position="center",
        )
        self.ids.menu.open()

    def set_item(self, text_item, tela):
        if tela == "add":
            self.ids.categoria_add.text = text_item
        elif tela == "pagamento":
            self.ids.pagamento.text = text_item
        else:
            self.ids.escolher_categoria.text = text_item
        self.ids.menu.dismiss()
        

    def adicionar_gasto(self, instance):
        mes_ano = self.ids.data.text[3:]
        dados_gasto = {
            'valor': self.ids.valor.text,
            'data': self.ids.data.text,
            'categoria': self.ids.categoria_add.text.lower(),
            'parcelas': 1,
            'descricao': self.ids.desc.text,
            'mes_ano': mes_ano,
            'pagamento': self.ids.pagamento.text,
        }
        print("Inserindo dados localmente...")
        banco_dados.adicionar(tabela=Gastos, gasto=dados_gasto)
        self.app_instance.atualizar_sessao() 
        self.app_instance.executor.submit(self.app_instance.adicao_dados)
        self.ids.container.clear_widgets()
        print("Apagados widgets.")
        self.app_instance.cards_categorias_home(self.app_instance.sessao)
        print("finalizado.")
       
        confirmacao = self.app_instance.confirmar(enviado="enviado")
        if confirmacao:
            self.ids.valor.text = ""
            self.ids.data.text = Tela.hoje
            self.ids.categoria_add.text = "Categoria"
            self.ids.desc.text = ""
            self.ids.pagamento.text = "Pagamento"

    def mostrar_calendario(self, instance):
        data = MDDatePicker()
        data.bind(on_save=self.on_save)
        data.open()

    def on_save(self, instance, value, date_range):
        data = str(value)
        self.ids.data.text = datetime.strptime(data, '%Y-%m-%d').strftime('%d/%m/%Y')

    def mostrar_sessao(self):
        print(self.app_instance.sessao)
        
class NavBar(CommonElevationBehavior, MDBoxLayout):
    pass

class TelaApp(MDApp):
    def __init__(self, **kwargs):
        super(TelaApp, self).__init__(**kwargs)
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.formatted_text = ""
        self.sessao = []
        self.executor.submit(self.atualizar_sessao)

    def build(self):
        root = self.root
        tela = Tela()
        tela.app_instance = self
        return tela

    def on_start(self):
        self.cards_categorias_home(self.sessao)
        self.estatisticas()   

    def on_text_change(self, text): 
        pass            

    def input_filter(self, text, from_undo):
        if text == '.' and '.' not in self.root.ids.valor.text:
            return text
        else:
            return re.sub(r'[^\d]', '', text)  
    
    def converter_virgula(self, valor):
        if ',' in str(valor):
            valor = str(valor).replace(',', '.')
        return valor

    def converter_dicionario(self, objeto):
        dicionario = {
            "id": objeto.id,
            'valor': objeto.valor,
            'data': objeto.data,
            'categoria': objeto.categoria,
            'parcelas': 1,
            'descricao': objeto.descricao,
            'mes_ano': objeto.mes_ano,
            'pagamento': objeto.pagamento,
        }
        return dicionario    

    def atualizar_sessao(self):
        print("Atualizando Sessão...")
        linhas = banco_dados.linhas_mes(tabela=Gastos, mes_ano=Tela.hoje[3:])
        self.sessao = []
        for linha in linhas:
            self.sessao.append(self.converter_dicionario(linha))
    
    def linhas_categoria(self, lista: list, categoria: str) -> list:
        response = []
        for item in lista:        
            if item["categoria"] == categoria:
                response.append(item)
        return response 
    
    def total_categoria(self, lista: list) -> float:
        total = 0
        for item in lista:
            total += float(item["valor"])
        return round(total, 2)
    
    def total_mes(self, lista: list) -> float:
        print("Atualizando valor total do mês...")        
        total = 0
        for item in lista:
            total += float(item["valor"])
        return round(total, 2)

    def adicao_dados(self):   
        print("Sincronizando com o banco de dados remoto...")
        self.sincronizar_banco()
        self.root.ids.valor_reais.text = f'R$ {self.total_mes(lista=self.sessao):.2f}'
        print("fim da thread")        
             

    def verificar_conexao(self):
        dados = {"ok": "ok"}
        try:
            response = requests.post(url=url, json=dados)
            if response.status_code == 200:                
                return True
            elif response.status_code == 400:
                return False
        except Exception as e:
            return False

    def checar_auxiliar(self):
        print("Buscando dados localmente...")
        dados_envio = banco_dados.todos_gastos(tabela=GastosAuxiliar)
        if dados_envio:
            print("Há dados para envio")
            for dado in dados_envio:
                print(f"INFO - ID:{dado.id}; VALOR:{dado.valor}; DESCRICAO: {dado.descricao}")
                dados_deletar = {'id_delete': dado.id}
                response = requests.post(url=url + "/deletar", json=dados_deletar)
                while response.status_code != 200:
                    response = requests.post(url=url + "/deletar", json=dados_deletar)
                if response.status_code == 200:
                    banco_dados.deletar(tabela=GastosAuxiliar, id_gasto=dado.id)
                else:
                    return False
            print("Dados enviados.")
        else:
            print("Não há dados para ser enviados.")        
        return True

    def deletar_entrada(self, dados, *args):
        def confirmar_delecao(inst):
            self.sessao = [item for item in self.sessao if item['id'] != dados['id']]
            self.executor.submit(banco_dados.deletar, id_gasto=dados['id'], tabela=Gastos)
            self.executor.submit(banco_dados.adicionar, tabela=GastosAuxiliar, gasto=dados)
            self.executor.submit(self.sincronizar_banco)               
            self.executor.submit(self.atualizar_sessao)            
            self.root.ids.valor_reais.text = f'R$ {self.total_mes(self.sessao):.2f}'
            self.root.ids.container.clear_widgets()
            self.cards_categorias_home(self.sessao)
            self.dialog.dismiss()

        # Função para fechar o diálogo sem deletar
        def cancelar_delecao(inst):
            self.dialog.dismiss()

        self.dialog = MDDialog(
            title="Confirmação",
            text="Você tem certeza que deseja deletar esta entrada?",
            buttons=[MDFlatButton(text="CANCELAR", on_release=cancelar_delecao),
                     MDFlatButton(text="DELETAR", on_release=confirmar_delecao), ], )
        self.dialog.open()

    def cards_categorias_home(self, lista_sessao):
        print(self.sessao)
        print("Atualizando cards na tela inicial...")
        for categoria in self.root.categorias:
            print('iterando...')
            linhas = self.linhas_categoria(lista=self.sessao, categoria=categoria)
            print("recebidas linhas do banco")
            categoria_dict = {categoria: self.total_categoria(lista=linhas)}
            print(categoria_dict)
            try:
                card = MDCard(
                    orientation='horizontal',
                    size_hint=(1, None),
                    size=("250dp", "100dp"),
                    pos_hint={"center_x": 0.5, "center_y": 0.5},
                    elevation=0,
                    ripple_behavior=True,
                    on_release=partial(self.mostrar_gastos_categoria, linhas))
            except Exception as e:
                print(f"FALHA AO CRIAR CARD = {e}")
            print(card)
            card_box = MDBoxLayout(orientation='vertical', padding="8dp")
            card_box.add_widget(MDLabel(text=f"{categoria.capitalize()}", theme_text_color="Secondary"))
            card_box.add_widget(MDLabel(text=f"{len(linhas)} registros", theme_text_color="Hint"))
            card_box_label = MDBoxLayout(orientation='horizontal', padding="8dp")
            card_box_label.add_widget(MDLabel(text=f'R$ {categoria_dict[categoria]:.2f}', theme_text_color="Secondary"))
            card.add_widget(card_box)
            card.add_widget(card_box_label)
            self.root.ids.container.add_widget(card)
            self.root.ids.container.add_widget(Widget(size_hint_y=None, height="10dp"))

    def mostrar_gastos_categoria(self, linhas, *args):
        self.root.ids.screen.current = "detalhes"
        card_container = self.root.ids.card_container
        card_container.clear_widgets()
        self.add_card(card_container, linhas)


    def add_card(self, container, linha):
        for line in linha:
            card = MDCard(
                orientation='horizontal',
                size_hint=(1, None),
                size=("250dp", "100dp"),
                pos_hint={"center_x": 0.5, "center_y": 0.5},
                elevation=0,
                ripple_behavior=False)

            card_box = MDBoxLayout(orientation='vertical', padding="8dp")
            card_box.add_widget(MDLabel(text=f"R$ {line['valor']:.2f}", theme_text_color="Secondary"))
            card_box.add_widget(MDLabel(text=f"{line['data']}", theme_text_color="Hint"))
            card_box.add_widget(MDLabel(text=f"{line['descricao']}", theme_text_color="Secondary"))
            card.add_widget(card_box)
            
            card_box_edit = MDBoxLayout(orientation='horizontal', padding="8dp")
            card_box_edit.add_widget(MDIconButton(icon="pencil", pos_hint={"center_x": 0.5, "center_y": 0.5}))
            card_box_edit.add_widget(MDIconButton(icon="delete", pos_hint={"center_x": 0.5, "center_y": 0.5},
                                                on_release=partial(self.deletar_entrada, line)))
            card.add_widget(card_box_edit)
            container.add_widget(card)
            # Adicionar um widget vazio para espaçamento
            container.add_widget(Widget(size_hint_y=None, height="10dp"))

    def confirmar(self, enviado):
        def confirmar_botao(inst):
            self.dialog_add.dismiss()

        self.dialog_add = MDDialog(buttons=[MDFlatButton(text="OK", on_release=confirmar_botao)])
        if enviado == 'enviado':
            self.dialog_add.title = "Sucesso"
            self.dialog_add.text = "Entrada adicionada com sucesso"
            self.dialog_add.open()
            return True
        else:
            self.dialog_add.title = "Erro"
            self.dialog_add.text = enviado.text.strip()
            self.dialog_add.open()
            return False
        
    def estatisticas(self):
        mes_ano.reverse()
        for item in mes_ano:            
            total = banco_dados.total_mes(tabela=Gastos, mes_ano=item)
            if total != 0:
                card = MDCard(orientation='horizontal', size_hint=(1, None), size=("250dp", "100dp"), pos_hint={"center_x": 0.5, "center_y": 0.5},
                    elevation=0, ripple_behavior=False)
                card_box = MDBoxLayout(orientation='vertical', padding="8dp")
                card_box.add_widget(MDLabel(text=f'Período: {item}', theme_text_color="Secondary"))
                card_box.add_widget(MDLabel(text=f'Total Gasto no mês: R$ {total}', theme_text_color="Secondary"))
                card.add_widget(card_box)
                self.root.ids.meses_container.add_widget(card)
                self.root.ids.meses_container.add_widget(Widget(size_hint_y=None, height="10dp"))
                dados_mes = []
                linhas_mes = banco_dados.linhas_mes(tabela=Gastos, mes_ano=item)
                for linha in linhas_mes:
                    dados_mes.append(self.converter_dicionario(linha))
                for categoria in self.root.categorias:
                    linhas = self.linhas_categoria(lista=dados_mes, categoria=categoria)            
                    categoria_dict = {categoria: self.total_categoria(lista=linhas)}
                

    def sincronizar_banco(self):
        print("Tentando conexão com o banco de dados...")
        if self.verificar_conexao():
            print("Há conexão com o banco de dados.")
            print("Checando se há dados a ser deletados no banco de dados remoto.")
            if self.checar_auxiliar():
                print("Iniciando sincronização...")
                dado = {"parametro": "todos"}
                response = requests.post(url=url + "/todos", json=dado)
                while response.status_code != 200:
                    print("Tentando conexão...")
                    response = requests.post(url=url + "/todos", json=dado)
                print("Dados do servidor recebidos.")
                response = response.json()
                banco_interno = banco_dados.todos_gastos(tabela=Gastos)
                for linha in response:
                    id_linha = banco_dados.consultar_id(tabela=Gastos, id_sinc=linha['id'])
                    if not id_linha:
                        dados_gasto = {
                            'id': linha['id'],
                            'valor': linha['valor'],
                            'data': linha['data'],
                            'categoria': linha['categoria'],
                            'parcelas': 1,
                            'descricao': linha['descricao'],
                            'mes_ano': linha['mes_ano'],
                            'pagamento': linha['pagamento'],
                        }
                        banco_dados.adicionar(tabela=Gastos, gasto=dados_gasto)
                dados_envio = []
                ids_servidor = [item['id'] for item in response]
                for linha in banco_interno:
                    if linha.id not in ids_servidor:
                        dados_local = self.converter_dicionario(linha)
                        dados_envio.append(dados_local)
                if dados_envio:
                    response = requests.post(url=url + "/add_multiplos", json=dados_envio)
                    while response.status_code != 200:
                        print(response.text)
                        print("Tentando novamente...")
                        response = requests.post(url=url + "/add_multiplos", json=dados_envio)
                    print("Dados enviados ao banco de dados remoto.")   
        else:
            print("Não há conexão com o banco de dados.")        

banco_dados.create_tables()

TelaApp().run()
