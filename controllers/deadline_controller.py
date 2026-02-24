from datetime import datetime
from peewee import fn, JOIN
import uuid
from database import Accountant, Deadline, WebClient, WebUser, WebDeadline, Client, db_desktop, db_web

def get_overdue_count():
    """Compte global des retards pour le badge (Local + Web)"""
    count = 0
    today = datetime.now().date() # On travaille directement avec la date
    try:
        # 1. Compte Desktop
        if db_desktop.is_closed(): db_desktop.connect()
        count += (Deadline.select()
                 .where((Deadline.status == 'PENDING') & 
                        (fn.DATE(Deadline.due_date) <= today)).count())
        
        # 2. Compte Web
        # Correction : On vérifie si l'URL ou la connexion existe
        if not db_web.is_closed() or db_web.obj:
            if db_web.is_closed(): db_web.connect()
            count += (WebDeadline.select()
                     .where((WebDeadline.status == 'PENDING') & 
                            (fn.DATE(WebDeadline.due_date) <= today)).count())
    except Exception as e:
        print(f"❌ Erreur get_overdue_count: {e}")
    return count

def get_all_overdue_deadlines():
    try:
        if db_desktop.is_closed(): db_desktop.connect()
        if db_web.is_closed(): db_web.connect()
        
        today = datetime.now().date()
        overdue_list = []

        # --- PARTIE WEB (Correction avec .dicts() car pas de FK explicites) ---
        query_web = (WebDeadline.select(
                        WebDeadline, 
                        WebClient.first_name.alias('cfn'), 
                        WebClient.last_name.alias('cln'),
                        WebUser.first_name.alias('ufn'),
                        WebUser.last_name.alias('uln'),
                        WebUser.id.alias('uid')
                    )
                    .join(WebClient, on=(WebDeadline.client_id == WebClient.id))
                    .join(WebUser, on=(WebDeadline.user_id == WebUser.id))
                    .where(WebDeadline.status == 'PENDING')
                    .dicts()) # <--- On transforme en dictionnaire ici

        for wd in query_web:
            raw_date = wd.get('due_date') # Peewee utilisera le nom du champ ou l'alias
            if isinstance(raw_date, str):
                raw_date = datetime.fromisoformat(raw_date.replace('Z', ''))
            
            target_date = raw_date.date() if hasattr(raw_date, 'date') else raw_date
            
            if target_date <= today:
                overdue_list.append({
                    "id": str(wd.get('id')),
                    "title": f"🌐 {wd.get('title')}",
                    "client_name": f"{wd.get('cfn')} {wd.get('cln')}", 
                    "due_date": raw_date,
                    "accountant_id": str(wd.get('uid')), 
                    "accountant_name": f"{wd.get('ufn')} {wd.get('uln')}",
                    "priority": wd.get('priority'),
                    "source": "Web"
                })

        # --- PARTIE DESKTOP (Ici les FK existent, donc on peut garder l'objet ou passer en dict) ---
        query_local = (Deadline.select(Deadline, Client, Accountant)
                      .join(Client, on=(Deadline.client_id == Client.id))
                      .join(Accountant, on=(Deadline.accountant_id == Accountant.id))
                      .where((Deadline.status == 'PENDING') & (fn.DATE(Deadline.due_date) <= today)))
        
        for d in query_local:
            overdue_list.append({
                "id": str(d.id),
                "title": f"💻 {d.title}",
                "client_name": f"{d.client.first_name} {d.client.last_name}",
                "due_date": d.due_date,
                "accountant_id": str(d.accountant.id),
                "accountant_name": f"{d.accountant.first_name} {d.accountant.last_name}",
                "priority": d.priority,
                "source": "Local"
            })

        return overdue_list
        
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des alertes: {e}")
        return []
    
def add_deadline(data):
    try:
        if db_desktop.is_closed(): db_desktop.connect()
        
        client_id = data.get('client_id')
        # On récupère l'ID du comptable
        acc_id = data.get('accountant_id')
        
        # --- FIX 1: Sécurité Accountant ---
        if not acc_id or acc_id == "None":
            client_obj = Client.get_or_none(Client.id == client_id)
            if client_obj:
                # On récupère le comptable lié au client
                acc_id = client_obj.accountant_id 

        if not acc_id:
            print("❌ Erreur : Impossible de trouver un comptable pour ce client.")
            return None

        # --- Insertion locale ---
        new_deadline_local = Deadline.create(
            id=str(uuid.uuid4()),
            title=data.get('title'),
            due_date=data.get('due_date'),
            priority=data.get('priority', 'MEDIUM'),
            status='PENDING',
            client=client_id,
            accountant=acc_id
        )

        # --- FIX 2: Synchro Web conditionnelle ---
        web_client_id = data.get('web_id')
        # On ne synchronise QUE si le client a un ID Web (UUID type Clerk/Neon)
        if web_client_id and "-" in str(web_client_id) and len(str(web_client_id)) > 20:
            try:
                if db_web.is_closed(): db_web.connect()
                WebDeadline.create(
                    id=str(uuid.uuid4()),
                    title=data.get('title'),
                    description=data.get('description', ''),
                    due_date=data.get('due_date'),
                    priority=data.get('priority', 'MEDIUM'),
                    status='PENDING',
                    type=data.get('type', 'FEDERAL'),
                    client_id=str(web_client_id),
                    user_id=str(acc_id) # Assurez-vous que cet ID existe sur le Web aussi
                )
                print("✅ Synchronisé sur Neon")
            except Exception as e:
                print(f"⚠️ Erreur Web : {e}")
        else:
            print("ℹ️ Synchro Web ignorée : Le client est uniquement local.")

        return new_deadline_local
    except Exception as e:
        print(f"❌ Erreur globale add_deadline : {e}")
        return None
    
