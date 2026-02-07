import os
from database import Accountant, Client, Document, Deadline, db
import uuid
from datetime import datetime
from peewee import fn, JOIN

# --- GESTION DES ALERTES  ---

def get_overdue_count():
    """Compte global des retards pour le badge de notification"""
    try:
        if db.is_closed(): db.connect()
        today = datetime.now().date()
        return (Deadline.select()
                .where((Deadline.status == 'PENDING') & 
                       (fn.DATE(Deadline.due_date) <= today)).count())
    except Exception as e:
        print(f"❌ Erreur get_overdue_count: {e}")
        return 0

def get_all_overdue_deadlines():
    """Récupère toutes les échéances en retard avec jointures sécurisées"""
    try:
        if db.is_closed(): db.connect()
        today = datetime.now().date()
        
        # Utilisation de LEFT_OUTER pour ne perdre aucune donnée si un lien est manquant
        query = (Deadline.select(Deadline, Client, Accountant)
                 .join(Client, JOIN.LEFT_OUTER)
                 .switch(Deadline)
                 .join(Accountant, JOIN.LEFT_OUTER)
                 .where(
                     (Deadline.status == 'PENDING') & 
                     (fn.DATE(Deadline.due_date) <= today)
                 )
                 .order_by(Deadline.due_date.asc()))
        return list(query)
    except Exception as e:
        print(f"❌ Erreur get_all_overdue: {e}")
        return []

def get_charts_data():
    """Récupère les données formatées pour pyqtgraph"""
    try:
        if db.is_closed(): db.connect()
        
        # 1. Données pour le bar chart horizontal (Clients par Comptable)
        query_pie = (Accountant
                     .select(Accountant.last_name, fn.COUNT(Client.id).alias('count'))
                     .join(Client, JOIN.LEFT_OUTER)
                     .group_by(Accountant.last_name))
        pie_data = {q.last_name: q.count for q in query_pie}

        # 2. Données pour le Bar Chart (Inscriptions par mois)
        # On cast 'month' en integer pour pyqtgraph
        bar_query = (Client
                     .select(fn.to_char(Client.created_at, 'MM').alias('month'), 
                             fn.COUNT(Client.id).alias('count'))
                     .group_by(fn.to_char(Client.created_at, 'MM'))
                     .order_by(fn.to_char(Client.created_at, 'MM')))
        
        # Conversion explicite : {'01': 5} -> {1: 5}
        bar_data = {int(q.month): q.count for q in bar_query}
        
        return {"pie": pie_data, "bar": bar_data}
    except Exception as e:
        print(f"❌ Erreur stats graphiques: {e}")
        return {"pie": {}, "bar": {}}

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
    

def add_document(data):
    """Enregistre un document en base de données"""
    try:
        if db.is_closed(): db.connect()
        # Calcul de l'extension et de la taille
        ext = os.path.splitext(data['name'])[1].lower()
        size = os.path.getsize(data['file_path'])
        
        return Document.create(
            name=data['name'],
            type=ext,
            size=size,
            file_path=data['file_path'],
            client=data['client'],
            accountant=data['accountant']
        )
    except Exception as e:
        print(f"❌ Erreur add_document: {e}")
        return None

def get_client_documents(client_id):
    """Récupère tous les docs d'un client spécifique"""
    try:
        if db.is_closed(): db.connect()
        return list(Document.select().where(Document.client == client_id).order_by(Document.uploaded_at.desc()))
    except Exception as e:
        print(f"❌ Erreur get_docs: {e}")
        return []

def delete_document(doc_id):
    """Supprime l'entrée DB et le fichier physique"""
    try:
        doc = Document.get_by_id(doc_id)
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        doc.delete_instance()
        return True
    except:
        return False
    
def add_deadline(data):
    """Crée une nouvelle échéance pour un client"""
    try:
        if db.is_closed(): db.connect()
        return Deadline.create(**data)
    except Exception as e:
        print(f"❌ Erreur add_deadline: {e}")
        return None

def get_client_deadlines(client_id):
    """Récupère les échéances non terminées d'un client"""
    try:
        if db.is_closed(): db.connect()
        # On filtre par statut PENDING (défini dans ton modèle)
        return list(Deadline.select().where(
            (Deadline.client == client_id) & (Deadline.status == 'PENDING')
        ).order_by(Deadline.due_date.asc()))
    except Exception as e:
        print(f"❌ Erreur get_deadlines: {e}")
        return []

def update_deadline_status(deadline_id, new_status='COMPLETED'):
    """Met à jour le statut (ex: PENDING -> COMPLETED)"""
    try:
        query = Deadline.update(status=new_status).where(Deadline.id == deadline_id)
        query.execute()
        return True
    except:
        return False