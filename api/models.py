from django.db import models

# Auth

class Profile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    biro = models.BooleanField(default=False)

    player = models.ForeignKey('Player', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.user.username

# Játék

class Player(models.Model):
    name = models.CharField(max_length=100)
    csk = models.BooleanField(default=False) # Csapatkapitány
    
    # Optional player-specific data, falls back to team data if empty
    start_year = models.IntegerField(null=True, blank=True)
    tagozat = models.CharField(max_length=100, blank=True, null=True)

    def get_start_year(self):
        """
        Returns player's start year if set, otherwise returns team's start year.
        """
        if self.start_year:
            return self.start_year
        
        # Get the first team this player belongs to
        team = self.team_set.first()
        return team.start_year if team else None

    def get_tagozat(self):
        """
        Returns player's tagozat if set, otherwise returns team's tagozat.
        """
        if self.tagozat:
            return self.tagozat
        
        # Get the first team this player belongs to
        team = self.team_set.first()
        return team.tagozat if team else None

    def get_stats(self):
        matches = Match.objects.filter(models.Q(team1__players=self) | models.Q(team2__players=self))
        return {
            'matches_played': matches.count(),
            'goals': Event.objects.filter(event_type='goal', player=self).count(),
            'yellow_cards': Event.objects.filter(event_type='yellow_card', player=self).count(),
            'red_cards': Event.objects.filter(event_type='red_card', player=self).count(),
        }

    def __str__(self):
        return self.name

class Team(models.Model):
    tournament = models.ForeignKey('Tournament', on_delete=models.CASCADE)
    players = models.ManyToManyField('Player')

    name = models.CharField(max_length=200, blank=True, null=True)
    start_year = models.IntegerField()
    tagozat = models.CharField(max_length=100)
    color = models.CharField(max_length=7, blank=True, null=True, help_text="Custom team color in hex format (e.g., #FF5733)")

    registration_time = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    active = models.BooleanField(default=True)

    def get_team_color(self):
        """
        Returns custom team color if set, otherwise returns default color based on tagozat.
        """
        if self.color:
            return self.color
        
        # Extract the class letter from tagozat (assuming first character)
        class_letter = self.tagozat[0].upper() if self.tagozat else ''
        
        color_map = {
            'A': '#66bb6a',  # Brighter green for better contrast
            'B': '#ffca28',  # Brighter yellow for better contrast
            'C': '#ba68c8',  # Brighter purple for better contrast
            'D': '#ef5350',  # Brighter red for better contrast
            'E': '#bdbdbd',  # Lighter gray for better contrast
            'F': '#5c6bc0',  # Brighter navy blue for better contrast
        }
        
        return color_map.get(class_letter, '#42a5f5')  # Brighter default blue

    def __str__(self):
        if self.name:
            return self.name
        return f"{self.start_year}{self.tagozat}"

class Tournament(models.Model):
    name = models.CharField(max_length=200)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    registration_open = models.BooleanField(default=False)
    registration_deadline = models.DateTimeField(null=True, blank=True)

    registration_by_link = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name

class Round(models.Model):
    tournament = models.ForeignKey('Tournament', on_delete=models.CASCADE)
    number = models.IntegerField()

    def __str__(self):
        return f"{self.tournament.name} - Round {self.number}"
    
class Match(models.Model):
    tournament = models.ForeignKey('Tournament', on_delete=models.CASCADE)
    team1 = models.ForeignKey('Team', related_name='team1_matches', on_delete=models.CASCADE)
    team2 = models.ForeignKey('Team', related_name='team2_matches', on_delete=models.CASCADE)
    datetime = models.DateTimeField()

    round_obj = models.ForeignKey('Round', on_delete=models.CASCADE)

    events = models.ManyToManyField('Event', blank=True)

    referee = models.ForeignKey('Profile', null=True, blank=True, on_delete=models.SET_NULL)


    def result(self):
        goals_team1 = self.events.filter(event_type='goal', player__in=self.team1.players.all()).count()
        goals_team2 = self.events.filter(event_type='goal', player__in=self.team2.players.all()).count()
        return (goals_team1, goals_team2)

    def team_goals(self, team):
        if team == self.team1:
            return self.events.filter(event_type='goal', player__in=self.team1.players.all()).count()
        elif team == self.team2:
            return self.events.filter(event_type='goal', player__in=self.team2.players.all()).count()
        else:
            return 0

    def __str__(self):
        return f"{self.team1} vs {self.team2} on {self.datetime}"

class Event(models.Model):
    EVENT_TYPES = [
        ('match_start', 'Match Start'),
        ('goal', 'Goal'),
        ('yellow_card', 'Yellow Card'),
        ('red_card', 'Red Card'),
        ('half_time', 'Half Time'),
        ('full_time', 'Full Time'),
        ('extra_time', 'Extra Time'),
        ('match_end', 'Match End'),
    ]

    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    half = models.IntegerField(choices=[(1, '1st Half'), (2, '2nd Half')], null=True, blank=True)
    minute = models.IntegerField()
    minute_extra_time = models.IntegerField(null=True, blank=True)

    exact_time = models.DateTimeField(null=True, blank=True)

    # Depending on event_type, player may be null (e.g., match_start)
    player = models.ForeignKey('Player', on_delete=models.CASCADE, null=True, blank=True)
    extra_time = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_event_type_display()} by {self.player} at {self.minute}'"

# Közlemények

class Kozlemeny(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Alacsony'),
        ('normal', 'Normál'),
        ('high', 'Magas'),
        ('urgent', 'Sürgős'),
    ]

    title = models.CharField(max_length=200, verbose_name="Cím")
    content = models.TextField(verbose_name="Tartalom")
    date_created = models.DateTimeField(auto_now_add=True, verbose_name="Létrehozás ideje")
    date_updated = models.DateTimeField(auto_now=True, verbose_name="Módosítás ideje")
    active = models.BooleanField(default=True, verbose_name="Aktív")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal', verbose_name="Prioritás")
    author = models.ForeignKey('Profile', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Szerző")

    class Meta:
        verbose_name = "Közlemény"
        verbose_name_plural = "Közlemények"
        ordering = ['-priority', '-date_created']

    def __str__(self):
        return self.title