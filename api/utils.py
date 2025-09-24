from .models import Match
from .schemas import Event, EventSchema, MatchSchema, TeamSchema, TournamentSchema, RoundSchema, ProfileSchema
from functools import cmp_to_key
from collections import defaultdict
from typing import Iterable


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




def csapat_pontkiosztas(csapatok, csapat, lott, kapott):
    if csapat.id not in csapatok:
        csapatok[csapat.id] = {
            'id': csapat.id,
            'nev': str(csapat),
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


def process_matches(bajnoksag):
    csapatok = {}
    head_to_head = defaultdict(lambda: defaultdict(lambda: {"points": 0, "golarany": 0, "lott": 0}))

    for match in bajnoksag.match_set.all():
        goals_team1, goals_team2 = match.result()
        t1, t2 = match.team1, match.team2

        # összesített statok
        csapat_pontkiosztas(csapatok, t1, goals_team1, goals_team2)
        csapat_pontkiosztas(csapatok, t2, goals_team2, goals_team1)

        # egymás elleni pontok
        if goals_team1 > goals_team2:
            head_to_head[t1.id][t2.id]["points"] += 3
        elif goals_team1 == goals_team2:
            head_to_head[t1.id][t2.id]["points"] += 1
            head_to_head[t2.id][t1.id]["points"] += 1
        else:
            head_to_head[t2.id][t1.id]["points"] += 3

        # egymás elleni gólkülönbség és gólok
        head_to_head[t1.id][t2.id]["golarany"] += goals_team1 - goals_team2
        head_to_head[t2.id][t1.id]["golarany"] += goals_team2 - goals_team1

        head_to_head[t1.id][t2.id]["lott"] += goals_team1
        head_to_head[t2.id][t1.id]["lott"] += goals_team2

    return rangsorolas(csapatok, head_to_head)


def rangsorolas(csapatok, head_to_head):
    teams = list(csapatok.values())

    def compare(a, b):
        # 1. pontok
        if a["points"] != b["points"]:
            return b["points"] - a["points"]

        # 2. egymás elleni pontok
        h2h_a = head_to_head[a["id"]][b["id"]]
        h2h_b = head_to_head[b["id"]][a["id"]]
        if h2h_a["points"] != h2h_b["points"]:
            return h2h_b["points"] - h2h_a["points"]

        # 3. egymás elleni gólkülönbség
        if h2h_a["golarany"] != h2h_b["golarany"]:
            return h2h_b["golarany"] - h2h_a["golarany"]

        # 4. egymás elleni lőtt gólok
        if h2h_a["lott"] != h2h_b["lott"]:
            return h2h_b["lott"] - h2h_a["lott"]

        # 5. összesített gólkülönbség
        if a["golarany"] != b["golarany"]:
            return b["golarany"] - a["golarany"]

        # 6. összesített lőtt gól
        return b["lott"] - a["lott"]

    rendezett = sorted(teams, key=cmp_to_key(compare))

    for i, team in enumerate(rendezett, start=1):
        team["position"] = i

    return rendezett

def event_to_schema(event: Event):
    return {
        "id": event.id,
        "event_type": event.event_type,
        "minute": event.minute,
        "player_id": event.player.id if event.player else None,
        "extra_time": event.extra_time,
    }

def match_to_schema(match: Match) -> MatchSchema:
    team1 = match.team1
    team2 = match.team2

    team1_schema = TeamSchema(
        id=team1.id,
        tournament_id=team1.tournament.id,
        start_year=team1.start_year,
        tagozat=team1.tagozat,
        active=team1.active,
        registration_time=team1.registration_time.isoformat() if team1.registration_time else None,
        name=str(team1),
    )

    team2_schema = TeamSchema(
        id=team2.id,
        tournament_id=team2.tournament.id,
        start_year=team2.start_year,
        tagozat=team2.tagozat,
        active=team2.active,
        registration_time=team2.registration_time.isoformat() if team2.registration_time else None,
        name=str(team2),
    )

    tournament_schema = TournamentSchema(id=match.tournament.id, name=str(match.tournament))
    round_schema = RoundSchema(id=match.round_obj.id, number=match.round_obj.number)
    referee_schema = ProfileSchema(id=match.referee.id, name=str(match.referee)) if match.referee else None

    # --- Gólok és lapok száma ---
    team1_score = match.events.filter(event_type="goal", player__in=team1.players.all()).count()
    team2_score = match.events.filter(event_type="goal", player__in=team2.players.all()).count()
    team1_yellow = match.events.filter(event_type="yellow_card", player__in=team1.players.all()).count()
    team2_yellow = match.events.filter(event_type="yellow_card", player__in=team2.players.all()).count()
    team1_red = match.events.filter(event_type="red_card", player__in=team1.players.all()).count()
    team2_red = match.events.filter(event_type="red_card", player__in=team2.players.all()).count()

    return MatchSchema(
        team1=team1_schema,
        team2=team2_schema,
        tournament=tournament_schema,
        round_obj=round_schema,
        referee=referee_schema,
        team1_score=team1_score,
        team2_score=team2_score,
        team1_yellow_cards=team1_yellow,
        team2_yellow_cards=team2_yellow,
        team1_red_cards=team1_red,
        team2_red_cards=team2_red,
    )

# --- Több Match -> list[MatchSchema] ---
def matches_to_schema(matches: Iterable[Match]) -> list[MatchSchema]:
    result = []
    for match in matches:
        team1 = match.team1
        team2 = match.team2

        # Számolás minden meccshez külön
        team1_score = match.events.filter(event_type="goal", player__in=team1.players.all()).count()
        team2_score = match.events.filter(event_type="goal", player__in=team2.players.all()).count()
        team1_yellow = match.events.filter(event_type="yellow_card", player__in=team1.players.all()).count()
        team2_yellow = match.events.filter(event_type="yellow_card", player__in=team2.players.all()).count()
        team1_red = match.events.filter(event_type="red_card", player__in=team1.players.all()).count()
        team2_red = match.events.filter(event_type="red_card", player__in=team2.players.all()).count()

        result.append(match_to_schema(match))  # passzolhatod a számokat is, ha módosítod a match_to_schema-t
    return result