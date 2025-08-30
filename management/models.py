from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Profil utilisateur pour stocker des informations supplémentaires."""
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    default_visa = models.CharField(
        "Visa par défaut",
        max_length=10,
        blank=True,
        help_text="Visa utilisé par défaut pour signer les checklists (ex: JD, MP, etc.)"
    )
    
    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"
    
    def __str__(self):
        return f"Profil de {self.user.username}"
