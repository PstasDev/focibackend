from ninja import ModelSchema, Schema
from .models import Team, Tournament, Match, Event, Player, Profile, Round, Kozlemeny
from django.contrib.auth.models import User

class UserSchema(ModelSchema):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']

class ProfileSchema(ModelSchema):
    player: 'PlayerSchema | None' = None
    class Meta:
        model = Profile
        fields = '__all__'

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
    active: bool = True

class TeamUpdateSchema(Schema):
    name: str | None = None
    start_year: int | None = None
    tagozat: str | None = None
    color: str | None = None
    active: bool | None = None

class EventSchema(ModelSchema):
    player: PlayerSchema | None = None
    match: 'MatchSchema | None' = None

    class Meta:
        model = Event
        fields = '__all__'

class MatchSchema(ModelSchema):
    team1: TeamSchema | None = None
    team2: TeamSchema | None = None
    tournament: TournamentSchema | None = None
    round_obj: RoundSchema | None = None
    referee: ProfileSchema | None = None
    events: list[EventSchema] = []

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
    goals: list[EventSchema] = []
    yellow_cards: list[EventSchema] = []
    red_cards: list[EventSchema] = []

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

