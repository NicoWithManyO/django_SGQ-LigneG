from django.contrib import admin
from django.contrib.sessions.models import Session
from django.utils.html import format_html
import json

# Register your models here.

class SessionAdmin(admin.ModelAdmin):
    """Admin pour visualiser les sessions Django."""
    list_display = ['session_key', 'formatted_data', 'expire_date']
    search_fields = ['session_key', 'session_data']
    readonly_fields = ['session_key', 'session_data', 'expire_date', 'get_decoded_data']
    
    def formatted_data(self, obj):
        """Affiche un aperçu des données de session."""
        try:
            data = obj.get_decoded()
            # Afficher uniquement v3_production
            v3_data = data.get('v3_production', {})
            if v3_data:
                preview = {
                    'shift': v3_data.get('shift', {}).get('shiftId', 'N/A'),
                    'roll_number': v3_data.get('sticky_roll_number', 'N/A'),
                    'of': v3_data.get('of', {}).get('ofEnCours', 'N/A')
                }
                return str(preview)
            return 'Pas de données V3'
        except:
            return 'Erreur décodage'
    formatted_data.short_description = 'Aperçu données'
    
    def get_decoded_data(self, obj):
        """Affiche les données de session décodées de manière lisible."""
        try:
            data = obj.get_decoded()
            formatted = json.dumps(data, indent=2, ensure_ascii=False, default=str)
            return format_html('<pre style="white-space: pre-wrap;">{}</pre>', formatted)
        except Exception as e:
            return f"Erreur lors du décodage: {str(e)}"
    get_decoded_data.short_description = 'Données décodées'

# Enregistrer uniquement si Session n'est pas déjà enregistré
if not admin.site.is_registered(Session):
    admin.site.register(Session, SessionAdmin)
