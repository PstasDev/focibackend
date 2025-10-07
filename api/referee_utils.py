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
    Get the current base minute of the match (without extra time)
    
    This returns the base minute from the most recent event.
    For example, if the last event was at "10+4'", this returns 10.
    
    Args:
        match: Match object
        
    Returns:
        Current base minute of the match or None if no events
    """
    # Get the most recent event by ID (most recently created)
    # This ensures we get the actual latest event regardless of minute ordering
    last_event = match.events.order_by('-id').first()
    
    if last_event:
        return last_event.minute
    
    return None


def get_current_extra_time(match: Match) -> Optional[int]:
    """
    Get the current extra time minute of the match
    
    This returns the extra time from the most recent event.
    For example, if the last event was at "10+4'", this returns 4.
    
    Args:
        match: Match object
        
    Returns:
        Current extra time minute or None if no extra time
    """
    # Get the most recent event by ID (most recently created)
    last_event = match.events.order_by('-id').first()
    
    if last_event:
        return last_event.minute_extra_time
    
    return None


def get_first_half_end_minute(match) -> int:
    """
    Get the minute when first half ended (considering extra time)
    
    Args:
        match: Match object
        
    Returns:
        Minute when first half ended (looks at actual half_time event)
    """
    half_time_event = match.events.filter(event_type='half_time').first()
    if half_time_event:
        return half_time_event.minute
    
    # If no half_time event, check the last event from first half
    first_half_events = match.events.filter(half=1).order_by('-minute', '-minute_extra_time')
    last_first_half_event = first_half_events.first()
    if last_first_half_event:
        return last_first_half_event.minute + (last_first_half_event.minute_extra_time or 0)
    
    # Fallback: no events in first half recorded yet
    return 1


def get_second_half_start_minute(match) -> int:
    """
    Get the minute when second half started
    
    Args:
        match: Match object
        
    Returns:
        Minute when second half started (based on actual events)
    """
    # Look for second half start event
    second_half_start = match.events.filter(event_type='second_half').first()
    if second_half_start:
        return second_half_start.minute
    
    # If no explicit second half start, use first event of second half
    first_second_half_event = match.events.filter(half=2).order_by('minute', 'minute_extra_time').first()
    if first_second_half_event:
        return first_second_half_event.minute
    
    # Fallback: first half end + 1
    return get_first_half_end_minute(match) + 1


def get_match_end_minute(match) -> int:
    """
    Get the minute when match ended (considering extra time)
    
    Args:
        match: Match object
        
    Returns:
        Minute when match ended (based on actual events, not assumptions)
    """
    # Check for match_end first, then full_time
    match_end_event = match.events.filter(event_type__in=['match_end', 'full_time']).last()
    if match_end_event:
        return match_end_event.minute + (match_end_event.minute_extra_time or 0)
    
    # If no end event, get the last event in the match
    last_event = match.events.order_by('-minute', '-minute_extra_time').first()
    if last_event:
        return last_event.minute + (last_event.minute_extra_time or 0)
    
    # No events at all
    return 0


def get_current_match_minute_with_extra_time(match) -> tuple[int, int]:
    """
    Get current match minute and extra time separately
    
    Args:
        match: Match object
        
    Returns:
        Tuple of (base_minute, extra_time_minute)
    """
    # Simplified version - in a real implementation, this would calculate
    # based on match start time and current time
    events = match.events.all().order_by('-minute', '-minute_extra_time')
    last_event = events.first()
    
    if last_event:
        return (last_event.minute, last_event.minute_extra_time or 0)
    
    return (0, 0)