from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
import json

# Lister toutes les sessions
sessions = Session.objects.all()
print(f"Nombre de sessions: {len(sessions)}")

for session in sessions[:5]:  # Afficher les 5 premières
    store = SessionStore(session_key=session.session_key)
    data = store.load()
    
    print(f"\nSession {session.session_key}:")
    print(f"  Expire: {session.expire_date}")
    
    if 'v3_production' in data:
        print("  v3_production data:")
        v3_data = data['v3_production']
        for key, value in v3_data.items():
            print(f"    {key}: {value}")
    else:
        print("  Pas de données v3_production")