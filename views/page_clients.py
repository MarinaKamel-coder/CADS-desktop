import os
from PyQt6 import QtWidgets, uic, QtCore
from controllers import client_controller as controller
from views.document_widget import DocumentManagerWidget  
from views.deadline_widget import DeadlineManagerWidget

class ClientDetailView(QtWidgets.QDialog):
    def __init__(self, main_page, client_data):
        super().__init__(main_page)
        self.main_page = main_page
        self.client_data = client_data
        
        # --- RÉPARATION ICI : on nomme la variable 'self.client' ---
        # On cherche l'objet en base locale
        self.client = controller.get_client_by_id(client_data['id'])
        
        self.setWindowTitle(f"Dossier Client : {client_data['first_name']} {client_data['last_name']}")
        self.setMinimumSize(800, 600)
        
        layout = QtWidgets.QVBoxLayout(self)
        self.tabs = QtWidgets.QTabWidget()
        
        # --- ONGLET 1 : INFORMATIONS ---
        self.tab_info = QtWidgets.QWidget()
        self.setup_info_tab()
        self.tabs.addTab(self.tab_info, "👤 Informations Profil")
        
        # --- ONGLET 2 : DOCUMENTS ---
        self.tab_docs = DocumentManagerWidget(self.client_data)
        self.tabs.addTab(self.tab_docs, "📂 Documents & Fichiers")

        # --- ONGLET 3 : ÉCHÉANCES ---
        # On vérifie si self.client existe avant de charger les échéances
        if self.client:
            self.tab_deadlines = DeadlineManagerWidget(self.client)
            self.tabs.addTab(self.tab_deadlines, "🔔 Échéances & Rappels")
        
        layout.addWidget(self.tabs)

    def setup_info_tab(self):
        layout = QtWidgets.QVBoxLayout(self.tab_info)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        container = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(container)
        form.setSpacing(15)

        def create_section(text):
            lbl = QtWidgets.QLabel(text)
            lbl.setStyleSheet("font-weight: bold; color: #3b82f6; border-bottom: 1px solid #334155; padding-top: 10px;")
            return lbl

        # Cette fonction va maintenant trouver self.client sans erreur
        def get_val(attr, default="---"):
            if self.client and hasattr(self.client, attr):
                return str(getattr(self.client, attr, default) or default)
            return str(self.client_data.get(attr, default))
        
        form.addRow(create_section("IDENTITÉ & CONTACT"))
        form.addRow("Prénom :", QtWidgets.QLabel(get_val('first_name')))
        form.addRow("Nom :", QtWidgets.QLabel(get_val('last_name')))
        form.addRow("NAS :", QtWidgets.QLabel(f"<b>{get_val('nas_number', 'Non renseigné')}</b>"))
        form.addRow("Courriel :", QtWidgets.QLabel(get_val('email')))
        form.addRow("Téléphone :", QtWidgets.QLabel(get_val('phone')))
        form.addRow("Adresse :", QtWidgets.QLabel(get_val('address')))

        form.addRow(create_section("SUIVI"))

        # Gestion sécurisée du comptable
        acc_name = "Non assigné"
        # On récupère l'ID stocké dans le client (Desktop ou Web)
        target_acc_id = None
        if self.client:
            target_acc_id = getattr(self.client, 'accountant_id', None)
        else:
            target_acc_id = self.client_data.get('accountant')

        if target_acc_id:
            # On cherche dans la liste fusionnée pour trouver le nom
            all_staff = controller.get_all_staff_combined()
            match = next((s for s in all_staff if str(s['id']) == str(target_acc_id)), None)
            
            if match:
                icon = "🌐 " if match['source'] == "Web" else "🖥️ "
                acc_name = f"{icon}{match['first_name']} {match['last_name']}"
            else:
                acc_name = "🌐 Portail Web"
            
        form.addRow("Comptable :", QtWidgets.QLabel(acc_name))
        
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Boutons
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_edit = QtWidgets.QPushButton(" 📝 Modifier les infos")
        self.btn_edit.clicked.connect(self.on_edit_clicked)
        btn_close = QtWidgets.QPushButton("Fermer")
        btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_edit); btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def on_edit_clicked(self):
        if not self.client:
            QtWidgets.QMessageBox.warning(self, "Action impossible", "Importez le client avant de le modifier.")
            return
            
        dialog = ClientFormDialog(self.main_page, client=self.client, mode="complet")
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            
            # On utilise la fonction qui met à jour Desktop ET Web
            success_local, success_web = controller.update_client_combined(
                client_id=self.client.id,
                web_id=self.client_data.get('web_id'), # Récupéré depuis le dictionnaire initial
                data=new_data
            )
            
            if success_local or success_web:
                # On demande à la page parente de recharger sa liste
                if hasattr(self.main_page, 'load_data'):
                    self.main_page.load_data()
                self.accept() # Ferme la vue détail pour voir les changements
                QtWidgets.QMessageBox.information(self, "Succès", "Informations mises à jour sur Desktop et Web.")
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
            d_arr = client.created_at
            self.date_arrivee.setDate(QtCore.QDate(d_arr.year, d_arr.month, d_arr.day))
            self.date_depart = QtWidgets.QDateEdit(calendarPopup=True)
            if client.date_left:
                d_dep = client.date_left
                self.date_depart.setDate(QtCore.QDate(d_dep.year, d_dep.month, d_dep.day))
            else:
                self.date_depart.setDate(QtCore.QDate.currentDate())
                
            self.form_layout.addRow("Arrivée :", self.date_arrivee)
            self.form_layout.addRow("Départ :", self.date_depart)

        layout.addLayout(self.form_layout)
        
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Save | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_accountants(self):
        """Charge les comptables locaux ET web dans le menu déroulant"""
        self.comptable_cb.clear()
        
        # On utilise la fonction fusionnée (Desktop + Web)
        all_staff = controller.get_all_staff_combined()
        
        for staff in all_staff:
            # On peut ajouter un petit indicateur visuel pour différencier les sources
            source_tag = " (Web)" if staff['source'] == "Web" else ""
            display_name = f"{staff['first_name']} {staff['last_name']}{source_tag}"
            
            # On stocke l'ID (int pour Desktop, UUID pour Web)
            self.comptable_cb.addItem(display_name, staff['id'])
            
        # --- Gestion de la présélection lors de l'édition ---
        if self.client:
            current_acc_id = getattr(self.client, 'accountant_id', None)
            
            if current_acc_id:
                # On cherche l'index de cet ID dans la ComboBox
                idx = self.comptable_cb.findData(str(current_acc_id))
                if idx >= 0:
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
        all_clients = controller.get_all_clients_combined()
        for row, c in enumerate(all_clients):
            self.table_clients.insertRow(row)

            # Sécurité : on s'assure que l'ID est bien converti en string
            id_val = str(c['id'])
            id_item = QtWidgets.QTableWidgetItem(id_val)
            id_item.setData(QtCore.Qt.ItemDataRole.UserRole, c['source'])
            self.table_clients.setItem(row, 0, id_item)

            # Prénom et Nom
            self.table_clients.setItem(row, 1, QtWidgets.QTableWidgetItem(c['first_name']))
            self.table_clients.setItem(row, 2, QtWidgets.QTableWidgetItem(c['last_name']))

            # Email avec icône de source
            email_item = QtWidgets.QTableWidgetItem(c['email'])
            if c['source'] == "Web":
               email_item.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_BrowserReload))
               email_item.setToolTip("Client provenant du portail Web - Importation requise")
            else:
               email_item.setToolTip("Client enregistré en base locale")
            
            self.table_clients.setItem(row, 3, email_item)
            
            self.table_clients.setItem(row, 4, QtWidgets.QTableWidgetItem(c['phone']))
            self.table_clients.setItem(row, 5, QtWidgets.QTableWidgetItem(c['accountant']))
            self.table_clients.setItem(row, 6, QtWidgets.QTableWidgetItem(c['created_at']))
            self.table_clients.setItem(row, 7, QtWidgets.QTableWidgetItem(c['date_left']))
            
            # Boutons d'actions
            if c['source'] == "Desktop":
                self.add_action_buttons(row, c['id'])
            else:
                # Bouton spécial pour "Importer" le client Web vers Desktop
                btn_import = QtWidgets.QPushButton("📥 Importer")
                btn_import.setStyleSheet("background-color: #0ea5e9; color: white; border-radius: 4px;")
                btn_import.clicked.connect(lambda _, data=c: self.handle_import_web_client(data))
                self.table_clients.setCellWidget(row, 8, btn_import)

    def handle_row_click(self, row, column):
        # 1. On récupère l'ID et la Source cachés dans la colonne 0
        id_item = self.table_clients.item(row, 0)
        if not id_item: return
        
        client_id = id_item.text()
        source = id_item.data(QtCore.Qt.ItemDataRole.UserRole)

        # 2. Si c'est un client Web non importé, on bloque
        if source == "Web":
            QtWidgets.QMessageBox.information(
                self, "Importation requise", 
                "Ce client est sur le Web. Cliquez sur '📥 Importer' avant d'ouvrir le dossier."
            )
            return

        # 3. C'est un client Desktop : on récupère l'objet Peewee
        client_obj = controller.get_client_by_id(client_id)
        
        if client_obj:
            # IMPORTANT : On transforme l'objet Peewee en dictionnaire 
            # pour que DocumentManagerWidget sache où chercher (local + web)
            client_data = {
                "id": client_obj.id,
                "web_id": client_obj.id, # L'ID est identique si importé via ton bouton
                "first_name": client_obj.first_name,
                "last_name": client_obj.last_name,
                "source": "Desktop"
            }
            
            # 4. On ouvre la vue avec ce dictionnaire
            dialog = ClientDetailView(self, client_data)
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
        client = controller.get_client_by_id(client_id)
        dialog = ClientFormDialog(self, client=client, mode="table")
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            
            # Mise à jour en base de données
            success_local, success_web = controller.update_client_combined(
                client_id=client_id,
                web_id=client_id, 
                data=new_data
            )
            
            if success_local:
                # 🔄 C'est ICI qu'on recharge le tableau principal
                self.load_data() 
                # On applique le filtre si une recherche était en cours
                self.filter_table()

    def handle_delete(self, client_id):
        if QtWidgets.QMessageBox.question(self, "Supprimer", "Confirmer ?") == QtWidgets.QMessageBox.StandardButton.Yes:
            if controller.delete_client(client_id): self.load_data()

    def on_sync_clicked(self):
        nb = controller.sync_web_clients_to_desktop()
        if nb > 0:
            self.load_data() # Recharge la table pour afficher les nouveaux
            QtWidgets.QMessageBox.information(self, "Succès", f"{nb} nouveaux clients synchronisés depuis le Web.")

    def handle_import_web_client(self, web_data):
        # web_data['raw_object'] est l'instance WebClient de ta base PostgreSQL
        wc = web_data['raw_object'] 
        
        confirm = QtWidgets.QMessageBox.question(
            self, "Importation", 
            f"Voulez-vous importer définitivement {wc.first_name} {wc.last_name} dans la base locale ?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        
        if confirm == QtWidgets.QMessageBox.StandardButton.Yes:
            # On mappe TOUS les champs disponibles sur le Web vers le Desktop
            import_data = {
                "id": wc.id, # On garde le même ID UUID pour la cohérence
                "first_name": wc.first_name,
                "last_name": wc.last_name,
                "email": wc.email,
                "phone": wc.phone,
                "nas_number": getattr(wc, 'nas_number', '000-000-000'),
                "address": getattr(wc, 'address', 'Importé du Web'),
                "created_at": wc.created_at if hasattr(wc, 'created_at') else QtCore.QDateTime.currentDateTime().toPyDateTime()
            }
            
            if controller.add_client(import_data):
                QtWidgets.QMessageBox.information(self, "Succès", "Le client a été basculé dans la base locale.")
                self.load_data()