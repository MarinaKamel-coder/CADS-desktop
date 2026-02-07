import os
import shutil
import uuid
from PyQt6 import QtWidgets, QtCore, QtGui
from controllers import admin_controller as controller

class DocumentManagerWidget(QtWidgets.QWidget):
    def __init__(self, client, parent=None):
        super().__init__(parent)
        self.client = client
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # --- BARRE D'OUTILS ---
        header = QtWidgets.QHBoxLayout()
        
        # Barre de recherche (Nouveau)
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Rechercher un document (nom, format...)...")
        self.search_bar.setMinimumHeight(35)
        self.search_bar.textChanged.connect(self.filter_documents)
        
        self.btn_add = QtWidgets.QPushButton(" 📤 Ajouter un fichier")
        self.btn_add.setMinimumHeight(35)
        self.btn_add.setFixedWidth(180)
        self.btn_add.setStyleSheet("background-color: #2563eb; color: white; font-weight: bold;")
        self.btn_add.clicked.connect(self.upload_file)
        
        header.addWidget(self.search_bar)
        header.addWidget(self.btn_add)
        layout.addLayout(header)

        # Table des documents
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Nom", "Format", "Taille (Ko)", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        # Style pour la sélection
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

    def filter_documents(self):
        """Filtre les lignes de la table selon le texte saisi"""
        search_text = self.search_bar.text().lower()
        for row in range(self.table.rowCount()):
            # On cherche dans le Nom (colonne 0) et le Format (colonne 1)
            name_item = self.table.item(row, 0)
            format_item = self.table.item(row, 1)
            
            match = False
            if name_item and search_text in name_item.text().lower():
                match = True
            elif format_item and search_text in format_item.text().lower():
                match = True
                
            self.table.setRowHidden(row, not match)

    def refresh_list(self):
        self.table.setRowCount(0)
        docs = controller.get_client_documents(self.client.id)
        for row, d in enumerate(docs):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(d.name))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(d.type.upper()))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(str(d.size // 1024)))
            
            # Actions
            actions = QtWidgets.QWidget()
            l = QtWidgets.QHBoxLayout(actions)
            l.setContentsMargins(2, 2, 2, 2)
            
            btn_open = QtWidgets.QPushButton("Ouvrir")
            btn_open.clicked.connect(lambda ch, p=d.file_path: os.startfile(p))
            
            btn_del = QtWidgets.QPushButton("X")
            btn_del.setStyleSheet("background-color: #7f1d1d; color: white;")
            btn_del.clicked.connect(lambda ch, id=d.id: self.delete_doc(id))
            
            l.addWidget(btn_open); l.addWidget(btn_del)
            self.table.setCellWidget(row, 3, actions)

    def upload_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choisir un document", "", 
            "Docs (*.pdf *.xlsx *.docx *.txt *.png *.jpg)")
        if path:
            os.makedirs("storage/documents", exist_ok=True)
            new_name = f"{uuid.uuid4().hex[:8]}_{os.path.basename(path)}"
            dest = os.path.join("storage/documents", new_name)
            shutil.copy(path, dest)
            
            data = {
                "name": os.path.basename(path),
                "file_path": dest,
                "client": self.client.id,
                "accountant": self.client.accountant.id if self.client.accountant else None
            }
            if controller.add_document(data):
                self.refresh_list()

    def delete_doc(self, doc_id):
        if controller.delete_document(doc_id):
            self.refresh_list()