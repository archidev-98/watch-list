from django.db import models

# Create your models here.
class Task(models.Model):
	title = models.CharField(max_length=200)
	complete = models.BooleanField(default=False)
	created = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.title
	
# Nouveau modèle pour la watchlist TMDB
class WatchlistItem(models.Model):
    tmdb_id = models.IntegerField()
    title = models.CharField(max_length=255)
    provider = models.CharField(max_length=50)
    poster_path = models.CharField(max_length=255, null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tmdb_id', 'provider')  # empêche les doublons par provider

    def __str__(self):
        return f"{self.title} ({self.provider})"