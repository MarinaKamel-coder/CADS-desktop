import sys
from PyQt6 import QtWidgets
from views.main_window import MainWindow
from database import init_database

def main():
    app = QtWidgets.QApplication(sys.argv)

    try:
        with open("styles.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Fichier styles.qss introuvable, chargement par défaut.")
    
    # Initialisation de la base Neon
    if not init_database():
        print("Erreur de connexion base de données. Arrêt.")
        return

    # On attache la fenêtre à l'objet 'app' pour la persistance
    app.main_window = MainWindow()
    app.main_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()