import re
from datetime import datetime, date
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Tournament, Team, Player, Match, Round, Event


class Command(BaseCommand):
    help = 'Import SZLG LIGA 24/25 tournament data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing SZLG LIGA 24/25 data before importing',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_existing_data()

        with transaction.atomic():
            self.stdout.write('Starting SZLG LIGA 24/25 import...')
            
            # Import data step by step
            tournament = self.create_tournament()
            teams_data = self.get_teams_data()
            teams = self.create_teams_and_players(tournament, teams_data)
            matches_data = self.get_matches_data()
            matches = self.create_matches(tournament, teams, matches_data)
            goals_data = self.get_goals_data()
            self.create_goal_events(matches, teams, goals_data)
            
            self.stdout.write(
                self.style.SUCCESS('Successfully imported SZLG LIGA 24/25 data')
            )

    def clear_existing_data(self):
        """Clear existing SZLG LIGA 24/25 data"""
        self.stdout.write('Clearing existing SZLG LIGA 24/25 data...')
        
        try:
            tournament = Tournament.objects.get(name='SZLG LIGA 24/25')
            # Delete all related data
            Event.objects.filter(player__team__tournament=tournament).delete()
            Match.objects.filter(tournament=tournament).delete()
            Round.objects.filter(tournament=tournament).delete()
            Team.objects.filter(tournament=tournament).delete()
            tournament.delete()
            self.stdout.write('Existing data cleared.')
        except Tournament.DoesNotExist:
            self.stdout.write('No existing tournament found.')

    def create_tournament(self):
        """Create the tournament"""
        self.stdout.write('Creating tournament...')
        
        tournament, created = Tournament.objects.get_or_create(
            name='SZLG LIGA 24/25',
            defaults={
                'start_date': date(2024, 10, 15),  # First match date
                'end_date': date(2025, 6, 19),     # Last match date
                'registration_open': False
            }
        )
        
        if created:
            self.stdout.write('Tournament created.')
        else:
            self.stdout.write('Tournament already exists.')
        
        return tournament

    def get_teams_data(self):
        """Return teams and their players data"""
        return {
            '22 E': [
                'Kurucz Zsombor', 'Gégény Krisztián', 'Bánhidi Csongor', 
                'Sági Zsombor Boldizsár', 'Czumpft Bálint', 'Deák Ferenc', 
                'Kocsis István', 'Luu Thanh Dat'
            ],
            '24 B': [
                'Molnár Botond', 'Kozma Domonkos', 'Nagy Levente Dániel', 
                'Nagy Ferenc Bálint', 'Majsai Máté Zoltán', 'Deli Botond Dániel', 
                'Simon Ákos Zsolt'
            ],
            '20 F': [
                'Müller Dávid Szilárd', 'Kerülő Ákos', 'Gulácsy Gergő', 
                'Bognár Bence', 'Bartha Bence László', 'Gazdag Dávid Benedek', 
                'Orsolya-Székely Ábel', 'Fazekas Milán', 'Keviczky-Tóth Boldizsár'
            ],
            '20 A': [
                'Varga Márk', 'Wootsch Gábor Tamás', 'Kispál Dániel', 
                'Maróti Gergő', 'Rábai Dávid Krisztián', 'Simon Benedek'
            ],
            '24 D': [
                'Fürész Mátyás', 'Frühwirth Bence', 'Tóth-Varsányi Zétény', 
                'Balogh Levente', 'Stark Péter Andor', 'Martits Gergő', 
                'Dévényi Péter', 'Mahler Artúr', 'Geleta Lilla', 'Tamási András István'
            ],
            '21 F': [
                'Kardos Áron Tóbiás', 'Mamira Máté Márk', 'Ekker Máté', 
                'Fodor Péter', 'Koncz Máté', 'Gál Nikolasz', 'Ács Péter Levente', 
                'Farkas Péter', 'Nagy Gergely', 'Viniczei Viktor'
            ],
            '24 F': [
                'Stépán Sámuel Zsolt', 'Péterfi Dénes', 'Görömbei Ervin', 
                'Bocsi Mátyás', 'Kordás Dávid', 'Váradi Szilárd Levente', 
                'Pavlicsek Huba', 'Kovács Ádám Lőrinc', 'Szabó-Kovács Kolos Gyula'
            ],
            '21 E': [
                'Pesti Márton', 'Geicsnek Ádám', 'Barczi Ádám', 'Várkonyi Péter Bátor', 
                'Szilaski Ádám', 'Reznák-Iskander Botond', 'Ye Daniel', 'Kele Áron', 
                'Kovács Bence', 'Fain László Bence', 'Mack Boldizsár', 'Budaházy Bernát'
            ],
            '23 B': [
                'Fias Máté', 'Gégény Bence', 'Ngo Xuan Nguyen', 'Horányi Dénes Tamás', 
                'Fábián Dániel', 'Pelle Péter', 'Réti Benedek', 'Rozmanitz Gergő', 
                'Gábor Marcell'
            ],
            '23 F': [
                'Bozsóki Áron', 'Kátai Kornél', 'Mechler Dénes', 'Csomós Dávid', 
                'Kecskeméti Mátyás', 'Kollár Milán', 'Geibinger Félix', 'Kocsis Ferenc Bálint'
            ],
            '21 B': [
                'Telkes Zoltán Dániel', 'Jancsár Botond', 'Borovics-Kocsis Bence', 
                'Csarankó Márk Róbert', 'Ursu Erik', 'Majsai Dávid', 'Nagy Patrik', 
                'Tóth Artúr', 'Bittera Berény Tibor', 'Majsai Kristóf János'
            ],
            '22 B': [
                'Zemen Zalán', 'Valentin Bendegúz', 'Gerzsényi Endre', 'Pákozdi Artúr Ferenc', 
                'Mécs Martin Levente', 'Gayer Borisz', 'Almási Attila István', 
                'Boronyai Dániel', 'Varga Levente'
            ],
            '24 A': [
                'Kovács András Márton', 'Gyurós-Rosivall Ábel', 'Varga Sebestyén', 
                'Raffay Zétény', 'Fényes Marcell', 'Megyeri Martin', 'McKie James Robert'
            ],
            '22 F': [
                'Szántai Csanád', 'Tatai Ádám', 'Vincze Dániel', 'Balázs Ádám Gábor', 
                'Gere Lukács', 'Minkó Marcell Levente', 'Töreky Gergő Gábor', 
                'Previák Richárd Áron'
            ],
            '24 C': [
                'Kálmán Roland', 'Kiss Domonkos', 'Nagy Bálint', 'Mikola Máté', 
                'Cséplő Tamás', 'Szabadi Zalán', 'Nagy Sándor Miklós', 'Chen Xianting', 
                'Bolla-Vakály Márton', 'Gyenge Márk Teofil'
            ],
            '21 A': [
                'Szabó Marcell Dénes', 'Tóbiás Levente Richárd', 'Szalay Tamás', 
                'Mérai Gergő', 'Raffay Kristóf', 'Stróbli Benjámin', 'Milo Tomas'
            ],
            '21 C': [
                'Nguyen Nhat Duy', 'Szilasi Benjámin Imre', 'Horváth Botond', 
                'Laczó András', 'Hallgas Benedek', 'Iván Márton', 'Garabics Dániel', 
                'Zack-Williams Balázs Olushola', 'Tóth-Vatai Tamás', 'Maigut Zita Klára'
            ]
        }

    def create_teams_and_players(self, tournament, teams_data):
        """Create teams and their players"""
        self.stdout.write('Creating teams and players...')
        
        teams = {}
        
        for team_name, player_names in teams_data.items():
            # Extract start year and tagozat from team name (e.g., "24 C" -> start_year=24, tagozat="C")
            parts = team_name.split()
            start_year = int(parts[0])
            tagozat = parts[1]
            
            # Create team
            team, created = Team.objects.get_or_create(
                tournament=tournament,
                start_year=start_year,
                tagozat=tagozat
            )
            
            if created:
                self.stdout.write(f'Created team: {team_name}')
            
            # Create players and add to team
            for player_name in player_names:
                player, player_created = Player.objects.get_or_create(
                    name=player_name
                )
                team.players.add(player)
                
                if player_created:
                    self.stdout.write(f'  Created player: {player_name}')
            
            teams[team_name] = team
        
        self.stdout.write(f'Created {len(teams)} teams with players.')
        return teams

    def get_matches_data(self):
        """Return match data from the provided text"""
        matches_text = """24 C vs 21 F|2 : 0|16. forduló|2025.06.19
24 D vs 21 F|1 : 6|14. forduló|2025.06.17
24 B vs 21 F|1 : 7|16. forduló|2025.06.17
24 A vs 24 D|3 : 0|16. forduló|2025.06.15
22 F vs 23 B|3 : 0|16. forduló|2025.06.15
20 F vs 21 B|0 : 3|16. forduló|2025.06.13
20 F vs 24 C|0 : 3|11. forduló|2025.06.13
20 F vs 22 B|0 : 3|15. forduló|2025.06.13
20 F vs 23 F|0 : 3|16. forduló|2025.06.13
20 F vs 21 E|0 : 3|14. forduló|2025.06.13
20 F vs 23 B|0 : 3|12. forduló|2025.06.13
24 B vs 24 A|1 : 2|16. forduló|2025.06.12
22 E vs 22 B|0 : 4|14. forduló|2025.06.04
21 E vs 22 F|0 : 4|14. forduló|2025.05.30
21 E vs 24 F|4 : 0|13. forduló|2025.05.23
21 E vs 22 B|3 : 2|12. forduló|2025.05.16
21 B vs 22 F|0 : 4|14. forduló|2025.04.28
21 C vs 22 E|6 : 0|16. forduló|2025.04.16
22 B vs 21 F|0 : 8|12. forduló|2025.04.16
22 B vs 24 F|11 : 1|11. forduló|2025.04.11
20 A vs 23 B|5 : 1|16. forduló|2025.04.09
21 C vs 21 F|1 : 1|15. forduló|2025.04.03
21 E vs 21 A|1 : 2|11. forduló|2025.03.31
21 B vs 24 A|4 : 1|13. forduló|2025.03.28
21 C vs 24 F|5 : 0|14. forduló|2025.03.28
21 B vs 20 A|2 : 6|12. forduló|2025.03.19
23 B vs 24 A|4 : 0|12. forduló|2025.03.12
22 E vs 24 B|4 : 2|13. forduló|2025.03.12
21 F vs 21 A|7 : 0|11. forduló|2025.03.12
24 F vs 24 D|1 : 8|12. forduló|2025.03.11
20 A vs 24 B|6 : 0|14. forduló|2025.03.10
21 C vs 24 D|6 : 2|14. forduló|2025.03.07
24 C vs 20 A|2 : 2|14. forduló|2025.03.06
24 C vs 22 E|1 : 0|13. forduló|2025.03.05
22 E vs 21 A|0 : 1|11. forduló|2025.02.26
21 C vs 22 B|5 : 3|12. forduló|2025.02.25
22 E vs 21 B|0 : 1|10. forduló|2025.02.20
24 B vs 24 F|6 : 0|12. forduló|2025.02.19
23 F vs 21 A|0 : 2|13. forduló|2025.02.19
22 E vs 23 B|1 : 2|9. forduló|2025.02.18
24 C vs 24 A|5 : 0|12. forduló|2025.02.18
23 F vs 22 F|1 : 2|12. forduló|2025.02.14
21 C vs 24 B|1 : 1|11. forduló|2025.02.06
21 A vs 24 D|4 : 3|12. forduló|2025.02.05
21 F vs 21 B|2 : 0|10. forduló|2025.02.05
22 F vs 20 F|9 : 1|12. forduló|2025.02.05
21 A vs 22 F|2 : 2|11. forduló|2025.02.03
20 A vs 21 E|1 : 0|12. forduló|2025.01.31
24 B vs 22 B|2 : 7|10. forduló|2025.01.30
20 A vs 23 F|4 : 0|11. forduló|2025.01.29
24 C vs 24 F|16 : 0|11. forduló|2025.01.28
24 A vs 21 E|1 : 0|11. forduló|2025.01.24
23 B vs 24 F|10 : 1|10. forduló|2025.01.22
22 F vs 20 A|1 : 2|10. forduló|2025.01.20
22 E vs 23 F|1 : 3|8. forduló|2025.01.20
24 A vs 23 F|0 : 0|10. forduló|2025.01.17
22 E vs 21 E|2 : 0|7. forduló|2025.01.17
21 A vs 20 F|1 : 2|10. forduló|2025.01.15
24 C vs 21 C|1 : 1|10. forduló|2025.01.14
21 F vs 23 B|6 : 0|9. forduló|2025.01.08
24 C vs 22 B|2 : 1|9. forduló|2025.01.08
21 C vs 21 B|4 : 0|9. forduló|2025.01.08
24 D vs 24 B|1 : 1|9. forduló|2025.01.07
20 A vs 20 F|1 : 1|10. forduló|2025.01.01
21 C vs 23 B|4 : 2|8. forduló|2024.12.19
24 C vs 24 D|3 : 0|8. forduló|2024.12.19
22 B vs 21 B|4 : 1|7. forduló|2024.12.18
22 F vs 24 A|1 : 0|9. forduló|2024.12.18
20 A vs 22 B|0 : 1|8. forduló|2024.12.17
21 A vs 24 B|6 : 2|9. forduló|2024.12.17
21 C vs 21 E|2 : 0|7. forduló|2024.12.13
21 F vs 21 E|2 : 0|8. forduló|2024.12.12
24 F vs 23 F|0 : 9|8. forduló|2024.12.12
24 B vs 24 C|1 : 4|7. forduló|2024.12.12
24 D vs 23 B|1 : 1|7. forduló|2024.12.11
21 A vs 20 A|0 : 0|8. forduló|2024.12.11
22 B vs 23 B|2 : 1|5. forduló|2024.12.11
24 A vs 20 F|2 : 3|8. forduló|2024.12.11
22 E vs 22 F|1 : 4|6. forduló|2024.12.10
21 B vs 24 D|4 : 5|7. forduló|2024.12.09
24 C vs 21 A|3 : 2|6. forduló|2024.12.06
21 F vs 22 F|0 : 0|7. forduló|2024.12.05
21 F vs 23 F|7 : 2|6. forduló|2024.12.04
22 E vs 20 F|3 : 1|5. forduló|2024.12.04
21 B vs 24 B|3 : 0|6. forduló|2024.12.04
24 F vs 22 F|0 : 13|7. forduló|2024.12.04
23 B vs 24 B|3 : 1|5. forduló|2024.12.03
20 A vs 24 F|9 : 0|6. forduló|2024.11.29
21 C vs 23 F|3 : 1|6. forduló|2024.11.29
21 E vs 24 D|3 : 1|5. forduló|2024.11.29
24 C vs 21 B|0 : 0|5. forduló|2024.11.28
20 A vs 22 E|3 : 1|5. forduló|2024.11.27
20 F vs 24 F|6 : 1|5. forduló|2024.11.27
21 A vs 24 A|2 : 1|6. forduló|2024.11.26
22 E vs 24 A|1 : 1|3. forduló|2024.11.25
22 B vs 23 F|2 : 1|4. forduló|2024.11.22
21 C vs 22 F|0 : 0|5. forduló|2024.11.22
24 C vs 23 B|2 : 1|4. forduló|2024.11.22
21 E vs 24 B|2 : 0|4. forduló|2024.11.21
20 F vs 21 C|4 : 2|4. forduló|2024.11.21
21 F vs 20 A|0 : 0|5. forduló|2024.11.20
21 A vs 21 B|1 : 2|5. forduló|2024.11.20
23 F vs 24 D|5 : 2|4. forduló|2024.11.18
21 F vs 20 F|5 : 0|4. forduló|2024.11.18
22 F vs 22 B|2 : 1|4. forduló|2024.11.14
24 A vs 24 F|4 : 1|5. forduló|2024.11.14
23 B vs 21 B|1 : 1|3. forduló|2024.11.14
21 A vs 22 B|4 : 3|4. forduló|2024.11.13
21 E vs 24 C|0 : 2|3. forduló|2024.11.08
22 F vs 24 D|9 : 1|3. forduló|2024.11.08
24 F vs 22 E|1 : 10|3. forduló|2024.11.08
21 E vs 21 B|1 : 3|2. forduló|2024.11.07
23 F vs 24 B|2 : 0|3. forduló|2024.11.07
21 F vs 24 A|6 : 1|3. forduló|2024.11.06
21 A vs 23 B|2 : 2|3. forduló|2024.11.06
21 C vs 24 A|4 : 0|3. forduló|2024.11.05
24 D vs 20 F|2 : 3|2. forduló|2024.11.04
21 C vs 20 A|0 : 1|2. forduló|2024.10.31
24 C vs 23 F|5 : 0|2. forduló|2024.10.25
22 F vs 24 B|8 : 0|2. forduló|2024.10.25
21 F vs 22 E|1 : 2|2. forduló|2024.10.21
21 A vs 24 F|12 : 0|2. forduló|2024.10.21
24 A vs 20 A|0 : 0|2. forduló|2024.10.21
21 A vs 21 C|0 : 1|1. forduló|2024.10.18
22 F vs 24 C|1 : 1|1. forduló|2024.10.18
23 F vs 21 B|1 : 2|1. forduló|2024.10.17
21 E vs 23 B|1 : 0|1. forduló|2024.10.17
22 B vs 24 A|3 : 1|1. forduló|2024.10.17
20 A vs 24 D|4 : 1|1. forduló|2024.10.16
21 F vs 24 F|7 : 0|1. forduló|2024.10.16
24 B vs 20 F|1 : 3|1. forduló|2024.10.15"""
        
        matches = []
        for line in matches_text.strip().split('\n'):
            parts = line.split('|')
            if len(parts) == 4:
                match_info = parts[0].strip()
                score = parts[1].strip()
                round_info = parts[2].strip()
                date_str = parts[3].strip()
                
                # Parse teams
                team1, team2 = match_info.split(' vs ')
                
                # Parse score
                score1, score2 = map(int, score.split(' : '))
                
                # Parse round number
                round_num = int(round_info.split('.')[0])
                
                # Parse date
                match_date = datetime.strptime(date_str, '%Y.%m.%d').date()
                
                matches.append({
                    'team1': team1.strip(),
                    'team2': team2.strip(),
                    'score1': score1,
                    'score2': score2,
                    'round': round_num,
                    'date': match_date
                })
        
        return matches

    def create_matches(self, tournament, teams, matches_data):
        """Create matches and rounds"""
        self.stdout.write('Creating matches and rounds...')
        
        matches = {}
        rounds = {}
        
        for match_data in matches_data:
            # Create round if it doesn't exist
            round_num = match_data['round']
            if round_num not in rounds:
                round_obj, created = Round.objects.get_or_create(
                    tournament=tournament,
                    number=round_num
                )
                rounds[round_num] = round_obj
                if created:
                    self.stdout.write(f'Created round {round_num}')
            
            # Get teams
            team1 = teams[match_data['team1']]
            team2 = teams[match_data['team2']]
            
            # Create match
            match = Match.objects.create(
                tournament=tournament,
                team1=team1,
                team2=team2,
                datetime=datetime.combine(match_data['date'], datetime.min.time()),
                round_obj=rounds[round_num]
            )
            
            # Store match with a unique identifier for goal assignment
            match_key = f"{match_data['team1']} vs {match_data['team2']} {match_data['date']}"
            matches[match_key] = {
                'match': match,
                'score1': match_data['score1'],
                'score2': match_data['score2']
            }
            
            self.stdout.write(f'Created match: {match_data["team1"]} vs {match_data["team2"]} ({match_data["score1"]}:{match_data["score2"]})')
        
        self.stdout.write(f'Created {len(matches)} matches across {len(rounds)} rounds.')
        return matches

    def get_goals_data(self):
        """Return goalscorer data"""
        goals_text = """Nagy Gergely|33|21 F
Vincze Dániel|30|22 F
Szabó Marcell Dénes|21|21 A
Fürész Mátyás|20|24 D
Szabadi Zalán|19|24 C
Varga Márk|16|20 A
Nguyen Nhat Duy|16|21 C
Kálmán Roland|15|24 C
Minkó Marcell Levente|15|22 F
Pelle Péter|15|23 B
Viniczei Viktor|13|21 F
Kátai Kornél|12|23 F
Garabics Dániel|12|21 C
Almási Attila István|11|22 B
Wootsch Gábor Tamás|10|20 A
Szántai Csanád|10|22 F
Czumpft Bálint|10|22 E
Fazekas Milán|9|20 F
Tóth-Vatai Tamás|9|21 C
Mérai Gergő|9|21 A
Molnár Botond|8|24 B
Fodor Péter|8|21 F
Sági Zsombor Boldizsár|8|22 E
Kiss Domonkos|8|24 C
Pákozdi Artúr Ferenc|8|22 B
Ursu Erik|7|21 B
Kispál Dániel|7|20 A
Laczó András|7|21 C
Majsai Dávid|6|21 B
Maróti Gergő|6|20 A
Deák Ferenc|6|22 E
Gazdag Dávid Benedek|5|20 F
Megyeri Martin|5|24 A
Gulácsy Gergő|5|20 F
Koncz Máté|5|21 F
Kollár Milán|5|23 F
Gerzsényi Endre|5|22 B
Péterfi Dénes|5|24 F
Zemen Zalán|5|22 B
McKie James Robert|5|24 A
Fain László Bence|4|21 E
Boronyai Dániel|4|22 B
Stróbli Benjámin|4|21 A
Kerülő Ákos|4|20 F
Gábor Marcell|4|23 B
Mechler Dénes|4|23 F
Rábai Dávid Krisztián|4|20 A
Frühwirth Bence|4|24 D
Nagy Bálint|4|24 C
Farkas Péter|4|21 F
Tóbiás Levente Richárd|3|21 A
Previák Richárd Áron|3|22 F
Ngo Xuan Nguyen|3|23 B
Milo Tomas|3|21 A
Mikola Máté|3|24 C
Telkes Zoltán Dániel|3|21 B
Kocsis Ferenc Bálint|3|23 F
Ye Daniel|2|21 E
Varga Sebestyén|2|24 A
Nagy Levente Dániel|2|24 B
Töreky Gergő Gábor|2|22 F
Balogh Levente|2|24 D
Deli Botond Dániel|2|24 B
Nagy Ferenc Bálint|2|24 B
Fábián Dániel|2|23 B
Réti Benedek|2|23 B
Kozma Domonkos|2|24 B
Reznák-Iskander Botond|2|21 E
Gayer Borisz|2|22 B
Tóth Artúr|1|21 B
Gégény Krisztián|1|22 E
Ekker Máté|1|21 F
Gyurós-Rosivall Ábel|1|24 A
Bánhidi Csongor|1|22 E
Tamási András István|1|24 D
Müller Dávid Szilárd|1|20 F
Simon Benedek|1|20 A
Barczi Ádám|1|21 E
Várkonyi Péter Bátor|1|21 E
Pesti Márton|1|21 E
Horányi Dénes Tamás|1|23 B
Nagy Patrik|1|21 B
Bozsóki Áron|1|23 F
Fias Máté|1|23 B
Szalay Tamás|1|21 A
Majsai Máté Zoltán|1|24 B
Horváth Botond|1|21 C
Stépán Sámuel Zsolt|1|24 F
Tóth-Varsányi Zétény|1|24 D
Csarankó Márk Róbert|1|21 B
Borovics-Kocsis Bence|1|21 B
Geicsnek Ádám|1|21 E
Kovács András Márton|1|24 A
Ács Péter Levente|1|21 F"""
        
        goals = []
        for line in goals_text.strip().split('\n'):
            parts = line.split('|')
            if len(parts) == 3:
                player_name = parts[0].strip()
                goal_count = int(parts[1].strip())
                team_name = parts[2].strip()
                
                goals.append({
                    'player': player_name,
                    'goals': goal_count,
                    'team': team_name
                })
        
        return goals

    def create_goal_events(self, matches, teams, goals_data):
        """Create goal events for matches based on goalscorer data and match results"""
        self.stdout.write('Creating goal events...')
        
        # Create a mapping of players to their teams
        player_to_team = {}
        for team_name, team in teams.items():
            for player in team.players.all():
                player_to_team[player.name] = team_name
        
        # Create a mapping of total goals per player
        player_goals = {goal['player']: goal['goals'] for goal in goals_data}
        
        # Track remaining goals for each player
        remaining_goals = player_goals.copy()
        
        # Process matches in chronological order
        sorted_matches = []
        for match_key, match_info in matches.items():
            sorted_matches.append((match_info['match'].datetime, match_key, match_info))
        sorted_matches.sort()
        
        total_events_created = 0
        
        for match_datetime, match_key, match_info in sorted_matches:
            match = match_info['match']
            team1_goals = match_info['score1']
            team2_goals = match_info['score2']
            
            # Get team names
            team1_name = f"{match.team1.start_year} {match.team1.tagozat}"
            team2_name = f"{match.team2.start_year} {match.team2.tagozat}"
            
            # Create goal events for team1
            team1_events = self.distribute_goals_for_team(
                match, team1_name, team1_goals, remaining_goals, player_to_team
            )
            
            # Create goal events for team2
            team2_events = self.distribute_goals_for_team(
                match, team2_name, team2_goals, remaining_goals, player_to_team
            )
            
            events_for_match = team1_events + team2_events
            total_events_created += len(events_for_match)
            
            # Add events to match
            for event in events_for_match:
                match.events.add(event)
            
            if events_for_match:
                self.stdout.write(f'  {team1_name} vs {team2_name}: Created {len(events_for_match)} goal events')
        
        self.stdout.write(f'Created {total_events_created} goal events total.')

    def distribute_goals_for_team(self, match, team_name, goals_needed, remaining_goals, player_to_team):
        """Distribute goals for a specific team in a match"""
        if goals_needed == 0:
            return []
        
        # Find players from this team who have remaining goals
        team_players_with_goals = []
        for player_name, remaining in remaining_goals.items():
            if remaining > 0 and player_to_team.get(player_name) == team_name:
                team_players_with_goals.append(player_name)
        
        if not team_players_with_goals:
            self.stdout.write(f'Warning: No players with remaining goals found for team {team_name}')
            return []
        
        # Distribute goals among available players
        events = []
        goals_assigned = 0
        
        # Try to assign goals fairly, giving preference to players with more total goals
        sorted_players = sorted(
            team_players_with_goals, 
            key=lambda p: remaining_goals[p], 
            reverse=True
        )
        
        for player_name in sorted_players:
            if goals_assigned >= goals_needed:
                break
            
            if remaining_goals[player_name] > 0:
                # Assign one goal to this player
                try:
                    player = Player.objects.get(name=player_name)
                    event = Event.objects.create(
                        event_type='goal',
                        minute=goals_assigned * 10 + 10,  # Distribute throughout match
                        player=player
                    )
                    events.append(event)
                    remaining_goals[player_name] -= 1
                    goals_assigned += 1
                except Player.DoesNotExist:
                    self.stdout.write(f'Warning: Player {player_name} not found')
                    continue
        
        # If we still need more goals, assign them to available players
        while goals_assigned < goals_needed and any(remaining_goals[p] > 0 for p in team_players_with_goals):
            for player_name in sorted_players:
                if goals_assigned >= goals_needed:
                    break
                if remaining_goals[player_name] > 0:
                    try:
                        player = Player.objects.get(name=player_name)
                        event = Event.objects.create(
                            event_type='goal',
                            minute=goals_assigned * 10 + 10,
                            player=player
                        )
                        events.append(event)
                        remaining_goals[player_name] -= 1
                        goals_assigned += 1
                    except Player.DoesNotExist:
                        continue
        
        if goals_assigned < goals_needed:
            self.stdout.write(f'Warning: Could only assign {goals_assigned}/{goals_needed} goals for {team_name}')
        
        return events