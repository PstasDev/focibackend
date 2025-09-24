from ninja import ModelSchema, Schema
from .models import Team, Tournament, Match, Event, Player, Profile, Round
from django.contrib.auth.models import User

class UserSchema(ModelSchema):
    class Meta:
        model = User
        fields = '__all__'

class ProfileSchema(ModelSchema):
    player: 'PlayerSchema | None' = None
    class Meta:
        model = Profile
        fields = '__all__'

class PlayerSchema(ModelSchema):
    class Meta:
        model = Player
        fields = '__all__'

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
    number: int | None = None

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
    tournament_id: int
    name: str | None = None
    start_year: int
    tagozat: str
    active: bool = True

class TeamUpdateSchema(Schema):
    name: str | None = None
    start_year: int | None = None
    tagozat: str | None = None
    active: bool | None = None

class EventSchema(ModelSchema):
    player: PlayerSchema | None = None

    class Meta:
        model = Event
        fields = '__all__'

class MatchSchema(Schema):
    team1: TeamSchema | None = None
    team2: TeamSchema | None = None
    tournament: TournamentSchema | None = None
    round_obj: RoundSchema | None = None
    referee: ProfileSchema | None = None
    team1_score: int = 0
    team2_score: int = 0
    team1_yellow_cards: int = 0
    team2_yellow_cards: int = 0
    team1_red_cards: int = 0
    team2_red_cards: int = 0

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
    position: int


class TopScorerSchema(Schema):
    id: int
    name: str
    goals: int

class AllEventsSchema(Schema):
    goals: list[EventSchema] = []
    yellow_cards: list[EventSchema] = []
    red_cards: list[EventSchema] = []

