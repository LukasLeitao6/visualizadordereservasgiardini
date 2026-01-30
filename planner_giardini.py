import customtkinter as ctk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime, timedelta
from PIL import Image
from tkcalendar import Calendar

# --- CONFIGURAÇÃO VISUAL ---
# Extraído aproximado da sua imagem (Verde Giardini)
COR_VERDE_GIARDINI = "#0f4d2a" 
COR_BRANCO = "#FFFFFF"

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("green")

class GiardiniPlannerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuração da Janela
        self.title("Giardini Café - Planner e Reservas")
        self.geometry("900x600")
        self.configure(fg_color=COR_BRANCO)

        # Inicializa Banco de Dados
        self.init_db()

        # Layout Principal (Grid)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- MENU LATERAL ---
        self.frame_menu = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=COR_VERDE_GIARDINI)
        self.frame_menu.grid(row=0, column=0, sticky="nsew")
        self.frame_menu.grid_rowconfigure(5, weight=1)

        # Logo (Placeholder de texto ou Imagem se disponível)
        try:
            # Tente carregar a imagem se ela existir na pasta
            img_logo = ctk.CTkImage(Image.open("logo_giardini.png"), size=(150, 150))
            self.lbl_logo = ctk.CTkLabel(self.frame_menu, text="", image=img_logo)
        except:
            self.lbl_logo = ctk.CTkLabel(self.frame_menu, text="GIARDINI\nCAFÉ", font=("Times New Roman", 24, "bold"), text_color="white")
        
        self.lbl_logo.grid(row=0, column=0, padx=20, pady=(20, 40))

        # Botões do Menu
        self.btn_nova_reserva = self.criar_botao_menu("Adicionar Reserva", self.abrir_popup_reserva, 1)
        self.btn_ver_planner = self.criar_botao_menu("Ver Planner (Semana)", self.ver_planner_semanal, 2)
        self.btn_todas_reservas = self.criar_botao_menu("Ver Todas Reservas", self.ver_todas_reservas, 3)

        # --- ÁREA DE CONTEÚDO ---
        self.frame_conteudo = ctk.CTkFrame(self, corner_radius=0, fg_color=COR_BRANCO)
        self.frame_conteudo.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        # Conteúdo Inicial
        self.lbl_titulo = ctk.CTkLabel(self.frame_conteudo, text="Bem-vindo ao Planner Giardini", font=("Arial", 24), text_color=COR_VERDE_GIARDINI)
        self.lbl_titulo.pack(pady=20)

    def criar_botao_menu(self, texto, comando, row):
        btn = ctk.CTkButton(self.frame_menu, text=texto, command=comando, 
                            fg_color="transparent", border_width=2, border_color="white", 
                            text_color="white", hover_color="#0b381e", anchor="w")
        btn.grid(row=row, column=0, padx=20, pady=10, sticky="ew")
        return btn

    # --- BANCO DE DADOS ---
    def init_db(self):
        self.conn = sqlite3.connect("giardini_reservas.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                telefone TEXT,
                pessoas INTEGER,
                local TEXT,
                consumacao TEXT,
                data TEXT,
                hora TEXT
            )
        """)
        self.conn.commit()

    # --- FUNCIONALIDADE 1: ADICIONAR RESERVA ---
    def abrir_popup_reserva(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Nova Reserva")
        popup.geometry("400x600")
        popup.attributes("-topmost", True)

        # Campos
        ctk.CTkLabel(popup, text="Nome do Cliente:").pack(pady=5)
        entry_nome = ctk.CTkEntry(popup)
        entry_nome.pack(pady=5)

        ctk.CTkLabel(popup, text="Telefone:").pack(pady=5)
        entry_tel = ctk.CTkEntry(popup)
        entry_tel.pack(pady=5)

        ctk.CTkLabel(popup, text="Nº de Pessoas:").pack(pady=5)
        entry_pessoas = ctk.CTkEntry(popup)
        entry_pessoas.pack(pady=5)

        ctk.CTkLabel(popup, text="Local do Evento:").pack(pady=5)
        entry_local = ctk.CTkEntry(popup)
        entry_local.pack(pady=5)
        
        check_consumacao_var = ctk.StringVar(value="Não")
        check_consumacao = ctk.CTkCheckBox(popup, text="Consumação Paga à Parte?", variable=check_consumacao_var, onvalue="Sim", offvalue="Não")
        check_consumacao.pack(pady=10)

        ctk.CTkLabel(popup, text="Data da Reserva:").pack(pady=5)
        cal = Calendar(popup, selectmode='day', date_pattern='yyyy-mm-dd')
        cal.pack(pady=5)

        ctk.CTkLabel(popup, text="Horário (HH:MM):").pack(pady=5)
        entry_hora = ctk.CTkEntry(popup)
        entry_hora.pack(pady=5)

        def salvar():
            data = cal.get_date()
            hora = entry_hora.get()
            
            # Validação simples
            if not data or not hora:
                messagebox.showwarning("Erro", "Preencha data e hora!")
                return

            # Verifica conflito
            self.cursor.execute("SELECT * FROM reservas WHERE data = ? AND hora = ?", (data, hora))
            conflito = self.cursor.fetchone()

            confirmar = True
            if conflito:
                confirmar = messagebox.askyesno("Conflito de Horário", 
                                                f"Já existe uma reserva para {data} às {hora}.\nDeseja reservar mesmo assim?")
            
            if confirmar:
                self.cursor.execute("""
                    INSERT INTO reservas (nome, telefone, pessoas, local, consumacao, data, hora)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (entry_nome.get(), entry_tel.get(), entry_pessoas.get(), entry_local.get(), check_consumacao_var.get(), data, hora))
                self.conn.commit()
                messagebox.showinfo("Sucesso", "Reserva salva com sucesso!")
                popup.destroy()

        ctk.CTkButton(popup, text="SALVAR RESERVA", fg_color=COR_VERDE_GIARDINI, command=salvar).pack(pady=20)

    # --- FUNCIONALIDADE 2 e 3: VISUALIZAR ---
    def limpar_conteudo(self):
        for widget in self.frame_conteudo.winfo_children():
            widget.destroy()

    def criar_tabela(self, dados):
        self.limpar_conteudo()
        
        colunas = ("ID", "Data", "Hora", "Nome", "Tel", "Pessoas", "Local", "Consumação")
        tree = ttk.Treeview(self.frame_conteudo, columns=colunas, show="headings", height=20)
        
        # Estilizando a tabela para combinar
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview.Heading", background=COR_VERDE_GIARDINI, foreground="white", font=('Arial', 10, 'bold'))

        for col in colunas:
            tree.heading(col, text=col)
            tree.column(col, width=80)
        
        tree.column("Nome", width=150) # Mais espaço para nome

        for linha in dados:
            tree.insert("", "end", values=linha)

        tree.pack(expand=True, fill="both", padx=10, pady=10)

    def ver_todas_reservas(self):
        self.cursor.execute("SELECT * FROM reservas ORDER BY data, hora")
        dados = self.cursor.fetchall()
        self.criar_tabela(dados)

    def ver_planner_semanal(self):
        # Lógica para pegar segunda a domingo da semana atual
        hoje = datetime.now().date()
        inicio_semana = hoje - timedelta(days=hoje.weekday()) # Segunda-feira
        fim_semana = inicio_semana + timedelta(days=6) # Domingo

        query = "SELECT * FROM reservas WHERE data BETWEEN ? AND ? ORDER BY data, hora"
        self.cursor.execute(query, (inicio_semana, fim_semana))
        dados = self.cursor.fetchall()
        
        self.criar_tabela(dados)
        
        # Título informativo
        lbl = ctk.CTkLabel(self.frame_conteudo, text=f"Exibindo semana: {inicio_semana.strftime('%d/%m')} até {fim_semana.strftime('%d/%m')}", 
                           text_color=COR_VERDE_GIARDINI, font=("Arial", 16, "bold"))
        lbl.pack(before=self.frame_conteudo.winfo_children()[0], pady=10)

if __name__ == "__main__":
    app = GiardiniPlannerApp()
    app.mainloop()