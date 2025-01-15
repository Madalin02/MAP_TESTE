import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
import random
import bcrypt
from datetime import datetime, timedelta
from ttkthemes import ThemedTk

class BankingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Internet Pay")
        self.root.geometry("400x600")

        self.colors = {
            'primary': '#0061F2',  
            'primary_dark': '#0052CC',  
            'secondary': '#F8F9FA',    
            'accent': '#FFDD00',      
            'text': '#2C3E50',         
            'text_light': '#FFFFFF',   
            'card_bg': '#0061F2',     
            'success': '#2ECC71',      
            'border': '#E9ECEF'        
        }

        # configurare stil
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # formatul frame-urilor
        self.style.configure('Modern.TFrame', background=self.colors['secondary'])
        self.style.configure('Modern.TLabel', background=self.colors['secondary'], foreground=self.colors['text'], font=('Segoe UI', 11))
        # formatul butoanelor
        self.style.configure('Modern.TButton', background=self.colors['primary'], foreground=self.colors['text_light'], font=('Segoe UI', 10, 'bold'), padding=(15, 10), borderwidth=0, relief='flat')
        
        self.connect_to_database()

        # initializare variabile globale
        self.current_user = None
        self.balance_visible = False  
        self.balance_button = None
        self.setup_login_screen()

    def connect_to_database(self):
        try:
            self.conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="", 
                database="banking"
            )
            self.cursor = self.conn.cursor()
        except mysql.connector.Error as err:
            messagebox.showerror("Eroare de conectare", f"Nu s-a putut conecta la baza de date: {err}")
            self.root.destroy()

    # creare dreptunghi cu colturi rotunde
    def create_rounded_rectangle(self, canvas, x1, y1, x2, y2, radius, fill='', outline=''):
        points = [
            x1 + radius, y1,     
            x2 - radius, y1,    
            x2, y1,              
            x2, y1 + radius,
            x2, y2 - radius,    
            x2, y2,
            x2 - radius, y2,     
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        
        return canvas.create_polygon(points, smooth=True, fill=fill, outline=outline)

    def create_card(self, card_canvas, card_number, card_name):
        self.create_rounded_rectangle(card_canvas, 0, 0, 340, 200, radius=20, fill='#F4EDE4', outline='#F4EDE4')
        card_canvas.create_text(20, 20, text="INTERNET BANKING", fill="black", font=('Arial', 10, 'bold'), anchor='w')

        # crearea cipului ca un dreptunghi cu colturi rotunde
        self.create_rounded_rectangle(card_canvas, 25, 70, 60, 95, radius=5, fill='#C0C0C0', outline='#A0A0A0')
        # creare text pentru numele utilizatorului
        card_canvas.create_text(25, 165, text=card_name.upper(), fill="black", font=('OCR-B', 9), anchor='w', tags="card_name_text")

        # creare detalii cip din paranteze rotunde si linii
        card_canvas.create_text(35, 75, text=")", fill="grey", font=('Arial', 8), anchor='e')
        card_canvas.create_text(35, 82, text=")", fill="grey", font=('Arial', 8), anchor='e')
        card_canvas.create_text(35, 89, text=")", fill="grey", font=('Arial', 8), anchor='e')
        card_canvas.create_text(33, 72, text="_", fill="grey", font=('Arial', 8), anchor='e')
        card_canvas.create_text(33, 82, text="_", fill="grey", font=('Arial', 8), anchor='e')
        card_canvas.create_text(49, 68, text="__", fill="grey", font=('Arial', 8), anchor='e')
        card_canvas.create_text(49, 87, text="__", fill="grey", font=('Arial', 8), anchor='e')
        card_canvas.create_text(55, 82, text="(", fill="grey", font=('Arial', 8), anchor='e')
        card_canvas.create_text(55, 89, text="(", fill="grey", font=('Arial', 8), anchor='e')
        card_canvas.create_text(60, 71, text="_", fill="grey", font=('Arial', 8), anchor='e')
        card_canvas.create_text(60, 81, text="_", fill="grey", font=('Arial', 8), anchor='e')

        # simbol contactless format din paranteze rotunde
        card_canvas.create_text(320, 80, text=")", fill="black", font=('Arial', 14, 'bold'), anchor='e')
        card_canvas.create_text(312, 80, text=")", fill="black", font=('Arial', 12, 'bold'), anchor='e')
        card_canvas.create_text(304, 80, text=")", fill="black", font=('Arial', 10, 'bold'), anchor='e')
        card_canvas.create_text(297, 80, text=")", fill="black", font=('Arial', 7, 'bold'), anchor='e')

        censored_card_number = "•" * 12 + card_number[-4:]
        formatted_card_number = "     ".join([censored_card_number[i:i+4] for i in range(0, len(censored_card_number), 4)])
        card_canvas.create_text(25, 130, text=formatted_card_number, 
                                fill="black", font=('OCR-A BT', 16), 
                                anchor='w')

        card_canvas.create_text(325, 170, text="VISA", 
                                fill="navy", font=('Arial', 16, 'bold', 'italic'), 
                                anchor='e')
        card_canvas.create_text(325, 185, text="Classic", 
                                fill="navy", font=('Arial', 8), 
                                anchor='e')

    def show_front_card(self):
        if hasattr(self, 'timer_id'):
            self.root.after_cancel(self.timer_id) # resetare id timer

        card_frame = self.main_frame.winfo_children()[0]
        card_canvas = card_frame.winfo_children()[0]

        card_canvas.delete("all") # curatare canvas
        self.remaining_time = 30 # resetare timer

        query = "SELECT card_number, name FROM users WHERE username=%s"
        self.cursor.execute(query, (self.current_user,))
        card_info = self.cursor.fetchone()

        if card_info:
            card_number = card_info[0]
            card_name = card_info[1]

            card_canvas.delete("card_name_text")

            self.create_card(card_canvas, card_number, card_name)

    def setup_main_screen(self):
        self.main_frame = ttk.Frame(self.root, style='Modern.TFrame')
        self.main_frame.pack(expand=True, fill='both')

        card_frame = ttk.Frame(self.main_frame, style='Modern.TFrame', relief='flat')
        card_frame.pack(pady=20)

        card_canvas = tk.Canvas(card_frame, width=340, height=200, bg='#F4EDE4', highlightthickness=0)
        card_canvas.pack()

        query = "SELECT card_number, name FROM users WHERE username=%s"
        self.cursor.execute(query, (self.current_user,))
        card_info = self.cursor.fetchone()

        if card_info:
            card_number = card_info[0]
            card_name = card_info[1]

            self.create_card(card_canvas, card_number, card_name) # apelare functie de generare card

        actions_frame = ttk.Frame(self.main_frame, style='Modern.TFrame')
        actions_frame.pack(pady=20)

        style = ttk.Style()
        style.configure('CustomBalance.TButton', background='#F8F9FA', foreground='#000000', font=('Segoe UI', 10, 'bold'), padding=(18, 6), borderwidth=0, anchor="center", focuscolor='none')

        # ascunderea hoverului pe buton folosind aceleasi culori ca fundalul aplicatiei
        style.map('CustomBalance.TButton', background=[('active', '#F8F9FA'), ('pressed', '#F8F9FA')])

        self.balance_button = ttk.Button(actions_frame, text="Vezi sold", style='CustomBalance.TButton', command=self.update_balance)
        self.balance_button.pack(pady=2)

        row1_frame = ttk.Frame(actions_frame, style='Modern.TFrame')
        row1_frame.pack(fill='x', pady=5)

        transfer_btn = ttk.Button(row1_frame, text="Transfer", style='Modern.TButton', command=self.show_transfers)
        transfer_btn.pack(side='left', expand=True, fill='x', padx=2)

        show_data_btn = ttk.Button(row1_frame, text="Afisare date", style='Modern.TButton', command=self.show_data)
        show_data_btn.pack(side='left', expand=True, fill='x', padx=2)

        row2_frame = ttk.Frame(actions_frame, style='Modern.TFrame')
        row2_frame.pack(fill='x', pady=5)

        history_btn = ttk.Button(row2_frame, text="Istoric tranzactii", style='Modern.TButton', command=self.show_history)
        history_btn.pack(side='left', expand=True, fill='x', padx=2)

    def update_balance(self): # preluam balanta contului userului din baza de date si o afisam
        if not self.balance_visible:
            query = "SELECT balance FROM users WHERE username=%s"
            self.cursor.execute(query, (self.current_user,))
            balance = self.cursor.fetchone()[0]
            
            self.balance_button.config(text=f"{balance} RON")
            self.balance_visible = True  
        else:
            self.balance_button.config(text="Vezi sold")
            self.balance_visible = False  

    def generate_romanian_iban(self):
        bank_code = "ITBK"
        account_number = ''.join([str(random.randint(0, 9)) for _ in range(16)])
        iban_without_check = f"RO00{bank_code}{account_number}"
        transformed = ""

        for char in iban_without_check[4:] + iban_without_check[:4]:
            if char.isalpha():
                transformed += str(ord(char.upper()) - 55)
            else:
                transformed += char
        
        check = 98 - (int(transformed) % 97)
        return f"RO{check:02d}{bank_code}{account_number}"

    def setup_login_screen(self):
        self.main_frame = ttk.Frame(self.root, style='Modern.TFrame')
        self.main_frame.pack(expand=True, fill='both')

        self.show_login_screen() # initializare frame de conectare

    def show_login_screen(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy() # stergere frame

        login_container = ttk.Frame(self.main_frame, style='Modern.TFrame', padding=(20, 20))
        login_container.place(relx=0.5, rely=0.5, anchor='center')

        title_label = ttk.Label(login_container, text="Internet Banking", style='Modern.TLabel', font=('Segoe UI', 18, 'bold'))
        title_label.pack(pady=(0, 20))

        self.login_entries_frame = ttk.Frame(login_container, style='Modern.TFrame')
        self.login_entries_frame.pack(fill='x')

        ttk.Label(self.login_entries_frame, text="Username", style='Modern.TLabel').pack(anchor='w')
        self.username_entry = ttk.Entry(self.login_entries_frame, width=25)
        self.username_entry.pack(fill='x', pady=(2, 10))

        ttk.Label(self.login_entries_frame, text="Parola", style='Modern.TLabel').pack(anchor='w')
        self.password_entry = ttk.Entry(self.login_entries_frame, show="\u2022", width=25)
        self.password_entry.pack(fill='x', pady=(2, 15))

        login_btn = ttk.Button(login_container, text="Autentificare", style='Modern.TButton', command=self.login)
        login_btn.pack(fill='x', pady=5)

        register_btn = ttk.Button(login_container, text="Inregistrare", style='Modern.TButton', command=self.show_register_screen)
        register_btn.pack(fill='x', pady=5)

    def show_register_screen(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy() # stergere frame

        register_container = ttk.Frame(self.main_frame, style='Modern.TFrame', padding=(20, 20))
        register_container.place(relx=0.5, rely=0.5, anchor='center')

        title_label = ttk.Label(register_container, text="Inregistrare", style='Modern.TLabel', font=('Segoe UI', 18, 'bold'))
        title_label.pack(pady=(0, 20))

        ttk.Label(register_container, text="Nume complet", style='Modern.TLabel').pack(anchor='w')
        self.fullname_entry = ttk.Entry(register_container, width=30)
        self.fullname_entry.pack(fill='x', pady=(2, 10))

        ttk.Label(register_container, text="Username", style='Modern.TLabel').pack(anchor='w')
        self.reg_username_entry = ttk.Entry(register_container, width=30)
        self.reg_username_entry.pack(fill='x', pady=(2, 10))

        ttk.Label(register_container, text="Parola", style='Modern.TLabel').pack(anchor='w')
        self.reg_password_entry = ttk.Entry(register_container, show="\u2022", width=30) # ascundem parola folosindu-ne de caracterele unicode-ul \u2022
        self.reg_password_entry.pack(fill='x', pady=(2, 10))

        register_btn = ttk.Button(register_container, text="Creeaza cont", style='Modern.TButton', command=self.register)
        register_btn.pack(fill='x', pady=5)

        back_btn = ttk.Button(register_container, text="Inapoi", style='Modern.TButton', command=self.show_login_screen)
        back_btn.pack(fill='x', pady=5)


    def back_to_login(self):
        self.register_frame.pack_forget()
        self.register_frame.destroy() # ascundem frame-ul de inregistrare

        self.login_frame.pack(expand=True, fill='both') # reafisare frame de logare

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Eroare", "Toate campurile trebuiesc completate.")
            return

        query = "SELECT * FROM users WHERE username=%s"
        self.cursor.execute(query, (username,))
        user = self.cursor.fetchone()

        if user:
            stored_hash = user[4]
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                self.current_user = username
                self.main_frame.destroy()
                self.setup_main_screen()
            else:
                messagebox.showerror("Eroare", "Username-ul introdus sau parola este incorecta.")
        else:
            messagebox.showerror("Eroare", "Username-ul introdus sau parola este incorecta.")


    def register(self):
        full_name = self.fullname_entry.get().strip() # preluare date din dialoguri
        username = self.reg_username_entry.get().strip()
        password = self.reg_password_entry.get().strip()

        # set de verificari
        if not full_name or not username or not password:
            messagebox.showerror("Eroare", "Toate campurile trebuiesc completate.")
            return

        if len(full_name) < 3:
            messagebox.showerror("Eroare", "Numele trebuie să aiba cel putin 3 caractere.")
            return

        if len(username) < 3:
            messagebox.showerror("Eroare", "Username-ul trebuie sa aiba cel putin 3 caractere.")
            return

        if len(password) < 6:
            messagebox.showerror("Eroare", "Parola trebuie să aiba cel putin 6 caractere.")
            return

        # criptare parola
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # generare date card
        card_number = "4000" + "".join([str(random.randint(0, 9)) for _ in range(12)])
        cvv = str(random.randint(100, 999))
        expiry_date = (datetime.now() + timedelta(days=3*365)).strftime("%m/%y")
        iban = self.generate_romanian_iban()

        # inserarea contului in baza de date
        query = """INSERT INTO users (username, name, password, balance, card_number, card_cvv, card_exp, iban) VALUES (%s, %s, %s, 0, %s, %s, %s, %s)"""

        try:
            self.cursor.execute(query, (username, full_name, hashed_password.decode('utf-8'), card_number, cvv, expiry_date, iban))
            self.conn.commit()
            messagebox.showinfo("Succes", "Contul a fost creat cu succes.")
            self.show_login_screen()
        except mysql.connector.IntegrityError:
            messagebox.showerror("Eroare", "Username-ul exista deja in baza de date.")

    def show_transfers(self):
        self.main_frame.destroy() # stergere frame pentru a crea unul nou
        self.main_frame = ttk.Frame(self.root, style='Modern.TFrame')
        self.main_frame.pack(expand=True, fill='both')

        transfer_container = ttk.Frame(self.main_frame, style='Modern.TFrame', padding=(20, 20))
        transfer_container.place(relx=0.5, rely=0.5, anchor='center')

        title_label = ttk.Label(transfer_container, text="Transfer", style='Modern.TLabel', font=('Segoe UI', 18, 'bold'))
        title_label.pack(pady=(0, 20))

        input_container = ttk.Frame(transfer_container, style='Modern.TFrame')
        input_container.pack(fill='x')

        ttk.Label(input_container, text="Username sau IBAN destinatar", style='Modern.TLabel').pack(anchor='w')
        self.recipient_entry = ttk.Entry(input_container, width=30)
        self.recipient_entry.pack(fill='x', pady=(2, 10))

        ttk.Label(input_container, text="Suma (RON)", style='Modern.TLabel').pack(anchor='w')
        self.amount_entry = ttk.Entry(input_container, width=30)
        self.amount_entry.pack(fill='x', pady=(2, 15))

        transfer_btn = ttk.Button(transfer_container, text="Transfera", style='Modern.TButton', command=self.make_transfer)
        transfer_btn.pack(fill='x', pady=5)

        back_btn = ttk.Button(transfer_container, text="Inapoi", style='Modern.TButton', command=self.return_to_main)
        back_btn.pack(fill='x', pady=5)

    def return_to_main(self):
        self.main_frame.destroy()
        self.setup_main_screen()

    def make_transfer(self):
        recipient = self.recipient_entry.get().strip()
        
        if recipient == self.current_user:
            messagebox.showerror("Eroare", "Nu poti transfera bani catre propriul tau cont.")
            return
            
        try:
            amount = float(self.amount_entry.get().strip())
        except ValueError:
            messagebox.showerror("Eroare", "Suma introdusa nu este valida.")
            return

        if amount <= 0:
            messagebox.showerror("Eroare", "Suma trebuie sa fie pozitiva.")
            return

        # preluare date despre contul bancar al userului
        self.cursor.execute("SELECT id, balance, iban FROM users WHERE username = %s", (self.current_user,))
        sender_data = self.cursor.fetchone()

        if not sender_data:
            messagebox.showerror("Eroare", "Eroare la procesarea transferului!")
            return
        
        sender_id, sender_balance, sender_iban = sender_data

        # erori specifice transferurilor
        if recipient == sender_iban:
            messagebox.showerror("Eroare", "Nu poti transfera bani catre propriul tau cont.")
            return

        if amount > sender_balance:
            messagebox.showerror("Eroare", "Detii fonduri insuficiente pentru a continua transferul.")
            return

        # cautare receiver pe baza la username sau IBAN
        self.cursor.execute("SELECT id, balance FROM users WHERE username = %s OR iban = %s", (recipient, recipient))
        recipient_data = self.cursor.fetchone()

        if not recipient_data:
            messagebox.showerror("Eroare", "Destinatarul nu a fost gasit.")
            return

        recipient_id = recipient_data[0]  # Extragem doar ID-ul din tuplu

        try:
            # actualizare balanta sender in sql
            self.cursor.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (amount, sender_id))
            # actualizare balanta receiver in sql
            self.cursor.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (amount, recipient_id))
            # inserare transfer in tabelul transfers pentru a vedea in viitor istoricul tranzactiilor
            self.cursor.execute("""INSERT INTO transfers (sender_id, recipient_id, amount) VALUES (%s, %s, %s)""", (sender_id, recipient_id, amount))

            self.conn.commit() # efectuarea transferului
            messagebox.showinfo("Succes", f"Transfer de {amount} RON efectuat cu succes!")
            
            self.return_to_main()

        except mysql.connector.Error as err:
            self.conn.rollback() # rollback in caz de eroare
            messagebox.showerror("Eroare", f"Eroare la procesarea transferului: {err}")

    def show_data(self):
        card_frame = self.main_frame.winfo_children()[0]
        card_canvas = card_frame.winfo_children()[0]
        
        actions_frame = self.main_frame.winfo_children()[1]
        row1_frame = actions_frame.winfo_children()[1]
        show_data_btn = row1_frame.winfo_children()[1]
        
        if show_data_btn['text'] == "Afisare date":
            show_data_btn.configure(text="Ascundere date") # modificare text buton in "Ascundere"
            
            query = "SELECT card_number, card_cvv, card_exp FROM users WHERE username=%s" # preluare date card pe baza username-ului
            self.cursor.execute(query, (self.current_user,))
            card_info = self.cursor.fetchone()

            if card_info:
                card_number, cvv, exp_date = card_info
                
                card_canvas.delete("all") # curatare canvas

                self.create_rounded_rectangle(card_canvas, 0, 0, 340, 200, radius=20, fill='#F4EDE4', outline='#F4EDE4') # creare spate card

                card_canvas.create_rectangle(0, 20, 340, 60, fill='#1A1A1A') # linie magnetica neagra
                card_canvas.create_rectangle(0, 90, 120, 110, fill='#e5d5c0', outline='#e5d5c0') # linie CVV
                card_canvas.create_rectangle(160, 90, 120, 110, fill='#FFFFFF', outline='#FFFFFF') # linie magnetica pentru CVV

                # creare timer
                self.remaining_time = 30 
                self.time_label = card_canvas.create_text(315, 40, text=f"0:{self.remaining_time:02d}", 
                                                        fill="white", font=('Digital-7', 10, 'bold'))

                # afisare informatii card
                card_canvas.create_text(10, 160, text="Numar card", fill="black", font=('Arial', 10), anchor='w')
                formatted_card_number = " ".join([card_number[i:i+4] for i in range(0, len(card_number), 4)])
                card_canvas.create_text(10, 180, text=formatted_card_number, fill="black", font=('OCR-A BT', 12), anchor='w')

                card_canvas.create_text(87, 100, text="CVV", fill="black", font=('Arial', 10), anchor='w')
                card_canvas.create_text(125, 100, text=cvv, fill="black", font=('OCR-A BT', 12), anchor='w')

                card_canvas.create_text(280, 160, text="Exp", fill="black", font=('Arial', 10), anchor='w')
                card_canvas.create_text(280, 180, text=exp_date, fill="black", font=('OCR-A BT', 12), anchor='w')

            if hasattr(self, 'timer_id'):
                self.root.after_cancel(self.timer_id)

            def update_timer():
                if self.remaining_time > 0:
                    self.remaining_time -= 1
                    card_canvas.itemconfig(self.time_label, text=f"0:{self.remaining_time:02d}")
                    self.timer_id = self.root.after(1000, update_timer)
                else:
                    show_data_btn.configure(text="Afisare date")
                    self.show_front_card()

            update_timer()
        else:
            if hasattr(self, 'timer_id'): # reafisare meniu principal dupa ce expira timerul
                self.root.after_cancel(self.timer_id)

            show_data_btn.configure(text="Afisare date")
            self.show_front_card()

    def show_history(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        main_container = ttk.Frame(self.main_frame, style='Modern.TFrame')
        main_container.pack(expand=True, fill='both', padx=20, pady=20)  

        card_frame = ttk.Frame(main_container, style='Modern.TFrame', relief='flat')
        card_frame.pack(pady=(10, 10)) 

        card_canvas = tk.Canvas(card_frame, width=340, height=200, bg='#F4EDE4', highlightthickness=0)
        card_canvas.pack()

        # preluare numar card si nume din tabelul sql
        query = "SELECT card_number, name FROM users WHERE username=%s"
        self.cursor.execute(query, (self.current_user,))
        card_info = self.cursor.fetchone()

        if card_info:
            card_number = card_info[0]
            card_name = card_info[1]
            self.create_card(card_canvas, card_number, card_name)

        history_container = ttk.Frame(main_container, style='Modern.TFrame')
        history_container.pack(fill='both', expand=True, pady=10)  

        title_label = ttk.Label(history_container, text="Istoric tranzacții", 
                            style='Modern.TLabel', font=('Segoe UI', 14, 'bold'))  
        title_label.pack(pady=(0, 10)) 

        # configurarea stilului pentru tabel
        style = ttk.Style()
        style.configure("Minimal.Treeview",
                    font=('Segoe UI', 9),  
                    rowheight=25)        
        
        style.configure("Minimal.Treeview.Heading",
                    font=('Segoe UI', 9, 'bold'), 
                    padding=(5, 2))                

        table_frame = ttk.Frame(history_container, style='Modern.TFrame')
        table_frame.pack(fill='both', expand=True)

        # creare scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side='right', fill='y')

        # creare tabel
        columns = ('De la', 'Catre', 'Suma', 'Data')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', 
                            height=6, 
                            selectmode='none',
                            style="Minimal.Treeview")
        tree.pack(fill='both', expand=True)

        scrollbar.config(command=tree.yview) 
        tree.config(yscrollcommand=scrollbar.set)

        # configurare coloane
        tree.heading('De la', text='De la')
        tree.heading('Catre', text='Catre')
        tree.heading('Suma', text='Suma')
        tree.heading('Data', text='Data')

        # setarea dimensiunilor coloanelor
        tree.column('De la', width=80, anchor='center')
        tree.column('Catre', width=80, anchor='center')
        tree.column('Suma', width=80, anchor='center')
        tree.column('Data', width=100, anchor='center')

        # interogare pentru a obtine istoricul tranzactiilor
        query = """
        SELECT sender.name AS sender_name, recipient.name AS recipient_name, t.amount, t.transfer_date FROM transfers t JOIN users sender ON t.sender_id = sender.id
        JOIN users recipient ON t.recipient_id = recipient.id WHERE t.sender_id = (SELECT id FROM users WHERE username = %s) OR t.recipient_id = (SELECT id FROM users WHERE username = %s)
        ORDER BY t.transfer_date DESC LIMIT 10
        """
        
        self.cursor.execute(query, (self.current_user, self.current_user))
        transfers = self.cursor.fetchall()

        for transfer in transfers: # iterare prin rezultatele interogarii
            date = transfer[3].strftime("%d-%m-%Y")  
            sender_name = transfer[0].split()[0]  
            recipient_name = transfer[1].split()[0]  
            amount = f"{transfer[2]:.2f}"
            
            if sender_name == card_name.split()[0]: 
                amount = f"-{amount}"
                tree.insert('', 'end', values=(date, sender_name, recipient_name, amount),
                        tags=('sent',))
            else:
                amount = f"+{amount}"
                tree.insert('', 'end', values=(date, sender_name, recipient_name, amount),
                        tags=('received',))

        tree.tag_configure('sent', foreground='#FF6B6B')
        tree.tag_configure('received', foreground='#4CAF50')

        back_btn = ttk.Button(history_container, text="Inapoi", # buton de inapoi
                            style='Modern.TButton', command=self.return_to_main)
        back_btn.pack(pady=10)  

if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    app = BankingApp(root)
    root.mainloop()
