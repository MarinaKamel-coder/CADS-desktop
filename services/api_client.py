import requests

BASE_URL = "https://cads-desktop.vercel.app/api"

def fetch_web_clients():
    try:
        response = requests.get(f"{BASE_URL}/clients")
        response.raise_for_status() # Vérifie si l'appel a réussi
        return response.json()
    except Exception as e:
        print(f"Erreur API : {e}")
        return []

def fetch_web_alerts():
    try:
        response = requests.get(f"{BASE_URL}/alerts")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erreur API : {e}")
        return []