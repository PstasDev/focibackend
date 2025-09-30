from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Profile, Player, Team, Tournament, Round, Match, Event, Kozlemeny

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

class KozlemenyAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_priority_display', 'active', 'author', 'date_created', 'date_updated')
    list_filter = ('active', 'priority', 'date_created', 'author')
    search_fields = ('title', 'content')
    readonly_fields = ('date_created', 'date_updated')
    ordering = ('-priority', '-date_created')
    
    fieldsets = (
        ('Alapvető információk', {
            'fields': ('title', 'content', 'author')
        }),
        ('Beállítások', {
            'fields': ('active', 'priority')
        }),
        ('Dátumok', {
            'fields': ('date_created', 'date_updated'),
            'classes': ('collapse',)
        }),
    )
    
    def get_priority_display(self, obj):
        priority_colors = {
            'low': '#28a745',      # Green
            'normal': '#6c757d',   # Gray
            'high': '#fd7e14',     # Orange
            'urgent': '#dc3545',   # Red
        }
        color = priority_colors.get(obj.priority, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">● {}</span>',
            color,
            obj.get_priority_display()
        )
    get_priority_display.short_description = 'Prioritás'
    
    def get_queryset(self, request):
        # Order by priority and creation date
        return super().get_queryset(request).order_by('-priority', '-date_created')
    
    actions = ['make_active', 'make_inactive', 'set_priority_high', 'set_priority_urgent']
    
    def make_active(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f'{updated} közlemény aktiválva.')
    make_active.short_description = "Kiválasztott közlemények aktiválása"
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f'{updated} közlemény deaktiválva.')
    make_inactive.short_description = "Kiválasztott közlemények deaktiválása"
    
    def set_priority_high(self, request, queryset):
        updated = queryset.update(priority='high')
        self.message_user(request, f'{updated} közlemény prioritása magasra állítva.')
    set_priority_high.short_description = "Prioritás beállítása: Magas"
    
    def set_priority_urgent(self, request, queryset):
        updated = queryset.update(priority='urgent')
        self.message_user(request, f'{updated} közlemény prioritása sürgősre állítva.')
    set_priority_urgent.short_description = "Prioritás beállítása: Sürgős"

# Register models with enhanced admin classes
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Tournament, TournamentAdmin)
admin.site.register(Round, RoundAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Kozlemeny, KozlemenyAdmin)
