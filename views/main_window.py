from PyQt6 import QtWidgets, uic
from views.auth_pages import LoginPage, SignupPage
from views.page_dashboard import DashboardPage
from views.page_accountants import AccountantsPage
from views.page_clients import ClientsPage
from views.page_alerts import AlertsPage


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        # Chargement de l'interface
        uic.loadUi("ui/main_window.ui", self)
        self.setWindowTitle("CADS Desktop - Administration")

        # Initialisation sécurisée des variables de page
        self.page_acc = None
        self.page_cli = None

        # 1. État initial : Cacher le menu 
        self.toolBox.setVisible(False)

        self.btn_logout.setVisible(False) # Cacher le bouton logout au début

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

        # Connexion du bouton Logout
        self.btn_logout.clicked.connect(self.logout)

        self.stackedWidget.setCurrentIndex(0)

    def cleanup_stacked_widget(self):
        """Vide proprement le stackedWidget"""
        while self.stackedWidget.count() > 0:
            widget = self.stackedWidget.widget(0)
            self.stackedWidget.removeWidget(widget)
            if widget: widget.deleteLater()

    def unlock_dashboard(self, admin_user):
        if self.page_acc is None:
            self.page_dash = DashboardPage() 
            self.page_acc = AccountantsPage()
            self.page_cli = ClientsPage()
            self.page_alerts = AlertsPage()
            
            # Ajout au StackedWidget
            self.stackedWidget.addWidget(self.page_dash) # Index 2
            self.stackedWidget.addWidget(self.page_acc)  # Index 3
            self.stackedWidget.addWidget(self.page_cli)  # Index 4
            self.stackedWidget.addWidget(self.page_alerts) # Index 5

        self.toolBox.setVisible(True)
        self.btn_logout.setVisible(True)
        self.stackedWidget.setCurrentIndex(2) 
        self.page_dash.load_data()



    def switch_view(self, toolbox_index):
        """Bascule entre les pages de gestion (Index + 2)"""
        # Sécurité : ne rien faire si le menu est caché (pendant le login)
        if not self.toolBox.isVisible():
            return

        # Index 0 du ToolBox -> Page 2 (Dashboard)
        # Index 1 du ToolBox -> Page 3 (Comptables)
        # Index 2 du ToolBox -> Page 4 (Clients)
        # +2 pour sauter Login (0) et Signup (1)
        target_index = toolbox_index + 2

        if target_index < self.stackedWidget.count():
            self.stackedWidget.setCurrentIndex(target_index)
            
            active_page = self.stackedWidget.currentWidget()
            if hasattr(active_page, 'load_data'):
                active_page.load_data()

    def logout(self):
        """Réinitialise l'application à l'état de login"""
        if hasattr(self, 'page_login'):
            self.page_login.clear_inputs()
            
        # 1. Cacher les éléments réservés aux admin
        self.toolBox.setVisible(False)
        self.btn_logout.setVisible(False)
        
        # 2. Revenir à la page de login (Index 0)
        self.stackedWidget.setCurrentIndex(0)
        
        # 3. Nettoyer les instances des pages de données pour la sécurité
        # Cela forcera la recréation des pages (et donc le refresh) à la prochaine connexion
        self.page_acc = None 
        self.page_cli = None
        
        # On nettoie le stackedWidget des pages privées (on garde Login et Signup)
        while self.stackedWidget.count() > 2:
            widget = self.stackedWidget.widget(2)
            self.stackedWidget.removeWidget(widget)
            if widget: widget.deleteLater()
            
        print("✅ Déconnexion réussie")