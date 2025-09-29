import os
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Tournament, Team, Player
from api.utils import get_latest_tournament


class Command(BaseCommand):
    help = 'Import team registration data from team_registrations.txt into the latest tournament'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='team_registrations.txt',
            help='Path to the team registrations file (default: team_registrations.txt)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing teams from latest tournament before importing',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually creating anything',
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        # If relative path, make it relative to the project root
        if not os.path.isabs(file_path):
            file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), file_path)
        
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
            return

        if options['clear'] and not options['dry_run']:
            self.clear_existing_data()

        try:
            tournament = get_latest_tournament()
            self.stdout.write(f'Target tournament: {tournament.name}')
        except:
            self.stdout.write(self.style.ERROR('No tournament found! Please create a tournament first.'))
            return

        with transaction.atomic():
            self.stdout.write('Starting team registration import...')
            
            teams_data = self.read_teams_from_file(file_path)
            
            if options['dry_run']:
                self.show_dry_run(teams_data)
            else:
                teams_created = self.create_teams_and_players(tournament, teams_data)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully imported {teams_created} teams')
                )

    def clear_existing_data(self):
        """Clear existing teams from the latest tournament"""
        self.stdout.write('Clearing existing teams from latest tournament...')
        
        tournament = get_latest_tournament()
        teams_count = Team.objects.filter(tournament=tournament).count()
        
        # Delete teams (this will also remove player associations but not players themselves)
        Team.objects.filter(tournament=tournament).delete()
        
        self.stdout.write(f'Cleared {teams_count} teams from {tournament.name}.')

    def read_teams_from_file(self, file_path):
        """Read team data from the CSV file"""
        teams_data = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                try:
                    team_data = self.parse_team_line(line)
                    if team_data:
                        teams_data.append(team_data)
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error parsing line {line_num}: {str(e)}')
                    )
                    continue
        
        return teams_data

    def parse_team_line(self, line):
        """Parse a CSV line into team data"""
        parts = [part.strip() for part in line.split(',')]
        
        if len(parts) < 4:
            return None
        
        try:
            start_year = int(parts[0])
        except ValueError:
            return None
        
        tagozat = parts[1]
        team_name = parts[2] if parts[2] else None
        
        # Collect all player names (starting from index 3)
        players = []
        for i in range(3, len(parts)):
            player_name = parts[i].strip()
            if player_name:
                players.append(player_name)
        
        captain_name = players[0] if players else None
        
        return {
            'start_year': start_year,
            'tagozat': tagozat,
            'team_name': team_name,
            'captain_name': captain_name,
            'players': players
        }

    def show_dry_run(self, teams_data):
        """Show what would be imported without actually doing it"""
        self.stdout.write(self.style.WARNING('DRY RUN - No data will be created'))
        self.stdout.write(f'Would import {len(teams_data)} teams:')
        
        for team_data in teams_data:
            team_display = f"{team_data['start_year']}{team_data['tagozat']}"
            if team_data['team_name']:
                team_display += f" ({team_data['team_name']})"
            
            self.stdout.write(f"  Team: {team_display}")
            self.stdout.write(f"    Captain: {team_data['captain_name']}")
            self.stdout.write(f"    Players ({len(team_data['players'])}): {', '.join(team_data['players'])}")
            self.stdout.write("")

    def create_teams_and_players(self, tournament, teams_data):
        """Create teams and players from the data"""
        teams_created = 0
        
        for team_data in teams_data:
            try:
                team = self.create_team_with_players(tournament, team_data)
                if team:
                    teams_created += 1
                    team_display = f"{team_data['start_year']}{team_data['tagozat']}"
                    if team_data['team_name']:
                        team_display += f" ({team_data['team_name']})"
                    self.stdout.write(f'Created team: {team_display} with {team.players.count()} players')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating team {team_data["start_year"]}{team_data["tagozat"]}: {str(e)}')
                )
                continue
        
        return teams_created

    def create_team_with_players(self, tournament, team_data):
        """Create a team and its players"""
        # Create or get the team
        team, created = Team.objects.get_or_create(
            tournament=tournament,
            start_year=team_data['start_year'],
            tagozat=team_data['tagozat'],
            defaults={
                'name': team_data['team_name'],
                'active': True
            }
        )
        
        if not created and team_data['team_name']:
            # Update team name if provided and team already exists
            team.name = team_data['team_name']
            team.save()
        
        # Clear existing players (in case we're re-importing)
        team.players.clear()
        
        # Create players and add them to the team
        for i, player_name in enumerate(team_data['players']):
            if not player_name:
                continue
                
            # Create or get player
            player, player_created = Player.objects.get_or_create(
                name=player_name,
                defaults={'csk': False}
            )
            
            # Set captain status for the first player
            if i == 0:  # First player is captain
                player.csk = True
                player.save()
            
            # Add player to team
            team.players.add(player)
            
            if player_created:
                self.stdout.write(f'  Created player: {player_name}')
        
        return team