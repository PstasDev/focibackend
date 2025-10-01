"""
Utility functions specifically for referee (bíró) operations
"""
from django.utils import timezone
from .models import Match, Event, Player
from typing import Optional, List, Dict, Any


def get_match_status(match: Match) -> str:
    """
    Determine the current status of a match based on its events
    
    Args:
        match: Match object
        
    Returns:
        String indicating match status: 'not_started', 'first_half', 'half_time', 
        'second_half', 'extra_time', 'finished'
    """
    events = match.events.all().order_by('minute', 'id')
    
    if not events.filter(event_type='match_start').exists():
        return "not_started"
    elif events.filter(event_type='match_end').exists():
        return "finished"
    elif events.filter(event_type='extra_time').exists():
        return "extra_time"
    elif events.filter(event_type='full_time').exists():
        return "second_half"
    elif events.filter(event_type='half_time').exists():
        return "half_time"
    else:
        return "first_half"


def validate_event_data(event_type: str, minute: int, half: Optional[int], 
                       player_id: Optional[int], match: Match) -> Dict[str, Any]:
    """
    Validate event data for creation
    
    Args:
        event_type: Type of event
        minute: Minute of the event
        half: Half of the match (1 or 2)
        player_id: ID of player involved (if applicable)
        match: Match object
        
    Returns:
        Dictionary with validation result and any errors
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Validate event type
    valid_event_types = [choice[0] for choice in Event.EVENT_TYPES]
    if event_type not in valid_event_types:
        result['valid'] = False
        result['errors'].append(f'Invalid event type: {event_type}')
    
    # Validate minute
    if minute < 0:
        result['valid'] = False
        result['errors'].append('Minute cannot be negative')
    elif minute > 120:  # Including extra time
        result['warnings'].append('Minute is beyond normal match time')
    
    # Validate half
    if half and half not in [1, 2]:
        result['valid'] = False
        result['errors'].append('Half must be 1 or 2')
    
    # Validate player for events that require players
    player_required_events = ['goal', 'yellow_card', 'red_card']
    if event_type in player_required_events:
        if not player_id:
            result['valid'] = False
            result['errors'].append(f'Player ID required for {event_type} events')
        else:
            # Check if player belongs to one of the teams
            try:
                player = Player.objects.get(id=player_id)
                if player not in match.team1.players.all() and player not in match.team2.players.all():
                    result['valid'] = False
                    result['errors'].append('Player does not belong to either team in this match')
            except Player.DoesNotExist:
                result['valid'] = False
                result['errors'].append('Player not found')
    
    # Validate match state for certain events
    match_status = get_match_status(match)
    
    if event_type == 'match_start' and match_status != 'not_started':
        result['valid'] = False
        result['errors'].append('Match has already started')
    
    if event_type == 'half_time' and match_status not in ['first_half']:
        result['valid'] = False
        result['errors'].append('Cannot end first half - match is not in first half')
    
    if event_type == 'full_time' and match_status not in ['second_half']:
        result['valid'] = False
        result['errors'].append('Cannot end second half - match is not in second half')
    
    if event_type == 'match_end' and match_status == 'finished':
        result['valid'] = False
        result['errors'].append('Match has already ended')
    
    return result


def get_half_time_score(match: Match) -> tuple[int, int]:
    """
    Calculate the score at half time
    
    Args:
        match: Match object
        
    Returns:
        Tuple of (team1_goals, team2_goals) at half time
    """
    # Get goals from first half only (minute <= 45)
    first_half_goals = match.events.filter(
        event_type='goal',
        minute__lte=45
    )
    
    goals_team1 = first_half_goals.filter(player__in=match.team1.players.all()).count()
    goals_team2 = first_half_goals.filter(player__in=match.team2.players.all()).count()
    
    return (goals_team1, goals_team2)


def get_match_timeline(match: Match) -> List[Dict[str, Any]]:
    """
    Get chronological timeline of match events
    
    Args:
        match: Match object
        
    Returns:
        List of events in chronological order with additional metadata
    """
    events = match.events.all().order_by('minute', 'minute_extra_time', 'id')
    timeline = []
    
    for event in events:
        timeline_event = {
            'id': event.id,
            'event_type': event.event_type,
            'event_type_display': event.get_event_type_display(),
            'minute': event.minute,
            'minute_extra_time': event.minute_extra_time,
            'half': event.half,
            'player': {
                'id': event.player.id,
                'name': event.player.name
            } if event.player else None,
            'team': None,
            'exact_time': event.exact_time.isoformat() if event.exact_time else None
        }
        
        # Determine which team the player belongs to
        if event.player:
            if event.player in match.team1.players.all():
                timeline_event['team'] = 'team1'
            elif event.player in match.team2.players.all():
                timeline_event['team'] = 'team2'
        
        timeline.append(timeline_event)
    
    return timeline


def get_player_statistics(player: Player, match: Match) -> Dict[str, Any]:
    """
    Get statistics for a specific player in a specific match
    
    Args:
        player: Player object
        match: Match object
        
    Returns:
        Dictionary with player statistics for this match
    """
    events = match.events.filter(player=player)
    
    return {
        'player_id': player.id,
        'player_name': player.name,
        'goals': events.filter(event_type='goal').count(),
        'yellow_cards': events.filter(event_type='yellow_card').count(),
        'red_cards': events.filter(event_type='red_card').count(),
        'total_events': events.count()
    }


def get_team_statistics(team_id: int, match: Match) -> Dict[str, Any]:
    """
    Get statistics for a team in a specific match
    
    Args:
        team_id: ID of the team (1 for team1, 2 for team2)
        match: Match object
        
    Returns:
        Dictionary with team statistics for this match
    """
    if team_id == 1:
        team = match.team1
        team_name = str(team)
    elif team_id == 2:
        team = match.team2
        team_name = str(team)
    else:
        raise ValueError("team_id must be 1 or 2")
    
    # Get all events for players in this team
    team_events = match.events.filter(player__in=team.players.all())
    
    return {
        'team_id': team_id,
        'team_name': team_name,
        'goals': team_events.filter(event_type='goal').count(),
        'yellow_cards': team_events.filter(event_type='yellow_card').count(),
        'red_cards': team_events.filter(event_type='red_card').count(),
        'players': [get_player_statistics(player, match) for player in team.players.all()]
    }


def can_referee_edit_match(user, match: Match) -> bool:
    """
    Check if a user (referee) can edit a specific match
    
    Args:
        user: Django User object
        match: Match object
        
    Returns:
        Boolean indicating if referee can edit this match
    """
    try:
        profile = user.profile
        return profile.biro and match.referee == profile
    except AttributeError:
        return False


def format_match_time(minute: int, minute_extra_time: Optional[int] = None) -> str:
    """
    Format match time for display
    
    Args:
        minute: Match minute
        minute_extra_time: Extra time minute (optional)
        
    Returns:
        Formatted time string (e.g., "45'", "90+3'")
    """
    if minute_extra_time:
        return f"{minute}+{minute_extra_time}'"
    return f"{minute}'"


def get_current_match_minute(match: Match) -> Optional[int]:
    """
    Calculate current match minute based on start time and current time
    
    Args:
        match: Match object
        
    Returns:
        Current minute of the match or None if match hasn't started
    """
    match_start_event = match.events.filter(event_type='match_start').first()
    if not match_start_event or not match_start_event.exact_time:
        return None
    
    now = timezone.now()
    elapsed = now - match_start_event.exact_time
    minutes_elapsed = int(elapsed.total_seconds() / 60)
    
    # Account for half time break (assume 15 minutes)
    half_time_event = match.events.filter(event_type='half_time').first()
    if half_time_event and half_time_event.exact_time:
        # Check if we're in second half
        if now > half_time_event.exact_time:
            half_time_break = 15  # minutes
            minutes_elapsed -= half_time_break
            minutes_elapsed = max(45, minutes_elapsed)  # Second half starts at 45'
    
    return min(minutes_elapsed, 120)  # Cap at 120 minutes