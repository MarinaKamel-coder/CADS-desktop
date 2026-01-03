import os
import uuid
import bcrypt
from PyQt6 import QtWidgets, uic, QtCore
from database import Admin  
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

def apply_modern_effects(widget):
    if hasattr(widget, 'frame_container'):
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(30)
        glow.setXOffset(0)
        glow.setYOffset(0)
        glow.setColor(QColor(59, 130, 246, 80)) 
        widget.frame_container.setGraphicsEffect(glow)

class SignupPage(QtWidgets.QWidget):
    """Page d'inscription pour le compte Administrateur uniquement"""
    switch_to_login = QtCore.pyqtSignal()
    signup_success = QtCore.pyqtSignal(object)

    def __init__(self):
        super().__init__()
        ui_path = os.path.join(os.path.dirname(__file__), "..", "ui", "page_signup.ui")
        uic.loadUi(ui_path, self)

        self.input_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.input_confirm_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        self.btn_submit.clicked.connect(self.handle_signup)
        self.btn_goto_login.clicked.connect(self.switch_to_login.emit)

    def handle_signup(self):
        prenom = self.input_prenom.text().strip()
        nom = self.input_nom.text().strip()
        email = self.input_email.text().strip()
        pwd = self.input_password.text()
        conf_pwd = self.input_confirm_password.text()

        if not all([prenom, nom, email, pwd, conf_pwd]):
            QtWidgets.QMessageBox.warning(self, "Champs requis", "Veuillez remplir tous les champs.")
            return

        if pwd != conf_pwd:
            QtWidgets.QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")
            return

        # Hachage du mot de passe
        salt = bcrypt.gensalt()
        hashed_pwd = bcrypt.hashpw(pwd.encode('utf-8'), salt)

        try:
            # Création dans la table ADMIN
            admin = Admin.create(
                id=str(uuid.uuid4()),
                first_name=prenom,
                last_name=nom,
                email=email,
                password=hashed_pwd.decode('utf-8')
            )
            QtWidgets.QMessageBox.information(self, "Succès", "Compte Administrateur créé avec succès !")
            self.signup_success.emit(admin)
            
        except Exception as e:
            if "unique constraint" in str(e).lower():
                QtWidgets.QMessageBox.critical(self, "Erreur", "Cet email est déjà utilisé par un administrateur.")
            else:
                QtWidgets.QMessageBox.critical(self, "Erreur DB", f"Erreur lors de l'inscription : {e}")

class LoginPage(QtWidgets.QWidget):
    """Page de connexion pour l'Administrateur"""
    switch_to_signup = QtCore.pyqtSignal()
    login_success = QtCore.pyqtSignal(object)

    def __init__(self):
        super().__init__()
        ui_path = os.path.join(os.path.dirname(__file__), "..", "ui", "page_login.ui")
        uic.loadUi(ui_path, self)

        self.input_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        apply_modern_effects(self)

        self.btn_submit.clicked.connect(self.handle_login)
        self.btn_goto_signup.clicked.connect(self.switch_to_signup.emit)

    def handle_login(self):
        email = self.input_email.text().strip()
        pwd_saisi = self.input_password.text()

        if not email or not pwd_saisi:
            QtWidgets.QMessageBox.warning(self, "Champs requis", "Email et mot de passe nécessaires.")
            return

        try:
            # On cherche uniquement dans la table ADMIN
            admin = Admin.get(Admin.email == email)
            
            # Vérification du mot de passe avec Bcrypt
            if bcrypt.checkpw(pwd_saisi.encode('utf-8'), admin.password.encode('utf-8')):
                print(f"✅ Authentification Admin réussie : {admin.first_name}")
                self.login_success.emit(admin)
            else:
                QtWidgets.QMessageBox.critical(self, "Erreur", "Mot de passe incorrect.")
                
        except Admin.DoesNotExist:
            QtWidgets.QMessageBox.critical(self, "Erreur", "Ce compte administrateur n'existe pas.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Erreur système", f"Erreur : {e}")