import configparser
import pandas as pd
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ttkthemes import ThemedTk 
import requests
import sys

# Função para ler o arquivo .ini diretamente do GitHub
def ler_arquivo_github(url):
    response = requests.get(url)
    if response.status_code == 200:
        print("Iniciando validação!")
        return response.text  # Retorna o conteúdo do arquivo como string
    else:
        messagebox.showerror("Erro", f"Erro ao acessar o arquivo: {response.status_code}")
        sys.exit()

# Função para validar a versão do arquivo .ini
def valida_versao(conteudo_ini, versao_atual, url_novo_arquivo):
    config = configparser.ConfigParser()
    config.read_string(conteudo_ini)
    
    try:
        versao_online = config.get('versao', 'numero').strip()
        print(f"Versão local: {versao_atual} | Versão no GitHub: {versao_online}")
        
        if versao_atual != versao_online:
            resposta = messagebox.askyesno("Atualização Disponível", "Uma versão mais recente está disponível. Deseja atualizar?")
            if resposta:
                # Baixar o novo arquivo .py
                messagebox.showinfo("Atualizando", "Baixando e atualizando para a versão mais recente.")
                download_novo_arquivo(url_novo_arquivo)
            else:
                messagebox.showinfo("Versão Atual", "Você está usando a versão mais antiga. Algumas funcionalidades podem não estar disponíveis.")
                sys.exit()
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        messagebox.showerror("Erro", f"Erro ao verificar versão: {e}")
        sys.exit()

# Função para baixar o novo arquivo .py
def download_novo_arquivo(url):
    response = requests.get(url)
    if response.status_code == 200:
        novo_arquivo = "Estoque_atualizado.py"
        
        # Salva o arquivo baixado
        with open(novo_arquivo, "wb") as f:
            f.write(response.content)
        
        # Substitui o arquivo antigo
        print(f"Arquivo atualizado baixado como {novo_arquivo}")
        
        # Fecha a aplicação e abre o novo arquivo
        messagebox.showinfo("Atualização Completa", "O arquivo foi atualizado com sucesso.")
        os.system(f"python {novo_arquivo}")  # Executa o novo arquivo
        sys.exit()  # Encerra o processo atual
    else:
        messagebox.showerror("Erro", f"Erro ao baixar o novo arquivo: {response.status_code}")
        sys.exit()

# Função para validar o conteúdo do arquivo .ini (validação de licença)
def valida_licenca(conteudo_ini):
    config = configparser.ConfigParser()
    config.read_string(conteudo_ini)

    try:
        confere_valor = config.get('valida', 'confere').strip()  # Remove espaços extras
        valores_validos = [v.strip() for v in confere_valor.replace(',', ' ').split()]

        # Verifica se '1' OU '2' estão na lista
        if '0' in valores_validos:
            print("✅ Validação ocorreu com êxito, Executando aplicação")
        else:
            messagebox.showerror("Erro", "❌ Validação não passou! Consulte o desenvolvedor para obter a licença!")
            sys.exit()

    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        messagebox.showerror("Erro", f"❌ Erro na validação! Consulte o desenvolvedor para obter a licença! {e}")
        sys.exit()

# URL do arquivo .ini no GitHub
url_github_ini = 'https://raw.githubusercontent.com/Bruno-BCR/valida/main/valida-contagem-estoque.ini'

# URL do arquivo atualizado (.py) no GitHub
url_novo_arquivo = 'https://raw.githubusercontent.com/Bruno-BCR/valida/a2125fb0ca9de613339c0f5f92be23d18ba4788e/Estoque.py'

# Versão atual do software
versao_atual = '1.0.1'  # Atualize conforme sua versão atual

# Baixar e validar o arquivo .ini
conteudo_ini = ler_arquivo_github(url_github_ini)  # Baixa o conteúdo do arquivo

# Validar a versão e licença
valida_versao(conteudo_ini, versao_atual, url_novo_arquivo)  # Valida versão
valida_licenca(conteudo_ini)  # Valida licença

# O restante do código continua normalmente abaixo...



# Nome do banco de dados
BANCO_DE_DADOS = "dados.db"
ultimos_bipados = []  

