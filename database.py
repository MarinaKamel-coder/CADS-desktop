from peewee import *
from dotenv import load_dotenv
from playhouse.db_url import connect
from datetime import datetime
import uuid
import os;

# Charger les variables du fichier .env
load_dotenv()

# ============================================================
# On crée le Proxy (boîte vide)
# ============================================================

db_desktop = Proxy()
db_web = Proxy()

# ============================================================
# MODÈLES 
# ============================================================

class BaseModel(Model):
    class Meta:
        database = db_desktop

class WebModel(Model):
    class Meta:
        database = db_web        

# ============================================================
# MODÈLES DE L'APPLICATION DESKTOP (CADS-DESKTOP)
# ============================================================

# --- TABLE ADMIN (Utilisée pour Sign Up / Login) ---
class Admin(BaseModel):
    id = CharField(primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = CharField()
    last_name = CharField()
    email = CharField(unique=True)
    password = CharField()  
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'admins'

# --- TABLE COMPTABLE (Gérée par l'Admin) ---
class Accountant(BaseModel):
    id = CharField(primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = CharField()
    last_name = CharField()
    email = CharField(unique=True)
    phone = CharField(null=True)
    role = CharField(default='COMPTABLE') # Junior, Senior, etc.
    status = CharField(default='ACTIF')    # Actif, Inactif
    date_joined = DateTimeField(default=datetime.now)
    date_left = DateTimeField(null=True)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'accountants'

# --- TABLE CLIENT (Liée au Comptable) ---
class Client(BaseModel):
    id = CharField(primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = CharField()
    last_name = CharField()
    email = CharField()
    phone = CharField()
    nas_number = CharField(index=True)
    address = TextField()
    status = CharField(default='ACTIVE')
    created_at = DateTimeField(default=datetime.now)
    date_left = DateField(null=True)
    
    web_id = CharField(null=True, column_name='web_id')
    
    # Un client est rattaché à un comptable spécifique
    accountant_id = CharField(null=True)

    class Meta:
        table_name = 'clients'

class Document(BaseModel):
    id = CharField(primary_key=True, default=lambda: str(uuid.uuid4()))
    name = CharField()
    type = CharField()
    size = IntegerField()
    file_path = CharField()
    file_content = BlobField(null=True, column_name='fileContent')
    status = CharField(default='PENDING')
    uploaded_at = DateTimeField(default=datetime.now)
    accountant = CharField(max_length=255, null=True, column_name='accountant_id')

    client = ForeignKeyField(Client, backref='documents', on_delete='CASCADE', column_name='client_id')
    

    class Meta:
        table_name = 'documents'

class Deadline(BaseModel):
    id = CharField(primary_key=True, default=lambda: str(uuid.uuid4()))
    title = CharField()
    due_date = DateTimeField()
    priority = CharField(default='MEDIUM')
    status = CharField(default='PENDING')

    client = ForeignKeyField(Client, backref='deadlines', on_delete='CASCADE')
    accountant = ForeignKeyField(Accountant, backref='deadlines', on_delete='CASCADE')

    class Meta:
        table_name = 'deadlines'

class Alert(BaseModel):
    id = UUIDField(primary_key=True)
    type = CharField() 
    title = CharField()
    message = TextField()
    priority = CharField(default='MEDIUM')
    read = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.now)
    
    accountant = ForeignKeyField(Accountant, backref='alerts', on_delete='CASCADE')

    class Meta:
        table_name = 'alerts'

# ============================================================
# MODÈLES DE L'APPLICATION WEB (CADS // Prisma)
# ============================================================

class WebUser(WebModel):
    id = CharField(primary_key=True)
    email = CharField(unique=True)
    first_name = CharField(column_name='firstName') 
    last_name = CharField(column_name='lastName')
    role = CharField()
    company = CharField(null=True)
    created_at = DateTimeField(column_name='createdAt', default=datetime.now)
    updated_at = DateTimeField(column_name='updatedAt', default=datetime.now)
    
    class Meta:
        table_name = 'users'

class WebClient(WebModel):
    id = CharField(primary_key=True)
    first_name = CharField(column_name='firstName')
    last_name = CharField(column_name='lastName')
    email = CharField()
    phone = CharField()
    nas_number = CharField(column_name='nasNumber')
    address = CharField()
    status = CharField(default='ACTIVE')
    user_id = CharField(column_name='userId') 
    created_at = DateTimeField(column_name='createdAt', default=datetime.now)
    updated_at = DateTimeField(column_name='updatedAt', default=datetime.now)

    class Meta:
        table_name = 'clients'

class WebDocument(WebModel):
    id = CharField(primary_key=True)
    name = CharField()
    type = CharField()
    size = IntegerField()
    file_path = CharField(column_name='filePath') 
    status = CharField(default='PENDING')
    uploaded_at = DateTimeField(column_name='uploadedAt', default=datetime.now) 
    updated_at = DateTimeField(column_name='updatedAt', default=datetime.now)
    client_id = CharField(column_name='clientId') 
    user_id = CharField(column_name='userId')     
    file_content = BlobField(column_name='fileContent', null=True) 

    class Meta:
        table_name = 'documents'

class WebDeadline(WebModel):
    id = CharField(primary_key=True)
    title = CharField()
    description = TextField()
    due_date = DateTimeField(column_name='dueDate') 
    priority = CharField(default='MEDIUM')
    status = CharField(default='PENDING')
    type = CharField()
    created_at = DateTimeField(column_name='createdAt', default=datetime.now)
    updated_at = DateTimeField(column_name='updatedAt', default=datetime.now)
  
    client_id = CharField(column_name='clientId')
    user_id = CharField(column_name='userId')

    class Meta:
        table_name = 'deadlines'

# ============================================================
# Initialise la connexion Neon et remplit le Proxy
# ============================================================

def init_databases():
    """Initialise les connexions et remplit les Proxies"""
    url1 = os.getenv("url1")   # Desktop
    url2 = os.getenv("url2")  # Web
    
    if not url1:
        print("❌ Erreur : URL Desktop manquante dans le fichier .env")
        return False

    try:
        # --- INITIALISATION DESKTOP ---
        # On transforme l'URL pour la compatibilité Peewee/Postgres
        formatted_url1 = url1.replace("postgres://", "postgresql://", 1)
        d_db = connect(formatted_url1)
        
        # REMPLISSAGE DU PROXY (Crucial pour éviter l'erreur)
        db_desktop.initialize(d_db)
        db_desktop.connect(reuse_if_open=True)
        
        # Création des tables locales
        db_desktop.create_tables([Admin, Accountant, Client, Document, Deadline, Alert], safe=True)
        print("✅ DB Desktop : Connectée et Tables initialisées")

        # --- INITIALISATION WEB ---
        if url2:
            formatted_url2 = url2.replace("postgres://", "postgresql://", 1)
            w_db = connect(formatted_url2)
            db_web.initialize(w_db)
            db_web.connect(reuse_if_open=True)
            print("✅ DB Web : Connectée")
        else:
            print("⚠️ DB Web : URL2 manquante, synchronisation indisponible")
            
        return True
    except Exception as e:
        print(f"❌ Erreur critique Double Connexion : {e}")
        return False