from django.contrib import admin
from django.contrib.sessions.models import Session
import json
from django.utils.html import format_html

class SessionAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'expire_date', 'get_decoded']
    readonly_fields = ['session_data', 'formatted_data']
    search_fields = ['session_key']
    
    def get_decoded(self, obj):
        return obj.get_decoded()
    get_decoded.short_description = 'Données décodées'
    
    def formatted_data(self, obj):
        """Affiche les données de session formatées en HTML."""
        try:
            data = obj.get_decoded()
            if not data:
                return "Session vide"
            
            # Formater en JSON indenté
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            
            # Retourner dans un bloc <pre> pour conserver le formatage
            return format_html('<pre style="background: #f5f5f5; padding: 10px; border-radius: 4px;">{}</pre>', json_str)
        except Exception as e:
            return f"Erreur: {str(e)}"
    
    formatted_data.short_description = "Données formatées"

admin.site.register(Session, SessionAdmin)