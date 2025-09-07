from django.contrib import admin
from .models import Profile, Player, Team, Tournament, Round, Match, Event

# Register your models here.
admin.site.register(Profile)
admin.site.register(Player)
admin.site.register(Team)
admin.site.register(Tournament)
admin.site.register(Round)
admin.site.register(Match)
admin.site.register(Event)
