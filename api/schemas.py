from ninja import ModelSchema, Schema
from .models import Team, Tournament, Match, Event, Player, Profile, Round, Kozlemeny, Photo, Szankcio
from django.contrib.auth.models import User

class UserSchema(ModelSchema):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']

class ProfileSchema(ModelSchema):
    user: UserSchema
    player: 'PlayerSchema | None' = None
    class Meta:
        model = Profile
        fields = ['id', 'user', 'biro', 'player']

class PlayerSchema(ModelSchema):
    class Meta:
        model = Player
        fields = '__all__'

class PlayerExtendedSchema(Schema):
    """Extended player schema with computed fields"""
    id: int
    name: str
    csk: bool
    start_year: int | None = None
    tagozat: str | None = None
    effective_start_year: int | None = None  # From get_start_year()
    effective_tagozat: str | None = None     # From get_tagozat()

class TeamExtendedSchema(Schema):
    """Extended team schema with computed fields"""
    id: int
    name: str | None = None
    start_year: int
    tagozat: str
    color: str  # Always returns computed color from get_team_color()
    logo_url: str | None = None
    active: bool
    players: list[PlayerExtendedSchema] = []

class TournamentSchema(ModelSchema):
    class Meta:
        model = Tournament
        fields = '__all__'

class TournamentCreateSchema(Schema):
    name: str
    start_date: str | None = None
    end_date: str | None = None
    registration_open: bool = False
    registration_deadline: str | None = None
    registration_by_link: str | None = None

class TournamentUpdateSchema(Schema):
    name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    registration_open: bool | None = None
    registration_deadline: str | None = None
    registration_by_link: str | None = None

class RoundSchema(ModelSchema):
    tournament: TournamentSchema | None = None
    class Meta:
        model = Round
        fields = '__all__'
        

class TeamSchema(ModelSchema):
    tournament: TournamentSchema | None = None
    players: list[PlayerSchema] = []
    class Meta:
        model = Team
        fields = '__all__'

class TeamCreateSchema(Schema):
    name: str | None = None
    start_year: int
    tagozat: str
    color: str | None = None
    logo_url: str | None = None
    active: bool = True

class TeamUpdateSchema(Schema):
    name: str | None = None
    start_year: int | None = None
    tagozat: str | None = None
    color: str | None = None
    logo_url: str | None = None
    active: bool | None = None

class EventSchema(ModelSchema):
    player: PlayerSchema | None = None
    match: 'MatchSchema | None' = None

    class Meta:
        model = Event
        fields = '__all__'

class EndHalfSchema(Schema):
    half: int
    minute: int
    minute_extra_time: int | None = None

class EndMatchSchema(Schema):
    half: int
    minute: int
    minute_extra_time: int | None = None


class EventResponseSchema(Schema):
    """Enhanced event schema with formatted time for API responses"""
    id: int
    event_type: str
    half: int | None = None
    minute: int
    minute_extra_time: int | None = None
    formatted_time: str  # Computed field for "X+A" format
    exact_time: str | None = None
    player: PlayerSchema | None = None
    extra_time: int | None = None

# Photo schemas

class PhotoSchema(ModelSchema):
    uploaded_by: ProfileSchema | None = None

    class Meta:
        model = Photo
        fields = '__all__'

class PhotoCreateSchema(Schema):
    url: str
    title: str | None = None
    description: str | None = None

class PhotoUpdateSchema(Schema):
    url: str | None = None
    title: str | None = None
    description: str | None = None

class MatchSchema(ModelSchema):
    team1: TeamSchema | None = None
    team2: TeamSchema | None = None
    tournament: TournamentSchema | None = None
    round_obj: RoundSchema | None = None
    referee: ProfileSchema | None = None
    events: list[EventResponseSchema] = []
    photos: list[PhotoSchema] = []
    status: str | None = None

    class Meta:
        model = Match
        fields = '__all__'

class StandingSchema(Schema):
    id: int
    nev: str
    meccsek: int
    wins: int
    ties: int
    losses: int
    lott: int
    kapott: int
    golarany: int
    points: int


class TopScorerSchema(Schema):
    id: int
    name: str
    goals: int

class AllEventsSchema(Schema):
    goals: list[EventResponseSchema] = []
    yellow_cards: list[EventResponseSchema] = []
    red_cards: list[EventResponseSchema] = []

# Közlemény schemas

class KozlemenySchema(ModelSchema):
    author: ProfileSchema | None = None

    class Meta:
        model = Kozlemeny
        fields = '__all__'

