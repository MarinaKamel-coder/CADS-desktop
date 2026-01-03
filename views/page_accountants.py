import os
from PyQt6 import QtWidgets, uic, QtCore, QtGui
from controllers import admin_controller as controller
from database import Accountant

class AccountantFormDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, accountant=None):
        super().__init__(parent)
        self.accountant = accountant
        is_edit = accountant is not None
        
        self.setWindowTitle("Modifier le profil" if is_edit else "Ajouter un comptable")
        self.setFixedWidth(500)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(30, 20, 30, 20)

        # --- CHAMPS COMMUNS (Ajout & Modification) ---
        self.first_name = QtWidgets.QLineEdit(placeholderText="Prénom")
        self.last_name = QtWidgets.QLineEdit(placeholderText="Nom")
        self.email = QtWidgets.QLineEdit(placeholderText="Courriel")
        self.phone = QtWidgets.QLineEdit(placeholderText="Téléphone")
        
        self.role_combo = QtWidgets.QComboBox()
        self.role_combo.addItems(["COMPTABLE", "COMPTABLE_SENIOR", "STAGIAIRE"])

        # --- CHAMPS SPÉCIFIQUES (Modification uniquement) ---
        self.status_combo = QtWidgets.QComboBox()
        self.status_combo.addItems(["ACTIF", "INACTIF"])
        
        self.nb_clients = QtWidgets.QSpinBox()
        self.nb_clients.setRange(0, 999)
        
        self.date_joined = QtWidgets.QDateEdit(calendarPopup=True)
        self.date_joined.setDate(QtCore.QDate.currentDate())
        
        self.date_left = QtWidgets.QDateEdit(calendarPopup=True)
        # On initialise à une date très lointaine ou on gère le "En poste"
        self.date_left.setSpecialValueText("En poste")

        # --- PRÉ-REMPLISSAGE SI MODIFICATION ---
        if is_edit:
            self.first_name.setText(self.accountant.first_name)
            self.last_name.setText(self.accountant.last_name)
            self.email.setText(self.accountant.email)
            self.phone.setText(self.accountant.phone if self.accountant.phone else "")
            self.role_combo.setCurrentText(self.accountant.role)
            self.status_combo.setCurrentText(self.accountant.status)
            
            nb = len(self.accountant.clients) if hasattr(self.accountant, 'clients') else 0
            self.nb_clients.setValue(nb)
            
            if self.accountant.date_joined:
                self.date_joined.setDate(self.accountant.date_joined)
            if self.accountant.date_left:
                self.date_left.setDate(self.accountant.date_left)

        # --- CONSTRUCTION DYNAMIQUE DU LAYOUT ---
        layout.addWidget(QtWidgets.QLabel("<b>INFORMATIONS GÉNÉRALES</b>"))
        
        # Prénom et Nom sur la même ligne
        name_layout = QtWidgets.QHBoxLayout()
        name_layout.addWidget(self.first_name)
        name_layout.addWidget(self.last_name)
        layout.addLayout(name_layout)

        layout.addWidget(self.email)
        layout.addWidget(self.phone)
        
        layout.addWidget(QtWidgets.QLabel("Rôle"))
        layout.addWidget(self.role_combo)

        # AJOUT DES CHAMPS SUPPLÉMENTAIRES SEULEMENT SI MODIFICATION
        if is_edit:
            layout.addSpacing(10)
            layout.addWidget(QtWidgets.QLabel("<b>GESTION ADMINISTRATIVE</b>"))
            
            layout.addWidget(QtWidgets.QLabel("Statut"))
            layout.addWidget(self.status_combo)
            
            layout.addWidget(QtWidgets.QLabel("Nombre de Clients"))
            layout.addWidget(self.nb_clients)
            
            layout.addWidget(QtWidgets.QLabel("Date d'Arrivée"))
            layout.addWidget(self.date_joined)
            
            layout.addWidget(QtWidgets.QLabel("Date de Départ"))
            layout.addWidget(self.date_left)

        # Bouton de validation
        self.btn_save = QtWidgets.QPushButton("Enregistrer" if is_edit else "Créer le compte")
        self.btn_save.setObjectName("btn_submit") 
        self.btn_save.setMinimumHeight(40)
        self.btn_save.clicked.connect(self.accept)
        
        layout.addSpacing(15)
        layout.addWidget(self.btn_save)

    def validate_and_accept(self):
        if not self.first_name.text() or not self.email.text():
            QtWidgets.QMessageBox.warning(self, "Erreur", "Le prénom et le courriel sont obligatoires.")
            return
        self.accept()

    def get_data(self):
        data = {
            "first_name": self.first_name.text(),
            "last_name": self.last_name.text(),
            "email": self.email.text(),
            "phone": self.phone.text(),
            "role": self.role_combo.currentText(),
        }
        # On ajoute les infos admin seulement si on est en mode édition
        if self.accountant:
            data.update({
                "status": self.status_combo.currentText(),
                "nb_clients": self.nb_clients.value(),
                "date_joined": self.date_joined.date().toPyDate(),
                "date_left": self.date_left.date().toPyDate() if self.date_left.date() > self.date_left.minimumDate() else None
            })
        return data


class AccountantsPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        base_path = os.path.dirname(__file__)
        ui_path = os.path.abspath(os.path.join(base_path, "..", "ui", "page_accountants.ui"))
        uic.loadUi(ui_path, self)
        
        self.setup_table()
        self.btn_ajouter.clicked.connect(self.handle_add)

        # Connecte la barre de recherche à la fonction de filtrage
        self.input_search.textChanged.connect(self.filter_table)

    def setup_table(self):
        """Configuration du tableau avec colonnes adaptatives"""
        headers = ["ID", "Prénom", "Nom", "Courriel", "Rôle", "Statut", "Clients", "Arrivée", "Départ", "Actions"]
        self.table_accountants.setColumnCount(len(headers))
        self.table_accountants.setHorizontalHeaderLabels(headers)
        
        self.table_accountants.setColumnHidden(0, True) # Cacher ID
        
        header = self.table_accountants.horizontalHeader()
        
        # --- RÉGLAGE DES TAILLES DE COLONNES ---
        # Colonnes compactes 
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.ResizeToContents) # Rôle
        header.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.ResizeToContents) # Statut
        header.setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeMode.ResizeToContents) # Clients
        header.setSectionResizeMode(7, QtWidgets.QHeaderView.ResizeMode.ResizeToContents) # Arrivée
        header.setSectionResizeMode(8, QtWidgets.QHeaderView.ResizeMode.ResizeToContents) # Départ
        
        # Colonnes extensibles 
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch) # Prénom
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch) # Nom
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch) # Courriel
        
        # Colonne Actions 
        header.setSectionResizeMode(9, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.table_accountants.setColumnWidth(9, 150)

        self.table_accountants.verticalHeader().setVisible(False)
        self.table_accountants.setAlternatingRowColors(True)

    def filter_table(self):
        """Filtre les lignes du tableau en fonction du texte saisi"""
        search_text = self.input_search.text().lower()
        for row in range(self.table_accountants.rowCount()):
            match = False
            # Colonnes indexées : Prénom(1), Nom(2), Courriel(3), Rôle(4)
            for col in [1, 2, 3, 4]:
                item = self.table_accountants.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.table_accountants.setRowHidden(row, not match)

    def load_data(self):
        self.table_accountants.setRowCount(0)
        accountants = controller.get_all_accountants()

        for row, acc in enumerate(accountants):
            self.table_accountants.insertRow(row)
            
            self.table_accountants.setItem(row, 1, QtWidgets.QTableWidgetItem(acc.first_name))
            self.table_accountants.setItem(row, 2, QtWidgets.QTableWidgetItem(acc.last_name))
            self.table_accountants.setItem(row, 3, QtWidgets.QTableWidgetItem(acc.email))
            self.table_accountants.setItem(row, 4, QtWidgets.QTableWidgetItem(acc.role))
            
            status_text = "✅ Actif" if acc.status == 'ACTIF' else "❌ Inactif"
            self.table_accountants.setItem(row, 5, QtWidgets.QTableWidgetItem(status_text))
            
            nb_clients = str(len(acc.clients)) if hasattr(acc, 'clients') else "0"
            self.table_accountants.setItem(row, 6, QtWidgets.QTableWidgetItem(nb_clients))
            
            arrival = acc.date_joined.strftime("%Y-%m-%d") if acc.date_joined else "-"
            departure = acc.date_left.strftime("%Y-%m-%d") if acc.date_left else "En poste"
            self.table_accountants.setItem(row, 7, QtWidgets.QTableWidgetItem(arrival))
            self.table_accountants.setItem(row, 8, QtWidgets.QTableWidgetItem(departure))

            self.add_action_buttons(row, acc.id)

    def add_action_buttons(self, row, acc_id):
        container = QtWidgets.QWidget()
        container.setMinimumWidth(100)
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(12)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Bouton Modifier (Icone SP_FileDialogDetailedView ou SP_MessageBoxInformation)
        btn_edit = QtWidgets.QPushButton()
        btn_edit.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView))
        btn_edit.setFixedSize(35, 35)
        btn_edit.setToolTip("Modifier le comptable")
        btn_edit.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        btn_edit.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background-color: #334155; border-radius: 5px; }")

        # Bouton Supprimer (Icone SP_TrashIcon)
        btn_delete = QtWidgets.QPushButton()
        btn_delete.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_TrashIcon))
        btn_delete.setFixedSize(35, 35)
        btn_delete.setToolTip("Supprimer le comptable")
        btn_delete.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        btn_delete.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background-color: #ef4444; border-radius: 5px; }")

        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)

        self.table_accountants.setCellWidget(row, 9, container)
        self.table_accountants.setRowHeight(row, 50)
        
        btn_edit.clicked.connect(lambda _, id=acc_id: self.handle_edit(id))
        btn_delete.clicked.connect(lambda _, id=acc_id: self.handle_delete(id))
        

    def handle_add(self):
        dialog = AccountantFormDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            if controller.add_accountant(dialog.get_data()):
                QtWidgets.QMessageBox.information(self, "Succès", "Comptable ajouté.")
                self.load_data()

    def handle_edit(self, acc_id):
        accountant = Accountant.get_or_none(Accountant.id == acc_id)
        if not accountant: return

        dialog = AccountantFormDialog(self, accountant=accountant)
        
        # exec() ouvre la fenêtre et attend le clic sur "Enregistrer"
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            new_data = dialog.get_data() # On récupère le dictionnaire
            
            # On envoie l'ID et le dictionnaire au contrôleur
            success = controller.update_accountant(acc_id, new_data)
            
            if success:
                #Recharger les données pour voir le changement dans la table
                self.load_data() 
                print(f"✅ Mise à jour réussie pour l'ID {acc_id}")
            else:
                print("❌ Erreur lors de la mise à jour en base de données")

    def handle_delete(self, acc_id):
        confirm = QtWidgets.QMessageBox.question(
            self, "Confirmation", "Voulez-vous vraiment supprimer ce comptable ?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if confirm == QtWidgets.QMessageBox.StandardButton.Yes:
            if controller.delete_accountant(acc_id):
                self.load_data()

    def filter_table(self):
        search_text = self.input_search.text().lower()
        for row in range(self.table_accountants.rowCount()):
            match = False
            # Filtre sur Prénom (1), Nom (2), Email (3) et Rôle (4)
            for col in [1, 2, 3, 4]:
                item = self.table_accountants.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.table_accountants.setRowHidden(row, not match)