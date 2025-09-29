from ninja import NinjaAPI, Router
from .models import Team, Tournament, Match, Event, Player, Profile, Round
from .schemas import TeamSchema, TeamCreateSchema, TeamUpdateSchema, TopScorerSchema, TournamentSchema, TournamentCreateSchema, TournamentUpdateSchema, PlayerSchema, MatchSchema, EventSchema, StandingSchema, AllEventsSchema, RoundSchema, ProfileSchema
from django.shortcuts import get_object_or_404
from django.db import models
from .utils import process_matches, get_goal_scorers, get_latest_tournament
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

# Aktuális (legújabb) bajnokság
@router.get("/tournament/current", response=TournamentSchema)
def get_current_tournament(request):
    return get_latest_tournament()

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

# Bajnokság állása (legújabb bajnokság)
@router.get("/standings", response=list[StandingSchema])
def get_standings(request):
    tournament = get_latest_tournament()
    return process_matches(tournament)

# Bajnokság meccsei (legújabb bajnokság)  
@router.get("/matches", response=list[MatchSchema])
def get_matches(request):
    tournament = get_latest_tournament()
    return Match.objects.filter(tournament=tournament)

# Bajnokság csapatai (legújabb bajnokság)
@router.get("/teams", response=list[TeamSchema])
def get_teams(request):
    tournament = get_latest_tournament()
    return Team.objects.filter(tournament=tournament)

# Csapat lekérdezése (legújabb bajnokságból)
@router.get("/teams/{team_id}", response=TeamSchema)  
def get_team(request, team_id: int):
    tournament = get_latest_tournament()
    team = get_object_or_404(Team, id=team_id, tournament=tournament)
    return team

# Csapat játékosai (legújabb bajnokság)
@router.get("/teams/{team_id}/players", response=list[PlayerSchema])
def get_team_players(request, team_id: int):
    tournament = get_latest_tournament()
    team = get_object_or_404(Team, id=team_id, tournament=tournament)
    return team.players.all()


# Csapat meccsei (legújabb bajnokság)
@router.get("/teams/{team_id}/matches", response=list[MatchSchema])
def get_team_matches(request, team_id: int):
    tournament = get_latest_tournament()
    team = get_object_or_404(Team, id=team_id, tournament=tournament)
    return Match.objects.filter(tournament=tournament).filter(
        models.Q(team1=team) | models.Q(team2=team)
    )

# Góllövők (legújabb bajnokság)
@router.get("/topscorers", response=list[TopScorerSchema])
def get_top_scorers(request):
    tournament = get_latest_tournament()
    matches = Match.objects.filter(tournament=tournament)
    goals = Event.objects.filter(event_type='goal').filter(match__in=matches)
    return get_goal_scorers(goals)

# Fordulók (legújabb bajnokság)
@router.get("/rounds", response=list[RoundSchema])
def get_rounds(request):
    tournament = get_latest_tournament()
    return Round.objects.filter(tournament=tournament).order_by('number')

# Forduló lekérdezése szám szerint (legújabb bajnokság)
@router.get("/rounds/{round_number}", response=RoundSchema)
def get_round(request, round_number: int):
    tournament = get_latest_tournament()
    round_obj = get_object_or_404(Round, tournament=tournament, number=round_number)
    return round_obj

# Forduló meccsei (legújabb bajnokság)
@router.get("/rounds/{round_number}/matches", response=list[MatchSchema])
def get_round_matches(request, round_number: int):
    tournament = get_latest_tournament()
    round_obj = get_object_or_404(Round, tournament=tournament, number=round_number)
    return Match.objects.filter(round_obj=round_obj)
    
# Összes gól (legújabb bajnokság)
@router.get("/goals", response=list[EventSchema])
def get_goals(request):
    tournament = get_latest_tournament()
    matches = Match.objects.filter(tournament=tournament)
    goals = Event.objects.filter(event_type='goal').filter(match__in=matches)
    return goals

# Összes sárga lap (legújabb bajnokság)
@router.get("/yellow_cards", response=list[EventSchema])
def get_yellow_cards(request):
    tournament = get_latest_tournament()
    matches = Match.objects.filter(tournament=tournament)
    yellow_cards = Event.objects.filter(event_type='yellow_card').filter(match__in=matches)
    return yellow_cards

# Összes piros lap (legújabb bajnokság)
@router.get("/red_cards", response=list[EventSchema])
def get_red_cards(request):
    tournament = get_latest_tournament()
    matches = Match.objects.filter(tournament=tournament)
    red_cards = Event.objects.filter(event_type='red_card').filter(match__in=matches)
    return red_cards

# Összes játékos (legújabb bajnokság)
@router.get("/players", response=list[PlayerSchema])
def get_players(request):
    tournament = get_latest_tournament()
    players = Player.objects.filter(team__tournament=tournament)
    return players