class KozlemenyCreateSchema(Schema):
    title: str
    content: str
    active: bool = True
    priority: str = 'normal'

class KozlemenyUpdateSchema(Schema):
    title: str | None = None
    content: str | None = None
    active: bool | None = None
    priority: str | None = None

# Szankció schemas

class SzankcioSchema(ModelSchema):
    team: TeamSchema | None = None
    tournament: TournamentSchema | None = None

    class Meta:
        model = Szankcio
        fields = '__all__'

class SzankcioCreateSchema(Schema):
    team_id: int
    tournament_id: int
    minus_points: int
    reason: str | None = None

class SzankcioUpdateSchema(Schema):
    minus_points: int | None = None
    reason: str | None = None

# Time sync schema

class TimeSyncSchema(Schema):
    server_time: str  # ISO format datetime string
    timezone: str     # Server timezone
    timestamp: int    # Unix timestamp

# Authentication schemas

class LoginSchema(Schema):
    username: str
    password: str

class LoginResponseSchema(Schema):
    success: bool
    message: str
    user: UserSchema | None = None
    token: str | None = None

class LogoutResponseSchema(Schema):
    success: bool
    message: str

class AuthStatusSchema(Schema):
    authenticated: bool
    user: UserSchema | None = None

# Referee (Bíró) specific schemas

class QuickGoalSchema(Schema):
    player_id: int
    minute: int
    minute_extra_time: int | None = None  # Support for extra time (A in X+A format)
    half: int = 1

class QuickOwnGoalSchema(Schema):
    player_id: int  # Player who scored the own goal
    minute: int
    minute_extra_time: int | None = None  # Support for extra time (A in X+A format)
    half: int = 1

class QuickCardSchema(Schema):
    player_id: int
    minute: int
    minute_extra_time: int | None = None  # Support for extra time (A in X+A format)
    half: int = 1
    card_type: str  # "yellow" or "red"

class ExtraTimeSchema(Schema):
    extra_time_minutes: int
    half: int = 1

class EventCreateSchema(Schema):
    event_type: str  # From EVENT_TYPES choices
    half: int | None = None
    minute: int
    minute_extra_time: int | None = None
    player_id: int | None = None
    extra_time: int | None = None

class EventUpdateSchema(Schema):
    event_type: str | None = None
    half: int | None = None
    minute: int | None = None
    minute_extra_time: int | None = None
    player_id: int | None = None
    extra_time: int | None = None

class MatchUpdateSchema(Schema):
    datetime: str | None = None
    referee_id: int | None = None
    status: str | None = None

class MatchStatusSchema(Schema):
    id: int
    team1: TeamExtendedSchema
    team2: TeamExtendedSchema
    datetime: str
    referee: ProfileSchema | None = None
    events: list[EventResponseSchema] = []
    score: tuple[int, int]  # (team1_goals, team2_goals)
    match_status: str  # 'not_started', 'first_half', 'half_time', 'second_half', 'extra_time', 'finished'
    status: str | None = None  # 'active', 'cancelled_new_date', 'cancelled_no_date'

class JegyzokonyeSchema(Schema):
    """Complete match record schema for detailed match reports"""
    match_id: int
    team1: TeamExtendedSchema
    team2: TeamExtendedSchema
    final_score: tuple[int, int]
    datetime: str
    referee: ProfileSchema | None = None
    events: list[EventResponseSchema] = []
    goals_team1: list[EventResponseSchema] = []
    goals_team2: list[EventResponseSchema] = []
    yellow_cards: list[EventResponseSchema] = []
    red_cards: list[EventResponseSchema] = []
    half_time_score: tuple[int, int]
    match_duration: int | None = None  # Duration in minutes
    notes: str | None = None

class LiveMatchUpdateSchema(Schema):
    """Schema for real-time match updates"""
    match_id: int
    action: str  # 'add_event', 'remove_event', 'update_event', 'start_match', 'end_match'
    event_data: EventCreateSchema | None = None
    event_id: int | None = None

# Undo operation schemas

class UndoEventResponseSchema(Schema):
    """Response schema for undo operations"""
    message: str
    removed_event: dict | None = None
    undone_event: dict | None = None
    updated_score: tuple[int, int]
    timestamp: str

class EventValidationSchema(Schema):
    """Schema for event validation responses"""
    can_remove: bool
    validation_errors: list[str] = []
    warnings: list[str] = []
    event_details: dict | None = None

