# 📁 CADS - Gestionnaire de Cabinet Comptable (Sync Hybride)

Une application de bureau robuste et intuitive développée en **Python 3** avec le framework **PyQt6**. Ce logiciel permet de centraliser la gestion des clients et des employés (comptables) pour optimiser le suivi des dossiers fiscaux.

---

## ✨ Fonctionnalités Clés

### 🔄 Synchronisation Hybride Directe

- **Double Source** : Fusion transparente des clients stockés localement et des clients provenant du portail Web (Neon).
- **Mode Temps Réel** : Les modifications apportées sur le bureau sont directement répercutées sur la base de données PostgreSQL.
- **Intégrité des Données** : Utilisation d'UUIDs pour garantir l'absence de conflits lors de la fusion des sources.

### 👥 Gestion des Clients & Staff

- **Tableau de Bord Dynamique** : Visualisation avec tri automatique et indicateurs de provenance (Desktop vs Web).
- **Portefeuille Client** : Attribution automatique des clients aux comptables avec suivi des statuts (Actif/Inactif).
- **Sécurité** : Hachage des mots de passe avec bcrypt pour la gestion des accès administrateur.

### 👔 Gestion des Employés

- **Rôles Hiérarchiques** : Distinction entre Comptables Seniors, Juniors et Stagiaires.
- **Portefeuille Client** : Calcul automatique du nombre de clients par comptable.
- **Statuts** : Gestion de l'état (Actif/Inactif) pour une administration fluide.

### 🔍 Outils Avancés

- **Recherche Instantanée** : Barre de recherche intelligente filtrant par nom, courriel ou rôle sans rechargement de page.
- **Interface Moderne** : Design épuré utilisant des fichiers `.ui` et une feuille de style `.qss` personnalisée.

---

## 🚀 Comment lancer le projet ?

### 1. Prérequis

Vous devez avoir installé **Python** (version 3.8 ou plus récente).

### 2. Installation

Ouvrez votre terminal (ou invite de commande) dans le dossier du projet :

```bash
# Création de l'environnement virtuel
python -m venv venv

# Activation de l'environnement

```bash
# Initialiser le projet avec uv
uv init

# Ajouter les dépendances nécessaires
uv add pyqt6 pyqt6-tools peewee psycopg2-binary setuptools

# Pour ouvrir Qt Designer et modifier les interfaces (.ui)
uv run pyqt6-tools designer

# Pour lancer l'application
uv run main.py



### 📂 Organisation du Code

L'architecture suit une séparation claire des responsabilités :

/controllers : Contient la logique de validation et les interactions avec la base de données.

/ui : Fichiers XML générés par Qt Designer pour le design visuel.

/views : Fichiers Python qui pilotent les fenêtres et gèrent les événements utilisateurs.

database.py : Modèles de données (Admin, Accountant, Client, Document, Deadline, Alert) et configuration SQL.

styles.qss : Le fichier CSS pour personnaliser l'apparence des boutons et des tableaux.

🛠️ Technologies utilisées
Langage : Python 3.12

Interface Graphique : PyQt6 (Qt Framework)

Design : Qt Designer (fichiers .ui)

Base de données : SQLite (via un ORM ou SQL direct).
