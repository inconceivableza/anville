from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def hub(request):
    return render(request, "engine/hub.html")
