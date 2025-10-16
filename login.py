import sys
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QInputDialog, QComboBox
)
from PyQt5.QtCore import Qt

# ===== Banco de dados =====
def criar_banco():
    conexao = sqlite3.connect("usuarios.db")
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            tipo TEXT,
            valor REAL,
            descricao TEXT,
            categoria TEXT,
            data TEXT,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    """)
    conexao.commit()
    conexao.close()

def cadastrar_usuario_bd(usuario, senha):
    conexao = sqlite3.connect("usuarios.db")
    cursor = conexao.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", (usuario, senha))
        conexao.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conexao.close()

def verificar_login_bd(usuario, senha):
    conexao = sqlite3.connect("usuarios.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
    resultado = cursor.fetchone()
    conexao.close()
    return resultado

def salvar_transacao(usuario_id, tipo, valor, descricao, categoria):
    conexao = sqlite3.connect("usuarios.db")
    cursor = conexao.cursor()
    data = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute(
        "INSERT INTO transacoes (usuario_id, tipo, valor, descricao, categoria, data) VALUES (?, ?, ?, ?, ?, ?)",
        (usuario_id, tipo, valor, descricao, categoria, data)
    )
    conexao.commit()
    conexao.close()

def pegar_transacoes(usuario_id):
    conexao = sqlite3.connect("usuarios.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT id, tipo, valor, descricao, categoria, data FROM transacoes WHERE usuario_id=? ORDER BY id DESC", (usuario_id,))
    resultado = cursor.fetchall()
    conexao.close()
    return resultado

def atualizar_transacao(transacao_id, tipo, valor, descricao, categoria):
    conexao = sqlite3.connect("usuarios.db")
    cursor = conexao.cursor()
    cursor.execute("UPDATE transacoes SET tipo=?, valor=?, descricao=?, categoria=? WHERE id=?",
                   (tipo, valor, descricao, categoria, transacao_id))
    conexao.commit()
    conexao.close()

def excluir_transacao(transacao_id):
    conexao = sqlite3.connect("usuarios.db")
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM transacoes WHERE id=?", (transacao_id,))
    conexao.commit()
    conexao.close()

def calcular_saldo(usuario_id):
    transacoes = pegar_transacoes(usuario_id)
    saldo = 0
    for _, tipo, valor, _, _, _ in transacoes:
        if tipo == "Receita":
            saldo += valor
        else:
            saldo -= valor
    return saldo

# ===== Tela de Cadastro =====
class TelaCadastro(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cadastro de Usuário")
        self.setGeometry(550, 300, 350, 200)
        self.setFixedSize(350, 200)

        self.label_usuario = QLabel("Novo usuário:")
        self.input_usuario = QLineEdit()
        self.label_senha = QLabel("Nova senha:")
        self.input_senha = QLineEdit()
        self.input_senha.setEchoMode(QLineEdit.Password)

        self.botao_cadastrar = QPushButton("Cadastrar")
        self.botao_voltar = QPushButton("Voltar")

        layout = QVBoxLayout()
        layout.addWidget(self.label_usuario)
        layout.addWidget(self.input_usuario)
        layout.addWidget(self.label_senha)
        layout.addWidget(self.input_senha)

        botoes = QHBoxLayout()
        botoes.addWidget(self.botao_cadastrar)
        botoes.addWidget(self.botao_voltar)
        layout.addLayout(botoes)

        self.setLayout(layout)

        self.botao_cadastrar.clicked.connect(self.fazer_cadastro)
        self.botao_voltar.clicked.connect(self.voltar_login)

    def fazer_cadastro(self):
        usuario = self.input_usuario.text().strip()
        senha = self.input_senha.text().strip()
        if not usuario or not senha:
            QMessageBox.warning(self, "Atenção", "Preencha todos os campos!")
            return
        if cadastrar_usuario_bd(usuario, senha):
            QMessageBox.information(self, "Sucesso", "Usuário cadastrado com sucesso!")
            self.input_usuario.clear()
            self.input_senha.clear()
            self.close()
        else:
            QMessageBox.warning(self, "Erro", "Usuário já existe!")

    def voltar_login(self):
        self.close()

# ===== Tela Principal =====
class TelaPrincipal(QWidget):
    def __init__(self, usuario_id, usuario_nome):
        super().__init__()
        self.usuario_id = usuario_id
        self.setWindowTitle(f"Sistema Financeiro - {usuario_nome}")
        self.setGeometry(400, 200, 700, 400)

        self.label_saldo = QLabel()
        self.label_saldo.setAlignment(Qt.AlignCenter)
        self.atualizar_saldo()

        self.botao_receita = QPushButton("Adicionar Receita")
        self.botao_despesa = QPushButton("Adicionar Despesa")
        self.botao_editar = QPushButton("Editar Transação")
        self.botao_excluir = QPushButton("Excluir Transação")

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels(["Tipo", "Valor", "Descrição", "Categoria", "Data"])
        self.tabela.horizontalHeader().setStretchLastSection(True)
        self.tabela.setEditTriggers(QTableWidget.NoEditTriggers)

        layout = QVBoxLayout()
        layout.addWidget(self.label_saldo)
        botoes = QHBoxLayout()
        botoes.addWidget(self.botao_receita)
        botoes.addWidget(self.botao_despesa)
        botoes.addWidget(self.botao_editar)
        botoes.addWidget(self.botao_excluir)
        layout.addLayout(botoes)
        layout.addWidget(self.tabela)
        self.setLayout(layout)

        self.botao_receita.clicked.connect(lambda: self.nova_transacao("Receita"))
        self.botao_despesa.clicked.connect(lambda: self.nova_transacao("Despesa"))
        self.botao_editar.clicked.connect(self.editar_transacao)
        self.botao_excluir.clicked.connect(self.excluir_transacao)

        self.atualizar_tabela()

    def atualizar_saldo(self):
        saldo = calcular_saldo(self.usuario_id)
        self.label_saldo.setText(f"Saldo Atual: R$ {saldo:.2f}")

    def atualizar_tabela(self):
        transacoes = pegar_transacoes(self.usuario_id)
        self.transacoes_ids = []
        self.tabela.setRowCount(len(transacoes))
        for i, (id_t, tipo, valor, descricao, categoria, data) in enumerate(transacoes):
            self.transacoes_ids.append(id_t)
            self.tabela.setItem(i, 0, QTableWidgetItem(tipo))
            self.tabela.setItem(i, 1, QTableWidgetItem(f"{valor:.2f}"))
            self.tabela.setItem(i, 2, QTableWidgetItem(descricao))
            self.tabela.setItem(i, 3, QTableWidgetItem(categoria))
            self.tabela.setItem(i, 4, QTableWidgetItem(data))

    def nova_transacao(self, tipo):
        valor_texto, ok = QInputDialog.getText(self, f"Nova {tipo}", f"Digite o valor da {tipo.lower()}:")
        if ok and valor_texto:
            try:
                valor = float(valor_texto)
                descricao, ok_desc = QInputDialog.getText(self, f"Nova {tipo}", "Descrição (opcional):")
                if not ok_desc:
                    return
                categorias = ["Alimentação", "Transporte", "Lazer", "Salário", "Outros"]
                categoria, ok_cat = QInputDialog.getItem(self, f"Categoria da {tipo}", "Escolha uma categoria:", categorias, 0, False)
                if ok_cat:
                    salvar_transacao(self.usuario_id, tipo, valor, descricao, categoria)
                    self.atualizar_saldo()
                    self.atualizar_tabela()
            except ValueError:
                QMessageBox.warning(self, "Erro", "Digite um valor numérico válido!")

    def editar_transacao(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma transação para editar!")
            return
        id_trans = self.transacoes_ids[linha]
        tipo = self.tabela.item(linha,0).text()
        valor_texto, ok = QInputDialog.getText(self, "Editar Valor", "Digite o novo valor:", text=self.tabela.item(linha,1).text())
        if ok and valor_texto:
            try:
                valor = float(valor_texto)
                descricao, ok_desc = QInputDialog.getText(self, "Editar Descrição", "Digite a descrição:", text=self.tabela.item(linha,2).text())
                if not ok_desc:
                    return
                categorias = ["Alimentação", "Transporte", "Lazer", "Salário", "Outros"]
                categoria, ok_cat = QInputDialog.getItem(self, "Editar Categoria", "Escolha uma categoria:", categorias, categories.index(self.tabela.item(linha,3).text()) if self.tabela.item(linha,3).text() in categorias else 0, False)
                if ok_cat:
                    atualizar_transacao(id_trans, tipo, valor, descricao, categoria)
                    self.atualizar_saldo()
                    self.atualizar_tabela()
            except ValueError:
                QMessageBox.warning(self, "Erro", "Digite um valor numérico válido!")

    def excluir_transacao(self):
        linha = self.tabela.currentRow()
        if linha < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma transação para excluir!")
            return
        id_trans = self.transacoes_ids[linha]
        confirmar = QMessageBox.question(self, "Confirmação", "Deseja realmente excluir esta transação?", QMessageBox.Yes | QMessageBox.No)
        if confirmar == QMessageBox.Yes:
            excluir_transacao(id_trans)
            self.atualizar_saldo()
            self.atualizar_tabela()

# ===== Tela de Login =====
class TelaLogin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - Sistema Financeiro")
        self.setGeometry(500, 250, 350, 200)
        self.setFixedSize(350, 200)

        self.label_usuario = QLabel("Usuário:")
        self.input_usuario = QLineEdit()
        self.label_senha = QLabel("Senha:")
        self.input_senha = QLineEdit()
        self.input_senha.setEchoMode(QLineEdit.Password)

        self.botao_login = QPushButton("Entrar")
        self.botao_cadastrar = QPushButton("Cadastrar")

        layout = QVBoxLayout()
        layout.addWidget(self.label_usuario)
        layout.addWidget(self.input_usuario)
        layout.addWidget(self.label_senha)
        layout.addWidget(self.input_senha)

        botoes = QHBoxLayout()
        botoes.addWidget(self.botao_login)
        botoes.addWidget(self.botao_cadastrar)
        layout.addLayout(botoes)

        self.setLayout(layout)

        self.botao_login.clicked.connect(self.fazer_login)
        self.botao_cadastrar.clicked.connect(self.abrir_cadastro)

    def fazer_login(self):
        usuario = self.input_usuario.text().strip()
        senha = self.input_senha.text().strip()
        dados = verificar_login_bd(usuario, senha)
        if dados:
            QMessageBox.information(self, "Login", f"Bem-vindo, {usuario}!")
            self.hide()
            self.tela_principal = TelaPrincipal(dados[0], usuario)
            self.tela_principal.show()
        else:
            QMessageBox.warning(self, "Erro", "Usuário ou senha incorretos!")

    def abrir_cadastro(self):
        self.tela_cadastro = TelaCadastro()
        self.tela_cadastro.show()

# ===== Execução =====
if __name__ == "__main__":
    criar_banco()
    app = QApplication(sys.argv)
    janela = TelaLogin()
    janela.show()
    sys.exit(app.exec_())
