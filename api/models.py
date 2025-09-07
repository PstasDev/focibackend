from django.db import models

# Auth

class Profile(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE)
    biro = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

# Játék

class Player(models.Model):
    name = models.CharField(max_length=100)

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

    start_year = models.IntegerField()
    tagozat = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.start_year}{self.tagozat} - {self.tournament.name}"

class Tournament(models.Model):
    name = models.CharField(max_length=200)

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

    def __str__(self):
        return f"{self.team1} vs {self.team2} on {self.datetime}"

class Event(models.Model):
    EVENT_TYPES = [
        ('goal', 'Goal'),
        ('yellow_card', 'Yellow Card'),
        ('red_card', 'Red Card'),
    ]

    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    player = models.ForeignKey('Player', on_delete=models.CASCADE)
    minute = models.IntegerField()

    def __str__(self):
        return f"{self.get_event_type_display()} by {self.player} at {self.minute}'"