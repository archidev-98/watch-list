from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
from .models import *
from .forms import *
import requests
import secrets
import uuid
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

# Create your views here.
@login_required
def index(request):
	watchlist_items = WatchlistItem.objects.filter(user=request.user)

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

def deleteTask(request, pk):
    item = get_object_or_404(Task, id=pk)

    if request.method == "POST":
        item.delete()
        return redirect("/")

    context = {"item": item}
    return render(request, "tasks/delete.html", context)

TMDB_BEARER_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJlZTQxMGZjMGIwZDgyMDVlZDMwZjk4ZmZiNWI4Yzg0OCIsIm5iZiI6MTc3MTMyMTY2Mi40NDUsInN1YiI6IjY5OTQzOTNlOGU1MTVlNmNkNDI4ODQwNSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.FK8vPIIDhfFS4Bp9zFaBWLjrsPBXNA8ykTq11F4Zbog"
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
					poster_path=series.get("poster_path"),
                    user=request.user
                )
                existing_ids = list(existing_ids) + [series["id"]]  # mettre à jour pour le prochain
                new_series_added += 1

        page += 1  # passer à la page suivante si nécessaire

    return redirect("/")


# Page d'inscription
def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # connexion automatique après inscription
            return redirect('list')
    else:
        form = UserCreationForm()
    return render(request, 'tasks/signup.html', {'form': form})

# Page de login
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('list')
    else:
        form = AuthenticationForm()
    return render(request, 'tasks/login.html', {'form': form})

# Déconnexion
def logout_view(request):
    logout(request)
    return redirect('login')

from urllib.parse import urlencode
# Rediriger vers France Connect
def fc_login_redirect(request):
    request.session.modified = True
    
    fc_authorize_url = "https://fcp.integ01.dev-franceconnect.fr/api/v1/authorize"
    client_id = "211286433e39cce01db448d80181bdfd005554b19cd51b3fe7943f6b3b86ab6e"
    redirect_uri = "http://localhost:8080/callback"
    eidas = "eidas1"
    nonce = secrets.token_urlsafe(16)
    state = uuid.uuid4().hex

    request.session['fc_nonce'] = nonce
    request.session["fc_state"] = state

    params = {
		"response_type": "code",
		"client_id": client_id,
		"redirect_uri": redirect_uri,
		"scope": "openid profile email",
		"state": state,
		"nonce": nonce,
		"acr_values": eidas,
	}
    url = f"{fc_authorize_url}?{urlencode(params)}"
    return redirect(url)


# Callback après auth
def fc_callback(request):
    code = request.GET.get("code")
    state = request.GET.get("state")

    if not code or not state:
        return HttpResponseBadRequest("Missing code or state")

    token_url = "https://fcp.integ01.dev-franceconnect.fr/api/v1/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://localhost:8080/callback",
        "client_id": "211286433e39cce01db448d80181bdfd005554b19cd51b3fe7943f6b3b86ab6e",
        "client_secret": "2791a731e6a59f56b6b4dd0d08c9b1f593b5f3658b9fd731cb24248e2669af4b",
    }
    response = requests.post(token_url, data=data)
    token_data = response.json()
    access_token = token_data.get("access_token")
    
    userinfo_url = "https://fcp.integ01.dev-franceconnect.fr/api/v1/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    userinfo = requests.get(userinfo_url, headers=headers).json()

    email = userinfo.get("email") or f"{userinfo['sub']}@franceconnect.local"

    user, created = User.objects.get_or_create(
        username=email,
        defaults={
            "email": email,
            "first_name": userinfo.get("given_name", ""),
            "last_name": userinfo.get("family_name", ""),
        }
    )

    login(request, user)
    return redirect("list") 