# Criar a tabela no banco de dados
def criar_tabela():
    conexao = sqlite3.connect(BANCO_DE_DADOS)
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barras TEXT UNIQUE,
            codigo TEXT,
            descricao TEXT,
            estoque INTEGER DEFAULT 0
        )
    """)
    conexao.close()

# Impede importação duplicada e importa os dados
def importar_excel():
    conexao = sqlite3.connect(BANCO_DE_DADOS)
    cursor = conexao.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone()[0] > 0:
        messagebox.showerror("Erro", "Já existem produtos cadastrados! Zere o banco antes de importar.")
        conexao.close()
        return

    arquivo_xlsx = filedialog.askopenfilename(filetypes=[("Arquivos Excel", "*.xlsx")])
    if not arquivo_xlsx:
        return  

    try:
        df = pd.read_excel(arquivo_xlsx, dtype={"barras": str, "codigo": str, "descricao": str})
        if not {"barras", "codigo", "descricao"}.issubset(df.columns):
            messagebox.showerror("Erro", "O arquivo precisa ter as colunas: barras, código e descrição.")
            return
        
        df["estoque"] = 0  
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO produtos (barras, codigo, descricao, estoque)
                    VALUES (?, ?, ?, ?)
                """, (row["barras"], row["codigo"], row["descricao"], 0))
            except sqlite3.IntegrityError:
                pass  

        conexao.commit()
        messagebox.showinfo("Sucesso", "Dados importados com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao importar: {e}")
    
    conexao.close()

# Função para visualizar os produtos cadastrados
def visualizar_dados():
    janela = tk.Toplevel(root)
    janela.title("Produtos Cadastrados")
    janela.geometry("500x300")

    tree = ttk.Treeview(janela, columns=("barras", "codigo", "descricao", "estoque"), show="headings")
    for col in ("barras", "codigo", "descricao", "estoque"):
        tree.heading(col, text=col.capitalize())
        tree.column(col, width=120)

    tree.pack(expand=True, fill="both")

    conexao = sqlite3.connect(BANCO_DE_DADOS)
    cursor = conexao.cursor()
    cursor.execute("SELECT barras, codigo, descricao, estoque FROM produtos")
    for row in cursor.fetchall():
        tree.insert("", tk.END, values=row)
    
    conexao.close()

# Função para criar o flip (combobox) para escolher "ACRESCENTAR" ou "REDUZIR"
def criar_flip_estoque():
    flip_estoque = ttk.Combobox(root, values=["ACRESCENTAR", "REDUZIR"], state="readonly", font=("Arial", 12))
    flip_estoque.set("ACRESCENTAR")  # Padrão é "ACRESCENTAR"
    flip_estoque.pack(pady=5)
    return flip_estoque

# Função para adicionar ou reduzir o estoque com base na seleção do flip
def adicionar_estoque(event=None):
    codigo_barras = entrada_codigo.get().strip().lstrip("0")
    if not codigo_barras:
        return  

    # Obtém a ação do Combobox
    acao = flip_estoque.get()

    conexao = sqlite3.connect(BANCO_DE_DADOS)
    cursor = conexao.cursor()
    cursor.execute("SELECT codigo, descricao, estoque FROM produtos WHERE barras = ?", (codigo_barras,))
    produto = cursor.fetchone()

    if produto:
        estoque_atual = produto[2]
        
        # Ajusta o estoque conforme a ação selecionada
        if acao == "ACRESCENTAR":
            novo_estoque = estoque_atual + 1
        elif acao == "REDUZIR":
            novo_estoque = max(estoque_atual - 1, 0)  # Evita que o estoque fique negativo

        cursor.execute("UPDATE produtos SET estoque = ? WHERE barras = ?", (novo_estoque, codigo_barras))
        conexao.commit()

        label_produto["text"] = f"📦 {produto[1]} - {produto[0]} (Novo estoque: {novo_estoque})"

        # Adiciona o produto à lista de últimos bipados
        ultimos_bipados.append((produto[0], produto[1], novo_estoque, codigo_barras))
        if len(ultimos_bipados) > 10:
            ultimos_bipados.pop(0)
    else:
        label_produto["text"] = "❌ Produto não encontrado!"

    conexao.close()
    entrada_codigo.delete(0, tk.END)