# Játékos lekérdezése (legújabb bajnokság)
@router.get("/players/{player_id}", response=PlayerSchema)
def get_player(request, player_id: int):
    tournament = get_latest_tournament()
    player = get_object_or_404(Player, id=player_id, team__tournament=tournament)
    return player

# Játékos eventjei (legújabb bajnokság)
@router.get("/players/{player_id}/events", response=AllEventsSchema)
def get_player_events(request, player_id: int):
    tournament = get_latest_tournament()
    player = get_object_or_404(Player, id=player_id, team__tournament=tournament)
    matches = Match.objects.filter(tournament=tournament)
    events = Event.objects.filter(player=player).filter(match__in=matches)

    return AllEventsSchema(
        goals=events.filter(event_type="goal"),
        yellow_cards=events.filter(event_type="yellow_card"),
        red_cards=events.filter(event_type="red_card"),
    )
 

# Minden csapat lekérdezése (minden bajnokságból) - admin use
@router.get("/admin/teams/all", response=list[TeamSchema])
def get_all_teams(request):
    return Team.objects.all()

# Csapat lekérdezése (admin - bármely bajnokságból)
@router.get("/admin/teams/{team_id}", response=TeamSchema)
def get_any_team(request, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    return team

# Aktív csapatok lekérdezése (legújabb bajnokság)
@router.get("/teams/active", response=list[TeamSchema])
def get_active_teams(request):
    tournament = get_latest_tournament()
    return Team.objects.filter(active=True, tournament=tournament)

# Inaktív csapatok lekérdezése (legújabb bajnokság)
@router.get("/teams/inactive", response=list[TeamSchema])
def get_inactive_teams(request):
    tournament = get_latest_tournament()
    return Team.objects.filter(active=False, tournament=tournament)

# Új csapat létrehozása (legújabb bajnokság)
@router.post("/teams", response=TeamSchema)
def create_team(request, payload: TeamCreateSchema):
    team_data = payload.dict()
    # Remove tournament_id if it exists - we'll use latest tournament
    team_data.pop('tournament_id', None)
    tournament = get_latest_tournament()
    
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


# Csapat eventjei (legújabb bajnokság)
@router.get("/teams/{team_id}/events", response=AllEventsSchema)
def get_team_events(request, team_id: int):
    tournament = get_latest_tournament()
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

# Csapat játékosai (admin - bármely bajnokságból)
@router.get("/admin/teams/{team_id}/players", response=list[PlayerSchema])
def get_any_team_players(request, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    return team.players.all()


# Minden player lekérdezése (admin - minden bajnokságból)
@router.get("/admin/players/all", response=list[PlayerSchema])
def get_all_players(request):
    players = Player.objects.all()
    return players

# Player lekérdezése (admin - bármely bajnokságból)
@router.get("/admin/players/{player_id}", response=PlayerSchema)
def get_any_player(request, player_id: int):
    player = get_object_or_404(Player, id=player_id)
    return player

# Csapatkapitányok lekérdezése
@router.get("/players/captains", response=list[PlayerSchema])
def get_captains(request):
    return Player.objects.filter(csk=True)

# Player összes eventje (admin - minden bajnokságból)
@router.get("/admin/players/{player_id}/events", response=AllEventsSchema)
def get_all_player_events(request, player_id: int):
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


# Minden meccs lekérdezése (admin - minden bajnokságból)
@router.get("/admin/matches/all", response=list[MatchSchema])
def get_all_matches(request):
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

# Minden gól lekérdezése (admin - minden bajnokságból)
@router.get("/admin/goals/all", response=list[EventSchema])
def get_all_goals_admin(request):
    goals = Event.objects.filter(event_type='goal')
    return goals

# Gólok lekérdezése
@router.get("/goals/{goal_id}", response=EventSchema)
def get_goal(request, goal_id: int):
    goal = get_object_or_404(Event, id=goal_id)
    return goal


# Sárga lapok lekérdezése (admin - minden bajnokságból)
@router.get("/admin/yellow_cards/all", response=list[EventSchema])
def get_all_yellow_cards_admin(request):
    cards = Event.objects.filter(event_type='yellow_card')
    return cards

# Sárga lap lekérdezése
@router.get("/yellow_cards/{card_id}", response=EventSchema)
def get_card(request, card_id: int):
    card = get_object_or_404(Event, id=card_id)
    return card


# Piros lapok lekérdezése (admin - minden bajnokságból)
@router.get("/admin/red_cards/all", response=list[EventSchema])
def get_all_red_cards_admin(request):
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

# Minden forduló lekérdezése (admin)
@router.get("/admin/rounds/all", response=list[RoundSchema])
def get_all_rounds(request):
    return Round.objects.all().order_by('tournament', 'number')

# Forduló lekérdezése ID alapján (admin)
@router.get("/admin/rounds/{round_id}", response=RoundSchema)
def get_round_by_id(request, round_id: int):
    round_obj = get_object_or_404(Round, id=round_id)
    return round_obj

