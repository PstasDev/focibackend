from ninja import NinjaAPI, Router
from .models import *
from django.contrib.auth.models import User
from .schemas import *
from django.shortcuts import get_object_or_404
from django.db import models
from .utils import process_matches, get_goal_scorers, get_latest_tournament
from .referee_utils import (
    get_match_status, validate_event_data, get_half_time_score, 
    get_match_timeline, get_player_statistics, get_team_statistics,
    can_referee_edit_match, format_match_time, get_current_match_minute,
    get_current_extra_time, get_first_half_end_minute, get_second_half_start_minute, get_match_end_minute
)
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import authenticate
from django.http import JsonResponse
from .auth import JWTAuth, jwt_auth, jwt_cookie_auth, admin_auth, biro_auth


def event_to_response_schema(event) -> EventResponseSchema:
    """Convert Event object to EventResponseSchema with formatted time"""
    formatted_time = f"{event.minute}+{event.minute_extra_time}'" if event.minute_extra_time else f"{event.minute}'"
    
    return EventResponseSchema(
        id=event.id,
        event_type=event.event_type,
        half=event.half,
        minute=event.minute,
        minute_extra_time=event.minute_extra_time,
        formatted_time=formatted_time,
        exact_time=event.exact_time.isoformat() if event.exact_time else None,
        player=PlayerSchema.from_orm(event.player) if event.player else None,
        extra_time=event.extra_time
    )


def match_to_schema(match) -> dict:
    """Convert Match object to MatchSchema dict with properly formatted events"""
    # Convert match to dict first, excluding problematic related fields
    match_dict = {
        'id': match.id,
        'team1': match.team1,
        'team2': match.team2,
        'tournament': match.tournament,
        'round_obj': match.round_obj,
        'referee': match.referee,
        'datetime': match.datetime,
        'status': match.status if match.status else 'active',
        'events': [event_to_response_schema(event) for event in match.events.all()],
        'photos': list(match.photos.all()) if hasattr(match, 'photos') else []
    }
    
    # Use MatchSchema to validate and serialize
    match_schema = MatchSchema.model_validate(match_dict)
    return match_schema.model_dump()


def matches_to_schema_list(matches) -> list:
    """Convert Match queryset to list of MatchSchema dicts with properly formatted events"""
    return [match_to_schema(match) for match in matches]


app = NinjaAPI(csrf=False)  # Disable CSRF for API since we use JWT
router = Router()
admin_router = Router()
biro_router = Router()
app.add_router("/", router) 
app.add_router("/admin", admin_router) 
app.add_router("/biro", biro_router) 

# Authentication endpoints

@router.post("/auth/login")
def login(request, payload: LoginSchema):
    """
    Login endpoint that validates credentials and returns JWT token
    """
    username = payload.username
    password = payload.password
    
    # Authenticate user
    user = authenticate(username=username, password=password)
    
    if user is not None:
        if user.is_active:
            # Generate JWT token
            token = JWTAuth.encode_token(user.id, user.username)
            
            # Create response
            response_data = {
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_staff": user.is_staff,
                    "is_active": user.is_active
                },
                "token": token
            }
            
            response = JsonResponse(response_data)
            
            # Set HTTP-only cookie for enhanced security
            response.set_cookie(
                'auth_token',
                token,
                max_age=24*60*60,  # 24 hours (same as JWT expiry)
                httponly=True,     # Prevent XSS attacks
                secure=False,      # Set to True in production with HTTPS
                samesite='Lax',    # CSRF protection
                path='/'           # Available for entire site
            )
            
            return response
        else:
            return JsonResponse({
                "success": False,
                "message": "Account is disabled",
                "user": None,
                "token": None
            })
    else:
        return JsonResponse({
            "success": False,
            "message": "Invalid username or password",
            "user": None,
            "token": None
        })

@router.post("/auth/logout")
def logout(request):
    """
    Logout endpoint - deletes HTTP-only authentication cookies
    """
    response = JsonResponse({
        "success": True,
        "message": "Logout successful"
    })
    
    # Delete the auth_token cookie by setting it to expire immediately
    response.delete_cookie(
        'auth_token',
        path='/',
        domain=None,  # Will use current domain
        samesite='Lax'  # or 'Strict' depending on your security requirements
    )
    
    return response

@router.get("/auth/status", response=AuthStatusSchema, auth=jwt_cookie_auth)
def auth_status(request):
    """
    Check authentication status of current user
    """
    return AuthStatusSchema(
        authenticated=True,
        user=UserSchema.from_orm(request.auth)
    ) 

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
    # Include all matches (including cancelled) for display purposes
    matches = Match.objects.filter(tournament=tournament).prefetch_related('events', 'events__player')
    return matches_to_schema_list(matches)

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
            logo_url=team.logo_url,
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
        logo_url=team.logo_url,
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
    # Include all matches (including cancelled) for display purposes
    matches = Match.objects.filter(tournament=tournament).filter(
        models.Q(team1=team) | models.Q(team2=team)
    ).prefetch_related('events', 'events__player')
    return matches_to_schema_list(matches)

# Góllövők (legújabb bajnokság)
@router.get("/topscorers", response=list[TopScorerSchema])
def get_top_scorers(request):
    tournament = get_latest_tournament()
    # Exclude cancelled matches from top scorers stats
    matches = Match.objects.filter(tournament=tournament).exclude(
        models.Q(status='cancelled_new_date') | models.Q(status='cancelled_no_date')
    )
    # Get all goal events from all matches in the tournament
    goals = []
    for match in matches:
        goals.extend(match.events.filter(event_type='goal'))
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
    matches = Match.objects.filter(round_obj=round_obj).prefetch_related('events', 'events__player')
    return matches_to_schema_list(matches)
    
# Összes gól (legújabb bajnokság)
@router.get("/goals", response=list[EventSchema])
def get_goals(request):
    tournament = get_latest_tournament()
    # Exclude cancelled matches from goal stats
    matches = Match.objects.filter(tournament=tournament).exclude(
        models.Q(status='cancelled_new_date') | models.Q(status='cancelled_no_date')
    )
    goals = []
    for match in matches:
        goals.extend(match.events.filter(event_type='goal'))
    return goals

# Összes sárga lap (legújabb bajnokság)
@router.get("/yellow_cards", response=list[EventSchema])
def get_yellow_cards(request):
    tournament = get_latest_tournament()
    # Exclude cancelled matches from card stats
    matches = Match.objects.filter(tournament=tournament).exclude(
        models.Q(status='cancelled_new_date') | models.Q(status='cancelled_no_date')
    )
    yellow_cards = []
    for match in matches:
        yellow_cards.extend(match.events.filter(event_type='yellow_card'))
    return yellow_cards

