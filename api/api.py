from ninja import NinjaAPI, Router
from .models import Team, Tournament, Match, Event, Player, Profile 
from .schemas import TeamSchema, TopScorerSchema, TournamentSchema, PlayerSchema, MatchSchema, EventSchema, StandingSchema, AllEventsSchema, PlayerStatSchema
from django.shortcuts import get_object_or_404
from .utils import process_matches, get_goal_scorers, calculate_player_stats

app = NinjaAPI()
router = Router()
app.add_router("/", router)

# Minden bajnokság lekérdezése
@router.get("/tournaments", response=list[TournamentSchema])
def get_tournaments(request):
    return Tournament.objects.all()

# Bajnokság lekérdezése
@router.get("/tournaments/{tournament_id}", response=TournamentSchema)
def get_tournament(request, tournament_id: int):
    device = get_object_or_404(Tournament, id=tournament_id)
    return device

# Bajnokság állása
@router.get("/tournaments/{tournament_id}/standings", response=list[StandingSchema])
def get_tournament_standings(request, tournament_id: int):
    bajnoksag = get_object_or_404(Tournament, id=tournament_id)
    return process_matches(bajnoksag)

# Bajnokság meccsei
@router.get("/tournaments/{tournament_id}/matches", response=list[MatchSchema])
def get_tournament_matches(request, tournament_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    return Match.objects.filter(tournament=tournament)

# Bajnokság csapatai
@router.get("/tournaments/{tournament_id}/teams", response=list[TeamSchema])
def get_tournament_teams(request, tournament_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    return Team.objects.filter(tournament=tournament)

# Adott csapat a bajnokságban
@router.get("/tournaments/{tournament_id}/teams/{team_id}", response=TeamSchema)
def get_tournament_team(request, tournament_id: int, team_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    team = get_object_or_404(Team, id=team_id, tournament=tournament)
    return team

# Adott csapat játékosai a bajnokságban
@router.get("/tournaments/{tournament_id}/teams/{team_id}/players", response=list[PlayerSchema])
def get_tournament_team_players(request, tournament_id: int, team_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    team = get_object_or_404(Team, id=team_id, tournament=tournament)
    return Player.objects.filter(team=team)


# Adott csapat meccsei a bajnokságban
@router.get("/tournaments/{tournament_id}/teams/{team_id}/matches", response=list[MatchSchema])
def get_tournament_team_matches(request, tournament_id: int, team_id: int): 
    tournament = get_object_or_404(Tournament, id=tournament_id)
    team = get_object_or_404(Team, id=team_id, tournament=tournament)
    return Match.objects.filter(tournament=tournament, team1=team) | Match.objects.filter(tournament=tournament, team2=team)

# Bajnokság góllövői
@router.get("/tournaments/{tournament_id}/topscorers", response=list[TopScorerSchema])
def get_tournament_top_scorers(request, tournament_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    matches = Match.objects.filter(tournament=tournament)
    goals = Event.objects.filter(event_type='goal').filter(match__in=matches)
    return get_goal_scorers(goals)
    
# Összes gól a bajnokságban
@router.get("/tournaments/{tournament_id}/goals", response=list[EventSchema])
def get_all_goals(request, tournament_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    goals = Event.objects.filter(event_type='goal', match__tournament=tournament)
    return goals

# Összes sárga lap a bajnokságban
@router.get("/tournaments/{tournament_id}/yellow_cards", response=list[EventSchema])
def get_all_yellow_cards(request, tournament_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    yellow_cards = Event.objects.filter(event_type='yellow_card', match__tournament=tournament)
    return yellow_cards

# Összes piros lap a bajnokságban
@router.get("/tournaments/{tournament_id}/red_cards", response=list[EventSchema])
def get_all_red_cards(request, tournament_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    red_cards = Event.objects.filter(event_type='red_card', match__tournament=tournament)
    return red_cards

# Összes játékos a bajnokságban
@router.get("/tournaments/{tournament_id}/players", response=list[PlayerSchema])
def get_tournament_players(request, tournament_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    players = Player.objects.filter(team__tournament=tournament)
    return players

# Adott játékos a bajnokságban
@router.get("/tournaments/{tournament_id}/players/{player_id}", response=PlayerSchema)
def get_tournament_player(request, tournament_id: int, player_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    player = get_object_or_404(Player, id=player_id, team__tournament=tournament)
    return player

# Adott játékos eventjei a bajnokságban
@router.get("/tournaments/{tournament_id}/players/{player_id}/events", response=AllEventsSchema)
def get_tournament_player_events(request, tournament_id: int, player_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    player = get_object_or_404(Player, id=player_id, team__tournament=tournament)
    events = Event.objects.filter(player=player, match__tournament=tournament)

    return AllEventsSchema(
        goals=events.filter(event_type="goal"),
        yellow_cards=events.filter(event_type="yellow_card"),
        red_cards=events.filter(event_type="red_card"),
    )
 

# Minden csapat lekérdezése
@router.get("/teams", response=list[TeamSchema])
def get_teams(request):
    return Team.objects.all()

# Csapat lekérdezése
@router.get("/teams/{team_id}", response=TeamSchema)
def get_team(request, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    return team


# Adott csapat eventjei a bajnokságban
@router.get("/tournaments/{tournament_id}/teams/{team_id}/events", response=AllEventsSchema)
def get_tournament_team_events(request, tournament_id: int, team_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    team = get_object_or_404(Team, id=team_id, tournament=tournament)
    events = Event.objects.filter(match__tournament=tournament).filter(
    match__team1=team
    ) | Event.objects.filter(match__tournament=tournament).filter(
        match__team2=team
    )

    return AllEventsSchema(
        goals=events.filter(event_type="goal"),
        yellow_cards=events.filter(event_type="yellow_card"),
        red_cards=events.filter(event_type="red_card"),
    )  

# Csapat játékosai
@router.get("/teams/{team_id}/players", response=list[PlayerSchema])
def get_team_players(request, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    return Player.objects.filter(team=team), Team.objects.filter(id=team_id)


# Minden player lekérdezése
@router.get("/players", response=list[PlayerSchema])
def get_players(request):
    players = Player.objects.all()
    return players

# Player lekérdezése
@router.get("/players/{player_id}", response=PlayerSchema)
def get_player(request, player_id: int):
    player = get_object_or_404(Player, id=player_id)
    return player

#Player összes eventje
@router.get("/players/{player_id}/events", response=AllEventsSchema)
def get_player_events(request, player_id: int):
    player = get_object_or_404(Player, id=player_id)
    events = Event.objects.filter(player=player)

    return AllEventsSchema(
        goals=events.filter(event_type="goal"),
        yellow_cards=events.filter(event_type="yellow_card"),
        red_cards=events.filter(event_type="red_card"),
    )


# Minden meccs lekérdezése
@router.get("/matches", response=list[MatchSchema])
def get_matches(request):
    return Match.objects.all()

# Meccs lekérdezése
@router.get("/matches/{match_id}", response=MatchSchema)
def get_match(request, match_id: int):
    match = get_object_or_404(Match, id=match_id)
    return match

# Minden gól lekérdezése
@router.get("/goals", response=list[EventSchema])
def get_goals(request):
    goals = Event.objects.filter(event_type='goal')
    return goals

# Gólok lekérdezése
@router.get("/goals/{goal_id}", response=EventSchema)
def get_goal(request, goal_id: int):
    goal = get_object_or_404(Event, id=goal_id)
    return goal


# Sárga lapok lekérdezése
@router.get("/yellow_cards", response=list[EventSchema])
def get_cards(request):
    cards = Event.objects.filter(event_type='yellow_card')
    return cards

# Sárga lap lekérdezése
@router.get("/yellow_cards/{card_id}", response=EventSchema)
def get_card(request, card_id: int):
    card = get_object_or_404(Event, id=card_id)
    return card


# Piros lapok lekérdezése
@router.get("/red_cards", response=list[EventSchema])
def get_red_cards(request):
    cards = Event.objects.filter(event_type='red_card')
    return cards

# Piros lap lekérdezése
@router.get("/red_cards/{card_id}", response=EventSchema)
def get_red_card(request, card_id: int):
    card = get_object_or_404(Event, id=card_id)
    return card


# Meccs gólok
@router.get("/matches/{match_id}/goals", response=list[EventSchema])
def get_match_goals(request, match_id: int):
    match = get_object_or_404(Match, id=match_id)
    match_goals = Event.objects.filter(event_type='goal').filter(match=match)
    return match_goals