def get_client_deadlines(client_id):
    """Récupère les échéances non terminées d'un client"""
    try:
        if db_desktop.is_closed(): db_desktop.connect()
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
    
def get_client_deadlines_combined(local_client_id, web_client_id):
    all_deadlines = []

    if local_client_id and not web_client_id:
        local_c = Client.get_or_none(Client.id == local_client_id)
        if local_c:
            web_client_id = link_client_by_email(local_c)
    
    # 1. LOCAL (SQLite)
    try:
        local_qs = Deadline.select().where(Deadline.client == local_client_id)
        for d in local_qs:
            all_deadlines.append({
                "id": str(d.id),
                "title": d.title,
                "due_date": d.due_date,
                "priority": d.priority,
                "source": "Local"
            })
    except Exception as e:
        print(f"❌ Erreur locale: {e}")


    # 2. WEB (Neon)
    # On force le nettoyage de l'ID
    target_web_id = str(web_client_id).strip() if web_client_id else None
    try:
        if db_web.is_closed(): db_web.connect()
        # Utilisation de .execute() pour contourner d'éventuels problèmes de cache Peewee
        web_qs = WebDeadline.select().where(WebDeadline.client_id == target_web_id)
        web_items = list(web_qs)
        for wd in web_items:
            all_deadlines.append({
                "id": str(wd.id),
                "title": wd.title,
                "due_date": wd.due_date, 
                "priority": wd.priority,
                "source": "Web" 
            })
    except Exception as e:
        print(f"⚠️ Erreur Neon : {e}")

    # 3. Tri
    def sort_key(x):
        d = x.get('due_date')
        if isinstance(d, str):
            try: return datetime.fromisoformat(d.replace('Z', ''))
            except: return datetime.max
        return d if d else datetime.max

    all_deadlines.sort(key=sort_key)
    return all_deadlines

def update_deadline_status_combined(deadline_id, title, due_date, web_id=None, new_status='COMPLETED'):
    """Marque une deadline comme terminée sur les deux sources"""
    success_local = False
    success_web = False
    
    # 1. Update Local
    try:
        if db_desktop.is_closed(): db_desktop.connect()
        q = Deadline.update(status=new_status).where(Deadline.id == deadline_id)
        rows= q.execute()
        if rows > 0:
            success_local = True
            print(f"✅ Local: Deadline {deadline_id} mise à jour.")
    except Exception as e:
        print(f"❌ Erreur update local: {e}")

    # 2. Update Web (basé sur le titre et la date car les IDs diffèrent souvent)
    if web_id:
        try:
            if db_web.is_closed(): db_web.connect()
            clean_title = title.replace("🌐", "").replace("💻", "").strip()

            q_web = WebDeadline.update(status=new_status).where(WebDeadline.id == deadline_id)
            web_rows = q_web.execute()
            if web_rows > 0:
                success_web = True
                print(f"✅ Web: {web_rows} deadline(s) mise(s) à jour sur Neon.")
            elif web_id:
                q_title = WebDeadline.update(status=new_status).where(
                    (WebDeadline.client_id == web_id) & 
                    (WebDeadline.title == clean_title)
                )
                if q_title.execute() > 0:
                    success_web = True
                    print(f"✅ Web: Synchronisation par titre réussie.")
                else:
                    print(f"⚠️ Web: Non trouvé par titre '{clean_title}'")
                    
        except Exception as e:
            print(f"⚠️ Échec mise à jour Web: {e}")
    return success_local or success_web

def delete_deadline_combined(deadline_id, title, web_id=None):
    """Supprime définitivement une deadline des deux sources"""
    success = False
    clean_title = title.replace("🌐", "").replace("💻", "").strip()

    # --- SUPPRESSION LOCAL ---
    try:
        if db_desktop.is_closed(): db_desktop.connect()
        # On tente de supprimer par ID
        q_local = Deadline.delete().where(Deadline.id == deadline_id)
        if q_local.execute() > 0:
            success = True
            print(f"🗑️ Local: Deadline supprimée.")
    except Exception as e:
        print(f"❌ Erreur suppression local: {e}")

    # --- SUPPRESSION WEB (Neon) ---
    try:
        if db_web.is_closed(): db_web.connect()
        
        # Chance 1 : Suppression par ID direct (si c'est une tâche Web)
        q_web_id = WebDeadline.delete().where(WebDeadline.id == deadline_id)
        if q_web_id.execute() > 0:
            success = True
            print(f"🗑️ Web: Deadline supprimée par ID.")
        
        # Chance 2 : Suppression par Titre + Client (si c'est une tâche synchro)
        elif web_id:
            q_web_title = WebDeadline.delete().where(
                (WebDeadline.client_id == web_id) & 
                (WebDeadline.title == clean_title)
            )
            if q_web_title.execute() > 0:
                success = True
                print(f"🗑️ Web: Deadline supprimée par titre.")
    except Exception as e:
        print(f"⚠️ Erreur suppression Web: {e}")

    return success

def link_client_by_email(client_obj):
    """
    Cherche un client sur le Web par son email et enregistre son web_id en local.
    Retourne le web_id trouvé ou None.
    """
    if not client_obj or not client_obj.email:
        return None
        
    try:
        if db_web.is_closed(): db_web.connect()
        
        # On cherche sur Neon Web par email
        web_match = WebClient.get_or_none(fn.LOWER(WebClient.email) == client_obj.email.lower().strip())
        
        if web_match:
            # On met à jour la base Desktop localement
            client_obj.web_id = web_match.id
            client_obj.save()
            print(f"✅ Liaison automatique : {client_obj.email} -> {web_match.id}")
            return web_match.id
            
    except Exception as e:
        print(f"⚠️ Erreur lors de la liaison automatique : {e}")
    
    return None