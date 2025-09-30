from ninja import NinjaAPI, Router
from .models import *
from django.contrib.auth.models import User
from .schemas import *
from django.shortcuts import get_object_or_404
from django.db import models
from .utils import process_matches, get_goal_scorers, get_latest_tournament
from datetime import datetime


app = NinjaAPI()
router = Router()
app.add_router("/", router) 

# Felhasználók
@router.get("/users/{user_id}", response=UserSchema)
def get_user(request, user_id: int):
    return get_object_or_404(User, id=user_id)

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

# # Új bajnokság létrehozása
# @router.post("/tournaments", response=TournamentSchema)
# def create_tournament(request, payload: TournamentCreateSchema):
#     tournament_data = payload.dict(exclude_unset=True)
    
#     # Convert date strings to date objects if provided
#     if 'start_date' in tournament_data and tournament_data['start_date']:
#         tournament_data['start_date'] = datetime.strptime(tournament_data['start_date'], '%Y-%m-%d').date()
#     if 'end_date' in tournament_data and tournament_data['end_date']:
#         tournament_data['end_date'] = datetime.strptime(tournament_data['end_date'], '%Y-%m-%d').date()
#     if 'registration_deadline' in tournament_data and tournament_data['registration_deadline']:
#         tournament_data['registration_deadline'] = datetime.strptime(tournament_data['registration_deadline'], '%Y-%m-%d %H:%M:%S')
    
#     tournament = Tournament.objects.create(**tournament_data)
#     return tournament

# Bajnokság frissítése
# @router.put("/tournaments/{tournament_id}", response=TournamentSchema)
# def update_tournament(request, tournament_id: int, payload: TournamentUpdateSchema):
#     tournament = get_object_or_404(Tournament, id=tournament_id)
    
#     update_data = payload.dict(exclude_unset=True)
    
#     # Convert date strings to date objects if provided
#     if 'start_date' in update_data and update_data['start_date']:
#         update_data['start_date'] = datetime.strptime(update_data['start_date'], '%Y-%m-%d').date()
#     if 'end_date' in update_data and update_data['end_date']:
#         update_data['end_date'] = datetime.strptime(update_data['end_date'], '%Y-%m-%d').date()
#     if 'registration_deadline' in update_data and update_data['registration_deadline']:
#         update_data['registration_deadline'] = datetime.strptime(update_data['registration_deadline'], '%Y-%m-%d %H:%M:%S')
    
#     for field, value in update_data.items():
#         setattr(tournament, field, value)
    
#     tournament.save()
#     return tournament

# Bajnokság részleges frissítése
# @router.patch("/tournaments/{tournament_id}", response=TournamentSchema)
# def patch_tournament(request, tournament_id: int, payload: TournamentUpdateSchema):
#     tournament = get_object_or_404(Tournament, id=tournament_id)
    
#     update_data = payload.dict(exclude_unset=True)
    
#     # Convert date strings to date objects if provided
#     if 'start_date' in update_data and update_data['start_date']:
#         update_data['start_date'] = datetime.strptime(update_data['start_date'], '%Y-%m-%d').date()
#     if 'end_date' in update_data and update_data['end_date']:
#         update_data['end_date'] = datetime.strptime(update_data['end_date'], '%Y-%m-%d').date()
#     if 'registration_deadline' in update_data and update_data['registration_deadline']:
#         update_data['registration_deadline'] = datetime.strptime(update_data['registration_deadline'], '%Y-%m-%d %H:%M:%S')
    
#     for field, value in update_data.items():
#         setattr(tournament, field, value)
    
#     tournament.save()
#     return tournament

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
@router.get("/teams", response=list[TeamExtendedSchema])
def get_teams(request):
    tournament = get_latest_tournament()
    teams = Team.objects.filter(tournament=tournament)
    return [
        TeamExtendedSchema(
            id=team.id,
            name=team.name,
            start_year=team.start_year,
            tagozat=team.tagozat,
            color=team.get_team_color(),
            active=team.active,
            players=[
                PlayerExtendedSchema(
                    id=player.id,
                    name=player.name,
                    csk=player.csk,
                    start_year=player.start_year,
                    tagozat=player.tagozat,
                    effective_start_year=player.get_start_year(),
                    effective_tagozat=player.get_tagozat()
                ) for player in team.players.all()
            ]
        ) for team in teams
    ]

