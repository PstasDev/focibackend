from ninja import NinjaAPI, Router
from .models import Team, Tournament, Match, Event, Player, Profile, Round
from .schemas import TeamSchema, TeamCreateSchema, TeamUpdateSchema, TopScorerSchema, TournamentSchema, TournamentCreateSchema, TournamentUpdateSchema, PlayerSchema, MatchSchema, EventSchema, StandingSchema, AllEventsSchema, RoundSchema, ProfileSchema
from django.shortcuts import get_object_or_404
from django.db import models
from .utils import process_matches, get_goal_scorers
from datetime import datetime

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

# Regisztrációra nyitott bajnokságok
@router.get("/tournaments/open-for-registration", response=list[TournamentSchema])
def get_open_tournaments(request):
    return Tournament.objects.filter(registration_open=True)

# Új bajnokság létrehozása
@router.post("/tournaments", response=TournamentSchema)
def create_tournament(request, payload: TournamentCreateSchema):
    tournament_data = payload.dict(exclude_unset=True)
    
    # Convert date strings to date objects if provided
    if 'start_date' in tournament_data and tournament_data['start_date']:
        tournament_data['start_date'] = datetime.strptime(tournament_data['start_date'], '%Y-%m-%d').date()
    if 'end_date' in tournament_data and tournament_data['end_date']:
        tournament_data['end_date'] = datetime.strptime(tournament_data['end_date'], '%Y-%m-%d').date()
    if 'registration_deadline' in tournament_data and tournament_data['registration_deadline']:
        tournament_data['registration_deadline'] = datetime.strptime(tournament_data['registration_deadline'], '%Y-%m-%d %H:%M:%S')
    
    tournament = Tournament.objects.create(**tournament_data)
    return tournament

# Bajnokság frissítése
@router.put("/tournaments/{tournament_id}", response=TournamentSchema)
def update_tournament(request, tournament_id: int, payload: TournamentUpdateSchema):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    update_data = payload.dict(exclude_unset=True)
    
    # Convert date strings to date objects if provided
    if 'start_date' in update_data and update_data['start_date']:
        update_data['start_date'] = datetime.strptime(update_data['start_date'], '%Y-%m-%d').date()
    if 'end_date' in update_data and update_data['end_date']:
        update_data['end_date'] = datetime.strptime(update_data['end_date'], '%Y-%m-%d').date()
    if 'registration_deadline' in update_data and update_data['registration_deadline']:
        update_data['registration_deadline'] = datetime.strptime(update_data['registration_deadline'], '%Y-%m-%d %H:%M:%S')
    
    for field, value in update_data.items():
        setattr(tournament, field, value)
    
    tournament.save()
    return tournament

# Bajnokság részleges frissítése
@router.patch("/tournaments/{tournament_id}", response=TournamentSchema)
def patch_tournament(request, tournament_id: int, payload: TournamentUpdateSchema):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    update_data = payload.dict(exclude_unset=True)
    
    # Convert date strings to date objects if provided
    if 'start_date' in update_data and update_data['start_date']:
        update_data['start_date'] = datetime.strptime(update_data['start_date'], '%Y-%m-%d').date()
    if 'end_date' in update_data and update_data['end_date']:
        update_data['end_date'] = datetime.strptime(update_data['end_date'], '%Y-%m-%d').date()
    if 'registration_deadline' in update_data and update_data['registration_deadline']:
        update_data['registration_deadline'] = datetime.strptime(update_data['registration_deadline'], '%Y-%m-%d %H:%M:%S')
    
    for field, value in update_data.items():
        setattr(tournament, field, value)
    
    tournament.save()
    return tournament

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
    return team.players.all()


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

