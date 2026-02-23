from database import Accountant, Client, db_desktop
from peewee import fn,JOIN

def get_admin_dashboard_stats():
    """Statistiques rapides pour l'accueil de l'admin"""
    try:
        if db_desktop.is_closed():
            db_desktop.connect()
        return {
            "total_accountants": Accountant.select().count(),
            "total_clients": Client.select().count(),
            "active_accountants": Accountant.select().where(Accountant.status == 'ACTIF').count()
        }
    except:
        return {"total_accountants": 0, "total_clients": 0, "active_accountants": 0}
    
def get_charts_data():
    try:
        if db_desktop.is_closed(): db_desktop.connect()
        
        
        query_pie = (Accountant
                     .select(Accountant.first_name, Accountant.last_name, fn.COUNT(Client.id).alias('count'))
                     .join(Client, JOIN.LEFT_OUTER, on=(Accountant.id == Client.accountant_id))
                     .group_by(Accountant.first_name, Accountant.last_name))
        
        pie_data = {f"{q.first_name} {q.last_name}": q.count for q in query_pie}
        return {"pie": pie_data}
    except Exception as e:
        print(f"❌ Erreur stats graphiques: {e}")
        return {"pie": {}}