import os
from PyQt6 import QtWidgets, QtCore, QtGui
from datetime import datetime
from controllers import admin_controller as controller

class DeadlineDialog(QtWidgets.QDialog):
    """Fenêtre surgissante pour créer une nouvelle échéance"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouvelle Échéance")
        self.setFixedWidth(400)
        
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()

        self.title = QtWidgets.QLineEdit()
        self.title.setPlaceholderText("ex: Fin d'année fiscale, Remise TPS/TVQ...")
        
        self.due_date = QtWidgets.QDateEdit(calendarPopup=True)
        self.due_date.setMinimumDate(QtCore.QDate.currentDate())
        self.due_date.setDate(QtCore.QDate.currentDate())
        
        self.priority = QtWidgets.QComboBox()
        self.priority.addItems(["LOW", "MEDIUM", "HIGH"])
        self.priority.setCurrentText("MEDIUM")

        form.addRow("Titre de la tâche :", self.title)
        form.addRow("Date d'échéance :", self.due_date)
        form.addRow("Niveau de priorité :", self.priority)
        
        layout.addLayout(form)

        # Boutons Sauvegarder / Annuler
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Save | 
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        """Récupère les informations saisies sous forme de dictionnaire"""
        return {
            "title": self.title.text(),
            "due_date": self.due_date.date().toPyDate(),
            "priority": self.priority.currentText()
        }


class DeadlineManagerWidget(QtWidgets.QWidget):
    """Widget principal gérant la liste des rappels pour un client spécifique"""
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
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
        """Recharge les données depuis la base de données et applique le style"""
        self.table.setRowCount(0)
        deadlines = controller.get_client_deadlines(self.client.id)
        
        for row, d in enumerate(deadlines):
            self.table.insertRow(row)
            
            # 1. Titre
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(d.title))
            
            # 2. Date avec détection de retard (Rouge si date passée)
            due_date_dt = d.due_date
            if isinstance(due_date_dt, str): # Sécurité si format string
                due_date_dt = datetime.strptime(due_date_dt, "%Y-%m-%d %H:%M:%S")
                
            due_str = due_date_dt.strftime("%d/%m/%Y")
            date_item = QtWidgets.QTableWidgetItem(due_str)
            
            if due_date_dt.date() < datetime.now().date():
                date_item.setForeground(QtGui.QColor("#ef4444")) # Rouge vif
                date_item.setText(f"⚠️ {due_str} (RETARD)")
                date_item.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Weight.Bold))
            
            self.table.setItem(row, 1, date_item)
            
            # 3. Priorité avec code couleur
            prio_item = QtWidgets.QTableWidgetItem(d.priority)
            if d.priority == 'HIGH':
                prio_item.setForeground(QtGui.QColor("#f97316")) # Orange
                prio_item.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Weight.Bold))
            elif d.priority == 'MEDIUM':
                prio_item.setForeground(QtGui.QColor("#fbbf24")) # Jaune
            
            self.table.setItem(row, 2, prio_item)

            # 4. Bouton d'action "Terminé"
            btn_done = QtWidgets.QPushButton("Terminé")
            btn_done.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            btn_done.clicked.connect(lambda ch, id=d.id: self.mark_as_completed(id))
            self.table.setCellWidget(row, 3, btn_done)

    def handle_add_deadline(self):
        """Ouvre le dialogue et enregistre l'échéance en DB"""
        dialog = DeadlineDialog(self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            # On lie automatiquement au client et au comptable assigné
            data["client"] = self.client.id
            data["accountant"] = self.client.accountant.id if self.client.accountant else None
            data["status"] = "PENDING"
            
            if controller.add_deadline(data):
                self.refresh_list()

    def mark_as_completed(self, deadline_id):
        """Change le statut en COMPLETED et retire de la liste active"""
        if controller.update_deadline_status(deadline_id, 'COMPLETED'):
            self.refresh_list()