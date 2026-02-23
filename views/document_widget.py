import os
from PyQt6 import QtWidgets, QtGui, QtCore
from controllers import document_controller as controller

class DocumentManagerWidget(QtWidgets.QWidget):
    def __init__(self, client_data):
        super().__init__()
        self.client_data = client_data
        self.setup_ui()
        self.refresh_list()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # --- BARRE D'OUTILS ---
        actions_layout = QtWidgets.QHBoxLayout()
        
        # Champ de recherche
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Rechercher un document...")
        self.search_bar.setClearButtonEnabled(True)
        self.search_bar.textChanged.connect(self.filter_documents)
        self.search_bar.setFixedWidth(250)

        self.btn_upload = QtWidgets.QPushButton("📤 Ajouter local")
        self.btn_upload.setStyleSheet("background-color: #2563eb; color: white; padding: 5px 15px;")
        self.btn_upload.clicked.connect(self.handle_upload)
        
        self.btn_refresh = QtWidgets.QPushButton("🔄")
        self.btn_refresh.setToolTip("Actualiser la liste")
        self.btn_refresh.clicked.connect(self.refresh_list)
        
        actions_layout.addWidget(self.search_bar)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_upload)
        actions_layout.addWidget(self.btn_refresh)
        layout.addLayout(actions_layout)

        # --- TABLE DES DOCUMENTS ---
        self.table = QtWidgets.QTableWidget()
        headers = ["Source", "Nom du fichier", "Taille", "Date d'ajout", "Actions"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        # Style de la table
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)

    def filter_documents(self):
        """Filtre les lignes selon le texte de recherche (Nom ou Source)"""
        search_text = self.search_bar.text().lower()
        for row in range(self.table.rowCount()):
            # Colonne 0 : Source, Colonne 1 : Nom
            source_item = self.table.item(row, 0)
            name_item = self.table.item(row, 1)
            
            match = (search_text in (source_item.text().lower() if source_item else "") or 
                     search_text in (name_item.text().lower() if name_item else ""))
            
            self.table.setRowHidden(row, not match)

    def refresh_list(self):
        self.table.setRowCount(0)
        docs = controller.get_client_documents_combined(self.client_data)

        for row, d in enumerate(docs):
            self.table.insertRow(row)
            
            # 1. Source (Icônes dynamiques)
            source_item = QtWidgets.QTableWidgetItem(d['source'])
            if d['source'] == 'Web':
                icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DriveNetIcon)
                source_item.setForeground(QtGui.QColor("#0ea5e9")) 
            else:
                icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DriveHDIcon)
                source_item.setForeground(QtGui.QColor("#64748b"))
            
            source_item.setIcon(icon)
            self.table.setItem(row, 0, source_item)

            # 2. Nom du fichier
            name_item = QtWidgets.QTableWidgetItem(d.get('name', 'Sans nom'))
            name_item.setFont(QtGui.QFont("Segoe UI", 9, QtGui.QFont.Weight.Bold))
            self.table.setItem(row, 1, name_item)

            # 3. Taille formatée
            size_kb = d.get('size', 0) / 1024
            size_text = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(size_text))

            # 4. Date d'ajout
            date_val = d.get('date')
            date_str = date_val.strftime("%Y-%m-%d %H:%M") if date_val else "---"
            self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(date_str))

            # 5. Actions
            self.add_row_actions(row, d)

    def add_row_actions(self, row, doc_data):
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)

        btn_action = QtWidgets.QPushButton()
        btn_action.setFixedSize(28, 28)
        btn_action.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        
        if doc_data['source'] == 'Web':
            # CAS WEB : TELECHARGEMENT
            btn_action.setText("📥")
            btn_action.setToolTip("Télécharger depuis le Cloud")
            btn_action.setStyleSheet("color: #0ea5e9;")
            btn_action.clicked.connect(lambda: self.handle_download(doc_data))
        else:
            # CAS LOCAL : OUVERTURE
            btn_action.setText("👁️")
            btn_action.setToolTip("Ouvrir le fichier local")
            btn_action.clicked.connect(lambda: self.handle_open(doc_data['file_path']))
        
        btn_del = QtWidgets.QPushButton("🗑️")
        btn_del.setFixedSize(28, 28)
        btn_del.setStyleSheet("color: #ef4444;")
        btn_del.clicked.connect(lambda: self.handle_delete(doc_data))

        layout.addWidget(btn_action)
        layout.addWidget(btn_del)
        self.table.setCellWidget(row, 4, container)

    def handle_download(self, doc_data):
        """Récupère le document depuis Neon (PostgreSQL) et l'enregistre sur le disque"""
        # 1. Demander où enregistrer le fichier
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Enregistrer le document", doc_data['name']
        )
        
        if not save_path:
            return

        try:
            # 2. Appeler le contrôleur pour récupérer les données binaires (Blob)
            # Cette fonction doit exister dans ton admin_controller
            content = controller.get_web_document_content(doc_data['id'])
            
            if content:
                # 3. Écrire le fichier sur le disque
                with open(save_path, 'wb') as f:
                    f.write(content)
                QtWidgets.QMessageBox.information(self, "Succès", "Document téléchargé avec succès !")
                
                # Optionnel : Demander s'il faut l'ouvrir maintenant
                if QtWidgets.QMessageBox.question(self, "Ouvrir", "Voulez-vous ouvrir le fichier ?") == QtWidgets.QMessageBox.StandardButton.Yes:
                    os.startfile(save_path)
            else:
                raise Exception("Contenu du fichier vide ou introuvable.")
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Erreur", f"Échec du téléchargement : {str(e)}")

    def handle_upload(self):
        if self.client_data.get('source') != "Desktop":
            QtWidgets.QMessageBox.information(self, "Client Web", 
                "Ce client est issu du portail Web. Importez-le en local pour gérer ses documents physiques.")
            return

        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Sélectionner un document")
        if file_path:
            # On prépare les données pour la DB
            new_doc = {
                "name": os.path.basename(file_path),
                "file_path": file_path,
                "client": self.client_data['id'],
                "accountant": self.client_data.get('accountant_id') # Assure-toi d'avoir cette info
            }
            if controller.add_document(new_doc):
                self.refresh_list()

    def handle_open(self, path):
        if os.path.exists(path):
            os.startfile(path)
        else:
            QtWidgets.QMessageBox.warning(self, "Erreur", "Le fichier n'existe plus à cet emplacement.")

    def handle_delete(self, doc):
        """Gère la suppression avec confirmation selon la source"""
        source_label = "le Cloud (Neon)" if doc['source'] == 'Web' else "votre base locale"
        
        msg = (f"Êtes-vous sûr de vouloir supprimer définitivement :\n\n"
               f"📄 {doc['name']}\n"
               f"📍 Depuis : {source_label} ?")

        confirm = QtWidgets.QMessageBox.question(
            self, 
            "Confirmation de suppression", 
            msg,
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if confirm == QtWidgets.QMessageBox.StandardButton.Yes:
            # Appel de la fonction combinée du contrôleur
            success = controller.delete_document_combined(doc['id'], doc['source'])
            
            if success:
                # Supprimer physiquement le fichier local s'il existe
                if doc['source'] == 'Desktop' and os.path.exists(doc.get('file_path', '')):
                    try:
                        os.remove(doc['file_path'])
                    except Exception as e:
                        print(f"⚠️ Fichier supprimé en DB mais erreur disque : {e}")
                
                self.refresh_list()
                QtWidgets.QMessageBox.information(self, "Succès", "Le document a été supprimé.")
            else:
                QtWidgets.QMessageBox.critical(self, "Erreur", "La suppression a échoué en base de données.")