#!/usr/bin/env python3
"""
Debug script to analyze scoring issues in the football tournament API
"""
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'focibackend.settings')
django.setup()

from api.models import Match, Event, Team, Tournament, Player

def debug_scoring():
    print("=== SCORING DEBUG ANALYSIS ===\n")
    
    # Get the current tournament
    tournaments = Tournament.objects.all()
    print(f"Total tournaments: {tournaments.count()}")
    for t in tournaments:
        print(f"- {t.name} (ID: {t.id})")
    
    # Get the latest tournament
    tournament = tournaments.first()
    if not tournament:
        print("No tournaments found!")
        return
    
    print(f"\nAnalyzing tournament: {tournament.name}")
    
    # Get matches in this tournament
    matches = Match.objects.filter(tournament=tournament)
    print(f"Total matches: {matches.count()}")
    
    for match in matches:
        print(f"\n--- MATCH {match.id}: {match.team1} vs {match.team2} ---")
        print(f"Date: {match.datetime}")
        
        # Get all events for this match
        events = match.events.all()
        print(f"Total events: {events.count()}")
        
        # List all events
        for event in events:
            player_name = event.player.name if event.player else "None"
            print(f"  - {event.event_type}: {player_name} at {event.minute}'")
        
        # Check goal calculation
        print(f"\n  Goal Analysis:")
        
        # Team 1 players
        team1_players = match.team1.players.all()
        print(f"  Team 1 ({match.team1}) players: {[p.name for p in team1_players]}")
        
        # Team 2 players  
        team2_players = match.team2.players.all()
        print(f"  Team 2 ({match.team2}) players: {[p.name for p in team2_players]}")
        
        # Goal events
        goal_events = match.events.filter(event_type='goal')
        print(f"  Total goal events: {goal_events.count()}")
        
        for goal in goal_events:
            if goal.player:
                # Check which team this player belongs to
                player_teams = goal.player.team_set.all()
                team_names = [str(t) for t in player_teams]
                is_team1 = goal.player in team1_players
                is_team2 = goal.player in team2_players
                print(f"    Goal by {goal.player.name} (Teams: {team_names}, Team1: {is_team1}, Team2: {is_team2})")
            else:
                print(f"    Goal with no player assigned!")
        
        # Current result calculation
        result = match.result()
        print(f"  Current result: {result}")
        
        # Manual calculation to verify
        team1_goals = match.events.filter(event_type='goal', player__in=team1_players).count()
        team2_goals = match.events.filter(event_type='goal', player__in=team2_players).count()
        print(f"  Manual calculation: Team1={team1_goals}, Team2={team2_goals}")
        
        # Check if there's a discrepancy
        if result != (team1_goals, team2_goals):
            print(f"  ⚠️  DISCREPANCY FOUND! API: {result} vs Manual: ({team1_goals}, {team2_goals})")
        else:
            print(f"  ✅ Calculations match!")

if __name__ == "__main__":
    debug_scoring()