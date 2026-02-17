from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import *
from .forms import *
import requests

# Create your views here.
def index(request):
	watchlist_items = WatchlistItem.objects.all()

	return render(request, "tasks/list.html", {
        "watchlist_items": watchlist_items,  # c'est cette variable qui sera accessible dans le template
    })

def updateTask(request,pk):
	task = Task.objects.get(id=pk)
	form = TaskForm(instance=task)

	if request.method == "POST":
		form = TaskForm(request.POST,instance=task)
		if form.is_valid():
			form.save()
			return redirect('/')


	context = {'form':form}
	return render(request, 'tasks/update_task.html',context)

def deleteTask(request,pk):
	item = Task.objects.get(id=pk)

	if request.method == "POST":
		item.delete()
		return redirect('/')

	context = {'item':item}
	return render(request, 'tasks/delete.html', context)


TMDB_BEARER_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjMzk5N2VlYmRmMGVlOGJiYjkyYjQwMzQ5MjA5OGI3YyIsIm5iZiI6MTc3MTMxOTU3NC44OTIsInN1YiI6IjY5OTQzMTE2MDJlN2Y1NTZiYTI4ODI1ZiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.jdCF0UlFOgfM3jWpYbAVGtgZC1jl5h2mesFo_zpy_g4"
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Mapping des providers
PROVIDER_IDS = {
    "netflix": 8,
    "amazon": 9,
    "apple": 2
}

def add_series_to_watchlist(request, provider):
    headers = {
        "Authorization": f"Bearer {TMDB_BEARER_TOKEN}",
        "Content-Type": "application/json;charset=utf-8"
    }

    # Récupérer les IDs déjà présents pour ce provider
    existing_ids = list(WatchlistItem.objects.values_list('tmdb_id', flat=True))

    page = 1
    new_series_added = 0

    while new_series_added < 10:
        params = {
            "with_watch_providers": PROVIDER_IDS[provider],
            "watch_region": "US",
            "sort_by": "vote_average.desc",
            "vote_count.gte": 50,
            "language": "en-US",
            "page": page
        }

        response = requests.get(f"{TMDB_BASE_URL}/discover/tv", headers=headers, params=params)
        data = response.json()
        results = data.get("results", [])

        if not results:
            break  # Plus de résultats disponibles

        for series in results:
            if series["id"] not in existing_ids and new_series_added < 10:
                WatchlistItem.objects.create(
                    tmdb_id=series["id"],
                    title=series["name"],
                    provider=provider.capitalize(),
					poster_path=series.get("poster_path")
                )
                existing_ids = list(existing_ids) + [series["id"]]  # mettre à jour pour le prochain
                new_series_added += 1

        page += 1  # passer à la page suivante si nécessaire

    return redirect("/")