# Função para exportar produtos com estoque positivo
def exportar_dados():
    conexao = sqlite3.connect(BANCO_DE_DADOS)
    cursor = conexao.cursor()
    cursor.execute("SELECT codigo, estoque FROM produtos WHERE estoque > 0")
    produtos = cursor.fetchall()

    if produtos:
        df = pd.DataFrame(produtos, columns=["Código", "Estoque"])
        arquivo_saida = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])
        if arquivo_saida:
            df.to_excel(arquivo_saida, index=False)
            messagebox.showinfo("Sucesso", "Dados exportados com sucesso!")
    else:
        messagebox.showinfo("Aviso", "Não há produtos com estoque para exportar.")

    conexao.close()

# Função para zerar todos os estoques
def zerar_estoques():
    resposta = messagebox.askyesno("Confirmar ação", "Você tem certeza de que deseja zerar todos os estoques?")
    
    if resposta:
        conexao = sqlite3.connect(BANCO_DE_DADOS)
        cursor = conexao.cursor()
        cursor.execute("UPDATE produtos SET estoque = 0")
        conexao.commit()
        conexao.close()
        messagebox.showinfo("Sucesso", "Todos os estoques foram zerados!")
    else:
        messagebox.showinfo("Cancelado", "Ação de zerar estoques cancelada.")

# Função para zerar banco de dados (excluir todos os produtos)
def zerar_banco():
    def verificar_senha():
        senha = entry_senha.get()
        if senha == "123":
            conexao = sqlite3.connect(BANCO_DE_DADOS)
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM produtos")
            conexao.commit()
            conexao.close()
            messagebox.showinfo("Sucesso", "Banco de dados zerado!")
            janela_senha.destroy()
        else:
            messagebox.showerror("Erro", "Senha incorreta!")

    janela_senha = tk.Toplevel(root)
    janela_senha.title("Confirmação de Senha")
    janela_senha.geometry("300x150")

    tk.Label(janela_senha, text="Digite a senha:", font=("Arial", 12)).pack(pady=10)
    entry_senha = tk.Entry(janela_senha, show="*", font=("Arial", 12))
    entry_senha.pack(pady=5)
    tk.Button(janela_senha, text="Confirmar", command=verificar_senha, bg="red", fg="white", font=("Arial", 12)).pack(pady=10)

# Função para desfazer o último bipado
def desfazer_estoque():
    if not ultimos_bipados:
        messagebox.showinfo("Aviso", "Nenhum produto foi bipado ainda.")
        return

    janela_desfazer = tk.Toplevel(root)
    janela_desfazer.title("Desfazer Estoque de Produto")
    janela_desfazer.geometry("450x350")

    tree = ttk.Treeview(janela_desfazer, columns=("codigo", "descricao", "estoque"), show="headings")
    tree.heading("codigo", text="Código")
    tree.heading("descricao", text="Descrição")
    tree.heading("estoque", text="Estoque")

    for col in ("codigo", "descricao", "estoque"):
        tree.column(col, width=140)

    tree.pack(expand=True, fill="both")

    for produto in ultimos_bipados:
        tree.insert("", tk.END, values=(produto[0], produto[1], produto[2]))

# Função para reverter o último produto bipado
def reverter_ultimo_bipado():
    if not ultimos_bipados:
        messagebox.showinfo("Aviso", "Nenhum produto foi bipado ainda.")
        return

    produto = ultimos_bipados[-1]
    codigo_barras = produto[3]  

    conexao = sqlite3.connect(BANCO_DE_DADOS)
    cursor = conexao.cursor()

    cursor.execute("SELECT estoque FROM produtos WHERE barras = ?", (codigo_barras,))
    estoque_atual = cursor.fetchone()[0]

    if estoque_atual > 0:
        novo_estoque = estoque_atual - 1
        cursor.execute("UPDATE produtos SET estoque = ? WHERE barras = ?", (novo_estoque, codigo_barras))
        conexao.commit()

        produto_lista = list(produto)
        produto_lista[2] = novo_estoque
        ultimos_bipados[-1] = tuple(produto_lista)

        messagebox.showinfo("Sucesso", f"Estoque de {produto[1]} revertido para {novo_estoque}.")
        
        if novo_estoque == 0:
            ultimos_bipados.pop()
    else:
        messagebox.showerror("Erro", "O estoque já é zero! Não pode ser desfeito.")

    conexao.close()

