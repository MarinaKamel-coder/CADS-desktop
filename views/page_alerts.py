from PyQt6 import QtWidgets, QtGui, QtCore
from controllers import deadline_controller 
from controllers import staff_controller 
from datetime import datetime

class AlertsPage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_filters()
        self.load_data() # charger les données dès l'ouverture

    def setup_ui(self):
        if self.layout():
            return
            
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- TITRE ET FILTRES ---
        header = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel("🚨 Centre de Supervision des Alertes")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ef4444; margin-bottom: 10px;")
        header.addWidget(title)

        filters_layout = QtWidgets.QHBoxLayout()
        
        self.combo_acc = QtWidgets.QComboBox()
        self.combo_acc.setMinimumWidth(200)
        self.combo_acc.currentIndexChanged.connect(self.load_data)

        self.combo_prio = QtWidgets.QComboBox()
        self.combo_prio.addItems(["Toutes les priorités", "HIGH", "MEDIUM", "LOW"])
        self.combo_prio.currentIndexChanged.connect(self.load_data)

        btn_refresh = QtWidgets.QPushButton("🔄 Actualiser")
        btn_refresh.clicked.connect(self.load_data)
        btn_refresh.setFixedWidth(120)

        filters_layout.addWidget(QtWidgets.QLabel("Comptable :"))
        filters_layout.addWidget(self.combo_acc)
        filters_layout.addWidget(QtWidgets.QLabel("Priorité :"))
        filters_layout.addWidget(self.combo_prio)
        filters_layout.addStretch()
        filters_layout.addWidget(btn_refresh)
        
        header.addLayout(filters_layout)
        layout.addLayout(header)

        # --- TABLE DES ALERTES ---
        self.table = QtWidgets.QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "CLIENT", "TÂCHE", "ÉCHÉANCE", "RETARD", "RESPONSABLE", "PRIORITÉ", "ACTIONS"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1e293b; color: white; gridline-color: #334155; alternate-background-color: #1e293b; }
            QHeaderView::section { background-color: #0f172a; color: #94a3b8; padding: 5px; border: 1px solid #334155; }
        """)
        layout.addWidget(self.table)

    def load_filters(self):
        """Remplit le combo des comptables en incluant les profils Web synchronisés"""
        self.combo_acc.clear()
        self.combo_acc.addItem("Tous les responsables", None)
        
        accountants = staff_controller.get_all_accountants()
        for acc in accountants:
            label = f"{acc.first_name} {acc.last_name}"
            self.combo_acc.addItem(label, acc.id)

    
    def load_data(self):
        self.table.setRowCount(0)
        deadlines = deadline_controller.get_all_overdue_deadlines()
        
        acc_filter = self.combo_acc.currentData()
        prio_filter = self.combo_prio.currentText()
        now = datetime.now()

        for d in deadlines:
            # --- 1. SÉCURITÉ DATE (Vérifie les deux formats possibles) ---
            d_date = d.get('due_date') or d.get('dueDate') 
            
            if d_date is None:
                continue 

            # --- 2. FILTRES (Conversion en string pour comparer UUID et Int) ---
            # On s'assure que acc_filter et l'ID du dictionnaire sont du même type
            if acc_filter and str(d.get('accountant_id')) != str(acc_filter):
                continue
            
            if prio_filter != "Toutes les priorités" and d.get('priority') != prio_filter:
                continue

            # --- 3. GESTION DES DATES ET CALCUL DU RETARD ---
            try:
                # Si c'est une string (ISO de Neon), on convertit
                if isinstance(d_date, str):
                    d_date = datetime.fromisoformat(d_date.replace('Z', ''))
                
                target_date = d_date.date() if hasattr(d_date, 'date') else d_date
                current_date = now.date()
                delta = (current_date - target_date).days
            except Exception as e:
                print(f"⚠️ Erreur format date sur {d.get('title')}: {e}")
                continue

            # --- 4. AFFICHAGE DANS LE TABLEAU ---
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Client
            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(d.get('client_name', 'Inconnu'))))

            # Tâche (On stocke l'ID et la Source à l'intérieur de l'item)
            title = str(d.get('title', 'Sans titre'))
            task_item = QtWidgets.QTableWidgetItem(title)
            # On cache l'ID technique et la source pour les récupérer au clic
            task_item.setData(QtCore.Qt.ItemDataRole.UserRole, d.get('id'))
            task_item.setData(QtCore.Qt.ItemDataRole.UserRole + 1, d.get('source'))
            self.table.setItem(row, 1, task_item)
            
            # Échéance / Retard / Responsable / Priorité (ton code existant)
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(target_date.strftime("%d/%m/%Y")))
            
            delay_text = f"⚠️ {delta} jours" if delta > 0 else "Aujourd'hui"
            delay_item = QtWidgets.QTableWidgetItem(delay_text)
            delay_item.setForeground(QtGui.QColor("#ef4444"))
            self.table.setItem(row, 3, delay_item)

            self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(str(d.get('accountant_name', 'Non assigné'))))
            
            prio = d.get('priority', 'MEDIUM')
            prio_item = QtWidgets.QTableWidgetItem(prio)
            self.table.setItem(row, 5, prio_item)

            # --- 3. AJOUT DU BOUTON TERMINER ---
            btn_finish = QtWidgets.QPushButton("Terminer")
            btn_finish.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            btn_finish.setStyleSheet("""
                QPushButton { 
                    background-color: #059669; color: white; border-radius: 4px; 
                    font-weight: bold; padding: 5px; margin: 2px;
                }
                QPushButton:hover { background-color: #10b981; }
            """)
            
            # On utilise une "closure" (r=row) pour capturer l'index de la ligne
            btn_finish.clicked.connect(lambda checked, r=row: self.terminate_task(r))
            self.table.setCellWidget(row, 6, btn_finish)

    def terminate_task(self, row):
        """Action déclenchée par le bouton Terminer"""
        task_item = self.table.item(row, 1)
        deadline_id = task_item.data(QtCore.Qt.ItemDataRole.UserRole)
        source = task_item.data(QtCore.Qt.ItemDataRole.UserRole + 1)
        title = task_item.text()

        reply = QtWidgets.QMessageBox.question(
            self, "Confirmation", 
            f"Voulez-vous marquer la tâche suivante comme terminée ?\n\n{title}",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            # On nettoie le titre des emojis avant l'envoi
            clean_title = title.replace("🌐", "").replace("💻", "").strip()
            
            # Appel au contrôleur
            # Note: pour le Web, on passe le deadline_id comme web_id si la source est 'Web'
            web_id_param = deadline_id if source == "Web" else None
            
            success = deadline_controller.update_deadline_status_combined(
                deadline_id=deadline_id,
                title=clean_title,
                due_date=None, # Pas strictement nécessaire si on a l'ID
                web_id=web_id_param
            )

            if success:
                QtWidgets.QMessageBox.information(self, "Succès", "La tâche a été mise à jour.")
                self.load_data() # Rafraîchir le tableau
            else:
                QtWidgets.QMessageBox.warning(self, "Erreur", "Impossible de mettre à jour la tâche.")