# Csapat lekérdezése (legújabb bajnokságból)
@router.get("/teams/{team_id}", response=TeamExtendedSchema)  
def get_team(request, team_id: int):
    tournament = get_latest_tournament()
    team = get_object_or_404(Team, id=team_id, tournament=tournament)
    return TeamExtendedSchema(
        id=team.id,
        name=team.name,
        start_year=team.start_year,
        tagozat=team.tagozat,
        color=team.get_team_color(),
        active=team.active,
        players=[
            PlayerExtendedSchema(
                id=player.id,
                name=player.name,
                csk=player.csk,
                start_year=player.start_year,
                tagozat=player.tagozat,
                effective_start_year=player.get_start_year(),
                effective_tagozat=player.get_tagozat()
            ) for player in team.players.all()
        ]
    )

# Csapat játékosai (legújabb bajnokság)
@router.get("/teams/{team_id}/players", response=list[PlayerExtendedSchema])
def get_team_players(request, team_id: int):
    tournament = get_latest_tournament()
    team = get_object_or_404(Team, id=team_id, tournament=tournament)
    players = team.players.all()
    return [
        PlayerExtendedSchema(
            id=player.id,
            name=player.name,
            csk=player.csk,
            start_year=player.start_year,
            tagozat=player.tagozat,
            effective_start_year=player.get_start_year(),
            effective_tagozat=player.get_tagozat()
        ) for player in players
    ]


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
@router.get("/players", response=list[PlayerExtendedSchema])
def get_players(request):
    tournament = get_latest_tournament()
    players = Player.objects.filter(team__tournament=tournament)
    return [
        PlayerExtendedSchema(
            id=player.id,
            name=player.name,
            csk=player.csk,
            start_year=player.start_year,
            tagozat=player.tagozat,
            effective_start_year=player.get_start_year(),
            effective_tagozat=player.get_tagozat()
        ) for player in players
    ]

# Játékos lekérdezése (legújabb bajnokság)
@router.get("/players/{player_id}", response=PlayerExtendedSchema)
def get_player(request, player_id: int):
    tournament = get_latest_tournament()
    player = get_object_or_404(Player, id=player_id, team__tournament=tournament)
    return PlayerExtendedSchema(
        id=player.id,
        name=player.name,
        csk=player.csk,
        start_year=player.start_year,
        tagozat=player.tagozat,
        effective_start_year=player.get_start_year(),
        effective_tagozat=player.get_tagozat()
    )

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
@router.get("/admin/teams/all", response=list[TeamExtendedSchema])
def get_all_teams(request):
    teams = Team.objects.all()
    return [
        TeamExtendedSchema(
            id=team.id,
            name=team.name,
            start_year=team.start_year,
            tagozat=team.tagozat,
            color=team.get_team_color(),
            active=team.active,
            players=[
                PlayerExtendedSchema(
                    id=player.id,
                    name=player.name,
                    csk=player.csk,
                    start_year=player.start_year,
                    tagozat=player.tagozat,
                    effective_start_year=player.get_start_year(),
                    effective_tagozat=player.get_tagozat()
                ) for player in team.players.all()
            ]
        ) for team in teams
    ]

