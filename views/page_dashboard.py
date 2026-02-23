import os
import pyqtgraph as pg
from PyQt6 import QtWidgets, uic
from controllers import dashboard_controller as controller

class DashboardPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        base_path = os.path.dirname(__file__)
        ui_path = os.path.abspath(os.path.join(base_path, "..", "ui", "page_dashboard.ui"))
        uic.loadUi(ui_path, self)

        # Initialisation des références aux conteneurs de graphiques
        self.setup_charts()

    def setup_charts(self):
        """Configure les layouts pour les conteneurs du .ui"""
        # On ne crée pas de nouveau layout, on utilise ce container

        if not self.container_pie.layout():
            self.layout_pie = QtWidgets.QVBoxLayout(self.container_pie)
        else:
            self.layout_pie = self.container_pie.layout()

    def load_data(self):
        """Méthode de rafraîchissement des données"""
        try:
            # 1. Mise à jour des stats (labels du .ui)
            stats = controller.get_admin_dashboard_stats()
            
            # Utilisation directe des objectName de ton fichier .ui
            self.lbl_total_acc.setText(str(stats.get("total_accountants", 0)))
            self.lbl_total_cli.setText(str(stats.get("total_clients", 0)))

            # 2. Mise à jour des graphiques
            data = controller.get_charts_data()
            self.draw_accountant_bars(data.get("pie", {}))
            
        except Exception as e:
            print(f"❌ Erreur refresh Dashboard: {e}")

    def draw_accountant_bars(self, data):
        """Graphique horizontal : Clients par Comptable"""
        self._clear_layout(self.layout_pie)
        
        plot = pg.PlotWidget(title="Répartition Clients / Comptable")
        plot.setBackground('#1f2937')
        
        if data:
            names = list(data.keys())
            y_indices = list(range(len(names)))
            widths = list(data.values())
            
            bg = pg.BarGraphItem(x0=0, y=y_indices, width=widths, height=0.1, brush='#10b981')
            plot.addItem(bg)
            
            # Axe Y (Noms des comptables)
            ax_y = plot.getAxis('left')
            ax_y.setTicks([[(i, name) for i, name in enumerate(names)]])
            
            # Axe X (Nombre de clients - Uniquement des ENTIERS)
            ax_x = plot.getAxis('bottom')
            max_clients = max(widths) if widths else 5
            # On crée une liste d'entiers de 0 jusqu'au maximum de clients + 1
            ticks = list(range(0, int(max_clients) + 2))
            ax_x.setTicks([[(t, str(t)) for t in ticks]])
            
        self.layout_pie.addWidget(plot)

    def _clear_layout(self, layout):
        """Supprime proprement l'ancien graphique"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()