# Összes piros lap (legújabb bajnokság)
@router.get("/red_cards", response=list[EventSchema])
def get_red_cards(request):
    tournament = get_latest_tournament()
    # Exclude cancelled matches from card stats
    matches = Match.objects.filter(tournament=tournament).exclude(
        models.Q(status='cancelled_new_date') | models.Q(status='cancelled_no_date')
    )
    red_cards = []
    for match in matches:
        red_cards.extend(match.events.filter(event_type='red_card'))
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
    # Exclude cancelled matches from player event stats
    matches = Match.objects.filter(tournament=tournament).exclude(
        models.Q(status='cancelled_new_date') | models.Q(status='cancelled_no_date')
    )
    # Get all events for this player from tournament matches
    all_events = []
    for match in matches:
        all_events.extend(match.events.filter(player=player))

    return AllEventsSchema(
        goals=[event for event in all_events if event.event_type == "goal"],
        yellow_cards=[event for event in all_events if event.event_type == "yellow_card"],
        red_cards=[event for event in all_events if event.event_type == "red_card"],
    )
 

# Minden csapat lekérdezése (minden bajnokságból) - admin use
@admin_router.get("/teams/all", response=list[TeamExtendedSchema], auth=admin_auth)
def get_all_teams(request):
    teams = Team.objects.all()
    return [
        TeamExtendedSchema(
            id=team.id,
            name=team.name,
            start_year=team.start_year,
            tagozat=team.tagozat,
            color=team.get_team_color(),
            logo_url=team.logo_url,
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
@admin_router.get("/teams/{team_id}", response=TeamExtendedSchema, auth=admin_auth)
def get_any_team(request, team_id: int):
    team = get_object_or_404(Team, id=team_id)
    return TeamExtendedSchema(
        id=team.id,
        name=team.name,
        start_year=team.start_year,
        tagozat=team.tagozat,
        color=team.get_team_color(),
        logo_url=team.logo_url,
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
            logo_url=team.logo_url,
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
            logo_url=team.logo_url,
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
    # Exclude cancelled matches from team event stats
    matches = Match.objects.filter(tournament=tournament).filter(
        models.Q(team1=team) | models.Q(team2=team)
    ).exclude(
        models.Q(status='cancelled_new_date') | models.Q(status='cancelled_no_date')
    )
    # Get all events from matches this team played in
    all_events = []
    for match in matches:
        all_events.extend(match.events.all())

    return AllEventsSchema(
        goals=[event for event in all_events if event.event_type == "goal"],
        yellow_cards=[event for event in all_events if event.event_type == "yellow_card"],
        red_cards=[event for event in all_events if event.event_type == "red_card"],
    )  

# Csapat játékosai (admin - bármely bajnokságból)
@admin_router.get("/teams/{team_id}/players", response=list[PlayerExtendedSchema], auth=admin_auth)
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
@admin_router.get("/players/all", response=list[PlayerExtendedSchema], auth=admin_auth)
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
@admin_router.get("/players/{player_id}", response=PlayerExtendedSchema, auth=admin_auth)
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
@admin_router.get("/players/{player_id}/events", response=AllEventsSchema, auth=admin_auth)
def get_all_player_events(request, player_id: int):
    player = get_object_or_404(Player, id=player_id)
    # Get all events for this player from all non-cancelled matches
    all_events = []
    all_matches = Match.objects.all().exclude(
        models.Q(status='cancelled_new_date') | models.Q(status='cancelled_no_date')
    )
    for match in all_matches:
        all_events.extend(match.events.filter(player=player))

    return AllEventsSchema(
        goals=[event for event in all_events if event.event_type == "goal"],
        yellow_cards=[event for event in all_events if event.event_type == "yellow_card"],
        red_cards=[event for event in all_events if event.event_type == "red_card"],
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
@admin_router.get("/matches/all", response=list[MatchSchema], auth=admin_auth)
def get_all_matches(request):
    matches = Match.objects.all().prefetch_related('events', 'events__player')
    return matches_to_schema_list(matches)

# Update match (admin)
@admin_router.put("/matches/{match_id}", response=MatchSchema, auth=admin_auth)
def update_match_admin(request, match_id: int, payload: MatchUpdateSchema):
    """
    Update match details including datetime, referee, and status (admin only)
    """
    match = get_object_or_404(Match, id=match_id)
    
    update_data = payload.dict(exclude_unset=True)
    
    # Handle datetime update
    if 'datetime' in update_data and update_data['datetime']:
        from datetime import datetime as dt
        match.datetime = dt.fromisoformat(update_data['datetime'].replace('Z', '+00:00'))
        del update_data['datetime']
    
    # Handle referee update
    if 'referee_id' in update_data:
        if update_data['referee_id']:
            referee = get_object_or_404(Profile, id=update_data['referee_id'], biro=True)
            match.referee = referee
        else:
            match.referee = None
        del update_data['referee_id']
    
    # Handle status update
    if 'status' in update_data:
        valid_statuses = [choice[0] for choice in Match.STATUS_CHOICES]
        if update_data['status'] not in valid_statuses and update_data['status'] is not None:
            return JsonResponse({'error': 'Invalid status value'}, status=400)
        match.status = update_data['status']
        del update_data['status']
    
    # Update any remaining fields
    for field, value in update_data.items():
        setattr(match, field, value)
    
    match.save()
    
    return match_to_schema(match)

# Patch match (admin)
@admin_router.patch("/matches/{match_id}", response=MatchSchema, auth=admin_auth)
def patch_match_admin(request, match_id: int, payload: MatchUpdateSchema):
    """
    Partially update match details (admin only)
    """
    match = get_object_or_404(Match, id=match_id)
    
    update_data = payload.dict(exclude_unset=True)
    
    # Handle datetime update
    if 'datetime' in update_data and update_data['datetime']:
        from datetime import datetime as dt
        match.datetime = dt.fromisoformat(update_data['datetime'].replace('Z', '+00:00'))
        del update_data['datetime']
    
    # Handle referee update
    if 'referee_id' in update_data:
        if update_data['referee_id']:
            referee = get_object_or_404(Profile, id=update_data['referee_id'], biro=True)
            match.referee = referee
        else:
            match.referee = None
        del update_data['referee_id']
    
    # Handle status update
    if 'status' in update_data:
        valid_statuses = [choice[0] for choice in Match.STATUS_CHOICES]
        if update_data['status'] not in valid_statuses and update_data['status'] is not None:
            return JsonResponse({'error': 'Invalid status value'}, status=400)
        match.status = update_data['status']
        del update_data['status']
    
    # Update any remaining fields
    for field, value in update_data.items():
        setattr(match, field, value)
    
    match.save()
    
    return match_to_schema(match)

# Get match status choices
@router.get("/match-status-choices")
def get_match_status_choices(request):
    """
    Get available match status choices
    """
    return JsonResponse({
        'choices': [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Match.STATUS_CHOICES
        ]
    })

# Meccs lekérdezése
@router.get("/matches/{match_id}", response=MatchSchema)
def get_match(request, match_id: int):
    match = get_object_or_404(Match, id=match_id)
    return match_to_schema(match)

# Adott bíró meccsei
@router.get("/profiles/{profile_id}/matches", response=list[MatchSchema])
def get_referee_matches(request, profile_id: int):
    profile = get_object_or_404(Profile, id=profile_id, biro=True)
    matches = Match.objects.filter(referee=profile).prefetch_related('events', 'events__player')
    return matches_to_schema_list(matches)

# Minden gól lekérdezése (admin - minden bajnokságból)
@admin_router.get("/goals/all", response=list[EventSchema], auth=admin_auth)
def get_all_goals_admin(request):
    # Get goal events only from non-cancelled matches
    non_cancelled_matches = Match.objects.exclude(
        models.Q(status='cancelled_new_date') | models.Q(status='cancelled_no_date')
    )
    goals = []
    for match in non_cancelled_matches:
        goals.extend(match.events.filter(event_type='goal'))
    return goals

# Gólok lekérdezése
@router.get("/goals/{goal_id}", response=EventSchema)
def get_goal(request, goal_id: int):
    goal = get_object_or_404(Event, id=goal_id)
    return goal


# Sárga lapok lekérdezése (admin - minden bajnokságból)
@admin_router.get("/yellow_cards/all", response=list[EventSchema], auth=admin_auth)
def get_all_yellow_cards_admin(request):
    # Get yellow card events only from non-cancelled matches
    non_cancelled_matches = Match.objects.exclude(
        models.Q(status='cancelled_new_date') | models.Q(status='cancelled_no_date')
    )
    cards = []
    for match in non_cancelled_matches:
        cards.extend(match.events.filter(event_type='yellow_card'))
    return cards

# Sárga lap lekérdezése
@router.get("/yellow_cards/{card_id}", response=EventSchema)
def get_card(request, card_id: int):
    card = get_object_or_404(Event, id=card_id)
    return card


# Piros lapok lekérdezése (admin - minden bajnokságból)
@admin_router.get("/red_cards/all", response=list[EventSchema], auth=admin_auth)
def get_all_red_cards_admin(request):
    # Get red card events only from non-cancelled matches
    non_cancelled_matches = Match.objects.exclude(
        models.Q(status='cancelled_new_date') | models.Q(status='cancelled_no_date')
    )
    cards = []
    for match in non_cancelled_matches:
        cards.extend(match.events.filter(event_type='red_card'))
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
        goals=[event for event in events if event.event_type == "goal"],
        yellow_cards=[event for event in events if event.event_type == "yellow_card"],
        red_cards=[event for event in events if event.event_type == "red_card"],
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
@admin_router.get("/rounds/all", response=list[RoundSchema], auth=admin_auth)
def get_all_rounds(request):
    return Round.objects.all().order_by('tournament', 'number')

# Forduló lekérdezése ID alapján (admin)
@admin_router.get("/rounds/{round_id}", response=RoundSchema, auth=admin_auth)
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

# Time sync endpoint for frontend synchronization
@router.get("/time", response=TimeSyncSchema)
def get_server_time(request):
    """
    Returns the current server time for frontend synchronization.
    Useful for ensuring consistent timestamps and time-based operations.
    """
    now = timezone.now()
    return TimeSyncSchema(
        server_time=now.isoformat(),
        timezone=str(timezone.get_current_timezone()),
        timestamp=int(now.timestamp())
    )

# Szankciók (Sanctions)

# Get all sanctions for a specific team
@router.get("/teams/{team_id}/sanctions", response=list[SzankcioSchema])
def get_team_sanctions(request, team_id: int):
    """
    Get all sanctions for a specific team in the current tournament
    """
    tournament = get_latest_tournament()
    team = get_object_or_404(Team, id=team_id, tournament=tournament)
    sanctions = Szankcio.objects.filter(team=team, tournament=tournament).order_by('-date_created')
    return sanctions

# Get all sanctions in current tournament
@router.get("/sanctions", response=list[SzankcioSchema])
def get_sanctions(request):
    """
    Get all sanctions in the current tournament
    """
    tournament = get_latest_tournament()
    sanctions = Szankcio.objects.filter(tournament=tournament).order_by('-date_created')
    return sanctions

# Get specific sanction by ID
@router.get("/sanctions/{sanction_id}", response=SzankcioSchema)
def get_sanction(request, sanction_id: int):
    """
    Get a specific sanction by ID
    """
    sanction = get_object_or_404(Szankcio, id=sanction_id)
    return sanction

# =============================================================================
# REFEREE (BÍRÓ) ENDPOINTS - Jegyzőkönyv Management
# =============================================================================

# Get referee's assigned matches
@biro_router.get("/my-matches", response=list[MatchSchema], auth=biro_auth)
def get_referee_matches(request):
    """
    Get all matches assigned to the current referee
    """
    try:
        profile = request.auth.profile
        matches = Match.objects.filter(referee=profile).order_by('datetime').prefetch_related('events', 'events__player')
        return matches_to_schema_list(matches)
    except AttributeError:
        return []

# Get live matches that referee can manage
@biro_router.get("/live-matches", response=list[MatchStatusSchema], auth=biro_auth)
def get_live_matches(request):
    """
    Get matches that are currently live or about to start
    """
    try:
        profile = request.auth.profile
        now = timezone.now()
        # Get all matches from today and tomorrow (not just assigned to this referee)
        matches = Match.objects.filter(
            datetime__gte=now.replace(hour=0, minute=0, second=0),
            datetime__lte=now + timedelta(days=1)
        ).order_by('datetime')
        
        match_statuses = []
        for match in matches:
            # Determine match status based on events
            events = match.events.all().order_by('minute', 'id')
            
            status = "not_started"
            if events.filter(event_type='match_start').exists():
                status = "first_half"
            if events.filter(event_type='half_time').exists():
                status = "half_time"
            if events.filter(event_type='full_time').exists():
                status = "second_half"
            if events.filter(event_type='extra_time').exists():
                status = "extra_time"
            if events.filter(event_type='match_end').exists():
                status = "finished"
            
            match_statuses.append(MatchStatusSchema(
                id=match.id,
                team1=TeamExtendedSchema(
                    id=match.team1.id,
                    name=match.team1.name,
                    start_year=match.team1.start_year,
                    tagozat=match.team1.tagozat,
                    color=match.team1.get_team_color(),
                    logo_url=match.team1.logo_url,
                    active=match.team1.active,
                    players=[
                        PlayerExtendedSchema(
                            id=player.id,
                            name=player.name,
                            csk=player.csk,
                            start_year=player.start_year,
                            tagozat=player.tagozat,
                            effective_start_year=player.get_start_year(),
                            effective_tagozat=player.get_tagozat()
                        ) for player in match.team1.players.all()
                    ]
                ),
                team2=TeamExtendedSchema(
                    id=match.team2.id,
                    name=match.team2.name,
                    start_year=match.team2.start_year,
                    tagozat=match.team2.tagozat,
                    color=match.team2.get_team_color(),
                    logo_url=match.team2.logo_url,
                    active=match.team2.active,
                    players=[
                        PlayerExtendedSchema(
                            id=player.id,
                            name=player.name,
                            csk=player.csk,
                            start_year=player.start_year,
                            tagozat=player.tagozat,
                            effective_start_year=player.get_start_year(),
                            effective_tagozat=player.get_tagozat()
                        ) for player in match.team2.players.all()
                    ]
                ),
                datetime=match.datetime.isoformat(),
                referee=ProfileSchema.from_orm(match.referee) if match.referee else None,
                events=[event_to_response_schema(event) for event in events],
                score=match.result(),
                match_status=status,
                status=match.status
            ))
        
        return match_statuses
    except AttributeError:
        return []

# Get specific match details for referee management
@biro_router.get("/matches/{match_id}", response=MatchStatusSchema, auth=biro_auth)
def get_match_for_referee(request, match_id: int):
    """
    Get specific match details that referee can manage
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        events = match.events.all().order_by('minute', 'id')
        
        # Determine match status
        status = "not_started"
        if events.filter(event_type='match_start').exists():
            status = "first_half"
        if events.filter(event_type='half_time').exists():
            status = "half_time"
        if events.filter(event_type='full_time').exists():
            status = "second_half"
        if events.filter(event_type='extra_time').exists():
            status = "extra_time"
        if events.filter(event_type='match_end').exists():
            status = "finished"
        
        return MatchStatusSchema(
            id=match.id,
            team1=TeamExtendedSchema(
                id=match.team1.id,
                name=match.team1.name,
                start_year=match.team1.start_year,
                tagozat=match.team1.tagozat,
                color=match.team1.get_team_color(),
                logo_url=match.team1.logo_url,
                active=match.team1.active,
                players=[
                    PlayerExtendedSchema(
                        id=player.id,
                        name=player.name,
                        csk=player.csk,
                        start_year=player.start_year,
                        tagozat=player.tagozat,
                        effective_start_year=player.get_start_year(),
                        effective_tagozat=player.get_tagozat()
                    ) for player in match.team1.players.all()
                ]
            ),
            team2=TeamExtendedSchema(
                id=match.team2.id,
                name=match.team2.name,
                start_year=match.team2.start_year,
                tagozat=match.team2.tagozat,
                color=match.team2.get_team_color(),
                logo_url=match.team2.logo_url,
                active=match.team2.active,
                players=[
                    PlayerExtendedSchema(
                        id=player.id,
                        name=player.name,
                        csk=player.csk,
                        start_year=player.start_year,
                        tagozat=player.tagozat,
                        effective_start_year=player.get_start_year(),
                        effective_tagozat=player.get_tagozat()
                    ) for player in match.team2.players.all()
                ]
            ),
            datetime=match.datetime.isoformat(),
            referee=ProfileSchema.from_orm(match.referee) if match.referee else None,
            events=[event_to_response_schema(event) for event in events],
            score=match.result(),
            match_status=status,
            status=match.status
        )
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

# Add event to match (live match updates)
@biro_router.post("/matches/{match_id}/events", response=EventResponseSchema, auth=biro_auth)
def add_match_event(request, match_id: int, payload: EventCreateSchema):
    """
    Add a new event to a match (goals, cards, etc.)
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        # Validate event type
        valid_event_types = [choice[0] for choice in Event.EVENT_TYPES]
        if payload.event_type not in valid_event_types:
            return JsonResponse({'error': 'Invalid event type'}, status=400)
        
        # Get player if specified
        player = None
        if payload.player_id:
            # Ensure player belongs to one of the teams in this match
            try:
                player = Player.objects.get(
                    id=payload.player_id,
                    team__in=[match.team1, match.team2]
                )
            except Player.DoesNotExist:
                return JsonResponse({'error': 'Player not found in match teams'}, status=400)
        
        # Create event
        event = Event.objects.create(
            event_type=payload.event_type,
            half=payload.half,
            minute=payload.minute,
            minute_extra_time=payload.minute_extra_time,
            player=player,
            extra_time=payload.extra_time,
            exact_time=timezone.now()
        )
        
        # Add event to match
        match.events.add(event)
        
        return event_to_response_schema(event)
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

# Update existing event
@biro_router.put("/matches/{match_id}/events/{event_id}", response=EventResponseSchema, auth=biro_auth)
def update_match_event(request, match_id: int, event_id: int, payload: EventUpdateSchema):
    """
    Update an existing event in a match
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        event = get_object_or_404(Event, id=event_id)
        
        # Ensure event belongs to this match
        if event not in match.events.all():
            return JsonResponse({'error': 'Event not found in this match'}, status=404)
        
        # Update event fields
        update_data = payload.dict(exclude_unset=True)
        
        if 'player_id' in update_data:
            if update_data['player_id']:
                try:
                    player = Player.objects.get(
                        id=update_data['player_id'],
                        team__in=[match.team1, match.team2]
                    )
                    event.player = player
                except Player.DoesNotExist:
                    return JsonResponse({'error': 'Player not found in match teams'}, status=400)
            else:
                event.player = None
            del update_data['player_id']
        
        # Update other fields
        for field, value in update_data.items():
            setattr(event, field, value)
        
        event.save()
        
        return event_to_response_schema(event)
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

# Update match details (including status)
@biro_router.put("/matches/{match_id}", response=MatchSchema, auth=biro_auth)
def update_match(request, match_id: int, payload: MatchUpdateSchema):
    """
    Update match details including datetime, referee, and status
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        update_data = payload.dict(exclude_unset=True)
        
        # Handle datetime update
        if 'datetime' in update_data and update_data['datetime']:
            from datetime import datetime as dt
            match.datetime = dt.fromisoformat(update_data['datetime'].replace('Z', '+00:00'))
            del update_data['datetime']
        
        # Handle referee update
        if 'referee_id' in update_data:
            if update_data['referee_id']:
                referee = get_object_or_404(Profile, id=update_data['referee_id'], biro=True)
                match.referee = referee
            else:
                match.referee = None
            del update_data['referee_id']
        
        # Handle status update
        if 'status' in update_data:
            valid_statuses = [choice[0] for choice in Match.STATUS_CHOICES]
            if update_data['status'] not in valid_statuses and update_data['status'] is not None:
                return JsonResponse({'error': 'Invalid status value'}, status=400)
            match.status = update_data['status']
            del update_data['status']
        
        # Update any remaining fields
        for field, value in update_data.items():
            setattr(match, field, value)
        
        match.save()
        
        return match_to_schema(match)
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

# Remove event from match (Enhanced for undo functionality)
@biro_router.delete("/matches/{match_id}/events/{event_id}", auth=biro_auth)
def remove_match_event(request, match_id: int, event_id: int):
    """
    Remove an event from a match (undo functionality)
    Enhanced with validation and audit logging
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        event = get_object_or_404(Event, id=event_id)
        
        # Ensure event belongs to this match
        if event not in match.events.all():
            return JsonResponse({'error': 'Event not found in this match'}, status=404)
        
        # Validate if event can be safely removed
        validation_errors = []
        
        # Check if removing critical match control events would break the match flow
        if event.event_type == 'match_start':
            # Can only remove match_start if no other events exist after it
            later_events = match.events.filter(
                minute__gt=event.minute
            ).exclude(id=event.id)
            if later_events.exists():
                validation_errors.append("Cannot remove match start - other events exist after it")
        
        elif event.event_type == 'half_time':
            # Can only remove half_time if no second half events exist
            second_half_events = match.events.filter(half=2).exclude(id=event.id)
            if second_half_events.exists():
                validation_errors.append("Cannot remove half-time - second half events exist")
        
        elif event.event_type == 'match_end':
            # Match end can usually be safely removed
            pass
        
        # Check for dependent events (e.g., if player has red card, can't have more events)
        if event.event_type == 'red_card' and event.player:
            # Check if player has events after the red card
            later_player_events = match.events.filter(
                player=event.player,
                minute__gt=event.minute
            ).exclude(id=event.id)
            if later_player_events.exists():
                validation_errors.append(f"Cannot remove red card - player {event.player.name} has events after the red card")
        
        if validation_errors:
            return JsonResponse({
                'error': 'Cannot remove event',
                'validation_errors': validation_errors
            }, status=400)
        
        # Store event details for response before deletion
        event_details = {
            'id': event.id,
            'event_type': event.event_type,
            'minute': event.minute,
            'half': event.half,
            'player_name': event.player.name if event.player else None,
            'exact_time': event.exact_time.isoformat() if event.exact_time else None
        }
        
        # Remove event from match and delete it
        match.events.remove(event)
        event.delete()
        
        # Get updated match score after removal
        updated_score = match.result()
        
        return JsonResponse({
            'message': 'Event successfully undone',
            'removed_event': event_details,
            'updated_score': updated_score,
            'timestamp': timezone.now().isoformat()
        })
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

# Undo last event in match
@biro_router.delete("/matches/{match_id}/undo-last-event", auth=biro_auth)
def undo_last_event(request, match_id: int):
    """
    Undo the most recent event in a match
    Convenient endpoint for quick corrections
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        # Get the most recent event (by exact_time if available, otherwise by minute)
        latest_event = match.events.all().order_by('-exact_time', '-minute', '-id').first()
        
        if not latest_event:
            return JsonResponse({'error': 'No events to undo'}, status=400)
        
        # Use the same validation logic as the regular remove endpoint
        validation_errors = []
        
        if latest_event.event_type == 'match_start':
            later_events = match.events.filter(
                minute__gt=latest_event.minute
            ).exclude(id=latest_event.id)
            if later_events.exists():
                validation_errors.append("Cannot remove match start - other events exist after it")
        
        elif latest_event.event_type == 'half_time':
            second_half_events = match.events.filter(half=2).exclude(id=latest_event.id)
            if second_half_events.exists():
                validation_errors.append("Cannot remove half-time - second half events exist")
        
        elif latest_event.event_type == 'red_card' and latest_event.player:
            later_player_events = match.events.filter(
                player=latest_event.player,
                minute__gt=latest_event.minute
            ).exclude(id=latest_event.id)
            if later_player_events.exists():
                validation_errors.append(f"Cannot remove red card - player {latest_event.player.name} has events after the red card")
        
        if validation_errors:
            return JsonResponse({
                'error': 'Cannot undo last event',
                'validation_errors': validation_errors,
                'event_details': {
                    'event_type': latest_event.event_type,
                    'minute': latest_event.minute,
                    'player_name': latest_event.player.name if latest_event.player else None
                }
            }, status=400)
        
        # Store event details before deletion
        event_details = {
            'id': latest_event.id,
            'event_type': latest_event.event_type,
            'minute': latest_event.minute,
            'half': latest_event.half,
            'player_name': latest_event.player.name if latest_event.player else None,
            'exact_time': latest_event.exact_time.isoformat() if latest_event.exact_time else None
        }
        
        # Remove and delete the event
        match.events.remove(latest_event)
        latest_event.delete()
        
        # Get updated match score and status
        updated_score = match.result()
        
        return JsonResponse({
            'message': 'Last event successfully undone',
            'undone_event': event_details,
            'updated_score': updated_score,
            'timestamp': timezone.now().isoformat()
        })
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

# Get undoable events for a match
@biro_router.get("/matches/{match_id}/undoable-events", auth=biro_auth)
def get_undoable_events(request, match_id: int):
    """
    Get list of events that can be safely undone
    Helps UI show which events can be removed
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        events = match.events.all().order_by('-exact_time', '-minute', '-id')
        undoable_events = []
        
        for event in events:
            can_undo = True
            reasons = []
            
            # Apply same validation logic as delete endpoints
            if event.event_type == 'match_start':
                later_events = match.events.filter(
                    minute__gt=event.minute
                ).exclude(id=event.id)
                if later_events.exists():
                    can_undo = False
                    reasons.append("Other events exist after match start")
            
            elif event.event_type == 'half_time':
                second_half_events = match.events.filter(half=2).exclude(id=event.id)
                if second_half_events.exists():
                    can_undo = False
                    reasons.append("Second half events exist")
            
            elif event.event_type == 'red_card' and event.player:
                later_player_events = match.events.filter(
                    player=event.player,
                    minute__gt=event.minute
                ).exclude(id=event.id)
                if later_player_events.exists():
                    can_undo = False
                    reasons.append("Player has events after red card")
            
            undoable_events.append({
                'id': event.id,
                'event_type': event.event_type,
                'minute': event.minute,
                'half': event.half,
                'player_name': event.player.name if event.player else None,
                'exact_time': event.exact_time.isoformat() if event.exact_time else None,
                'can_undo': can_undo,
                'cannot_undo_reasons': reasons
            })
        
        return JsonResponse({
            'match_id': match.id,
            'undoable_events': undoable_events,
            'total_events': len(undoable_events),
            'undoable_count': len([e for e in undoable_events if e['can_undo']])
        })
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

# Bulk undo events (undo all events after a certain minute)
@biro_router.delete("/matches/{match_id}/undo-after-minute/{minute}", auth=biro_auth)
def undo_events_after_minute(request, match_id: int, minute: int):
    """
    Undo all events that occurred after a specific minute
    Useful for correcting major timing errors
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        # Get events after the specified minute
        events_to_remove = match.events.filter(minute__gt=minute).order_by('-minute', '-id')
        
        if not events_to_remove.exists():
            return JsonResponse({'error': f'No events found after minute {minute}'}, status=400)
        
        # Validate that we can safely remove all these events
        validation_errors = []
        removed_events = []
        
        for event in events_to_remove:
            # Store event details before removal
            event_detail = {
                'id': event.id,
                'event_type': event.event_type,
                'minute': event.minute,
                'half': event.half,
                'player_name': event.player.name if event.player else None,
                'exact_time': event.exact_time.isoformat() if event.exact_time else None
            }
            removed_events.append(event_detail)
        
        # Check if any critical events would be affected
        critical_events = events_to_remove.filter(
            event_type__in=['match_start', 'half_time', 'match_end']
        )
        
        if critical_events.exists():
            critical_list = [f"{e.event_type} at {e.minute}'" for e in critical_events]
            validation_errors.append(f"Would remove critical events: {', '.join(critical_list)}")
        
        # If there are validation errors, return them without making changes
        if validation_errors:
            return JsonResponse({
                'error': 'Cannot perform bulk undo',
                'validation_errors': validation_errors,
                'events_that_would_be_removed': removed_events
            }, status=400)
        
        # Perform the bulk removal
        for event in events_to_remove:
            match.events.remove(event)
            event.delete()
        
        # Get updated match score
        updated_score = match.result()
        
        return JsonResponse({
            'message': f'Successfully undid {len(removed_events)} events after minute {minute}',
            'removed_events': removed_events,
            'removed_count': len(removed_events),
            'updated_score': updated_score,
            'timestamp': timezone.now().isoformat()
        })
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

# Get complete match record (jegyzőkönyv)
@biro_router.get("/matches/{match_id}/jegyzokonyv", response=JegyzokonyeSchema, auth=biro_auth)
def get_match_jegyzokonyv(request, match_id: int):
    """
    Get complete match record (jegyzőkönyv) with all details
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        events = match.events.all().order_by('minute', 'minute_extra_time', 'id')
        goals = events.filter(event_type='goal')
        yellow_cards = events.filter(event_type='yellow_card')
        red_cards = events.filter(event_type='red_card')
        
        # Calculate half-time score using dynamic first half end minute
        first_half_end_minute = get_first_half_end_minute(match)
        half_time_events = events.filter(minute__lte=first_half_end_minute, event_type='goal')
        goals_team1_ht = half_time_events.filter(player__in=match.team1.players.all()).count()
        goals_team2_ht = half_time_events.filter(player__in=match.team2.players.all()).count()
        
        # Calculate match duration
        match_duration = None
        match_start = events.filter(event_type='match_start').first()
        match_end = events.filter(event_type='match_end').first()
        if match_start and match_end and match_start.exact_time and match_end.exact_time:
            duration = match_end.exact_time - match_start.exact_time
            match_duration = int(duration.total_seconds() / 60)
        
        return JegyzokonyeSchema(
            match_id=match.id,
            team1=TeamExtendedSchema(
                id=match.team1.id,
                name=match.team1.name,
                start_year=match.team1.start_year,
                tagozat=match.team1.tagozat,
                color=match.team1.get_team_color(),
                logo_url=match.team1.logo_url,
                active=match.team1.active,
                players=[
                    PlayerExtendedSchema(
                        id=player.id,
                        name=player.name,
                        csk=player.csk,
                        start_year=player.start_year,
                        tagozat=player.tagozat,
                        effective_start_year=player.get_start_year(),
                        effective_tagozat=player.get_tagozat()
                    ) for player in match.team1.players.all()
                ]
            ),
            team2=TeamExtendedSchema(
                id=match.team2.id,
                name=match.team2.name,
                start_year=match.team2.start_year,
                tagozat=match.team2.tagozat,
                color=match.team2.get_team_color(),
                logo_url=match.team2.logo_url,
                active=match.team2.active,
                players=[
                    PlayerExtendedSchema(
                        id=player.id,
                        name=player.name,
                        csk=player.csk,
                        start_year=player.start_year,
                        tagozat=player.tagozat,
                        effective_start_year=player.get_start_year(),
                        effective_tagozat=player.get_tagozat()
                    ) for player in match.team2.players.all()
                ]
            ),
            final_score=match.result(),
            datetime=match.datetime.isoformat(),
            referee=ProfileSchema.from_orm(match.referee) if match.referee else None,
            events=[event_to_response_schema(event) for event in events],
            goals_team1=[event_to_response_schema(goal) for goal in goals.filter(player__in=match.team1.players.all())],
            goals_team2=[event_to_response_schema(goal) for goal in goals.filter(player__in=match.team2.players.all())],
            yellow_cards=[event_to_response_schema(card) for card in yellow_cards],
            red_cards=[event_to_response_schema(card) for card in red_cards],
            half_time_score=(goals_team1_ht, goals_team2_ht),
            match_duration=match_duration,
            notes=None  # Could be extended to store referee notes
        )
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

# Quick actions for common events
@biro_router.post("/matches/{match_id}/start-match", auth=biro_auth)
def start_match(request, match_id: int):
    """
    Quick action to start a match
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        # Check if match already started
        if match.events.filter(event_type='match_start').exists():
            return JsonResponse({'error': 'Match already started'}, status=400)
        
        # Create match start event
        event = Event.objects.create(
            event_type='match_start',
            half=1,
            minute=1,
            exact_time=timezone.now()
        )
        
        match.events.add(event)
        
        return JsonResponse({'message': 'Match started successfully', 'event_id': event.id})
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

@biro_router.post("/matches/{match_id}/end-half", auth=biro_auth)
def end_half(request, match_id: int, payload: EndHalfSchema):
    """
    Quick action to end current half
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        events = match.events.all()
        
        # Determine what half we're ending
        if not events.filter(event_type='half_time').exists():
            # End first half - use dynamic minute (default 45 if no specific events)
            current_minute = get_current_match_minute(match) or 45
            event = Event.objects.create(
                event_type='half_time',
                half=1,
                minute=payload.minute,
                minute_extra_time=payload.minute_extra_time,
                exact_time=timezone.now()
            )
            message = 'First half ended'
        elif not events.filter(event_type='full_time').exists():
            # End second half - use dynamic minute (default 90 if no specific events)
            current_minute = get_current_match_minute(match) or 90
            event = Event.objects.create(
                event_type='full_time',
                half=2,
                minute=current_minute,
                exact_time=timezone.now()
            )
            message = 'Second half ended'
        else:
            return JsonResponse({'error': 'Match is already finished'}, status=400)
        
        match.events.add(event)
        
        return JsonResponse({'message': message, 'event_id': event.id})
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

@biro_router.post("/matches/{match_id}/start-second-half", auth=biro_auth)
def start_second_half(request, match_id: int):
    """
    Quick action to start the second half of a match
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        # Check if first half has ended
        if not match.events.filter(event_type='half_time').exists():
            return JsonResponse({'error': 'First half must be ended before starting second half'}, status=400)
        
        # Check if second half already started
        second_half_events = match.events.filter(half=2, event_type='match_start')
        if second_half_events.exists():
            return JsonResponse({'error': 'Second half already started'}, status=400)
        
        event = Event.objects.create(
            event_type='match_start',
            half=2,
            minute=11,
            exact_time=timezone.now()
        )
        
        match.events.add(event)
        
        return JsonResponse({'message': 'Second half started successfully', 'event_id': event.id})
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

@biro_router.post("/matches/{match_id}/end-match", auth=biro_auth)
def end_match(request, match_id: int, payload: EndMatchSchema):
    """
    Quick action to end a match completely
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        # Check if match is not already ended
        if match.events.filter(event_type='match_end').exists():
            return JsonResponse({'error': 'Match already ended'}, status=400)
        
        # Create match end event - use dynamic minute (default 90 if no specific events)
        current_minute = get_current_match_minute(match) or 90
        event = Event.objects.create(
            event_type='match_end',
            half=2,
            minute=payload.minute,
            minute_extra_time=payload.minute_extra_time,
            exact_time=timezone.now()
        )
        
        match.events.add(event)
        
        return JsonResponse({'message': 'Match ended successfully', 'event_id': event.id})
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

# Additional utility endpoints for referees

@biro_router.get("/matches/{match_id}/timeline", auth=biro_auth)
def get_match_timeline_endpoint(request, match_id: int):
    """
    Get chronological timeline of match events
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        timeline = get_match_timeline(match)
        return JsonResponse({'timeline': timeline})
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

@biro_router.get("/matches/{match_id}/current-minute", auth=biro_auth)
def get_current_minute(request, match_id: int):
    """
    Get current match minute based on match progression logic
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        # Check all events for this match
        events = match.events.all().order_by('id')
        
        # Check if there was a half_time event
        half_time_event = events.filter(event_type='half_time').first()
        full_time_event = events.filter(event_type='full_time').first()
        match_start_events = events.filter(event_type='match_start').order_by('id')
        
        current_minute = None
        current_extra_time = None
        match_status = get_match_status(match)
        
        if full_time_event:
            # Match is over
            current_minute = full_time_event.minute
            current_extra_time = full_time_event.minute_extra_time
        elif half_time_event and not match_start_events.filter(half=2).exists():
            # Half time break
            current_minute = half_time_event.minute
            current_extra_time = half_time_event.minute_extra_time
            match_status = "half_time"
        else:
            # Match is in progress - calculate current minute
            from django.utils import timezone
            now = timezone.now()
            
            if match_start_events.filter(half=2).exists():
                # Second half logic
                second_half_start = match_start_events.filter(half=2).first()
                if second_half_start and second_half_start.exact_time:
                    elapsed_seconds = (now - second_half_start.exact_time).total_seconds()
                    elapsed_minutes = int(elapsed_seconds / 60)
                    
                    first_half_end = get_first_half_end_minute(match)
                    
                    # Match the first half pattern:
                    # elapsed_minutes 1-10: show as normal minutes
                    # elapsed_minutes 11+: show as last_regular_minute + extra_time
                    if elapsed_minutes <= 10:
                        current_minute = first_half_end + elapsed_minutes
                        current_extra_time = None
                    else:
                        # Extra time: minute stays at the end of regular second half time
                        current_minute = first_half_end + 10
                        current_extra_time = elapsed_minutes - 10
                else:
                    current_minute = get_first_half_end_minute(match) + 1
                    current_extra_time = None
            else:
                # First half logic
                first_half_start = match_start_events.filter(half=1).first()
                if first_half_start and first_half_start.exact_time:
                    elapsed_seconds = (now - first_half_start.exact_time).total_seconds()
                    elapsed_minutes = int(elapsed_seconds / 60)
                    
                    if elapsed_minutes < 11:
                        current_minute = max(1, elapsed_minutes)
                        current_extra_time = None
                    else:
                        current_minute = 10
                        current_extra_time = elapsed_minutes - 10
                else:
                    current_minute = 1
                    current_extra_time = None
        
        return JsonResponse({
            'current_minute': current_minute,
            'current_extra_time': current_extra_time,
            'status': match_status,
            'formatted_time': format_match_time(current_minute, current_extra_time) if current_minute else None
        })
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

@biro_router.get("/matches/{match_id}/statistics", auth=biro_auth)
def get_match_statistics(request, match_id: int):
    """
    Get comprehensive match statistics
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        team1_stats = get_team_statistics(1, match)
        team2_stats = get_team_statistics(2, match)
        half_time_score = get_half_time_score(match)
        final_score = match.result()
        
        return JsonResponse({
            'match_id': match.id,
            'team1': team1_stats,
            'team2': team2_stats,
            'half_time_score': half_time_score,
            'final_score': final_score,
            'status': get_match_status(match)
        })
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

@biro_router.post("/matches/{match_id}/validate-event", auth=biro_auth)
def validate_event_endpoint(request, match_id: int, payload: EventCreateSchema):
    """
    Validate event data before creation (dry run)
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        validation_result = validate_event_data(
            payload.event_type,
            payload.minute,
            payload.half,
            payload.player_id,
            match
        )
        
        return JsonResponse(validation_result)
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

# Bulk operations for referees

@biro_router.post("/matches/{match_id}/quick-goal", auth=biro_auth)
def quick_add_goal(request, match_id: int, payload: QuickGoalSchema):
    """
    Quick action to add a goal with minimal data
    Expected payload: {"player_id": int, "minute": int, "half": int}
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        # Extract validated data from schema
        player_id = payload.player_id
        minute = payload.minute
        minute_extra_time = payload.minute_extra_time
        half = payload.half
        
        # Validate player belongs to match teams
        try:
            player = Player.objects.get(
                id=player_id,
                team__in=[match.team1, match.team2]
            )
        except Player.DoesNotExist:
            return JsonResponse({'error': 'Player not found in match teams'}, status=400)
        
        # Create goal event
        event = Event.objects.create(
            event_type='goal',
            half=half,
            minute=minute,
            minute_extra_time=minute_extra_time,
            player=player,
            exact_time=timezone.now()
        )
        
        match.events.add(event)
        
        return JsonResponse({
            'message': 'Goal added successfully',
            'event_id': event.id,
            'player_name': player.name,
            'minute': minute,
            'minute_extra_time': minute_extra_time,
            'formatted_time': f"{minute}+{minute_extra_time}'" if minute_extra_time else f"{minute}'",
            'new_score': match.result()
        })
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

@biro_router.post("/matches/{match_id}/quick-card", auth=biro_auth)
def quick_add_card(request, match_id: int, payload: QuickCardSchema):
    """
    Quick action to add a yellow or red card
    Expected payload: {"player_id": int, "minute": int, "card_type": "yellow"|"red", "half": int}
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        # Extract validated data from schema
        player_id = payload.player_id
        minute = payload.minute
        minute_extra_time = payload.minute_extra_time
        card_type = payload.card_type
        half = payload.half
        
        if card_type not in ['yellow', 'red']:
            return JsonResponse({'error': 'card_type must be "yellow" or "red"'}, status=400)
        
        # Validate player belongs to match teams
        try:
            player = Player.objects.get(
                id=player_id,
                team__in=[match.team1, match.team2]
            )
        except Player.DoesNotExist:
            return JsonResponse({'error': 'Player not found in match teams'}, status=400)
        
        # Create card event
        event_type = 'yellow_card' if card_type == 'yellow' else 'red_card'
        event = Event.objects.create(
            event_type=event_type,
            half=half,
            minute=minute,
            minute_extra_time=minute_extra_time,
            player=player,
            exact_time=timezone.now()
        )
        
        match.events.add(event)
        
        return JsonResponse({
            'message': f'{card_type.capitalize()} card added successfully',
            'event_id': event.id,
            'player_name': player.name,
            'minute': minute,
            'minute_extra_time': minute_extra_time,
            'formatted_time': f"{minute}+{minute_extra_time}'" if minute_extra_time else f"{minute}'",
            'card_type': card_type
        })
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

@biro_router.post("/matches/{match_id}/extra-time", auth=biro_auth)
def add_extra_time(request, match_id: int, payload: ExtraTimeSchema):
    """
    Add extra time to a match half
    Expected payload: {"extra_time_minutes": int, "half": int}
    """
    try:
        profile = request.auth.profile
        match = get_object_or_404(Match, id=match_id)
        
        # Extract validated data from schema
        extra_time_minutes = payload.extra_time_minutes
        half = payload.half
        
        # Create extra time event - use dynamic end of regular time for each half
        if half == 1:
            regular_time_end = get_first_half_end_minute(match)
        else:
            regular_time_end = get_match_end_minute(match)
        
        event = Event.objects.create(
            event_type='extra_time',
            half=half,
            minute=regular_time_end,
            extra_time=extra_time_minutes,
            exact_time=timezone.now()
        )
        
        match.events.add(event)
        
        return JsonResponse({
            'message': f'{extra_time_minutes} minutes of extra time added to half {half}',
            'event_id': event.id,
            'extra_time_minutes': extra_time_minutes,
            'half': half
        })
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

# Referee dashboard endpoint

@biro_router.get("/dashboard", auth=biro_auth)
def referee_dashboard(request):
    """
    Get referee dashboard with upcoming and current matches
    """
    try:
        profile = request.auth.profile
        now = timezone.now()
        
        # Get today's matches (all matches, not just assigned to this referee)
        today_matches = Match.objects.filter(
            datetime__date=now.date()
        ).order_by('datetime')
        
        # Get upcoming matches (next 7 days, all matches)
        upcoming_matches = Match.objects.filter(
            datetime__gt=now,
            datetime__lte=now + timedelta(days=7)
        ).order_by('datetime')
        
        # Get recent completed matches (all matches from last 7 days)
        recent_matches = Match.objects.filter(
            datetime__lt=now,
            datetime__gte=now - timedelta(days=7)
        ).order_by('-datetime')
        
        # Process matches to include status
        def process_match_list(matches):
            result = []
            for match in matches:
                result.append({
                    'id': match.id,
                    'team1': str(match.team1),
                    'team2': str(match.team2),
                    'datetime': match.datetime.isoformat(),
                    'status': get_match_status(match),
                    'score': match.result()
                })
            return result
        
        return JsonResponse({
            'today_matches': process_match_list(today_matches),
            'upcoming_matches': process_match_list(upcoming_matches),
            'recent_matches': process_match_list(recent_matches),
            'total_matches': Match.objects.count()
        })
    except AttributeError:
        return JsonResponse({'error': 'No profile found'}, status=403)

