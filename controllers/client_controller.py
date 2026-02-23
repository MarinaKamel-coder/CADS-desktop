import uuid
from database import Client, WebClient, db_desktop, db_web
from .staff_controller import get_all_staff_combined


def get_all_clients():
    """Récupère tous les clients avec tri par nom"""
    try:
        if db_desktop.is_closed():
            db_desktop.connect()
        # On trie par nom de famille par défaut
        return list(Client.select().order_by(Client.last_name.asc()))
    except Exception as e:
        print(f"❌ Erreur get_all_clients: {e}")
        return []
    
def get_client_by_id(client_id):
    try:
        if db_desktop.is_closed(): db_desktop.connect()
        return Client.get_or_none(Client.id == str(client_id))
    except Exception as e:
        print(f"Erreur recherche client {client_id}: {e}")
        return None

def add_client(data):
    """Ajoute un client en générant un UUID unique"""
    try:
        if db_desktop.is_closed():
            db_desktop.connect()
            
        with db_desktop.atomic():
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
        if db_desktop.is_closed(): db_desktop.connect()
        
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
        if db_desktop.is_closed():
            db_desktop.connect()
            
        client = Client.get_or_none(Client.id == client_id)
        if client:
            client.delete_instance()
            return True
        return False
    except Exception as e:
        print(f"❌ Erreur delete_client : {e}")
        return False
    
def get_all_clients_combined():
    clients_list = []
    merged_data = {}

    # --- 1. CHARGEMENT DESKTOP ---
    try:
        if db_desktop.is_closed(): db_desktop.connect()
        
        # On récupère d'abord tout le staff pour faire un dictionnaire de correspondance rapide
        # Cela évite de faire une requête SQL à chaque ligne du tableau
        all_staff = get_all_staff_combined()
        staff_map = {str(s['id']): f"{s['first_name']} {s['last_name']}" for s in all_staff}

        for c in Client.select().dicts():
            email_key = str(c.get('email', '')).lower().strip()
            
            # 🔄 CORRECTION ICI :
            # Peewee .dicts() renvoie souvent la clé étrangère sous 'accountant' ou 'accountant_id'
            acc_id = str(c.get('accountant') or c.get('accountant_id') or "")
            
            # On cherche le nom dans notre map, sinon "Non assigné"
            acc_name = staff_map.get(acc_id, "Non assigné")

            merged_data[email_key] = {
                "id": c['id'],
                "web_id": None, 
                "source": "Desktop",
                "is_synced": True,
                "first_name": c.get('first_name', ''),
                "last_name": c.get('last_name', ''),
                "email": c.get('email', ''),
                "phone": c.get('phone', ''),
                "accountant_id": acc_id,
                "accountant": acc_name,  # On envoie bien le TEXTE au tableau
                "created_at": c.get('created_at').strftime("%Y-%m-%d") if c.get('created_at') else "-",
                "date_left": c.get('date_left').strftime("%Y-%m-%d") if c.get('date_left') else "---",
            }
    except Exception as e:
        print(f"❌ Erreur lecture Desktop : {e}")

    # --- 2. CHARGEMENT WEB ---
    try:
        if db_web.is_closed(): db_web.connect()
        query_web = WebClient.select()
        
        for wc in query_web:
            email_key = str(wc.email).lower().strip()

            if email_key in merged_data:
                # MISE À JOUR : On garde les infos Web prioritaires
                merged_data[email_key]["web_id"] = wc.id
                merged_data[email_key]["first_name"] = wc.first_name
                merged_data[email_key]["last_name"] = wc.last_name
                merged_data[email_key]["phone"] = wc.phone
                
                # --- AJOUT INDISPENSABLE POUR ÉVITER KEYERROR ---
                merged_data[email_key]["raw_object"] = wc 
                
                # Sync physique SQLite
                Client.update({
                    Client.first_name: wc.first_name,
                    Client.last_name: wc.last_name,
                    Client.phone: wc.phone
                }).where(Client.email == wc.email).execute()
                
            else:
                # Client uniquement sur le Web
                merged_data[email_key] = {
                    "id": wc.id,
                    "web_id": wc.id,
                    "source": "Web",
                    "is_synced": False,
                    "raw_object": wc, # <--- AJOUT INDISPENSABLE ICI AUSSI
                    "first_name": wc.first_name,
                    "last_name": wc.last_name,
                    "email": wc.email,
                    "phone": wc.phone,
                    "accountant": "🌐 Portail Web",
                    "created_at": "Via Web",
                    "date_left": "---",
                }
    except Exception as e:
        print(f"❌ Erreur Sync Web -> Desktop : {e}")

    final_list = list(merged_data.values())
    final_list.sort(key=lambda x: x['last_name'].lower())
    return final_list
    



    
def update_client_combined(client_id, web_id, data):
    success_local = False
    success_web = False

    # 1. Mise à jour Locale 
    try:
        from database import Client
        client = Client.get_by_id(client_id)
        client.first_name = data.get('first_name', client.first_name)
        client.last_name = data.get('last_name', client.last_name)
        client.email = data.get('email', client.email)
        client.phone = data.get('phone', client.phone)
        
        # On enregistre l'ID du comptable (qu'il soit int ou UUID)
        if 'accountant' in data:
            client.accountant_id = data['accountant']
            
        client.save()
        success_local = True
    except Exception as e:
        print(f"❌ Erreur update local: {e}")

    # 2. Mise à jour Web (Neon / PostgreSQL)
    if web_id:
        try:
            from database import WebClient
            # On mappe les champs vers la structure Neon
            web_update_data = {
                "first_name": data.get('first_name'),
                "last_name": data.get('last_name'),
                "email": data.get('email'),
                "phone": data.get('phone')
            }
            
            # 🔄 SYNCHRONISATION DU COMPTABLE SUR LE WEB
            # Si l'ID du comptable est un UUID (donc un WebUser), on l'assigne sur Neon
            if 'accountant' in data and isinstance(data['accountant'], str):
               web_update_data["user_id"] = data['accountant']

            query = WebClient.update(**web_update_data).where(WebClient.id == web_id)
            query.execute()
            success_web = True
        except Exception as e:
            print(f"❌ Erreur update web: {e}")

    return success_local, success_web
