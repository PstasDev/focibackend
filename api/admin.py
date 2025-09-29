from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Profile, Player, Team, Tournament, Round, Match, Event

# Admin Site Customization
admin.site.site_header = "Foci Liga Adminisztráció"
admin.site.site_title = "Foci Liga Adminisztráció"
admin.site.index_title = "Üdvözöljük a Foci Liga Adminisztrációban"

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'player_link', 'biro', 'get_user_email')
    list_filter = ('biro', 'user__is_active', 'user__is_staff')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    
    def get_user_email(self, obj):
        return obj.user.email
    get_user_email.short_description = 'Email'
    
    def player_link(self, obj):
        if obj.player:
            url = reverse('admin:api_player_change', args=[obj.player.id])
            return format_html('<a href="{}">{}</a>', url, obj.player.name)
        return '-'
    player_link.short_description = 'Player'

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'csk', 'get_teams_count', 'get_goals', 'get_cards')
    list_filter = ('csk',)
    search_fields = ('name',)
    
    def get_teams_count(self, obj):
        return obj.team_set.count()
    get_teams_count.short_description = 'Teams'
    
    def get_goals(self, obj):
        return obj.get_stats()['goals']
    get_goals.short_description = 'Goals'
    
    def get_cards(self, obj):
        stats = obj.get_stats()
        yellow = stats['yellow_cards']
        red = stats['red_cards']
        return format_html(
            '<span style="color: #ffa500;">⚠ {}</span> <span style="color: #ff0000;">🟥 {}</span>',
            yellow, red
        )
    get_cards.short_description = 'Cards (Y/R)'

class PlayerInline(admin.TabularInline):
    model = Team.players.through
    extra = 1
    verbose_name = "Player"
    verbose_name_plural = "Players"

class TeamAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'tournament', 'active', 'get_players_count', 'registration_time')
    list_filter = ('active', 'tournament', 'tagozat', 'start_year')
    search_fields = ('__str__', 'tagozat')
    filter_horizontal = ('players',)
    readonly_fields = ('registration_time',)
    
    def get_display_name(self, obj):
        return str(obj)
    get_display_name.short_description = 'Display Name'
    
    def get_players_count(self, obj):
        return obj.players.count()
    get_players_count.short_description = 'Players'

class RoundInline(admin.TabularInline):
    model = Round
    extra = 1

class TournamentAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'registration_open', 'registration_deadline', 'get_teams_count')
    list_filter = ('registration_open', 'start_date')
    search_fields = ('name',)
    inlines = [RoundInline]
    
    def get_teams_count(self, obj):
        return obj.team_set.count()
    get_teams_count.short_description = 'Teams'

class RoundAdmin(admin.ModelAdmin):
    list_display = ('tournament', 'number', 'get_matches_count')
    list_filter = ('tournament',)
    
    def get_matches_count(self, obj):
        return obj.match_set.count()
    get_matches_count.short_description = 'Matches'

class MatchAdmin(admin.ModelAdmin):
    list_display = ('get_match_title', 'datetime', 'tournament', 'round_obj', 'get_score', 'referee')
    list_filter = ('tournament', 'round_obj', 'datetime')
    search_fields = ('team1__name', 'team2__name', 'tournament__name')
    filter_horizontal = ('events',)
    
    def get_match_title(self, obj):
        return f"{obj.team1} vs {obj.team2}"
    get_match_title.short_description = 'Match'
    
    def get_score(self, obj):
        goals1, goals2 = obj.result()
        return f"{goals1} - {goals2}"
    get_score.short_description = 'Score'

class EventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'player', 'minute', 'extra_time', 'exact_time')
    list_filter = ('event_type', 'exact_time')
    search_fields = ('player__name',)

# Register models with enhanced admin classes
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Round, RoundAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(Event, EventAdmin)
