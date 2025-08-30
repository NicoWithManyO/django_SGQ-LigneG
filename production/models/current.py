from django.db import models


class CurrentProfile(models.Model):
    """Profil actuellement sélectionné dans la production."""
    
    profile = models.ForeignKey(
        'catalog.ProfileTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Profil actuel"
    )
    
    selected_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Sélectionné le"
    )
    
    class Meta:
        verbose_name = "Profil actuel"
        verbose_name_plural = "Profils actuels"
    
    def __str__(self):
        return f"Profil actuel: {self.profile.name if self.profile else 'Aucun'}"