# Bajnokság fordulói
@router.get("/tournaments/{tournament_id}/rounds", response=list[RoundSchema])
def get_tournament_rounds(request, tournament_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    return Round.objects.filter(tournament=tournament).order_by('number')

# Adott forduló lekérdezése
@router.get("/tournaments/{tournament_id}/rounds/{round_number}", response=RoundSchema)
def get_tournament_round(request, tournament_id: int, round_number: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    round_obj = get_object_or_404(Round, tournament=tournament, number=round_number)
    return round_obj

# Adott forduló meccsei
@router.get("/tournaments/{tournament_id}/rounds/{round_number}/matches", response=list[MatchSchema])
def get_tournament_round_matches(request, tournament_id: int, round_number: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    round_obj = get_object_or_404(Round, tournament=tournament, number=round_number)
    return Match.objects.filter(round_obj=round_obj)
    
# Összes gól a bajnokságban
@router.get("/tournaments/{tournament_id}/goals", response=list[EventSchema])
def get_all_goals(request, tournament_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    matches = Match.objects.filter(tournament=tournament)
    goals = Event.objects.filter(event_type='goal').filter(match__in=matches)
    return goals

# Összes sárga lap a bajnokságban
@router.get("/tournaments/{tournament_id}/yellow_cards", response=list[EventSchema])
def get_all_yellow_cards(request, tournament_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    matches = Match.objects.filter(tournament=tournament)
    yellow_cards = Event.objects.filter(event_type='yellow_card').filter(match__in=matches)
    return yellow_cards

# Összes piros lap a bajnokságban
@router.get("/tournaments/{tournament_id}/red_cards", response=list[EventSchema])
def get_all_red_cards(request, tournament_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    matches = Match.objects.filter(tournament=tournament)
    red_cards = Event.objects.filter(event_type='red_card').filter(match__in=matches)
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
    matches = Match.objects.filter(tournament=tournament)
    events = Event.objects.filter(player=player).filter(match__in=matches)

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

# Aktív csapatok lekérdezése
@router.get("/teams/active", response=list[TeamSchema])
def get_active_teams(request):
    return Team.objects.filter(active=True)

# Inaktív csapatok lekérdezése
@router.get("/teams/inactive", response=list[TeamSchema])
def get_inactive_teams(request):
    return Team.objects.filter(active=False)

# Új csapat létrehozása
@router.post("/teams", response=TeamSchema)
def create_team(request, payload: TeamCreateSchema):
    team_data = payload.dict()
    tournament_id = team_data.pop('tournament_id')
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    team = Team.objects.create(tournament=tournament, **team_data)
    return team

# Csapat frissítése
@router.put("/teams/{team_id}", response=TeamSchema)
def update_team(request, team_id: int, payload: TeamUpdateSchema):
    team = get_object_or_404(Team, id=team_id)
    
    update_data = payload.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(team, field, value)
    
    team.save()
    return team

# Csapat részleges frissítése
@router.patch("/teams/{team_id}", response=TeamSchema)
def patch_team(request, team_id: int, payload: TeamUpdateSchema):
    team = get_object_or_404(Team, id=team_id)
    
    update_data = payload.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(team, field, value)
    
    team.save()
    return team


# Adott csapat eventjei a bajnokságban
@router.get("/tournaments/{tournament_id}/teams/{team_id}/events", response=AllEventsSchema)
def get_tournament_team_events(request, tournament_id: int, team_id: int):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    team = get_object_or_404(Team, id=team_id, tournament=tournament)
    matches = Match.objects.filter(tournament=tournament).filter(
        models.Q(team1=team) | models.Q(team2=team)
    )
    events = Event.objects.filter(match__in=matches)

    return AllEventsSchema(
        goals=events.filter(event_type="goal"),
        yellow_cards=events.filter(event_type="yellow_card"),
        red_cards=events.filter(event_type="red_card"),
    )  

# Csapat játékosai
@router.get("/teams/{team_id}/players", response=list[PlayerSchema])
def get_team_players(request, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    return team.players.all()


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

# Csapatkapitányok lekérdezése
@router.get("/players/captains", response=list[PlayerSchema])
def get_captains(request):
    return Player.objects.filter(csk=True)

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

# Minden profil lekérdezése
@router.get("/profiles", response=list[ProfileSchema])
def get_profiles(request):
    return Profile.objects.all()

# Profil lekérdezése
@router.get("/profiles/{profile_id}", response=ProfileSchema)
def get_profile(request, profile_id: int):
    profile = get_object_or_404(Profile, id=profile_id)
    return profile

# Bírói profilok lekérdezése
@router.get("/profiles/referees", response=list[ProfileSchema])
def get_referee_profiles(request):
    return Profile.objects.filter(biro=True)


# Minden meccs lekérdezése
@router.get("/matches", response=list[MatchSchema])
def get_matches(request):
    return Match.objects.all()

# Meccs lekérdezése
@router.get("/matches/{match_id}", response=MatchSchema)
def get_match(request, match_id: int):
    match = get_object_or_404(Match, id=match_id)
    return match

# Adott bíró meccsei
@router.get("/profiles/{profile_id}/matches", response=list[MatchSchema])
def get_referee_matches(request, profile_id: int):
    profile = get_object_or_404(Profile, id=profile_id, biro=True)
    return Match.objects.filter(referee=profile)

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
    match_goals = match.events.filter(event_type='goal')
    return match_goals

# Meccs összes eventje
@router.get("/matches/{match_id}/events", response=AllEventsSchema)
def get_match_events(request, match_id: int):
    match = get_object_or_404(Match, id=match_id)
    events = match.events.all()

    return AllEventsSchema(
        goals=events.filter(event_type="goal"),
        yellow_cards=events.filter(event_type="yellow_card"),
        red_cards=events.filter(event_type="red_card"),
    )

# Meccs sárga lapok
@router.get("/matches/{match_id}/yellow_cards", response=list[EventSchema])
def get_match_yellow_cards(request, match_id: int):
    match = get_object_or_404(Match, id=match_id)
    return match.events.filter(event_type='yellow_card')

# Meccs piros lapok
@router.get("/matches/{match_id}/red_cards", response=list[EventSchema])
def get_match_red_cards(request, match_id: int):
    match = get_object_or_404(Match, id=match_id)
    return match.events.filter(event_type='red_card')

# Minden forduló lekérdezése
@router.get("/rounds", response=list[RoundSchema])
def get_rounds(request):
    return Round.objects.all().order_by('tournament', 'number')

# Forduló lekérdezése
@router.get("/rounds/{round_id}", response=RoundSchema)
def get_round(request, round_id: int):
    round_obj = get_object_or_404(Round, id=round_id)
    return round_obj