# Csapat lekérdezése (admin - bármely bajnokságból)
@router.get("/admin/teams/{team_id}", response=TeamExtendedSchema)
def get_any_team(request, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    return TeamExtendedSchema(
        id=team.id,
        name=team.name,
        start_year=team.start_year,
        tagozat=team.tagozat,
        color=team.get_team_color(),
        active=team.active,
        players=[
            PlayerExtendedSchema(
                id=player.id,
                name=player.name,
                csk=player.csk,
                start_year=player.start_year,
                tagozat=player.tagozat,
                effective_start_year=player.get_start_year(),
                effective_tagozat=player.get_tagozat()
            ) for player in team.players.all()
        ]
    )

# Aktív csapatok lekérdezése (legújabb bajnokság)
@router.get("/teams/active", response=list[TeamExtendedSchema])
def get_active_teams(request):
    tournament = get_latest_tournament()
    teams = Team.objects.filter(active=True, tournament=tournament)
    return [
        TeamExtendedSchema(
            id=team.id,
            name=team.name,
            start_year=team.start_year,
            tagozat=team.tagozat,
            color=team.get_team_color(),
            active=team.active,
            players=[
                PlayerExtendedSchema(
                    id=player.id,
                    name=player.name,
                    csk=player.csk,
                    start_year=player.start_year,
                    tagozat=player.tagozat,
                    effective_start_year=player.get_start_year(),
                    effective_tagozat=player.get_tagozat()
                ) for player in team.players.all()
            ]
        ) for team in teams
    ]

# Inaktív csapatok lekérdezése (legújabb bajnokság)
@router.get("/teams/inactive", response=list[TeamExtendedSchema])
def get_inactive_teams(request):
    tournament = get_latest_tournament()
    teams = Team.objects.filter(active=False, tournament=tournament)
    return [
        TeamExtendedSchema(
            id=team.id,
            name=team.name,
            start_year=team.start_year,
            tagozat=team.tagozat,
            color=team.get_team_color(),
            active=team.active,
            players=[
                PlayerExtendedSchema(
                    id=player.id,
                    name=player.name,
                    csk=player.csk,
                    start_year=player.start_year,
                    tagozat=player.tagozat,
                    effective_start_year=player.get_start_year(),
                    effective_tagozat=player.get_tagozat()
                ) for player in team.players.all()
            ]
        ) for team in teams
    ]

# Új csapat létrehozása (legújabb bajnokság)
# @router.post("/teams", response=TeamExtendedSchema)
# def create_team(request, payload: TeamCreateSchema):
#     team_data = payload.dict()
#     # Remove tournament_id if it exists - we'll use latest tournament
#     team_data.pop('tournament_id', None)
#     tournament = get_latest_tournament()
    
#     team = Team.objects.create(tournament=tournament, **team_data)
#     return TeamExtendedSchema(
#         id=team.id,
#         name=team.name,
#         start_year=team.start_year,
#         tagozat=team.tagozat,
#         color=team.get_team_color(),
#         active=team.active,
#         players=[
#             PlayerExtendedSchema(
#                 id=player.id,
#                 name=player.name,
#                 csk=player.csk,
#                 start_year=player.start_year,
#                 tagozat=player.tagozat,
#                 effective_start_year=player.get_start_year(),
#                 effective_tagozat=player.get_tagozat()
#             ) for player in team.players.all()
#         ]
#     )

# Csapat frissítése
# @router.put("/teams/{team_id}", response=TeamExtendedSchema)
# def update_team(request, team_id: int, payload: TeamUpdateSchema):
#     team = get_object_or_404(Team, id=team_id)
    
#     update_data = payload.dict(exclude_unset=True)
    
#     for field, value in update_data.items():
#         setattr(team, field, value)
    
#     team.save()
#     return TeamExtendedSchema(
#         id=team.id,
#         name=team.name,
#         start_year=team.start_year,
#         tagozat=team.tagozat,
#         color=team.get_team_color(),
#         active=team.active,
#         players=[
#             PlayerExtendedSchema(
#                 id=player.id,
#                 name=player.name,
#                 csk=player.csk,
#                 start_year=player.start_year,
#                 tagozat=player.tagozat,
#                 effective_start_year=player.get_start_year(),
#                 effective_tagozat=player.get_tagozat()
#             ) for player in team.players.all()
#         ]
#     )

# # Csapat részleges frissítése
# @router.patch("/teams/{team_id}", response=TeamExtendedSchema)
# def patch_team(request, team_id: int, payload: TeamUpdateSchema):
#     team = get_object_or_404(Team, id=team_id)
    
#     update_data = payload.dict(exclude_unset=True)
    
#     for field, value in update_data.items():
#         setattr(team, field, value)
    
#     team.save()
#     return TeamExtendedSchema(
#         id=team.id,
#         name=team.name,
#         start_year=team.start_year,
#         tagozat=team.tagozat,
#         color=team.get_team_color(),
#         active=team.active,
#         players=[
#             PlayerExtendedSchema(
#                 id=player.id,
#                 name=player.name,
#                 csk=player.csk,
#                 start_year=player.start_year,
#                 tagozat=player.tagozat,
#                 effective_start_year=player.get_start_year(),
#                 effective_tagozat=player.get_tagozat()
#             ) for player in team.players.all()
#         ]
#     )


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
@router.get("/admin/teams/{team_id}/players", response=list[PlayerExtendedSchema])
def get_any_team_players(request, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    players = team.players.all()
    return [
        PlayerExtendedSchema(
            id=player.id,
            name=player.name,
            csk=player.csk,
            start_year=player.start_year,
            tagozat=player.tagozat,
            effective_start_year=player.get_start_year(),
            effective_tagozat=player.get_tagozat()
        ) for player in players
    ]


# Minden player lekérdezése (admin - minden bajnokságból)
@router.get("/admin/players/all", response=list[PlayerExtendedSchema])
def get_all_players(request):
    players = Player.objects.all()
    return [
        PlayerExtendedSchema(
            id=player.id,
            name=player.name,
            csk=player.csk,
            start_year=player.start_year,
            tagozat=player.tagozat,
            effective_start_year=player.get_start_year(),
            effective_tagozat=player.get_tagozat()
        ) for player in players
    ]

# Player lekérdezése (admin - bármely bajnokságból)
@router.get("/admin/players/{player_id}", response=PlayerExtendedSchema)
def get_any_player(request, player_id: int):
    player = get_object_or_404(Player, id=player_id)
    return PlayerExtendedSchema(
        id=player.id,
        name=player.name,
        csk=player.csk,
        start_year=player.start_year,
        tagozat=player.tagozat,
        effective_start_year=player.get_start_year(),
        effective_tagozat=player.get_tagozat()
    )

# Csapatkapitányok lekérdezése
@router.get("/players/captains", response=list[PlayerExtendedSchema])
def get_captains(request):
    players = Player.objects.filter(csk=True)
    return [
        PlayerExtendedSchema(
            id=player.id,
            name=player.name,
            csk=player.csk,
            start_year=player.start_year,
            tagozat=player.tagozat,
            effective_start_year=player.get_start_year(),
            effective_tagozat=player.get_tagozat()
        ) for player in players
    ]

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

# Közlemények

# Minden közlemény lekérdezése
@router.get("/kozlemenyek", response=list[KozlemenySchema])
def get_kozlemenyek(request):
    return Kozlemeny.objects.all().order_by('-priority', '-date_created')

# Aktív közlemények lekérdezése
@router.get("/kozlemenyek/active", response=list[KozlemenySchema])
def get_active_kozlemenyek(request):
    return Kozlemeny.objects.filter(active=True).order_by('-priority', '-date_created')

# Közlemény lekérdezése ID alapján
@router.get("/kozlemenyek/{kozlemeny_id}", response=KozlemenySchema)
def get_kozlemeny(request, kozlemeny_id: int):
    kozlemeny = get_object_or_404(Kozlemeny, id=kozlemeny_id)
    return kozlemeny

# Prioritás alapján közlemények lekérdezése
@router.get("/kozlemenyek/priority/{priority}", response=list[KozlemenySchema])
def get_kozlemenyek_by_priority(request, priority: str):
    valid_priorities = ['low', 'normal', 'high', 'urgent']
    if priority not in valid_priorities:
        return []
    return Kozlemeny.objects.filter(priority=priority, active=True).order_by('-date_created')

# # Új közlemény létrehozása
# @router.post("/kozlemenyek", response=KozlemenySchema)
# def create_kozlemeny(request, payload: KozlemenyCreateSchema):
#     kozlemeny_data = payload.dict()
#     kozlemeny = Kozlemeny.objects.create(**kozlemeny_data)
#     return kozlemeny

# # Közlemény frissítése
# @router.put("/kozlemenyek/{kozlemeny_id}", response=KozlemenySchema)
# def update_kozlemeny(request, kozlemeny_id: int, payload: KozlemenyUpdateSchema):
#     kozlemeny = get_object_or_404(Kozlemeny, id=kozlemeny_id)
    
#     update_data = payload.dict(exclude_unset=True)
    
#     for field, value in update_data.items():
#         setattr(kozlemeny, field, value)
    
#     kozlemeny.save()
#     return kozlemeny

# # Közlemény részleges frissítése
# @router.patch("/kozlemenyek/{kozlemeny_id}", response=KozlemenySchema)
# def patch_kozlemeny(request, kozlemeny_id: int, payload: KozlemenyUpdateSchema):
#     kozlemeny = get_object_or_404(Kozlemeny, id=kozlemeny_id)
    
#     update_data = payload.dict(exclude_unset=True)
    
#     for field, value in update_data.items():
#         setattr(kozlemeny, field, value)
    
#     kozlemeny.save()
#     return kozlemeny

# # Közlemény deaktiválása
# @router.patch("/kozlemenyek/{kozlemeny_id}/deactivate")
# def deactivate_kozlemeny(request, kozlemeny_id: int):
#     kozlemeny = get_object_or_404(Kozlemeny, id=kozlemeny_id)
#     kozlemeny.active = False
#     kozlemeny.save()
#     return {"message": "Közlemény deaktiválva"}

# # Közlemény aktiválása
# @router.patch("/kozlemenyek/{kozlemeny_id}/activate")
# def activate_kozlemeny(request, kozlemeny_id: int):
#     kozlemeny = get_object_or_404(Kozlemeny, id=kozlemeny_id)
#     kozlemeny.active = True
#     kozlemeny.save()
#     return {"message": "Közlemény aktiválva"}

