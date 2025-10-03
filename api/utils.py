from .models import Match, Tournament, Szankcio
from django.shortcuts import get_object_or_404


def get_team_rank(bajnoksag, keresett_csapat_nev):
    meccsek = Match.objects.filter(bajnoksag=bajnoksag)
    csapatok = []

    for meccs in meccsek:
        # Assign default values of 0 for any missing scores
        hazai_pontszam = meccs.hazai_pontszam if meccs.hazai_pontszam is not None else 0
        vendeg_pontszam = meccs.vendeg_pontszam if meccs.vendeg_pontszam is not None else 0
        
        for csapat, hazai in [(meccs.hazai_csapat, True), (meccs.vendeg_csapat, False)]:
            if (hazai_pontszam > vendeg_pontszam and hazai) or (vendeg_pontszam > hazai_pontszam and not hazai):
                pontok = 3  # Win
            elif hazai_pontszam == vendeg_pontszam:
                pontok = 1  # Draw
            else:
                pontok = 0  # Loss

            # Update or create entry for the team
            found = False
            for csapat_info in csapatok:
                if csapat_info['nev'] == csapat.osztaly:  
                    csapat_info['meccsek'] += 1
                    csapat_info['points'] += pontok
                    csapat_info['lott'] += hazai_pontszam if hazai else vendeg_pontszam
                    csapat_info['kapott'] += vendeg_pontszam if hazai else hazai_pontszam
                    csapat_info['golarany'] = csapat_info['lott'] - csapat_info['kapott']
                    if pontok == 3:
                        csapat_info['wins'] += 1
                    elif pontok == 1:
                        csapat_info['ties'] += 1
                    else:
                        csapat_info['losses'] += 1
                    found = True
                    break
            
            if not found:
                csapatok.append({
                    'nev': csapat.osztaly,  
                    'meccsek': 1,
                    'points': pontok,
                    'lott': hazai_pontszam if hazai else vendeg_pontszam,
                    'kapott': vendeg_pontszam if hazai else hazai_pontszam,
                    'golarany': (hazai_pontszam if hazai else vendeg_pontszam) - (vendeg_pontszam if hazai else hazai_pontszam),
                    'wins': 1 if pontok == 3 else 0,
                    'ties': 1 if pontok == 1 else 0,
                    'losses': 1 if pontok == 0 else 0,
                })

    # Sort teams based on points, goal difference, goals scored, and wins
    csapatok = sorted(csapatok, key=lambda x: (x['points'], x['golarany'], x['lott'], x['wins']), reverse=True)

    # Find the rank of the requested team
    for idx, csapat in enumerate(csapatok, start=1):
        if csapat['nev'] == keresett_csapat_nev:
            return idx

    return None

def get_goal_scorers(events, team_filter=None):
    goal_scorers = []

    # Csak gól események
    goals = [e for e in events if e.event_type == "goal"]

    for goal in goals:
        scorer = goal.player
        scorer_name = scorer.name

        # játékos csapata (feltételezve, hogy mindig pontosan 1 team tagja)
        scorer_team = scorer.team_set.first()  # M2M miatt .team_set.all() lenne több is

        if team_filter and (not scorer_team or scorer_team.tagozat != team_filter):
            continue

        found = False
        for item in goal_scorers:
            if item['id'] == scorer.id:
                item['goals'] += 1
                found = True
                break

        if not found:
            goal_scorers.append({
                'id': scorer.id,
                'name': scorer_name,
                'goals': 1,
                'team': str(scorer_team) if scorer_team else None,
                'team_id': scorer_team.id if scorer_team else None
            })

    # rendezés gólok szerint
    goal_scorers = sorted(goal_scorers, key=lambda x: x['goals'], reverse=True)

    # ranglista pozíció hozzáadása
    ranked_scorers = []
    last_goals = None
    rank = 0
    actual_position = 0

    for scorer in goal_scorers:
        actual_position += 1
        if scorer['goals'] != last_goals:
            rank = actual_position
        scorer['rank'] = rank
        last_goals = scorer['goals']
        ranked_scorers.append(scorer)

    return ranked_scorers


def get_player_rank(goals, student):
    scorers = get_goal_scorers(goals)

    for scorer in scorers:
        if scorer['name'] == student:
            return scorer['rank']

    return None


def process_matches(tournament):
    csapatok = {}

    # Csak az adott bajnokság meccsei
    # AHOL VANNAK A MATCHNEK EVENTJEI IS
    meccsek = Match.objects.filter(tournament=tournament, events__isnull=False).distinct()

    for meccs in meccsek:
        # Meccsen belül gólok számolása Event alapján
        team1_goals = meccs.events.filter(event_type='goal', player__in=meccs.team1.players.all()).count()
        team2_goals = meccs.events.filter(event_type='goal', player__in=meccs.team2.players.all()).count()

        # Pontkiosztás
        csapat_pontkiosztas(csapatok, meccs.team1, team1_goals, team2_goals)
        csapat_pontkiosztas(csapatok, meccs.team2, team2_goals, team1_goals)

    # Apply sanctions (subtract points for each team)
    apply_sanctions(csapatok, tournament)

    # Rendezés: pont, gólkülönbség, lőtt gól
    csapatok = sorted(
        csapatok.values(),
        key=lambda x: (x['points'], x['golarany'], x['lott']),
        reverse=True
    )
    return csapatok


def csapat_pontkiosztas(csapatok, csapat, lott, kapott):
    if csapat.id not in csapatok:
        csapatok[csapat.id] = {
            'id': csapat.id,
            'nev': str(csapat),   # __str__ -> "9A - Tournament neve"
            'meccsek': 0,
            'wins': 0,
            'ties': 0,
            'losses': 0,
            'lott': 0,
            'kapott': 0,
            'golarany': 0,
            'points': 0
        }

    team = csapatok[csapat.id]

    team['meccsek'] += 1
    team['lott'] += lott
    team['kapott'] += kapott
    team['golarany'] = team['lott'] - team['kapott']

    if lott > kapott:
        team['points'] += 3
        team['wins'] += 1
    elif lott == kapott:
        team['points'] += 1
        team['ties'] += 1
    else:
        team['losses'] += 1


def apply_sanctions(csapatok, tournament):
    """
    Apply sanctions (point deductions) to teams in the tournament.
    Subtracts minus_points from each team's total points.
    """
    # Get all sanctions for this tournament
    sanctions = Szankcio.objects.filter(tournament=tournament)
    
    for sanction in sanctions:
        team_id = sanction.team.id
        if team_id in csapatok:
            # Subtract sanction points from team's total points
            csapatok[team_id]['points'] -= sanction.minus_points
            # Ensure points don't go below 0
            if csapatok[team_id]['points'] < 0:
                csapatok[team_id]['points'] = 0


def get_latest_tournament():
    """
    Returns the latest tournament based on start_date, falling back to creation order if no start_date.
    Raises 404 if no tournaments exist.
    """
    try:
        # Try to get the latest tournament by start_date (most recent first)
        tournament = Tournament.objects.filter(start_date__isnull=False).order_by('-start_date').first()
        
        if tournament:
            return tournament
            
        # If no tournaments have start_date, get the most recently created one
        tournament = Tournament.objects.order_by('-id').first()
        
        if tournament:
            return tournament
            
        # If no tournaments exist at all, raise 404
        raise Tournament.DoesNotExist()
        
    except Tournament.DoesNotExist:
        # Convert to 404 error for API consumers
        raise get_object_or_404(Tournament, id=0)  # This will always raise 404


