from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.urls import path
from .models import Tournament, Team, Player, Match, Event

class FociAdminSite(AdminSite):
    site_header = "Foci Liga Admin"
    site_title = "Foci Liga Admin Portal"
    index_title = "Welcome to Foci Liga Administration"
    
    def index(self, request, extra_context=None):
        """
        Display the main admin index page with custom statistics.
        """
        extra_context = extra_context or {}
        
        # Add statistics to the context
        extra_context.update({
            'tournaments_count': Tournament.objects.count(),
            'teams_count': Team.objects.count(),
            'players_count': Player.objects.count(),
            'matches_count': Match.objects.count(),
            'events_count': Event.objects.count(),
            'active_tournaments': Tournament.objects.filter(registration_open=True).count(),
            'recent_matches': Match.objects.order_by('-datetime')[:5],
        })
        
        return super().index(request, extra_context)

# Create an instance of the custom admin site
admin_site = FociAdminSite(name='foci_admin')