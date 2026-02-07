import os
import pyqtgraph as pg
from PyQt6 import QtWidgets, QtCore, uic
from controllers import admin_controller as controller

class DashboardCard(QtWidgets.QFrame):
    """Petite carte pour afficher une statistique"""
    def __init__(self, title, value, color="#3b82f6"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #1f2937;
                border-radius: 15px;
                border: 1px solid #374151;
            }}
            QLabel {{ border: none; color: white; }}
        """)
        self.setMinimumSize(250, 150)
        
        layout = QtWidgets.QVBoxLayout(self)
        
        self.lbl_title = QtWidgets.QLabel(title)
        self.lbl_title.setStyleSheet("font-size: 14px; color: #9ca3af;")
        
        self.lbl_value = QtWidgets.QLabel(str(value))
        self.lbl_value.setStyleSheet(f"font-size: 36px; font-weight: bold; color: {color};")
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value, 0, QtCore.Qt.AlignmentFlag.AlignCenter)

class DashboardPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        base_path = os.path.dirname(__file__)
        ui_path = os.path.abspath(os.path.join(base_path, "..", "ui", "page_dashboard.ui"))
        uic.loadUi(ui_path, self)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)

        # Titre
        self.title = QtWidgets.QLabel("Tableau de Bord")
        self.title.setStyleSheet("font-size: 24px; font-weight: bold; color: white; margin-bottom: 10px;")
        self.layout.addWidget(self.title)

        # Grille pour les cartes
        self.cards_layout = QtWidgets.QHBoxLayout()
        self.card_acc = DashboardCard("COMPTABLES", 0, "#3b82f6")
        self.card_cli = DashboardCard("CLIENTS", 0, "#10b981")
        self.card_active = DashboardCard("ACTIFS", 0, "#f59e0b")
        
        self.cards_layout.addWidget(self.card_acc)
        self.cards_layout.addWidget(self.card_cli)
        self.cards_layout.addWidget(self.card_active)
        
        self.layout.addLayout(self.cards_layout)
        self.layout.addStretch() # Pousse tout vers le haut

        self.setup_charts()

    def setup_charts(self):
        # Layouts pour accueillir les graphiques
        self.layout_pie = QtWidgets.QVBoxLayout(self.container_pie)
        self.layout_bar = QtWidgets.QVBoxLayout(self.container_bar)

    def load_data(self):
        """Méthode appelée par la MainWindow pour rafraîchir la page"""
        try:
            # 1. Stats numériques (Cartes)
            stats = controller.get_admin_dashboard_stats()
            if hasattr(self, 'lbl_total_acc'): 
                self.lbl_total_acc.setText(str(stats.get("total_accountants", 0)))
            if hasattr(self, 'lbl_total_cli'): 
                self.lbl_total_cli.setText(str(stats.get("total_clients", 0)))
            
            # 2. Graphiques
            data = controller.get_charts_data()
            self.draw_monthly_bars(data.get("bar", {}))
            self.draw_accountant_bars(data.get("pie", {}))
            
        except Exception as e:
            print(f"❌ Erreur refresh Dashboard: {e}")

    def draw_monthly_bars(self, data):
        """Graphique vertical : Inscriptions par mois"""
        self._clear_layout(self.layout_bar)
        
        plot = pg.PlotWidget(title="Inscriptions par Mois")
        plot.setBackground('#1f2937') # Couleur sombre assortie à ton UI
        
        if data:
            months = list(data.keys())
            counts = list(data.values())
            bg = pg.BarGraphItem(x=months, height=counts, width=0.6, brush='#3b82f6')
            plot.addItem(bg)
            
        self.layout_bar.addWidget(plot)

    def draw_accountant_bars(self, data):
        """Graphique horizontal : Clients par Comptable"""
        self._clear_layout(self.layout_pie)
        
        plot = pg.PlotWidget(title="Répartition Clients / Comptable")
        plot.setBackground('#1f2937')
        
        if data:
            names = list(data.keys())
            y_indices = list(range(len(names)))
            widths = list(data.values())
            
            bg = pg.BarGraphItem(x0=0, y=y_indices, width=widths, height=0.6, brush='#10b981')
            plot.addItem(bg)
            
            # Affichage des noms des comptables sur l'axe Y
            ax = plot.getAxis('left')
            ax.setTicks([[(i, name) for i, name in enumerate(names)]])
            
        self.layout_pie.addWidget(plot)

    def _clear_layout(self, layout):
        """Supprime les anciens graphiques du layout"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()