from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Tournament, Team, Player
from api.utils import get_latest_tournament


class Command(BaseCommand):
    help = 'Import team registration data into the latest tournament'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data',
            type=str,
            help='TSV data as a string (each line represents a team registration)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing teams from latest tournament before importing',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.clear_existing_data()

        # Get the raw data - either from argument or embedded in the command
        data = options.get('data') or self.get_embedded_data()
        
        if not data:
            self.stdout.write(
                self.style.ERROR('No data provided. Use --data argument or embed data in the command.')
            )
            return

        with transaction.atomic():
            self.stdout.write('Starting team registration import...')
            
            tournament = get_latest_tournament()
            self.stdout.write(f'Importing into tournament: {tournament.name}')
            
            teams_created = self.process_registration_data(tournament, data)
            
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

    def get_embedded_data(self):
        """Return the embedded registration data"""
        return """geibinger.felix.23f@szlgbp.hu	23	F			Kátai Kornél	Geibinger Félix	Csomós Dávid	Bozsóki Áron	Mechler Dénes	Kocsis Fecó	Kecskeméti Mátyás	Kollár Milán			Kollár Milán más osztályba jár
ye.daniel.21e@szlgbp.hu	21	E			Reznák-Iskander Botond	Reznák-Iskander Botond	Pesti Márton	Kovács Bence	Fain Laszlo	Réti Szasza	Ye Daniel	Szilaski Ádám	Geicsnek Ádám		
szantai.csanad.22f@szlgbp.hu	22	F		https://drive.google.com/open?id=1Mho4tF6GdKWxYCQ0EsoSyGhqmqWj_lZZ	Szántai Csanád	Vincze Dániel	Gere Lukács	Töreky Gergő	Balázs Ádám	Previák Richárd	Eigner Krisztián	Tatai Ádám	Minko Marcell		Minkó másik osztályba jár
szabo.marcell.21a@szlgbp.hu	21	A	12.A		Szabó Marcell	Tóbiás Levente	Szalay Tamás	Raffay Kristóf	Stróbli Benjamin	Baran Bertalan	Bordás Péter				
mckie.james.24a@szlgbp.hu	24	A	24NY	https://drive.google.com/open?id=1UoBSE50szU4Kh9sm-MWQqOM2OalLN6IB	McKie James 	McKie James	Kovács András Márton	Megyeri Martin	Varga Sebestyén	Raffay Zétény	Gyuros-Rosivall Ábel	Fényes Marcell	Péterfi Dénes	Stepán Samu	Kovács, Gyuros-Rosivall 24E, Péterfi, Stepán 24F
csaranko.mark.21b@szlgbp.hu	21	B	Halker	https://drive.google.com/open?id=1-fu3LaBKYIlyc81P5S0bQEHB5ChBHUD6	Kant	Tanár	Ramos	Messi	Xavi	Zidane	Dybala	Casillas	Anthony	Dembele	
kozma.domonkos.24b@szlgbp.hu	24	B	Trianon FC	https://drive.google.com/open?id=1rR3JKImYLK2e6WVlpd5VyQr-8GbXHwSx	Molnár Botond	Majsai Máté	Deli Botond	Nagy Levente	Kozma Domonkos 	Bercez Bálint	Nagy Ferenc	Simon Ákos	Matlák Bálint	Karminás Zolta	
viniczei.viktor.21f@szlgbp.hu	21	F	Fegyencváros	https://drive.google.com/open?id=1HSkiSPw6ptoKNXk_oPvkLGvvzPEXMNAP	Farkas Péter	Mamira Máté Márk	Ács Péter Levente	Ekker Máté	Nagy Gergely	Viniczei Viktor	Koncz Máté	Fodor Péter	Kardos Áron Tóbiás	Novák Simon	
szabo-aross.misa.25f@szlgbp.hu	25	F	Shaolin FC	https://drive.google.com/open?id=10CLf96sM-ir2aRkGglw1b4R9LjQqBNL2	Simák Boldizsár	Levente Gábor	Vincze Zoltán	Bánóczi Áron	Gelencsér Bence	Szabó-Aross Misa	Kaldau Sebestyén		Mikuska Botond	Gajdos Zétény	Lesz egy E-s srác, (ők nem indítanak csapatot) csak nem tudom per pill a teljes nevét, holnap írom.
zemen.zalan.22b@szlgbp.hu	22	B	Hortobágyi FC	https://drive.google.com/open?id=1JiLJ7TUfAWDaRUsQUass6VREfnwNI-PJ	Zemen Zalán	Almási Attila István	Pákozdi Artúr Ferenc	Boronyai Dániel	Valentin Bendegúz	Gerzsényi Endre	Mécs Martin	Gayer Borisz	Varga Levente	Gagyi Ábel	
toth-varsanyi.zeteny.24d@szlgbp.hu	24	D	Al Föld FC	https://drive.google.com/open?id=15TEmhcz54Dq5MW_Q4mFGW72lgMqddA6p	peczely.patrik@szlgbp.hu	fruhwirth.bence.24d@szlgbp.hu	furesz.matyas.24d@szlgbp.hu	toth-varsanyi.zeteny.24d@szlgbp.hu	balogh.levente.24d@szlgbp.hu	tamasi.andras.24d@szlgbp.hu	mathe.patrik.25d@szlgbp.hu	varga.zsombor.25d@szlgbp.hu	berecz.szilard.25b@szlgbp.hu	martits.gergo.24d@szlgbp.hu	Máthé Patrik 25d, Varga Zsombor 25d, Berecz Szilárd 25b
fias.mate.23b@szlgbp.hu	23	B		https://drive.google.com/open?id=1HV3UAowXFBgeXPmrKonPndz6D5RQYWAi	Fias Máté	Gégény Bence	Rozmanitz Gergő	Pelle Péter	Fábián Dániel	Ngo Xuan Nguyen	Réti Benedek	Zsák Balázs	Drágus Attila	Gábor Marcell	
kemecsey.ferenc.22a@szlgbp.hu	22	A	Rémisztő Pénisztő	https://drive.google.com/open?id=1EgyvCpObOxEdhUrEb1vxJhjPdoNHxVzk	Minkó Marcell	Minkó Marcell	Fedor Levente	Szimeonov Áron 	Őrlős Dániel	Brugnara Erik Josef	Hegedűs Martin	Kemecsey Ferenc Áron	Polákovits Miklós 	Nemes Milán Gellért	
szilagyi.attila.25f@szlgbp.hu	25	F	Zs csapat		Kavács Donát	Kiss Benedek	Bagoly-Kis Ákos	Pusztai Zsombor	Fülöp Ádám Tamás	Farnady Botond	Lengyel Ákos	Szalma-Baksi Ábel	Gál Bercell		
kalman.roland.24c@szlgbp.hu	24	C	24C		Kálmán Roland	Szabadi Zalán	Nagy Bálint	Kiss Domonkos	Mikola Máté	Nagy Sándor	Chen Xianting	Berényi Soma	Béres Marcell	Bolla-Vakály Márton	Szanka Fruzsina (10.c)
han.ngoc.23e@szlgbp.hu	23	E			Gera Sándor	Pozsonyi Bálint	Csata Péter	Acsai Zalán	Ujlakán Farkas	Tief Géza	Zongor Szablocs	Szabó Bence	Dudás-Györki Csaba	Zomborcsevics Mirkó	Dudás-Györki Csaba, Zomborcsevics Mirkó-> Knya"""

    def process_registration_data(self, tournament, data):
        """Process the registration data and create teams and players"""
        teams_created = 0
        
        for line_num, line in enumerate(data.strip().split('\n'), 1):
            if not line.strip():
                continue
                
            try:
                team_data = self.parse_team_line(line)
                if team_data:
                    team = self.create_team_with_players(tournament, team_data)
                    if team:
                        teams_created += 1
                        self.stdout.write(f'Created team: {team} with {team.players.count()} players')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing line {line_num}: {str(e)}')
                )
                continue
        
        return teams_created

    def parse_team_line(self, line):
        """Parse a single team registration line"""
        parts = line.split('\t')
        
        if len(parts) < 6:
            self.stdout.write(self.style.WARNING(f'Skipping line with insufficient data: {line[:50]}...'))
            return None
        
        email = parts[0].strip()
        year = parts[1].strip()
        tagozat = parts[2].strip()
        team_name = parts[3].strip() if len(parts) > 3 and parts[3].strip() else None
        drive_link = parts[4].strip() if len(parts) > 4 and parts[4].strip() else None
        
        # Extract player names (starting from index 5)
        players = []
        for i in range(5, len(parts)):
            player_name = parts[i].strip()
            # Skip empty cells, email addresses, and the notes column (last column often has notes)
            if (player_name and 
                not '@' in player_name and 
                not player_name.startswith('http') and
                len(player_name) > 2 and  # Skip very short entries
                not self.is_notes_column(player_name)):
                # Clean up player names
                cleaned_name = self.clean_player_name(player_name)
                if cleaned_name:
                    players.append(cleaned_name)
        
        # Remove duplicates while preserving order
        unique_players = []
        seen = set()
        for player in players:
            if player not in seen:
                unique_players.append(player)
                seen.add(player)
        
        players = unique_players
        
        # Captain is typically the first player
        captain_name = players[0] if players else None
        
        try:
            start_year = int(year)
        except ValueError:
            self.stdout.write(self.style.ERROR(f'Invalid year format: {year}'))
            return None
        
        return {
            'email': email,
            'start_year': start_year,
            'tagozat': tagozat,
            'team_name': team_name,
            'drive_link': drive_link,
            'captain_name': captain_name,
            'players': players
        }

    def clean_player_name(self, name):
        """Clean and normalize player names"""
        # Remove extra whitespace and normalize
        name = ' '.join(name.split())
        
        # Skip obviously invalid entries
        if any(indicator in name.lower() for indicator in ['osztályba', 'másik', 'nem tudom', 'holnap', '->']):
            return None
            
        # Handle parenthetical class information (e.g., "Szanka Fruzsina (10.c)")
        if '(' in name and ')' in name:
            name = name.split('(')[0].strip()
        
        # Skip if name is too short after cleaning
        if len(name) < 3:
            return None
            
        return name

    def is_notes_column(self, text):
        """Check if this text appears to be from the notes column"""
        notes_indicators = [
            'osztályba jár', 'másik osztály', 'nem tudom', 'holnap írom',
            'lesz egy', 'ők nem indítanak', '->', 'knya'
        ]
        return any(indicator in text.lower() for indicator in notes_indicators)

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
        
        # Create players and add them to the team
        players_added = 0
        captain_set = False
        
        for player_name in team_data['players']:
            if not player_name:
                continue
                
            # Create or get player
            player, player_created = Player.objects.get_or_create(
                name=player_name,
                defaults={'csk': False}
            )
            
            # Set captain status for the first player (captain)
            if not captain_set and player_name == team_data['captain_name']:
                player.csk = True
                player.save()
                captain_set = True
            
            # Add player to team
            team.players.add(player)
            players_added += 1
            
            if player_created:
                self.stdout.write(f'  Created player: {player_name}')
        
        self.stdout.write(f'  Added {players_added} players to team {team}')
        return team