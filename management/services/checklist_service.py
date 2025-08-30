from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Count

from wcm.models import ChecklistResponse
from production.models import Shift
from catalog.models import WcmChecklistItem


class ChecklistService:
    """Service pour la gestion et validation des checklists."""
    
    @staticmethod
    @transaction.atomic
    def add_management_visa(checklist_id, visa, user=None):
        """
        Ajoute le visa management à une checklist.
        
        Args:
            checklist_id: ID de la checklist
            visa: Initiales du manager (min 2 caractères)
            user: Utilisateur Django (optionnel)
            
        Returns:
            ChecklistResponse: La checklist mise à jour
            
        Raises:
            ValueError: Si le visa est invalide
        """
        if not visa or len(visa) < 2:
            raise ValueError("Le visa doit contenir au moins 2 caractères")
        
        checklist = ChecklistResponse.objects.select_related(
            'shift__operator'
        ).get(pk=checklist_id)
        
        # Vérifier que la checklist n'est pas déjà visée
        if checklist.management_visa:
            raise ValueError("Cette checklist a déjà été visée")
        
        # Mettre à jour le visa
        checklist.management_visa = visa.upper()
        checklist.management_visa_date = timezone.now()
        checklist.save(update_fields=['management_visa', 'management_visa_date'])
        
        return checklist
    
    @staticmethod
    def get_pending_checklists():
        """
        Récupère toutes les checklists en attente de visa management.
        
        Returns:
            QuerySet: Checklists sans visa management
        """
        return ChecklistResponse.objects.filter(
            Q(management_visa='') | Q(management_visa__isnull=True)
        ).select_related(
            'shift',
            'shift__operator',
            'operator'
        ).order_by('-created_at')
    
    @staticmethod
    def get_all_checklists(days=7):
        """
        Récupère toutes les checklists (visées ou non) des N derniers jours.
        
        Args:
            days: Nombre de jours à regarder (par défaut 7)
            
        Returns:
            QuerySet: Toutes les checklists triées par date
        """
        since_date = timezone.now() - timezone.timedelta(days=days)
        return ChecklistResponse.objects.filter(
            created_at__gte=since_date
        ).select_related(
            'shift',
            'shift__operator',
            'operator'
        ).order_by('-created_at')
    
    @staticmethod
    def get_checklist_details(checklist_id):
        """
        Récupère les détails complets d'une checklist.
        
        Args:
            checklist_id: ID de la checklist
            
        Returns:
            dict: Détails de la checklist avec items et réponses
        """
        checklist = ChecklistResponse.objects.select_related(
            'shift',
            'shift__operator',
            'operator'
        ).get(pk=checklist_id)
        
        # Récupérer uniquement les items qui ont des réponses dans cette checklist
        # La nouvelle structure a les réponses dans les clés numériques
        # et les métadonnées dans _items, _items_order, _comments
        item_ids_with_responses = []
        for item_id in checklist.responses.keys():
            if item_id.startswith('_'):
                continue  # Ignorer les clés metadata
            try:
                item_ids_with_responses.append(int(item_id))
            except ValueError:
                continue
        
        # Récupérer les items correspondants
        items_with_responses = WcmChecklistItem.objects.filter(
            id__in=item_ids_with_responses
        ).order_by('category', 'text')
        
        # Créer un dictionnaire pour accès rapide
        items_dict = {item.id: item for item in items_with_responses}
        
        # Organiser les réponses par catégorie
        items_by_category = {}
        
        # Récupérer les commentaires s'ils existent
        comments = checklist.responses.get('_comments', {})
        
        # Parcourir les réponses de la checklist
        for item_id_str, response in checklist.responses.items():
            # Ignorer les clés metadata
            if item_id_str.startswith('_'):
                continue
                
            try:
                item_id = int(item_id_str)
            except ValueError:
                continue
            
            # Récupérer l'item correspondant
            item = items_dict.get(item_id)
            if not item:
                # Si l'item n'existe plus dans la base, utiliser le texte stocké dans _items
                items_data = checklist.responses.get('_items', {})
                item_text = items_data.get(item_id_str, f"Item #{item_id}")
                # Créer un objet factice pour cet item
                class FakeItem:
                    def __init__(self, id, text):
                        self.id = id
                        self.text = text
                        self.category = "Autres"  # Catégorie par défaut
                item = FakeItem(item_id, item_text)
            
            # Ajouter la catégorie si elle n'existe pas
            if item.category not in items_by_category:
                items_by_category[item.category] = []
            
            # Récupérer le commentaire s'il existe
            comment = comments.get(item_id_str, '')
            
            items_by_category[item.category].append({
                'id': item.id,
                'label': item.text,
                'is_mandatory': False,  # Ce champ n'existe plus dans le modèle
                'response': response,
                'comment': comment,
                'is_ok': response == 'ok',
                'is_nok': response == 'nok',
                'is_na': response == 'na'
            })
        
        # Trier les items dans chaque catégorie par texte
        for category in items_by_category:
            items_by_category[category].sort(key=lambda x: x['label'])
        
        # Calculer les statistiques basées sur les réponses réelles
        total_items = len(checklist.responses)
        ok_count = sum(1 for r in checklist.responses.values() if r == 'ok')
        nok_count = sum(1 for r in checklist.responses.values() if r == 'nok')
        na_count = sum(1 for r in checklist.responses.values() if r == 'na')
        
        return {
            'checklist': checklist,
            'items_by_category': items_by_category,
            'statistics': {
                'total_items': total_items,
                'ok_count': ok_count,
                'nok_count': nok_count,
                'na_count': na_count,
                'completion_rate': 100.0  # Toujours 100% car on n'affiche que les items remplis
            }
        }
    
    @staticmethod
    def get_checklist_statistics(days=30):
        """
        Statistiques sur les checklists pour les N derniers jours.
        
        Args:
            days: Nombre de jours à analyser
            
        Returns:
            dict: Statistiques des checklists
        """
        since_date = timezone.now() - timezone.timedelta(days=days)
        
        checklists = ChecklistResponse.objects.filter(
            created_at__gte=since_date
        )
        
        total = checklists.count()
        signed = checklists.exclude(
            Q(management_visa='') | Q(management_visa__isnull=True)
        ).count()
        
        # Temps moyen de signature (en heures)
        signed_checklists = checklists.exclude(
            Q(management_visa='') | Q(management_visa__isnull=True)
        ).filter(
            management_visa_date__isnull=False
        )
        
        avg_signature_time = None
        if signed_checklists.exists():
            total_time = 0
            count = 0
            
            for checklist in signed_checklists:
                if checklist.management_visa_date and checklist.created_at:
                    time_diff = (checklist.management_visa_date - checklist.created_at).total_seconds() / 3600
                    total_time += time_diff
                    count += 1
            
            if count > 0:
                avg_signature_time = round(total_time / count, 1)
        
        # Analyse des non-conformités
        nok_analysis = ChecklistService._analyze_non_conformities(checklists)
        
        return {
            'total_checklists': total,
            'signed_checklists': signed,
            'pending_checklists': total - signed,
            'signature_rate': round((signed / total * 100) if total > 0 else 0, 1),
            'avg_signature_time_hours': avg_signature_time,
            'non_conformities': nok_analysis
        }
    
    @staticmethod
    def _analyze_non_conformities(checklists):
        """
        Analyse les non-conformités dans les checklists.
        
        Args:
            checklists: QuerySet de checklists
            
        Returns:
            dict: Analyse des non-conformités
        """
        # Récupérer tous les items
        all_items = {
            str(item.id): item 
            for item in WcmChecklistItem.objects.filter(is_active=True)
        }
        
        # Compter les NOK par item
        nok_counts = {}
        total_nok = 0
        
        for checklist in checklists:
            for item_id, response in checklist.responses.items():
                if response == 'nok':
                    total_nok += 1
                    if item_id not in nok_counts:
                        nok_counts[item_id] = {
                            'count': 0,
                            'label': all_items.get(item_id).text if item_id in all_items else 'Item inconnu',
                            'category': all_items.get(item_id).category if item_id in all_items else 'Inconnu'
                        }
                    nok_counts[item_id]['count'] += 1
        
        # Trier par nombre de NOK décroissant
        top_nok_items = sorted(
            nok_counts.values(),
            key=lambda x: x['count'],
            reverse=True
        )[:10]
        
        return {
            'total_nok': total_nok,
            'checklists_with_nok': sum(
                1 for c in checklists 
                if any(r == 'nok' for r in c.responses.values())
            ),
            'top_nok_items': top_nok_items
        }
    
    @staticmethod
    def validate_checklist_completion(shift):
        """
        Valide qu'une checklist est complète pour un shift.
        
        Args:
            shift: Instance de Shift
            
        Returns:
            tuple: (is_complete, missing_items)
        """
        if not hasattr(shift, 'checklist_response'):
            return False, ["Aucune checklist n'a été remplie"]
        
        checklist = shift.checklist_response
        mandatory_items = WcmChecklistItem.objects.filter(
            is_active=True,
            is_mandatory=True
        )
        
        missing_items = []
        for item in mandatory_items:
            if str(item.id) not in checklist.responses:
                missing_items.append(item.text)
        
        is_complete = len(missing_items) == 0
        return is_complete, missing_items