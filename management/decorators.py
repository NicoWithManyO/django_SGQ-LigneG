from django.core.exceptions import PermissionDenied
from django.shortcuts import render


def superuser_required(function=None):
    """
    Décorateur qui vérifie que l'utilisateur est un superuser.
    Retourne une erreur 403 si l'utilisateur n'est pas autorisé.
    """
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated or not request.user.is_superuser:
                # Retourner une page 403 personnalisée
                return render(request, '403.html', {
                    'message': "Accès refusé. Vous devez être administrateur pour accéder à cette section."
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    
    if function:
        return decorator(function)
    return decorator