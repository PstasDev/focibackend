from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import Profile, Player, Team, Tournament, Round, Match, Event
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Create sample data for testing the admin interface'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')
        
        # Create sample tournament
        tournament, created = Tournament.objects.get_or_create(
            name="SZLG Liga 2024/25",
            defaults={
                'start_date': datetime.now().date(),
                'end_date': (datetime.now() + timedelta(days=180)).date(),
                'registration_open': True,
                'registration_deadline': datetime.now() + timedelta(days=30)
            }
        )
        
        # Create sample players
        player_names = [
            "Kovács János", "Nagy Péter", "Szabó László", "Kiss Gábor", "Varga Zoltán",
            "Horváth Márk", "Balogh Dávid", "Molnár Tamás", "Simon András", "Takács Bence"
        ]
        
        players = []
        for name in player_names:
            player, created = Player.objects.get_or_create(
                name=name,
                defaults={'csk': random.choice([True, False])}
            )
            players.append(player)
        
        # Create sample teams
        team_configs = [
            {'start_year': 2023, 'tagozat': 'Informatika'},
            {'start_year': 2022, 'tagozat': 'Gépészet'},
            {'start_year': 2024, 'tagozat': 'Villamosmérnök'},
            {'start_year': 2023, 'tagozat': 'Építészet'}
        ]
        
        teams = []
        for config in team_configs:
            team, created = Team.objects.get_or_create(
                tournament=tournament,
                start_year=config['start_year'],
                tagozat=config['tagozat'],
                defaults={'active': True}
            )
            
            # Add random players to team
            team_players = random.sample(players, random.randint(3, 6))
            team.players.set(team_players)
            teams.append(team)
        
        # Create rounds
        round1, created = Round.objects.get_or_create(
            tournament=tournament,
            number=1
        )
        
        # Create sample matches
        if len(teams) >= 2:
            match, created = Match.objects.get_or_create(
                tournament=tournament,
                team1=teams[0],
                team2=teams[1],
                defaults={
                    'datetime': datetime.now() + timedelta(days=1),
                    'round_obj': round1
                }
            )
            
            # Create sample events for the match
            if created:
                Event.objects.create(
                    event_type='goal',
                    minute=15,
                    player=teams[0].players.first()
                )
                Event.objects.create(
                    event_type='yellow_card',
                    minute=30,
                    player=teams[1].players.first()
                )
                
                match.events.set(Event.objects.filter(player__in=[teams[0].players.first(), teams[1].players.first()]))
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )