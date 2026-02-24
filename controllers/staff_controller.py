import uuid
from datetime import datetime
from database import Accountant, Client, WebUser, WebClient, db_desktop, db_web

def add_accountant(data):
    """Crée un nouveau comptable dans la table accountants"""
    try:
        if db_desktop.is_closed():
            db_desktop.connect()
            
        with db_desktop.atomic():
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
def get_all_accountants():
    try:
        if db_desktop.is_closed(): db_desktop.connect()
        # 1. Récupérer les comptables
        accountants = list(Accountant.select().order_by(Accountant.last_name.asc()))
        # 2. Récupérer tous les clients
        clients = list(Client.select())
        # 3. Associer manuellement 
        for acc in accountants:
            acc.clients = [c for c in clients if str(c.accountant_id) == str(acc.id)]
        return accountants
    except Exception as e:
        print(f"❌ Erreur contrôleur get_all_accountants: {e}")
        return []

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
        if db_desktop.is_closed():
            db_desktop.connect()
            
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

def get_all_staff_combined():
    staff_list = []
    try:
        # 1. Connexions
        if db_desktop.is_closed(): db_desktop.connect()
        if db_web.is_closed(): db_web.connect()

        # 2. PHASE DE SYNCHRONISATION (Web -> Desktop)
        # On récupère tous les utilisateurs du Web pour les "apprendre" en local
        distants_web = list(WebUser.select())
        
        for user in distants_web:
            # Cette commande magique crée le comptable en local s'il n'existe pas,
            # ou le met à jour s'il a changé (Upsert)
            Accountant.get_or_create(
                id=user.id, # On garde le même ID (user_...)
                defaults={
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "role": user.role or 'COMPTABLE',
                    "status": 'ACTIF',
                    "date_joined": datetime.now()
                }
            )
        
        # 3. RÉCUPÉRATION FINALE (Maintenant que tout est en local)
        locaux = list(Accountant.select().order_by(Accountant.last_name.asc()))
        all_clients_locaux = list(Client.select())

        for acc in locaux:
            # On compte les clients sur les deux bases pour ce comptable
            count_locaux = sum(1 for c in all_clients_locaux if str(c.accountant_id) == str(acc.id))
            count_web = WebClient.select().where(WebClient.user_id == acc.id).count()
            
            # On détermine la source pour l'affichage
            # Si l'ID commence par 'user_', il vient de Clerk (Web)
            source_label = "Web" if str(acc.id).startswith("user_") else "Desktop"

            staff_list.append({
                "id": acc.id,
                "source": source_label,
                "first_name": acc.first_name,
                "last_name": acc.last_name,
                "email": acc.email,
                "role": acc.role,
                "status": acc.status,
                "nb_clients": count_locaux + count_web,
                "date_joined": acc.date_joined.strftime("%Y-%m-%d") if acc.date_joined else "Inconnue",
                "date_left": acc.date_left.strftime("%Y-%m-%d") if acc.date_left else "En poste"
            })

        return staff_list

    except Exception as e:
        print(f"❌ Erreur synchro/fusion staff: {e}")
        return []

def update_staff_member(member_id, data, source="Desktop"):
    """Modifie un membre du staff en filtrant les champs calculés"""
    try:
        # 1. Sélection de la cible
        if source == "Web":
            model = WebUser
            db_target = db_web
            # Champs acceptés par ton schéma Prisma (Web)
            filtered_data = {
                "first_name": data.get('first_name'),
                "last_name": data.get('last_name'),
                "email": data.get('email'),
                "role": data.get('role'),
                "updated_at": datetime.now()
            }
        else:
            model = Accountant
            db_target = db_desktop

            # Conversion des chaînes "YYYY-MM-DD" en objets datetime si nécessaire
            def parse_date(d):
                if not d or str(d).strip() in ["En poste", "---", "Inconnue", ""]: return None
                if isinstance(d, datetime): return d
                try:
                    return datetime.strptime(str(d), "%Y-%m-%d")
                except:
                    return None
            # Champs acceptés par ton modèle Accountant (Desktop)
            # On EXCLUT explicitement 'nb_clients' car c'est un calcul
            filtered_data = {
                "first_name": data.get('first_name'),
                "last_name": data.get('last_name'),
                "email": data.get('email'),
                "phone": data.get('phone'),
                "role": data.get('role'),
                "status": data.get('status')
            }

            # On ne met à jour la date d'arrivée QUE si une date valide est fournie
            new_date_joined = parse_date(data.get('date_joined'))
            if new_date_joined:
                filtered_data["date_joined"] = new_date_joined

            # Pour la date de départ, on accepte le None (si le stagiaire est toujours là)
            filtered_data["date_left"] = parse_date(data.get('date_left'))

        if db_target.is_closed(): db_target.connect()

        with db_target.atomic():
            # On utilise filtered_data au lieu de data
            query = model.update(**filtered_data).where(model.id == member_id)
            result = query.execute()

            # Si on modifie le Web, on met à jour la copie locale aussi
            if source == "Web":
                Accountant.update(**filtered_data).where(Accountant.id == member_id).execute()
            print(f"✅ Mise à jour réussie ({source})")
            return result > 0
            
    except Exception as e:
        print(f"❌ Erreur Update ({source}) pour ID {member_id}: {e}")
        return False
    
def delete_staff_member(member_id, source="Desktop"):
    """Supprime un compte de n'importe quelle source"""
    try:
        model = WebUser if source == "Web" else Accountant
        db_target = db_web if source == "Web" else db_desktop

        if db_target.is_closed(): db_target.connect()

        # On récupère l'instance pour la supprimer
        obj = model.get_or_none(model.id == member_id)
        if obj:
            obj.delete_instance(recursive=True)
            return True
        return False
    except Exception as e:
        print(f"❌ Erreur Delete ({source}): {e}")
        return False