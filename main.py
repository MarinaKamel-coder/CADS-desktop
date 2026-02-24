import sys
from PyQt6 import QtWidgets, QtCore
from views.main_window import MainWindow
from database import init_databases

# Filtre de messages personnalisé
def silent_handler(mode, context, message):
    # Liste des mots-clés à censurer
    blacklist = ["setPointSize"]
    if any(word in message for word in blacklist):
        return
    # Affiche le reste uniquement si c'est important
    if mode in [QtCore.QtMsgType.QtCriticalMsg, QtCore.QtMsgType.QtFatalMsg]:
        print(f"CRITICAL: {message}")

def main():
    app = QtWidgets.QApplication(sys.argv)

    try:
        with open("styles.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Fichier styles.qss introuvable, chargement par défaut.")
    
    # Initialisation de la base Neon
    if not init_databases():
        print("Erreur de connexion base de données. Arrêt.")
        return

    # On attache la fenêtre à l'objet 'app' pour la persistance
    app.main_window = MainWindow()
    app.main_window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()