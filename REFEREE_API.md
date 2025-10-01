# Referee (Bíró) API Endpoints Documentation

This document describes the referee-only endpoints for managing live matches and creating detailed match records (jegyzőkönyv).

## Authentication

All referee endpoints require:
1. Valid JWT authentication token (stored in `auth_token` cookie)
2. User profile with `biro=True` flag

Base URL for all referee endpoints: `/api/biro/`

## Overview of Endpoints

### 1. Match Management

#### Get Referee's Matches
- **GET** `/my-matches`
- Returns all matches assigned to the current referee
- Response: Array of `MatchSchema` objects

#### Get Live Matches
- **GET** `/live-matches`
- Returns matches that are currently live or scheduled for today/tomorrow
- Response: Array of `MatchStatusSchema` objects with additional status information

#### Get Specific Match
- **GET** `/matches/{match_id}`
- Returns detailed information about a specific match
- Response: `MatchStatusSchema` object

### 2. Live Match Updates

#### Add Event to Match
- **POST** `/matches/{match_id}/events`
- Add any type of event (goal, card, match control events)
- Body: `EventCreateSchema`
```json
{
  "event_type": "goal|yellow_card|red_card|match_start|half_time|full_time|match_end",
  "minute": 45,
  "half": 1,
  "minute_extra_time": 3,  // optional
  "player_id": 123,        // optional, required for player events
  "extra_time": 5          // optional
}
```

#### Update Event
- **PUT** `/matches/{match_id}/events/{event_id}`
- Update existing event
- Body: `EventUpdateSchema` (same as create but all fields optional)

#### Remove Event
- **DELETE** `/matches/{match_id}/events/{event_id}`
- Remove an event from the match

### 3. Quick Actions

#### Start Match
- **POST** `/matches/{match_id}/start-match`
- Automatically creates a "match_start" event
- No body required

#### End Half
- **POST** `/matches/{match_id}/end-half`
- Automatically creates "half_time" or "full_time" event based on current state
- No body required

#### End Match
- **POST** `/matches/{match_id}/end-match`
- Automatically creates "match_end" event
- No body required

#### Quick Add Goal
- **POST** `/matches/{match_id}/quick-goal`
- Simplified goal addition
- Body:
```json
{
  "player_id": 123,
  "minute": 67,
  "half": 2
}
```

#### Quick Add Card
- **POST** `/matches/{match_id}/quick-card`
- Simplified card addition
- Body:
```json
{
  "player_id": 123,
  "minute": 30,
  "card_type": "yellow",  // or "red"
  "half": 1
}
```

### 4. Match Records (Jegyzőkönyv)

#### Get Complete Match Record
- **GET** `/matches/{match_id}/jegyzokonyv`
- Returns comprehensive match report with all details
- Response: `JegyzokonyeSchema` object including:
  - Team information and players
  - Final and half-time scores
  - Complete event timeline
  - Goals separated by team
  - All cards
  - Match duration
  - Referee information

### 5. Utility Endpoints

#### Get Match Timeline
- **GET** `/matches/{match_id}/timeline`
- Returns chronological timeline of all match events
- Response: Array of timeline events with metadata

#### Get Current Match Minute
- **GET** `/matches/{match_id}/current-minute`
- Returns current minute based on elapsed time since match start
- Response:
```json
{
  "current_minute": 67,
  "status": "second_half",
  "formatted_time": "67'"
}
```

#### Get Match Statistics
- **GET** `/matches/{match_id}/statistics`
- Returns comprehensive statistics for both teams
- Response: Detailed statistics including player-level data

#### Validate Event
- **POST** `/matches/{match_id}/validate-event`
- Dry run validation of event data before creation
- Body: `EventCreateSchema`
- Response: Validation result with errors/warnings

#### Referee Dashboard
- **GET** `/dashboard`
- Overview of referee's schedule and recent activity
- Response:
```json
{
  "today_matches": [...],
  "upcoming_matches": [...],
  "recent_matches": [...],
  "total_assigned_matches": 25
}
```

## Event Types

The following event types are available:

- `match_start` - Match begins
- `goal` - Goal scored (requires player_id)
- `yellow_card` - Yellow card shown (requires player_id)
- `red_card` - Red card shown (requires player_id)
- `half_time` - End of first half
- `full_time` - End of second half (90 minutes)
- `extra_time` - Extra time begins
- `match_end` - Match completely finished

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200` - Success
- `400` - Bad request (validation errors)
- `401` - Authentication required
- `403` - Access denied (not a referee or not assigned to match)
- `404` - Match/Event not found

Error responses include descriptive messages:
```json
{
  "error": "Invalid event type",
  "message": "Event type 'invalid' is not supported"
}
```

## Usage Examples

### Complete Match Flow

1. **Start a match:**
```bash
POST /api/biro/matches/123/start-match
```

2. **Add a goal in 23rd minute:**
```bash
POST /api/biro/matches/123/quick-goal
{
  "player_id": 456,
  "minute": 23,
  "half": 1
}
```

3. **Show yellow card:**
```bash
POST /api/biro/matches/123/quick-card
{
  "player_id": 789,
  "minute": 35,
  "card_type": "yellow",
  "half": 1
}
```

4. **End first half:**
```bash
POST /api/biro/matches/123/end-half
```

5. **Get final match report:**
```bash
GET /api/biro/matches/123/jegyzokonyv
```

This API provides comprehensive tools for referees to manage live matches and generate detailed match records efficiently.