import os
from PyQt6 import QtWidgets, uic, QtCore, QtGui
from controllers import admin_controller as controller
from database import Client

class ClientDetailView(QtWidgets.QDialog):
    def __init__(self, main_page, client):
        super().__init__(main_page)
        self.main_page = main_page  # Référence à ClientsPage
        self.client = client
        self.setWindowTitle(f"Profil Client : {client.first_name} {client.last_name}")
        self.setMinimumSize(550, 600)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        # Zone défilante pour les infos
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        container = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(container)
        form.setSpacing(15)

        def create_section(text):
            lbl = QtWidgets.QLabel(text)
            lbl.setStyleSheet("font-weight: bold; color: #3b82f6; margin-top: 10px; border-bottom: 1px solid #334155;")
            return lbl

        # --- Affichage des informations ---
        form.addRow(create_section("IDENTITÉ & CONTACT"))
        form.addRow("Prénom :", QtWidgets.QLabel(client.first_name))
        form.addRow("Nom :", QtWidgets.QLabel(client.last_name))
        form.addRow("NAS :", QtWidgets.QLabel(f"<b>{client.nas_number}</b>"))
        form.addRow("Courriel :", QtWidgets.QLabel(client.email))
        form.addRow("Téléphone :", QtWidgets.QLabel(client.phone))
        form.addRow("Adresse :", QtWidgets.QLabel(client.address))

        form.addRow(create_section("SUIVI & DOSSIER"))
        acc_name = f"{client.accountant.first_name} {client.accountant.last_name}" if client.accountant else "Non assigné"
        form.addRow("Comptable :", QtWidgets.QLabel(acc_name))
        form.addRow("Date Arrivée :", QtWidgets.QLabel(str(client.created_at.date())))
        form.addRow("Date Départ :", QtWidgets.QLabel(str(getattr(client, 'date_left', '---'))))

        scroll.setWidget(container)
        layout.addWidget(scroll)

        # --- Barre d'actions ---
        actions_layout = QtWidgets.QHBoxLayout()
        
        self.btn_edit_all = QtWidgets.QPushButton(" 📝 Modifier toutes les informations")
        self.btn_edit_all.setObjectName("btn_edit_full")
        self.btn_edit_all.setMinimumHeight(40)
        self.btn_edit_all.clicked.connect(self.on_edit_clicked)
        
        btn_close = QtWidgets.QPushButton("Fermer")
        btn_close.setMinimumHeight(40)
        btn_close.clicked.connect(self.reject)

        actions_layout.addWidget(self.btn_edit_all)
        actions_layout.addWidget(btn_close)
        layout.addLayout(actions_layout)

    def on_edit_clicked(self):
        """Lance la modification COMPLETE (incluant NAS et Adresse)"""
        self.accept()
        # On force le mode "complet"
        dialog = ClientFormDialog(self.main_page, client=self.client, mode="complet")
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            if controller.update_client(self.client.id, dialog.get_data()):
                self.main_page.load_data()

class ClientFormDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, client=None, mode="table"):
        super().__init__(parent)
        self.client = client
        self.is_edit = client is not None
        self.mode = mode # "table" (rapide) ou "complet" (NAS + Adresse)
        
        self.setWindowTitle("Modifier Client" if self.is_edit else "Nouveau Client")
        self.setFixedWidth(450)

        layout = QtWidgets.QVBoxLayout(self)
        self.form_layout = QtWidgets.QFormLayout()
        
        # --- CHAMPS COMMUNS ---
        self.first_name = QtWidgets.QLineEdit(client.first_name if client else "")
        self.last_name = QtWidgets.QLineEdit(client.last_name if client else "")
        self.email = QtWidgets.QLineEdit(client.email if client else "")
        self.phone = QtWidgets.QLineEdit(client.phone if client else "")
        self.comptable_cb = QtWidgets.QComboBox()
        self.load_accountants()

        self.form_layout.addRow("Prénom :", self.first_name)
        self.form_layout.addRow("Nom :", self.last_name)
        self.form_layout.addRow("Courriel :", self.email)
        self.form_layout.addRow("Téléphone :", self.phone)
        self.form_layout.addRow("Comptable :", self.comptable_cb)

        # --- CHAMPS SPÉCIFIQUES ---
        if self.mode == "complet" or not self.is_edit:
            self.nas = QtWidgets.QLineEdit(client.nas_number if client else "")
            self.address = QtWidgets.QTextEdit()
            self.address.setPlainText(client.address if client else "")
            self.address.setMaximumHeight(70)
            self.form_layout.addRow("NAS :", self.nas)
            self.form_layout.addRow("Adresse :", self.address)

        if self.is_edit:
            self.date_arrivee = QtWidgets.QDateEdit(calendarPopup=True)
            self.date_arrivee.setDate(QtCore.QDate(client.created_at.year, client.created_at.month, client.created_at.day))
            self.date_depart = QtWidgets.QDateEdit(calendarPopup=True)
            self.form_layout.addRow("Arrivée :", self.date_arrivee)
            self.form_layout.addRow("Départ :", self.date_depart)

        layout.addLayout(self.form_layout)
        
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Save | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_accountants(self):
        accountants = controller.get_all_accountants()
        for acc in accountants:
            self.comptable_cb.addItem(f"{acc.first_name} {acc.last_name}", acc.id)
        if self.client and self.client.accountant:
            idx = self.comptable_cb.findData(self.client.accountant.id)
            self.comptable_cb.setCurrentIndex(idx)

    def get_data(self):
        data = {
            "first_name": self.first_name.text(),
            "last_name": self.last_name.text(),
            "email": self.email.text(),
            "phone": self.phone.text(),
            "accountant": self.comptable_cb.currentData()
        }
        if self.is_edit:
            data["created_at"] = self.date_arrivee.date().toPyDate()
            data["date_left"] = self.date_depart.date().toPyDate()
        
        if self.mode == "complet" or not self.is_edit:
            data["nas_number"] = self.nas.text()
            data["address"] = self.address.toPlainText()
        return data

class ClientsPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/page_clients.ui", self)
        self.setup_table()
        self.btn_ajouter.clicked.connect(self.handle_add)
        self.table_clients.cellDoubleClicked.connect(self.handle_row_click)

        # Ajout du filtre de recherche en temps réel
        self.input_search.textChanged.connect(self.filter_table)

    def setup_table(self):
        headers = ["ID", "Prénom", "Nom", "Courriel", "Téléphone", "Comptable", "Arrivée", "Départ", "Actions"]
        self.table_clients.setColumnCount(len(headers))
        self.table_clients.setHorizontalHeaderLabels(headers)
        self.table_clients.setColumnHidden(0, True)
        self.table_clients.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table_clients.setColumnWidth(8, 120)

    def filter_table(self):
        """Masque ou affiche les lignes selon la recherche"""
        search_text = self.input_search.text().lower()
        for row in range(self.table_clients.rowCount()):
            match = False
            # On cherche dans : Prénom(1), Nom(2), Courriel(3) et Comptable(5)
            for col in [1, 2, 3, 5]:
                item = self.table_clients.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.table_clients.setRowHidden(row, not match)

    def load_data(self):
        self.table_clients.setRowCount(0)
        clients = controller.get_all_clients()
        for row, c in enumerate(clients):
            self.table_clients.insertRow(row)
            self.table_clients.setItem(row, 0, QtWidgets.QTableWidgetItem(str(c.id)))
            self.table_clients.setItem(row, 1, QtWidgets.QTableWidgetItem(c.first_name))
            self.table_clients.setItem(row, 2, QtWidgets.QTableWidgetItem(c.last_name))
            self.table_clients.setItem(row, 3, QtWidgets.QTableWidgetItem(c.email))
            self.table_clients.setItem(row, 4, QtWidgets.QTableWidgetItem(c.phone))
            if c.accountant:
                acc_display = f"{c.accountant.first_name} {c.accountant.last_name}"
            else:
                acc_display = "Non assigné"
            
            self.table_clients.setItem(row, 5, QtWidgets.QTableWidgetItem(acc_display))
            
            self.table_clients.setItem(row, 6, QtWidgets.QTableWidgetItem(str(c.created_at.date())))
            depart = str(c.date_left) if hasattr(c, 'date_left') and c.date_left else "---"
            self.table_clients.setItem(row, 7, QtWidgets.QTableWidgetItem(depart))
            self.add_action_buttons(row, c.id)

    def handle_row_click(self, row, column):
        client_id = self.table_clients.item(row, 0).text()
        client = controller.get_client_by_id(client_id)
        if client:
            dialog = ClientDetailView(self, client)
            dialog.exec()

    def add_action_buttons(self, row, client_id):
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        
        btn_edit = QtWidgets.QPushButton()
        btn_edit.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView))
        btn_edit.setFixedSize(30, 30)
        btn_edit.clicked.connect(lambda: self.handle_edit(client_id))
        
        btn_del = QtWidgets.QPushButton()
        btn_del.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TrashIcon))
        btn_del.setFixedSize(30, 30)
        btn_del.clicked.connect(lambda: self.handle_delete(client_id))
        
        layout.addWidget(btn_edit); layout.addWidget(btn_del)
        self.table_clients.setCellWidget(row, 8, container)

    def handle_add(self):
        dialog = ClientFormDialog(self, mode="complet")
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            if controller.add_client(dialog.get_data()): self.load_data()

    def handle_edit(self, client_id):
        """Modification RAPIDE (mode table)"""
        client = Client.get_by_id(client_id)
        dialog = ClientFormDialog(self, client=client, mode="table")
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            if controller.update_client(client_id, dialog.get_data()): self.load_data()

    def handle_delete(self, client_id):
        if QtWidgets.QMessageBox.question(self, "Supprimer", "Confirmer ?") == QtWidgets.QMessageBox.StandardButton.Yes:
            if controller.delete_client(client_id): self.load_data()