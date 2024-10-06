import customtkinter as ctk
import mysql.connector
from mysql.connector import Error
import requests
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime
import os
from openpyxl import Workbook
import math
from tkinter import Canvas, Frame
import tkinter as tk

ctk.set_appearance_mode("dark")  # Activer le mode sombre par défaut
BACKGROUND_COLOR = "#1e1e1e"
BUTTON_COLOR = "#3a3a3a"
TEXT_COLOR = "#ffffff"
TABLE_COLOR = "#2e2e2e"


class ScrollableTableGrid(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.canvas = Canvas(
            self, borderwidth=0, highlightthickness=0, width=300, height=40
        )
        self.frame = Frame(self.canvas, width=300, height=40)
        self.vsb = ctk.CTkScrollbar(
            self, orientation="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window(
            (4, 4), window=self.frame, anchor="nw", tags="self.frame"
        )
        self.frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class ConnectionWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Connexion à la base de données")
        self.geometry("400x300")
        self.resizable(False, False)
        self.grab_set()
        self.focus_set()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.title_label = ctk.CTkLabel(
            self, text="Connexion MySQL", font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, pady=(20, 10), sticky="ew")
        self.frame = ctk.CTkFrame(self)
        self.frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.frame.grid_columnconfigure(1, weight=1)
        self.host_entry = self.create_entry(self.frame, "Hôte:", 0)
        self.user_entry = self.create_entry(self.frame, "Utilisateur:", 1)
        self.password_entry = self.create_entry(
            self.frame, "Mot de passe:", 2, show="*"
        )
        self.database_entry = self.create_entry(self.frame, "Base de données:", 3)
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.grid(row=2, column=0, padx=20, pady=(10, 20), sticky="ew")
        self.button_frame.grid_columnconfigure((0, 1), weight=1)
        self.connect_button = ctk.CTkButton(
            self.button_frame, text="Se connecter", command=self.connect
        )
        self.connect_button.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="ew")
        self.cancel_button = ctk.CTkButton(
            self.button_frame, text="Annuler", command=self.destroy
        )
        self.cancel_button.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="ew")

    def create_entry(self, parent, label_text, row, show=None):
        label = ctk.CTkLabel(parent, text=label_text)
        label.grid(row=row, column=0, padx=(10, 5), pady=5, sticky="e")
        entry = ctk.CTkEntry(parent, show=show)
        entry.grid(row=row, column=1, padx=(5, 10), pady=5, sticky="ew")
        return entry

    def connect(self):
        host = self.host_entry.get()
        user = self.user_entry.get()
        password = self.password_entry.get()
        database = self.database_entry.get()
        if not all([host, user, password, database]):
            messagebox.showwarning(
                "Champs manquants", "Veuillez remplir tous les champs."
            )
            return
        self.master.connect_to_database(host, user, password, database)
        self.destroy()


class AIAssistantWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Assistant IA")
        self.geometry("600x400")
        self.resizable(True, True)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.chat_history = ctk.CTkTextbox(self, state="disabled")
        self.chat_history.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.user_input = ctk.CTkEntry(self.input_frame)
        self.user_input.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.send_button = ctk.CTkButton(
            self.input_frame, text="Envoyer", command=self.send_message
        )
        self.send_button.grid(row=0, column=1)

    def send_message(self):
        user_message = self.user_input.get()
        self.user_input.delete(0, "end")
        self.update_chat_history(f"Vous : {user_message}")
        ai_response = self.get_ai_response(user_message)
        self.update_chat_history(f"Assistant : {ai_response}")

    def update_chat_history(self, message):
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", message + "\n\n")
        self.chat_history.configure(state="disabled")
        self.chat_history.see("end")

    def get_ai_response(self, user_message):
        """Appel à l'API Mistral AI pour interpréter la demande utilisateur et générer la commande SQL."""
        try:
            api_url = "https://api.mistral.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer TAYWvVnNyLn7gyHH3soHMIQjpOXwl9xE",
                "Content-Type": "application/json",
            }
            messages = [
                {
                    "role": "system",
                    "content": "Tu es un assistant spécialisé dans la génération de requêtes SQL. Traduis les demandes en langage naturel en requêtes SQL valides.",
                },
                {
                    "role": "user",
                    "content": f"Transforme la demande suivante en une commande SQL : '{user_message}'. Ne retourne que la commande SQL.",
                },
            ]
            payload = {
                "model": "mistral-tiny",
                "messages": messages,
                "max_tokens": 150,
                "temperature": 0.3,
            }
            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"].strip()
            else:
                return "Erreur : Réponse inattendue de l'API."
        except requests.exceptions.HTTPError as http_err:
            return f"Erreur HTTP : {http_err}"
        except Exception as e:
            return f"Erreur : {str(e)}"


class CommandsWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Liste des commandes")
        self.geometry("1500x700")
        self.resizable(True, True)
        self.grab_set()
        self.focus_set()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.frame = ctk.CTkFrame(self)
        self.frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        self.commands = [
            (
                "CREATE TABLE",
                "crée une nouvelle table",
                "Exemple : CREATE TABLE nom_table (id INT, nom VARCHAR(255));",
            ),
            (
                "INSERT INTO",
                "ajoute une nouvelle ligne à une table",
                "Exemple : INSERT INTO nom_table (id, nom) VALUES (1, 'Alice');",
            ),
            ("DROP TABLE", "supprime une table", "Exemple : DROP TABLE nom_table;"),
            (
                "SELECT *",
                "sélectionne toutes les lignes d'une table",
                "Exemple : SELECT * FROM nom_table;",
            ),
            (
                "UPDATE",
                "met à jour une ligne dans une table",
                "Exemple : UPDATE nom_table SET nom = 'Bob' WHERE id = 1;",
            ),
            (
                "DELETE",
                "supprime des lignes d'une table",
                "Exemple : DELETE FROM nom_table WHERE id = 1;",
            ),
            (
                "TRUNCATE TABLE",
                "supprime toutes les lignes d'une table sans supprimer la table elle-même",
                "Exemple : TRUNCATE TABLE nom_table;",
            ),
            (
                "CREATE INDEX",
                "crée un index sur une table",
                "Exemple : CREATE INDEX idx_nom ON nom_table (nom);",
            ),
            (
                "DROP INDEX",
                "supprime un index d'une table",
                "Exemple : DROP INDEX idx_nom ON nom_table;",
            ),
            (
                "ALTER TABLE ADD",
                "ajoute une colonne à une table",
                "Exemple : ALTER TABLE nom_table ADD age INT;",
            ),
            (
                "ALTER TABLE DROP",
                "supprime une colonne d'une table",
                "Exemple : ALTER TABLE nom_table DROP COLUMN age;",
            ),
            (
                "RENAME TABLE",
                "renomme une table",
                "Exemple : RENAME TABLE nom_table TO nouvelle_table;",
            ),
            (
                "CREATE USER",
                "crée un utilisateur MySQL",
                "Exemple : CREATE USER 'utilisateur'@'localhost' IDENTIFIED BY 'mot_de_passe';",
            ),
            (
                "DROP USER",
                "supprime un utilisateur MySQL",
                "Exemple : DROP USER 'utilisateur'@'localhost';",
            ),
            (
                "GRANT",
                "donne des droits à un utilisateur sur une base de données",
                "Exemple : GRANT ALL PRIVILEGES ON base_de_donnees.* TO 'utilisateur'@'localhost';",
            ),
            (
                "REVOKE",
                "révoque des droits d'un utilisateur sur une base de données",
                "Exemple : REVOKE ALL PRIVILEGES ON base_de_donnees.* FROM 'utilisateur'@'localhost';",
            ),
            (
                "BACKUP DATABASE",
                "sauvegarde une base de données",
                "Exemple : mysqldump -u utilisateur -p base_de_donnees > sauvegarde.sql;",
            ),
            (
                "RESTORE DATABASE",
                "restaure une base de données depuis une sauvegarde",
                "Exemple : mysql -u utilisateur -p base_de_donnees < sauvegarde.sql;",
            ),
            ("BEGIN", "démarre une nouvelle transaction", "Exemple : BEGIN;"),
            (
                "COMMIT",
                "valide les modifications effectuées dans une transaction",
                "Exemple : COMMIT;",
            ),
            (
                "ROLLBACK",
                "annule les modifications d'une transaction",
                "Exemple : ROLLBACK;",
            ),
            (
                "CREATE VIEW",
                "crée une vue",
                "Exemple : CREATE VIEW nom_vue AS SELECT * FROM nom_table;",
            ),
            ("DROP VIEW", "supprime une vue", "Exemple : DROP VIEW nom_vue;"),
            (
                "CREATE PROCEDURE",
                "crée une procédure stockée",
                "Exemple : CREATE PROCEDURE nom_procedure() BEGIN ... END;",
            ),
            (
                "DROP PROCEDURE",
                "supprime une procédure stockée",
                "Exemple : DROP PROCEDURE nom_procedure;",
            ),
            (
                "EXPLAIN",
                "fournit des informations sur la manière dont MySQL exécute une requête",
                "Exemple : EXPLAIN SELECT * FROM nom_table;",
            ),
            (
                "SHOW TABLES",
                "affiche la liste des tables dans une base de données",
                "Exemple : SHOW TABLES;",
            ),
            (
                "SHOW DATABASES",
                "affiche la liste des bases de données disponibles",
                "Exemple : SHOW DATABASES;",
            ),
        ]
        self.tree = ttk.Treeview(
            self.frame, columns=("Command", "Description", "Example"), show="headings"
        )
        self.tree.heading("Command", text="Commande")
        self.tree.heading("Description", text="Description")
        self.tree.heading("Example", text="Exemple")
        self.tree.column("Command", width=300, anchor="w")
        self.tree.column("Description", width=450, anchor="w")
        self.tree.column("Example", width=300, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        for command in self.commands:
            self.tree.insert("", "end", values=command)
        self.scrollbar = ttk.Scrollbar(
            self.frame, orient="vertical", command=self.tree.yview
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.download_button = ctk.CTkButton(
            self, text="Télécharger la liste", command=self.download_commands
        )
        self.download_button.grid(row=1, column=0, pady=10)
        self.close_button = ctk.CTkButton(self, text="Fermer", command=self.destroy)
        self.close_button.grid(row=2, column=0, pady=10)

    def download_commands(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Enregistrer la liste des commandes",
        )
        if file_path:
            self.save_commands_to_excel(file_path)

    def save_commands_to_excel(self, file_path):
        wb = Workbook()
        ws = wb.active
        ws.title = "Liste des commandes"
        ws.append(["Commande", "Description", "Exemple"])
        for command in self.commands:
            ws.append(command)
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = max_length + 2
            ws.column_dimensions[column_letter].width = adjusted_width
        wb.save(file_path)
        messagebox.showinfo(
            "Téléchargement terminé",
            f"La liste des commandes a été téléchargée dans le fichier '{file_path}'",
        )


class DatabaseHistory:
    def __init__(self, filename="database_history.json"):
        self.filename = filename
        self.history = self.load_history()

    def load_history(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r") as f:
                return json.load(f)
        return []

    def save_history(self):
        with open(self.filename, "w") as f:
            json.dump(self.history, f)

    def add_entry(self, command, result):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "result": result,
        }
        self.history.append(entry)
        self.save_history()


class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, master, history):
        super().__init__(master)
        self.title("Historique de la base de données")
        self.geometry("800x600")
        self.history = history
        self.grab_set()
        self.focus_set()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.frame = ctk.CTkFrame(self)
        self.frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(
            self.frame, columns=("Timestamp", "Command", "Result"), show="headings"
        )
        self.tree.heading("Timestamp", text="Horodatage")
        self.tree.heading("Command", text="Commande")
        self.tree.heading("Result", text="Résultat")
        self.tree.column("Timestamp", width=200)
        self.tree.column("Command", width=300)
        self.tree.column("Result", width=300)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = ttk.Scrollbar(
            self.frame, orient="vertical", command=self.tree.yview
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.load_history()
        self.download_button = ctk.CTkButton(
            self, text="Télécharger l'historique", command=self.download_history
        )
        self.download_button.grid(row=1, column=0, pady=10)

    def load_history(self):
        for entry in self.history.history:
            self.tree.insert(
                "",
                "end",
                values=(entry["timestamp"], entry["command"], entry["result"]),
            )

    def download_history(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Enregistrer l'historique",
        )
        if file_path:
            self.save_history_to_excel(file_path)

    def save_history_to_excel(self, file_path):
        wb = Workbook()
        ws = wb.active
        ws.title = "Historique de la base de données"
        ws.append(["Horodatage", "Commande", "Résultat"])
        for entry in self.history.history:
            ws.append([entry["timestamp"], entry["command"], entry["result"]])
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = max_length + 2
            ws.column_dimensions[column_letter].width = adjusted_width
        wb.save(file_path)
        messagebox.showinfo(
            "Téléchargement terminé",
            f"L'historique a été téléchargé dans le fichier '{file_path}'",
        )


class DatabaseOverviewWindow(ctk.CTkToplevel):
    def __init__(self, master, connection):
        super().__init__(master)
        self.title("Aperçu de la base de données")
        self.geometry("800x600")
        self.connection = connection
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.frame = ctk.CTkFrame(self)
        self.frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(
            self.frame, columns=("Table", "Columns", "Rows"), show="headings"
        )
        self.tree.heading("Table", text="Table")
        self.tree.heading("Columns", text="Colonnes")
        self.tree.heading("Rows", text="Lignes")
        self.tree.column("Table", width=200)
        self.tree.column("Columns", width=400)
        self.tree.column("Rows", width=100)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = ttk.Scrollbar(
            self.frame, orient="vertical", command=self.tree.yview
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.load_database_overview()
        self.download_button = ctk.CTkButton(
            self, text="Télécharger l'aperçu", command=self.download_overview
        )
        self.download_button.grid(row=1, column=0, pady=10)

    def load_database_overview(self):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"DESCRIBE {table_name}")
                    columns = cursor.fetchall()
                    column_names = ", ".join([col[0] for col in columns])
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    self.tree.insert(
                        "", "end", values=(table_name, column_names, row_count)
                    )
        except Error as e:
            messagebox.showerror(
                "Erreur",
                f"Une erreur est survenue lors du chargement de l'aperçu de la base de données : {e}",
            )

    def download_overview(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Enregistrer l'aperçu de la base de données",
        )
        if file_path:
            self.save_overview_to_excel(file_path)

    def save_overview_to_excel(self, file_path):
        wb = Workbook()
        ws = wb.active
        ws.title = "Aperçu de la base de données"
        ws.append(["Table", "Colonnes", "Lignes"])
        for item in self.tree.get_children():
            values = self.tree.item(item)["values"]
            ws.append(values)
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = max_length + 2
            ws.column_dimensions[column_letter].width = adjusted_width
        wb.save(file_path)
        messagebox.showinfo(
            "Téléchargement terminé",
            f"L'aperçu de la base de données a été téléchargé dans le fichier '{file_path}'",
        )


class MySQLDBAInterface(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Assistant DBA MySQL")
        self.geometry("1400x800")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.current_page = 1
        self.page_size = 100
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.create_sidebar()
        self.create_main_frame()
        self.connection = None
        self.history = DatabaseHistory()
        self.current_table = None
        self.current_filter = ""

    def create_main_frame(self):
        self.main_frame = ctk.CTkScrollableFrame(self, fg_color="#2E2E2E")
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=1)
        self.create_table_selector()
        self.create_input_area()
        self.create_output_area()
        self.create_result_table()
        self.create_pagination_buttons()

    def create_pagination_buttons(self):
        self.pagination_frame = ctk.CTkFrame(self.main_frame, fg_color="#2E2E2E")
        self.pagination_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        self.previous_button = ctk.CTkButton(
            self.pagination_frame,
            text="Page précédente",
            command=self.previous_page,
            height=35,
            corner_radius=8,
        )
        self.previous_button.grid(row=0, column=0, padx=10, pady=10)
        self.next_button = ctk.CTkButton(
            self.pagination_frame,
            text="Page suivante",
            command=self.next_page,
            height=35,
            corner_radius=8,
        )
        self.next_button.grid(row=0, column=1, padx=10, pady=10)
        self.page_label = ctk.CTkLabel(
            self.pagination_frame, text=f"Page {self.current_page}"
        )
        self.page_label.grid(row=0, column=2, padx=10, pady=10)

    def display_table_content(self, table_name):
        self.current_table = table_name
        try:
            query = f"SELECT * FROM {table_name} LIMIT {self.page_size} OFFSET {(self.current_page - 1) * self.page_size};"
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [i[0] for i in cursor.description]
            self.update_table(columns, rows)
            self.update_output(
                f"Affichage du contenu de la table '{table_name}', page {self.current_page}."
            )
        except Error as e:
            self.show_error("Erreur lors de l'affichage de la table", str(e))

    def next_page(self):
        self.current_page += 1
        self.page_label.configure(text=f"Page {self.current_page}")
        self.refresh_table_content()

    def previous_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.page_label.configure(text=f"Page {self.current_page}")
            self.refresh_table_content()

    def refresh_table_content(self):
        if hasattr(self, "current_table"):
            self.display_table_content(self.current_table)
        else:
            self.update_output("Veuillez sélectionner une table à afficher.")

    def create_table_selector(self):
        self.table_selector_frame = ctk.CTkFrame(self.main_frame, fg_color="#2E2E2E")
        self.table_selector_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.table_selector_frame.grid_columnconfigure(1, weight=1)

        self.search_entry = ctk.CTkEntry(
            self.table_selector_frame,
            placeholder_text="Rechercher une table",
            height=35,
            corner_radius=8,
        )
        self.search_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self.filter_tables)

        self.sort_selector = ctk.CTkComboBox(
            self.table_selector_frame,
            values=[
                "Nom (A-Z)",
                "Nom (Z-A)",
                "ID (croissant)",
                "ID (décroissant)",
                "Date (croissant)",
                "Date (décroissant)",
            ],
            height=35,
            corner_radius=8,
        )
        self.sort_selector.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.sort_selector.set("Trier par")
        self.sort_selector.bind("<<ComboboxSelected>>", self.sort_table_content)

        self.refresh_button = ctk.CTkButton(
            self.table_selector_frame,
            text="Rafraîchir",
            command=self.refresh_table,
            height=35,
            corner_radius=8,
        )
        self.refresh_button.grid(row=0, column=2, padx=10, pady=10)

        self.table_list_frame = ctk.CTkScrollableFrame(
            self.table_selector_frame, height=200, width=200
        )
        self.table_list_frame.grid(
            row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew"
        )
        self.table_buttons = []

    def create_output_area(self):
        self.output_text = ctk.CTkTextbox(self.main_frame, height=80, corner_radius=8)
        self.output_text.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    def create_result_table(self):
        self.table_frame = ctk.CTkFrame(self.main_frame, fg_color="#2E2E2E")
        self.table_frame.grid(row=3, column=0, padx=20, pady=20, sticky="nsew")
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table = ttk.Treeview(self.table_frame, height=50, style="Custom.Treeview")
        self.table.grid(row=0, column=0, sticky="nsew")
        style = ttk.Style()
        style.configure(
            "Custom.Treeview",
            background="#F8F8F8",
            foreground="#333333",
            rowheight=25,
            bordercolor="#CCCCCC",
            borderwidth=1,
            highlightthickness=0,
            selectbackground="#E0E0E0",
            selectforeground="#333333",
        )
        style.configure(
            "Custom.Frame",
            background="#2E2E2E",
            bordercolor="#555555",
            borderwidth=2,
        )
        style.configure(
            "Custom.Treeview.Heading",
            background="#D3D3D3",
            foreground="#333333",
            font=("Arial", 12, "bold"),
            anchor="center",
            borderwidth=0,
        )
        self.table_scrollbar_y = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.table.yview
        )
        self.table_scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.table_scrollbar_x = ttk.Scrollbar(
            self.table_frame, orient="horizontal", command=self.table.xview
        )
        self.table_scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.table.configure(
            yscrollcommand=self.table_scrollbar_y.set,
            xscrollcommand=self.table_scrollbar_x.set,
        )
        self.table.column("#0", width=0, stretch=tk.NO)
        for col in self.table["columns"]:
            self.table.column(col, width=150, anchor="center")
        for col in self.table["columns"]:
            self.table.heading(col, text=col, anchor="center")
            self.table.column(col, stretch=tk.YES)

    def update_table_list(self, table_names):
        for button in self.table_buttons:
            button.destroy()
        self.table_buttons.clear()

        for i, table in enumerate(table_names):
            btn = ctk.CTkButton(
                self.table_list_frame,
                text=table,
                width=60,
                height=25,
                command=lambda t=table: self.display_table_content(t),
            )
            btn.grid(row=i, column=0, padx=2, pady=2, sticky="ew")
            self.table_buttons.append(btn)

        self.table_list_frame.grid_columnconfigure(0, weight=1)

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)
        self.logo_label = ctk.CTkLabel(
            self.sidebar, text="MySQL DBA", font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))
        buttons = [
            ("Connexion", self.open_connection_window),
            ("Actualiser", self.refresh_table),
            ("Commandes", self.open_commands_window),
            ("Historique", self.open_history_window),
            ("Aperçu BDD", self.open_database_overview),
            ("Assistant IA", self.open_ai_assistant),
        ]
        for i, (text, command) in enumerate(buttons, start=1):
            btn = ctk.CTkButton(
                self.sidebar, text=text, command=command, height=40, corner_radius=8
            )
            btn.grid(row=i, column=0, padx=20, pady=10, sticky="ew")

    def create_input_area(self):
        self.input_frame = ctk.CTkFrame(self.main_frame)
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        self.input_frame.grid_columnconfigure(1, weight=1)
        self.input_label = ctk.CTkLabel(self.input_frame, text="Commande:")
        self.input_label.grid(row=0, column=0, padx=(10, 5), pady=10)
        self.input_entry = ctk.CTkEntry(self.input_frame, height=35, corner_radius=8)
        self.input_entry.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")
        self.execute_button = ctk.CTkButton(
            self.input_frame,
            text="Exécuter",
            command=self.execute_command,
            height=35,
            corner_radius=8,
        )
        self.execute_button.grid(row=1, column=1, padx=(0, 10), pady=5, sticky="e")

    def open_connection_window(self):
        ConnectionWindow(self)

    def open_commands_window(self):
        CommandsWindow(self)

    def open_ai_assistant(self):
        AIAssistantWindow(self)

    def connect_to_database(self, host, user, password, database):
        try:
            self.connection = mysql.connector.connect(
                host=host, user=user, password=password, database=database
            )
            if self.connection.is_connected():
                self.output_text.insert("end", "Connecté à la base de données MySQL.\n")
                self.refresh_table()
        except Error as e:
            self.output_text.insert(
                "end", f"Erreur lors de la connexion à MySQL: {e}\n"
            )
            messagebox.showerror("Erreur de connexion", str(e))

    def execute_command(self):
        command = self.input_entry.get()
        if not self.connection or not self.connection.is_connected():
            self.show_error(
                "Non connecté", "Veuillez vous connecter à la base de données d'abord."
            )
            return
        try:
            sql_query = command
            with self.connection.cursor() as cursor:
                cursor.execute(sql_query)
                if cursor.with_rows:
                    result = cursor.fetchall()
                    if result:
                        column_names = [i[0] for i in cursor.description]
                        self.update_table(column_names, result)
                        result_message = "Résultat affiché dans le tableau."
                        self.update_output(result_message)
                        self.download_button.configure(
                            command=lambda: self.download_results(column_names, result)
                        )
                    else:
                        result_message = "Aucun résultat trouvé."
                        self.update_output(result_message)
                else:
                    self.connection.commit()
                    result_message = (
                        "Requête exécutée avec succès (aucun résultat à afficher)."
                    )
                    self.update_output(result_message)
                    self.refresh_table()
                self.history.add_entry(command, result_message)
        except Error as e:
            self.show_error("Erreur d'exécution", str(e))
            self.history.add_entry(command, str(e))

    def download_results(self, columns, data):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if file_path:
            workbook = Workbook()
            sheet = workbook.active
            sheet.append(columns)
            for row in data:
                sheet.append(row)
            workbook.save(file_path)
            self.update_output("Résultats téléchargés avec succès!")

    def refresh_table(self):
        if not self.connection or not self.connection.is_connected():
            self.show_error(
                "Non connecté", "Veuillez vous connecter à la base de données d'abord."
            )
            return
        try:
            query = "SHOW TABLES;"
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                tables = cursor.fetchall()
                table_names = [table[0] for table in tables]

            self.update_table_list(table_names)

            # Appliquer le filtre actuel
            self.filter_tables(None)

            # Sélectionner la table à afficher
            visible_tables = [
                btn.cget("text") for btn in self.table_buttons if btn.winfo_viewable()
            ]
            if self.current_table and self.current_table in visible_tables:
                self.display_table_content(self.current_table)
            elif visible_tables:
                self.display_table_content(visible_tables[0])
            else:
                self.clear_table()

            self.update_output("Tables rafraîchies avec succès.")
        except Error as e:
            self.show_error("Erreur lors du rafraîchissement", str(e))

    def display_table_content(self, table_name):
        self.current_table = table_name
        try:
            query = f"SELECT * FROM {table_name} LIMIT 100;"
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [i[0] for i in cursor.description]
            self.update_table(columns, rows)
            self.update_output(f"Affichage du contenu de la table '{table_name}'.")
        except Error as e:
            self.show_error("Erreur lors de l'affichage de la table", str(e))

    def clear_table(self):
        for item in self.table.get_children():
            self.table.delete(item)
        self.table["columns"] = ()
        self.update_output("Aucune table sélectionnée.")

    def show_table_content(self, event=None):
        selected_table = self.table_selector.get()
        if not selected_table:
            return
        try:
            query = f"SELECT * FROM {selected_table} LIMIT 100;"
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [i[0] for i in cursor.description]
            self.update_table(columns, rows)
            self.update_output(f"Affichage du contenu de la table '{selected_table}'.")
        except Error as e:
            self.show_error("Erreur lors de l'affichage de la table", str(e))

    def filter_tables(self, event):
        self.current_filter = self.search_entry.get().lower()
        for button in self.table_buttons:
            if self.current_filter in button.cget("text").lower():
                button.grid()
            else:
                button.grid_remove()

    def sort_table_content(self, event):
        sort_by = self.sort_selector.get()
        data = [self.table.item(item)["values"] for item in self.table.get_children()]

        if not data:
            return

        def safe_lower(x):
            return x.lower() if isinstance(x, str) else ""

        def safe_int(x):
            try:
                return int(x)
            except (ValueError, TypeError):
                return float("-inf")

        def safe_date(x):
            try:
                return datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                return datetime.min

        sort_functions = {
            "Nom (A-Z)": lambda x: safe_lower(x[0]),
            "Nom (Z-A)": lambda x: safe_lower(x[0]),
            "ID (croissant)": lambda x: safe_int(x[1]),
            "ID (décroissant)": lambda x: safe_int(x[1]),
            "Date (croissant)": lambda x: safe_date(x[2]),
            "Date (décroissant)": lambda x: safe_date(x[2]),
        }

        reverse = sort_by.endswith("(Z-A)") or sort_by.endswith("(décroissant)")

        try:
            sorted_data = sorted(data, key=sort_functions[sort_by], reverse=reverse)
        except IndexError:
            self.show_error(
                "Erreur de tri",
                "Les données ne correspondent pas au critère de tri sélectionné.",
            )
            return
        except Exception as e:
            self.show_error(
                "Erreur de tri", f"Une erreur inattendue s'est produite : {str(e)}"
            )
            return

        self.table.delete(*self.table.get_children())
        for row in sorted_data:
            self.table.insert("", "end", values=row)

        self.update_output(f"Tableau trié par {sort_by}")

    def update_table(self, column_names, rows):
        self.table["columns"] = column_names
        self.table["show"] = "headings"
        for col in column_names:
            self.table.heading(col, text=col)
        self.table.delete(*self.table.get_children())
        for row in rows:
            self.table.insert("", "end", values=row)

    def update_output(self, message):
        self.output_text.insert("end", message + "\n")
        self.output_text.see("end")

    def show_error(self, title, message):
        messagebox.showerror(title, message)

    def open_database_overview(self):
        if self.connection and self.connection.is_connected():
            DatabaseOverviewWindow(self, self.connection)
        else:
            messagebox.showwarning(
                "Non connecté", "Veuillez vous connecter à la base de données d'abord."
            )

    def open_history_window(self):
        HistoryWindow(self, self.history)

    def create_table_overview(self):
        self.table_frame = ctk.CTkFrame(self.main_frame, fg_color="#2E2E2E")
        self.table_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_tree = ttk.Treeview(
            self.table_frame, columns=("Table",), show="headings"
        )
        self.table_tree.heading("Table", text="Tables disponibles")
        self.table_tree.column("Table", width=300, anchor="w")
        self.table_tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.table_tree.yview
        )
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.table_tree.configure(yscrollcommand=self.scrollbar.set)
        self.back_button = ctk.CTkButton(
            self.main_frame, text="Retour", command=self.show_main_view
        )
        self.back_button.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.back_button.grid_forget()
        self.load_tables()

    def load_tables(self):
        if self.connection and self.connection.is_connected():
            try:
                with self.connection.cursor() as cursor:
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()
                    for table in tables:
                        self.table_tree.insert("", "end", values=table)
                    self.table_tree.bind("<Double-1>", self.on_table_select)
            except Error as e:
                self.output_text.insert("end", f"Erreur: {e}\n")

    def on_table_select(self, event):
        selected_item = self.table_tree.selection()
        if selected_item:
            table_name = self.table_tree.item(selected_item)["values"][0]
            self.show_table_details(table_name)

    def show_table_details(self, table_name):
        self.back_button.grid()
        self.table_frame.grid_forget()
        self.details_frame = ctk.CTkFrame(self.main_frame, fg_color="#2E2E2E")
        self.details_frame.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")
        self.details_frame.grid_columnconfigure(0, weight=1)
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
                rows = cursor.fetchall()
            self.details_tree = ttk.Treeview(
                self.details_frame, columns=("Column", "Type"), show="headings"
            )
            self.details_tree.heading("Column", text="Colonne")
            self.details_tree.heading("Type", text="Type de données")
            for col in columns:
                self.details_tree.insert("", "end", values=(col[0], col[1]))
            self.details_tree.grid(row=0, column=0, sticky="nsew")
            self.data_tree = ttk.Treeview(
                self.details_frame, columns=[col[0] for col in columns], show="headings"
            )
            for col in columns:
                self.data_tree.heading(col[0], text=col[0])
            for row in rows:
                self.data_tree.insert("", "end", values=row)
            self.data_tree.grid(row=1, column=0, sticky="nsew")
        except Error as e:
            self.output_text.insert(
                "end", f"Erreur lors du chargement des détails de la table: {e}\n"
            )

    def show_main_view(self):
        self.details_frame.grid_forget()
        self.back_button.grid_forget()
        self.table_frame.grid()


if __name__ == "__main__":
    app = MySQLDBAInterface()
    app.mainloop()
