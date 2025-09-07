from ninja import NinjaAPI, Router
from .models import Team, Tournament, Match, Event, Player, Profile 
from .schemas import TeamSchema, TopScorerSchema, TournamentSchema, PlayerSchema, MatchSchema, EventSchema, StandingSchema
from django.shortcuts import get_object_or_404
from .utils import process_matches, get_goal_scorers

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

# Bajnokság góllövői
@router.get("/tournaments/{tournament_id}/topscorers", response=list[TopScorerSchema])
def get_tournament_top_scorers(request, tournament_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    matches = Match.objects.filter(tournament=tournament)
    goals = Event.objects.filter(event_type='goal').filter(match__in=matches)
    return get_goal_scorers(goals)
    

# Minden csapat lekérdezése
@router.get("/teams", response=list[TeamSchema])
def get_teams(request):
    return Team.objects.all()

# Csapat lekérdezése
@router.get("/teams/{team_id}", response=TeamSchema)
def get_team(request, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    return team

# Minden player lekérdezése
@router.get("/players", response=list[PlayerSchema])
def get_players(request):
    players = Player.objects.all()
    return players

# Minden player lekérdezése
@router.get("/players/{player_id}", response=PlayerSchema)
def get_player(request, player_id: int):
    player = get_object_or_404(Player, id=player_id)
    return player

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

