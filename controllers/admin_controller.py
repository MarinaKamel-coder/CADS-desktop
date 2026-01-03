from database import Accountant, Client, db
import uuid
from datetime import datetime
from peewee import fn

def get_all_accountants():
    """Version ultra-sécurisée pour éviter l'erreur de liste"""
    try:
        if db.is_closed():
            db.connect()
            
        # 1. On prépare la requête (sans exécuter)
        query = Accountant.select()
        
        # 2. On ajoute le tri (toujours sur l'objet query)
        query = query.order_by(Accountant.last_name.asc())
        
        # 3. On ajoute le chargement des clients liés
        query = query.prefetch(Client)
        
        # 4. C'est UNIQUEMENT ici qu'on transforme en liste pour Python
        results = []
        for acc in query:
            results.append(acc)
            
        return results
        
    except Exception as e:
        print(f"❌ Erreur contrôleur get_all_accountants: {e}")
        return []

def add_accountant(data):
    """Crée un nouveau comptable dans la table accountants"""
    try:
        if db.is_closed():
            db.connect()
            
        with db.atomic():
            # Utilisation du modèle Accountant
            new_acc = Accountant.create(
                id=str(uuid.uuid4()),
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                email=data.get('email').lower().strip(),
                phone=data.get('phone'), 
                role=data.get('role', 'COMPTABLE'),
                status='ACTIF',
                date_joined=datetime.now()
            )
            return new_acc
    except Exception as e:
        print(f"❌ Erreur add_accountant: {e}")
        return None

def update_accountant(acc_id, data):
    try:
        # On cherche le comptable par son ID
        accountant = Accountant.get_by_id(acc_id)
        
        # On met à jour chaque champ reçu
        accountant.first_name = data.get('first_name')
        accountant.last_name = data.get('last_name')
        accountant.email = data.get('email')
        accountant.phone = data.get('phone')
        accountant.role = data.get('role')
        
        # Champs spécifiques à la modification (admin)
        if 'status' in data:
            accountant.status = data.get('status')
        if 'date_joined' in data:
            accountant.date_joined = data.get('date_joined')
        if 'date_left' in data:
            accountant.date_left = data.get('date_left')
            
        accountant.save() 
        return True
    except Exception as e:
        print(f"Erreur controller: {e}")
        return False

def delete_accountant(acc_id):
    """Supprime un comptable et ses liens (clients, docs, etc.)"""
    try:
        if db.is_closed():
            db.connect()
            
        acc = Accountant.get_or_none(Accountant.id == acc_id)
        if acc:
            # delete_instance(recursive=True) supprimera les clients associés 
            # si on_delete='CASCADE' est bien configuré
            acc.delete_instance(recursive=True)
            return True
        return False
    except Exception as e:
        print(f"❌ Erreur delete_accountant: {e}")
        return False

def get_admin_dashboard_stats():
    """Statistiques rapides pour l'accueil de l'admin"""
    try:
        if db.is_closed():
            db.connect()
        return {
            "total_accountants": Accountant.select().count(),
            "total_clients": Client.select().count(),
            "active_accountants": Accountant.select().where(Accountant.status == 'ACTIF').count()
        }
    except:
        return {"total_accountants": 0, "total_clients": 0, "active_accountants": 0}
    

# --- CLIENTS ---
def get_all_clients():
    """Récupère tous les clients avec tri par nom"""
    try:
        if db.is_closed():
            db.connect()
        # On trie par nom de famille par défaut
        return list(Client.select().order_by(Client.last_name.asc()))
    except Exception as e:
        print(f"❌ Erreur get_all_clients: {e}")
        return []
    
def get_client_by_id(client_id):
    try:
        if db.is_closed(): db.connect()
        return Client.get_by_id(client_id)
    except:
        return None

def add_client(data):
    """Ajoute un client en générant un UUID unique"""
    try:
        if db.is_closed():
            db.connect()
            
        with db.atomic():
            # On s'assure que l'ID est généré ici si non défini dans le modèle
            client_data = data.copy()
            if 'id' not in client_data:
                client_data['id'] = str(uuid.uuid4())
            
            new_client = Client.create(**client_data)
            return True
    except Exception as e:
        print(f"❌ Erreur ajout client : {e}")
        return False

def update_client(client_id, data):
    try:
        if db.is_closed(): db.connect()
        
        # On récupère le client
        client = Client.get_by_id(client_id)
        
        # Mise à jour des champs
        client.first_name = data.get('first_name')
        client.last_name = data.get('last_name')
        client.email = data.get('email')
        client.phone = data.get('phone')
        client.accountant = data.get('accountant')
        
        # Gestion des dates (si présentes dans le dictionnaire)
        if 'created_at' in data:
            client.created_at = data.get('created_at')
        if 'date_left' in data:
            client.date_left = data.get('date_left')

        client.save()
        return True
    except Exception as e:
        print(f"Erreur modification : {e}")
        return False

def delete_client(client_id):
    """Suppression d'un client par son ID"""
    try:
        if db.is_closed():
            db.connect()
            
        client = Client.get_or_none(Client.id == client_id)
        if client:
            client.delete_instance()
            return True
        return False
    except Exception as e:
        print(f"❌ Erreur delete_client : {e}")
        return False