# Função para mudar o estilo ao passar o mouse sobre os botões
def on_enter(event, widget, bg_color):
    widget.config(bg=bg_color)

def on_leave(event, widget, original_bg):
    widget.config(bg=original_bg)

# Criar a interface gráfica
root = ThemedTk()
root.set_theme("radiance")
root.title("Gestão de Estoque")
root.geometry("400x450")

criar_tabela()

tk.Label(root, text="🔹 Gerenciamento de Estoque", font=("Arial", 16, "bold"), fg="blue").pack(pady=10)

# Layout dos botões
frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=5)

button_importar = tk.Button(frame_buttons, text="📥 Importar", command=importar_excel, font=("Arial", 12), bg="#4682B4", width=12)
button_importar.pack(side="left", padx=5)
button_importar.bind("<Enter>", lambda event: on_enter(event, button_importar, "#5A9BD5"))
button_importar.bind("<Leave>", lambda event: on_leave(event, button_importar, "#4682B4"))

button_visualizar = tk.Button(frame_buttons, text="📊 Visualizar", command=visualizar_dados, font=("Arial", 12), bg="#32CD32", width=12)
button_visualizar.pack(side="left", padx=5)
button_visualizar.bind("<Enter>", lambda event: on_enter(event, button_visualizar, "#4bd64b"))
button_visualizar.bind("<Leave>", lambda event: on_leave(event, button_visualizar, "#32CD32"))

# Criando o flip (combobox) acima do campo de código de barras
flip_estoque = criar_flip_estoque()

# Input de código de barras
tk.Label(root, text="🔎 Digite o código de barras:", font=("Arial", 12)).pack(pady=5)
entrada_codigo = tk.Entry(root, bd=2, font=("Arial", 14))
entrada_codigo.pack(pady=5)
entrada_codigo.bind("<Return>", adicionar_estoque)

label_produto = tk.Label(root, text="", font=("Arial", 12), fg="blue")
label_produto.pack(pady=5)

# Outros botões
button_reverter = tk.Button(root, text="⏪ Reverter Estoque", command=reverter_ultimo_bipado, font=("Arial", 12), bg="#FFA500", width=25)
button_reverter.pack(pady=5)
button_reverter.bind("<Enter>", lambda event: on_enter(event, button_reverter, "#FF8C00"))
button_reverter.bind("<Leave>", lambda event: on_leave(event, button_reverter, "#FFA500"))

button_exportar = tk.Button(root, text="📤 Exportar Estoque", command=exportar_dados, font=("Arial", 12), bg="#32CD32", width=25)
button_exportar.pack(pady=5)
button_exportar.bind("<Enter>", lambda event: on_enter(event, button_exportar, "#4bd64b"))
button_exportar.bind("<Leave>", lambda event: on_leave(event, button_exportar, "#32CD32"))

button_zerar_estoques = tk.Button(root, text="⏺️ Zerar Estoques", command=zerar_estoques, font=("Arial", 12), bg="#FF6347", width=25)
button_zerar_estoques.pack(pady=5)
button_zerar_estoques.bind("<Enter>", lambda event: on_enter(event, button_zerar_estoques, "#FF4500"))
button_zerar_estoques.bind("<Leave>", lambda event: on_leave(event, button_zerar_estoques, "#FF6347"))

button_zerar_banco = tk.Button(root, text="❌ Zerar Banco", command=zerar_banco, font=("Arial", 12), bg="#808080", width=25)
button_zerar_banco.pack(pady=5)
button_zerar_banco.bind("<Enter>", lambda event: on_enter(event, button_zerar_banco, "#A9A9A9"))
button_zerar_banco.bind("<Leave>", lambda event: on_leave(event, button_zerar_banco, "#808080"))

root.mainloop()
