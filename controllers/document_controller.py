import os
import uuid
from datetime import datetime
from database import Document, WebDocument, Client, db_desktop, db_web

def add_document(data):
    try:
        if db_desktop.is_closed(): db_desktop.connect()
        
        file_path = data.get('file_path')
        client_id = data.get('client')
        
        # 1. On lit le binaire UNE SEULE FOIS au début
        file_binary = None
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                file_binary = f.read()
        
        if not file_binary:
            print(f"❌ Erreur : Impossible de lire {file_path}")
            return None

        acc_id = data.get('accountant_id') or data.get('accountant')
  
        client_obj = Client.get_or_none(Client.id == client_id)
        if not acc_id and client_obj:
            acc_id = getattr(client_obj, 'accountant_id', None)


        doc_fields = {
            "name": data.get('name'),
            "type": os.path.splitext(data.get('name'))[1].lower(),
            "size": os.path.getsize(file_path),
            "file_path": file_path,
            "file_content": file_binary,
            "status": 'PENDING',
            "uploaded_at": datetime.now(),
            "client": client_id,    
            "accountant": acc_id   
        }

        # 3. Insertion Desktop
        new_doc_local = Document.create(**doc_fields)
        print("✅ Document enregistré en local")

        # 4. Synchronisation Web (Si web_id disponible)
        # On essaie de trouver le web_id si non fourni
        web_id = data.get('web_id') or client_id
        
        # On force la vérification : est-ce un UUID valide pour Neon ?
        if web_id and "-" in str(web_id):
            try:
                
                if db_web.is_closed(): db_web.connect()
                
                WebDocument.create(
                    id=str(uuid.uuid4()),
                    name=doc_fields["name"],
                    type=doc_fields["type"],
                    size=doc_fields["size"],
                    file_content=file_binary, 
                    file_path=f"uploads/{doc_fields['name']}",
                    status='PENDING',
                    uploaded_at=datetime.now(),
                    updated_at=datetime.now(),
                    client_id=str(web_id),
                    user_id=str(acc_id)
                )
                print("✅ Document synchronisé sur le Web avec contenu binaire")
            except Exception as e:
                print(f"⚠️ Erreur synchro Web : {e}")
        else:
            print(f"⚠️ Synchro Web annulée : ID '{web_id}' non valide (pas un UUID Neon)")

        return new_doc_local

    except Exception as e:
        print(f"❌ Erreur globale add_document: {e}")
        return None

def get_client_documents(client_id):
    """Récupère tous les docs d'un client spécifique"""
    try:
        if db_desktop.is_closed(): db_desktop.connect()
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

def get_web_document_content(doc_id):
    """Récupère les octets du document directement depuis le BLOB de la DB Web"""
    from database import WebDocument, db_web
    try:
        if db_web.is_closed(): 
            db_web.connect()
        
        # On récupère l'enregistrement
        doc = WebDocument.get_or_none(WebDocument.id == doc_id)
        
        # On vérifie si le champ binaire contient des données
        if doc and doc.file_content:
            # doc.file_content contient déjà les octets (bytes)
            return doc.file_content
            
        print(f"⚠️ Aucun contenu binaire trouvé pour le document {doc_id}")
        return None
    except Exception as e:
        print(f"❌ Erreur lecture BLOB Web : {e}")
        return None
    
def delete_document_combined(doc_id, source):
    """Supprime le document en DB et le fichier physique si local"""
    try:
        if source == 'Desktop':
            doc = Document.get_or_none(Document.id == doc_id)
            if doc:
                # 1. Supprimer le fichier physique
                if os.path.exists(doc.file_path):
                    try:
                        os.remove(doc.file_path)
                    except Exception as e:
                        print(f"⚠️ Erreur suppression fichier disque : {e}")
                
                # 2. Supprimer l'entrée en base SQLite
                return doc.delete_instance() > 0
        else:
            # Suppression Web (Neon)
            if db_web.is_closed(): db_web.connect()
            query = WebDocument.delete().where(WebDocument.id == doc_id)
            return query.execute() > 0
    except Exception as e:
        print(f"❌ Erreur lors de la suppression ({source}): {e}")
        return False
    
def get_client_documents_combined(client_data):
    """
    Récupère les documents des deux sources en évitant les doublons.
    Si un document porte le même nom en local et sur le Web, on privilégie l'affichage local.
    """
    docs_map = {} # Utilise un dictionnaire pour éviter les doublons par nom
    local_id = client_data.get('id')
    web_id = client_data.get('web_id') or local_id

    # --- 1. DOCUMENTS DESKTOP ---
    try:
        if db_desktop.is_closed(): db_desktop.connect()
        # On cherche uniquement si le client a un ID en base locale
        if client_data.get('source') == "Desktop":
            local_docs = list(Document.select().where(Document.client == local_id).dicts())
            for d in local_docs:
                doc_name = d.get('name')
                d['source'] = 'Desktop'
                d['date'] = d.get('uploaded_at')
                docs_map[doc_name] = d # On stocke dans le dictionnaire avec le nom comme clé
    except Exception as e: print(f"❌ Erreur docs Desktop: {e}")

    # --- 2. DOCUMENTS WEB ---
    try:
        if db_web.is_closed(): db_web.connect()
        if web_id:
            search_id = str(web_id).strip()
            
            # On ne demande PAS file_content ici pour ne pas alourdir la liste
            # On le chargera uniquement au clic sur Télécharger
            query = WebDocument.select(
                WebDocument.id, 
                WebDocument.name, 
                WebDocument.size, 
                WebDocument.uploaded_at,
                WebDocument.file_path
            ).where(WebDocument.client_id == search_id).dicts()

            for wd in query:
                doc_name = wd['name']
                if doc_name not in docs_map:
                    docs_map[doc_name] = {
                        'id': wd['id'],
                        'name': doc_name,
                        'size': wd['size'],
                        'date': wd['uploaded_at'],
                        'source': 'Web',
                        'file_path': wd['file_path']
                    }
                else:
                    docs_map[doc_name]['is_synced'] = True
    except Exception as e: 
        print(f"❌ Erreur accès table Web Documents : {e}")
    final_docs = list(docs_map.values())
    final_docs.sort(key=lambda x: x.get('date') or datetime.min, reverse=True)
    return final_docs
