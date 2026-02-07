from PyQt6 import QtWidgets, QtCore, QtGui
from controllers import admin_controller as controller

class AlertsPage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_filters()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- TITRE ET FILTRES ---
        header = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel("🚨 Centre de Supervision des Alertes")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #ef4444; margin-bottom: 10px;")
        header.addWidget(title)

        filters_layout = QtWidgets.QHBoxLayout()
        
        # Filtre Comptable
        self.combo_acc = QtWidgets.QComboBox()
        self.combo_acc.setMinimumWidth(200)
        self.combo_acc.setPlaceholderText("Filtrer par comptable")
        self.combo_acc.currentIndexChanged.connect(self.load_data)

        # Filtre Priorité
        self.combo_prio = QtWidgets.QComboBox()
        self.combo_prio.addItems(["Toutes les priorités", "HIGH", "MEDIUM", "LOW"])
        self.combo_prio.currentIndexChanged.connect(self.load_data)

        # Bouton Rafraîchir
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
        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "CLIENT", "TÂCHE", "ÉCHÉANCE", "RETARD (JOURS)", "COMPTABLE", "PRIORITÉ"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #1e293b; color: white; gridline-color: #334155; }
            QHeaderView::section { background-color: #0f172a; color: #94a3b8; padding: 5px; }
        """)
        layout.addWidget(self.table)

    def load_filters(self):
        """Remplit le combo des comptables"""
        self.combo_acc.clear()
        self.combo_acc.addItem("Tous les comptables", None)
        accountants = controller.get_all_accountants()
        for acc in accountants:
            self.combo_acc.addItem(f"{acc.first_name} {acc.last_name}", acc.id)

    def load_data(self):
        """Récupère et filtre les données"""
        self.table.setRowCount(0)
        deadlines = controller.get_all_overdue_deadlines()
        
        acc_filter = self.combo_acc.currentData()
        prio_filter = self.combo_prio.currentText()

        from datetime import datetime
        now = datetime.now()

        for d in deadlines:
            # Application des filtres
            if acc_filter and d.accountant.id != acc_filter: continue
            if prio_filter != "Toutes les priorités" and d.priority != prio_filter: continue

            row = self.table.rowCount()
            self.table.insertRow(row)

            # Calcul des jours de retard
            delta = (now.date() - d.due_date.date()).days

            self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(f"{d.client.first_name} {d.client.last_name}"))
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(d.title))
            
            date_item = QtWidgets.QTableWidgetItem(d.due_date.strftime("%d/%m/%Y"))
            date_item.setForeground(QtGui.QColor("#ef4444"))
            self.table.setItem(row, 2, date_item)

            delay_item = QtWidgets.QTableWidgetItem(f"+ {delta} jours")
            delay_item.setFont(QtGui.QFont("Arial", weight=QtGui.QFont.Weight.Bold))
            delay_item.setForeground(QtGui.QColor("#ef4444"))
            self.table.setItem(row, 3, delay_item)

            self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{d.accountant.first_name} {d.accountant.last_name}"))
            
            prio_item = QtWidgets.QTableWidgetItem(d.priority)
            if d.priority == "HIGH": prio_item.setForeground(QtGui.QColor("#f97316"))
            self.table.setItem(row, 5, prio_item)