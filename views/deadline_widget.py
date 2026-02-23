import os
import uuid
from PyQt6 import QtWidgets, QtCore, QtGui
from datetime import datetime
from database import Client, Deadline, db_web, db_desktop, WebDeadline
from controllers import deadline_controller as controller

class DeadlineDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouvelle Échéance")
        self.setFixedWidth(400)
        
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self.title = QtWidgets.QLineEdit()
        self.description = QtWidgets.QTextEdit() # Ajout Description
        self.description.setMaximumHeight(60)
        
        self.due_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.due_date.setDate(QtCore.QDate.currentDate())
        
        self.priority = QtWidgets.QComboBox()
        self.priority.addItems(["LOW", "MEDIUM", "HIGH"])
        self.priority.setCurrentText("MEDIUM")

        # Ajout du Type pour Prisma
        self.type = QtWidgets.QComboBox()
        self.type.addItems(["FEDERAL", "PROVINCIAL", "MUNICIPAL"])

        form.addRow("Titre :", self.title)
        form.addRow("Description :", self.description)
        form.addRow("Date limite :", self.due_date)
        form.addRow("Priorité :", self.priority)
        form.addRow("Juridiction :", self.type)
        
        layout.addLayout(form)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save | 
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {
            "title": self.title.text(),
            "description": self.description.toPlainText(),
            "due_date": self.due_date.date().toString(QtCore.Qt.DateFormat.ISODate),
            "priority": self.priority.currentText(),
            "type": self.type.currentText()
        }

class DeadlineManagerWidget(QtWidgets.QWidget):
    def __init__(self, client_data, parent=None):
        super().__init__(parent)
        self.client_data = client_data
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # --- BARRE D'OUTILS ---
        header = QtWidgets.QHBoxLayout()
        
        self.lbl_status = QtWidgets.QLabel("📋 Échéances en cours")
        self.lbl_status.setStyleSheet("font-weight: bold; font-size: 14px; color: #94a3b8;")
        
        self.btn_add = QtWidgets.QPushButton(" 🔔 Ajouter un rappel / Rappel impôt")
        self.btn_add.setMinimumHeight(35)
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6; 
                color: white; 
                font-weight: bold; 
                padding: 0 15px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        self.btn_add.clicked.connect(self.handle_add_deadline)
        
        header.addWidget(self.lbl_status)
        header.addStretch()
        header.addWidget(self.btn_add)
        layout.addLayout(header)

        # --- TABLE DES ÉCHÉANCES ---
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["TITRE", "DATE LIMITE", "PRIORITÉ", "ACTION"])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("gridline-color: #334155; alternate-background-color: #1e293b;")
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def refresh_list(self):
        self.table.setRowCount(0)
        
        # 1. Identification des IDs
        if isinstance(self.client_data, dict):
            c_id = self.client_data.get('id')
            w_id = self.client_data.get('web_id')
        else:
            c_id = self.client_data.id
            w_id = getattr(self.client_data, 'web_id', None)

        # Liaison auto (ton code existant)
        if not w_id:
            from database import Client
            client_obj = Client.get_or_none(Client.id == c_id)
            w_id = controller.link_client_by_email(client_obj)

        self.w_id = w_id 

        # 2. Récupération et Dédoublonnage
        raw_deadlines = controller.get_client_deadlines_combined(c_id, w_id)
        
        # On trie pour que 'Web' soit traité avant 'Local' (pour l'icône 🌐)
        raw_deadlines.sort(key=lambda x: x.get('source', ''), reverse=True)

        seen_titles = set()
        final_deadlines = []

        for d in raw_deadlines:
            # Nettoyage du titre pour comparer (on enlève les icônes si déjà présentes)
            clean_title = d['title'].replace("🌐", "").replace("💻", "").strip()
            
            if clean_title not in seen_titles:
                final_deadlines.append(d)
                seen_titles.add(clean_title)

        # 3. Affichage des données uniques
        for row, d in enumerate(final_deadlines):
            self.table.insertRow(row)
            source_prefix = "🌐 " if d.get('source') == 'Web' else "💻 "
            
            # Titre
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(f"{source_prefix}{d['title']}"))
            
            # Date
            due_date = d['due_date']
            due_str = "Date inconnue"
            is_overdue = False
            try:
                if isinstance(due_date, str):
                    due_date_obj = datetime.strptime(due_date[:10], "%Y-%m-%d")
                else:
                    due_date_obj = due_date

                if due_date_obj:
                    due_str = due_date_obj.strftime("%d/%m/%Y")
                    if due_date_obj.date() < datetime.now().date():
                        is_overdue = True
            except: pass

            date_item = QtWidgets.QTableWidgetItem(due_str)
            if is_overdue:
                date_item.setForeground(QtGui.QColor("#ef4444"))
                date_item.setText(f"⚠️ {due_str} (RETARD)")
            self.table.setItem(row, 1, date_item)
            
            # Priorité
            prio_item = QtWidgets.QTableWidgetItem(str(d['priority']))
            if d['priority'] == 'HIGH':
                prio_item.setForeground(QtGui.QColor("#f97316"))
            self.table.setItem(row, 2, prio_item)

            # Bouton Terminé (qui va supprimer)
            btn_done = QtWidgets.QPushButton("Terminé")
            # Utilisation de la nouvelle fonction de suppression
            btn_done.clicked.connect(lambda ch, item=d: self.mark_as_completed(item))
            self.table.setCellWidget(row, 3, btn_done)

    def handle_add_deadline(self):
        dialog = DeadlineDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            # 1. On récupère les infos saisies (titre, date, etc.)
            data = dialog.get_data()
            
            # 2. Injection sécurisée des IDs (Dictionnaire ou Objet Peewee)
            if isinstance(self.client_data, dict):
                # Cas : Ton dictionnaire merged_data
                data["client_id"] = self.client_data.get('id')
                data["web_id"] = self.client_data.get('web_id')
                data["accountant_id"] = self.client_data.get('accountant_id')
            else:
                # Cas de secours : Objet Peewee direct
                data["client_id"] = getattr(self.client_data, 'id', None)
                data["web_id"] = getattr(self.client_data, 'web_id', None)
                data["accountant_id"] = getattr(self.client_data, 'accountant_id', None)

            # 3. Vérification de sécurité avant le DEBUG pour éviter le crash
            c_id = data.get("client_id")
            a_id = data.get("accountant_id")

            if not c_id:
                QtWidgets.QMessageBox.warning(self, "Erreur", "Impossible d'identifier le client.")
                return

            print(f"DEBUG: Tentative d'envoi -> Client: {c_id} | Accountant: {a_id}")

            # 4. Envoi au contrôleur
            if controller.add_deadline(data):
                self.refresh_list()
            else:
                QtWidgets.QMessageBox.critical(self, "Erreur", "L'insertion en base de données a échoué.")
    def mark_as_completed(self, item):
        # 1. Nettoyage du titre
        title = item['title']
        
        # 2. Confirmation de l'utilisateur
        reply = QtWidgets.QMessageBox.question(
            self, "Confirmation de suppression", 
            f"Voulez-vous supprimer définitivement la tâche :\n'{title}' ?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            w_id = getattr(self, 'w_id', None)
            
            # Appel de la nouvelle fonction de suppression
            if controller.delete_deadline_combined(
                deadline_id=item['id'], 
                title=title, 
                web_id=w_id
            ):
                # 3. Rafraîchissement immédiat : la ligne disparaît
                self.refresh_list()
                print("✅ Tâche supprimée avec succès")
            else:
                QtWidgets.QMessageBox.warning(self, "Erreur", "Impossible de supprimer la tâche.")