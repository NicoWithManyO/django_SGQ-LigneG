"""
API DRF unifiée pour la gestion de session de production
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from django.core.serializers.json import DjangoJSONEncoder
from .models import CurrentSession
from .serializers import CurrentSessionSerializer


class DecimalJSONRenderer(JSONRenderer):
    encoder_class = DjangoJSONEncoder


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([AllowAny])  # TODO: Mettre IsAuthenticated en production
def current_session(request):
    """
    API unifiée pour toute la session de production
    
    GET: Récupère l'état complet de la session
    PATCH: Met à jour n'importe quelle partie de la session
    DELETE: Réinitialise la session (après sauvegarde d'un poste)
    """
    
    # S'assurer qu'on a une session
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    
    if request.method == 'GET':
        # Récupérer ou créer le draft de session
        draft, created = CurrentSession.objects.get_or_create(
            session_key=session_key,
            defaults={'session_data': {}}
        )
        
        # Utiliser le serializer pour formater la réponse
        serializer = CurrentSessionSerializer(
            instance={'draft': draft},
            context={'request': request}
        )
        
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        # Récupérer ou créer les objets
        draft, _ = CurrentSession.objects.get_or_create(
            session_key=session_key,
            defaults={'session_data': {}}
        )
        
        # Passer au serializer pour validation et sauvegarde
        serializer = CurrentSessionSerializer(
            instance={'draft': draft},
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(
                {
                    'errors': serializer.errors,
                    'data': serializer.data
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    elif request.method == 'DELETE':
        # Réinitialiser seulement le draft (pas l'état persistant)
        CurrentSession.objects.filter(session_key=session_key).delete()
        
        return Response({'message': 'Session réinitialisée'})