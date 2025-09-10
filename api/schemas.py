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

class EventSchema(ModelSchema):
    player: PlayerSchema | None = None

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

