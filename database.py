from peewee import *
from playhouse.db_url import connect
from datetime import datetime
import uuid

# ============================================================
# On crée le Proxy (boîte vide)
# ============================================================

db = Proxy()

# ============================================================
# MODÈLES 
# ============================================================

class BaseModel(Model):
    class Meta:
        database = db

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
    
    # Un client est rattaché à un comptable spécifique
    accountant = ForeignKeyField(Accountant, backref='clients', on_delete='CASCADE', null=True)

    class Meta:
        table_name = 'clients'

class Document(BaseModel):
    id = CharField(primary_key=True, default=lambda: str(uuid.uuid4()))
    name = CharField()
    type = CharField()
    size = IntegerField()
    file_path = CharField()
    status = CharField(default='PENDING')
    uploaded_at = DateTimeField(default=datetime.now)

    client = ForeignKeyField(Client, backref='documents', on_delete='CASCADE')
    accountant = ForeignKeyField(Accountant, backref='documents', on_delete='CASCADE')

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
# Initialise la connexion Neon et remplit le Proxy
# ============================================================

def init_database():
    """Initialise la connexion Neon et remplit le Proxy"""
    url = 'postgresql://neondb_owner:npg_R9TJApM4YfDg@ep-winter-pine-ah27219u-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require'
    try:
        # 2. On crée la connexion réelle
        real_db = connect(url)
        # 3. On initialise le Proxy avec la vraie connexion
        db.initialize(real_db)
        
        # 4. On connecte et crée les tables
        db.connect(reuse_if_open=True)
        db.create_tables([Admin, Accountant, Client], safe=True)
        print("✅ Base de données CADS initialisée")
        return True
    except Exception as e:
        print(f"❌ Erreur critique DB: {e}")
        return False