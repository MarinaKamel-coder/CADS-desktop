import os
from PyQt6 import QtWidgets, uic, QtCore
from views.auth_pages import LoginPage, SignupPage
from views.page_accountants import AccountantsPage
from views.page_clients import ClientsPage

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Chargement de l'interface
        uic.loadUi("ui/main_window.ui", self)
        self.setWindowTitle("CADS Desktop - Administration")

        # Initialisation sécurisée des variables de page
        self.page_acc = None
        self.page_cli = None

        # 1. État initial
        self.toolBox.setVisible(False)
        self.cleanup_stacked_widget()

        # 2. Pages d'Auth
        self.page_login = LoginPage()
        self.page_signup = SignupPage()
        self.stackedWidget.addWidget(self.page_login)  # Index 0
        self.stackedWidget.addWidget(self.page_signup) # Index 1

        # 3. Connexions des signaux (Une seule fois dans __init__)
        self.page_login.switch_to_signup.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.page_signup.switch_to_login.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.page_login.login_success.connect(self.unlock_dashboard)
        self.page_signup.signup_success.connect(self.unlock_dashboard)
        
        # Connecter le menu latéral une seule fois ici
        self.toolBox.currentChanged.connect(self.switch_view)

        self.stackedWidget.setCurrentIndex(0)

    def cleanup_stacked_widget(self):
        """Vide proprement le stackedWidget"""
        while self.stackedWidget.count() > 0:
            widget = self.stackedWidget.widget(0)
            self.stackedWidget.removeWidget(widget)
            if widget: widget.deleteLater()

    def unlock_dashboard(self, admin_user):
        """Initialise le dashboard après login"""
        print(f"✅ Accès autorisé : {admin_user.first_name}")
        
        # Éviter de recréer les pages si elles existent déjà
        if self.page_acc is None:
            self.page_acc = AccountantsPage()
            self.page_cli = ClientsPage()
            self.stackedWidget.addWidget(self.page_acc) # Index 2
            self.stackedWidget.addWidget(self.page_cli) # Index 3

        self.toolBox.setVisible(True)
        self.stackedWidget.setCurrentIndex(2) # Direction page Comptables
        self.page_acc.load_data()

    def switch_view(self, toolbox_index):
        """Bascule entre les pages de gestion (Index + 2)"""
        # Sécurité : ne rien faire si le menu est caché (pendant le login)
        if not self.toolBox.isVisible():
            return

        target_index = toolbox_index + 2
        if target_index < self.stackedWidget.count():
            self.stackedWidget.setCurrentIndex(target_index)
            
            active_page = self.stackedWidget.currentWidget()
            if hasattr(active_page, 'load_data'):
                active_page.load_data()