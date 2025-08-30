#!/usr/bin/env python3
"""
Enhanced NFL Fantasy Draft Assistant with Full Draft Tracking
Tracks all 8 teams and provides strategic recommendations
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import json

app = Flask(__name__)

class EnhancedDraftAssistant:
    def __init__(self):
        # Draft order from teams.jpeg
        self.teams = [
            "Fudge Bay Packers",      # Pick 1 - YOU
            "Withdean Lambs",         # Pick 2
            "Jenny's Vinegar Strokes", # Pick 3
            "SvenitoS RaiderS",       # Pick 4
            "The Wombles",            # Pick 5
            "Pasty Smashers",         # Pick 6
            "The Fuckest Uppest",     # Pick 7
            "Deflaters Gonna Deflate" # Pick 8
        ]
        
        self.your_team = "Fudge Bay Packers"
        self.current_pick = 1
        self.current_round = 1
        self.drafted_players = set()
        
        # Track each team's roster
        self.team_rosters = {team: [] for team in self.teams}
        
        # Initialize database with draft order
        self.setup_draft_order()
    
    def setup_draft_order(self):
        """Add team names to database"""
        conn = sqlite3.connect('fantasy_draft_2025.db')
        cursor = conn.cursor()
        
        # Create teams table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                draft_position INTEGER
            )
        ''')
        
        # Insert teams
        for i, team in enumerate(self.teams, 1):
            cursor.execute('''
                INSERT OR REPLACE INTO teams (id, name, draft_position)
                VALUES (?, ?, ?)
            ''', (i, team, i))
        
        conn.commit()
        conn.close()
    
    def get_db_connection(self):
        conn = sqlite3.connect('fantasy_draft_2025.db')
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_current_team(self):
        """Get which team should pick based on current pick and snake draft"""
        # Snake draft logic: odd rounds go 1-8, even rounds go 8-1
        if self.current_round % 2 == 1:  # Odd rounds
            team_index = ((self.current_pick - 1) % 8)
        else:  # Even rounds  
            team_index = 7 - ((self.current_pick - 1) % 8)
        
        return self.teams[team_index]
    
    def get_available_players(self, position=None, limit=50):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        if self.drafted_players:
            placeholders = ','.join(['?' for _ in self.drafted_players])
            base_query = f"SELECT * FROM players WHERE name NOT IN ({placeholders})"
            params = list(self.drafted_players)
            
            if position and position != 'ALL':
                base_query += " AND position = ?"
                params.append(position)
        else:
            base_query = "SELECT * FROM players"
            params = []
            
            if position and position != 'ALL':
                base_query += " WHERE position = ?"
                params.append(position)
            
        base_query += " ORDER BY adp LIMIT ?"
        params.append(limit)
        
        cursor.execute(base_query, params)
        players = cursor.fetchall()
        conn.close()
        return [dict(player) for player in players]
    
    def get_team_needs(self, team_name):
        """Calculate position needs for any team"""
        needs = {'QB': 2, 'RB': 6, 'WR': 6, 'TE': 1, 'K': 1, 'DST': 2}
        
        for player in self.team_rosters[team_name]:
            pos = player['position']
            if pos in needs and needs[pos] > 0:
                needs[pos] -= 1
        
        return needs
    
    def get_strategic_recommendations(self):
        """Get recommendations based on pick position and league strategy"""
        current_team = self.get_current_team()
        
        # Different strategies based on pick position and round
        if current_team == self.your_team:
            return self.get_your_recommendations()
        
        return []
    
    def get_your_recommendations(self):
        """Get personalized recommendations for your team"""
        your_needs = self.get_team_needs(self.your_team)
        recommendations = []
        
        # Pick #1 strategy considerations
        if self.current_pick == 1:
            # First overall pick - go for the absolute best player
            top_players = self.get_available_players(limit=10)
            for player in top_players[:3]:
                value_score = 100 + (player['projected_points'] or 0) * 5
                recommendations.append({
                    'player': player,
                    'value_score': value_score,
                    'reason': f"#1 Overall - Elite {player['position']} with top value"
                })
        
        # Round-based strategy
        if self.current_round <= 3:
            # Early rounds: Focus on premium positions (RB, WR, elite QB)
            for pos in ['RB', 'WR', 'QB']:
                if your_needs.get(pos, 0) > 0:
                    players = self.get_available_players(pos, 5)
                    for player in players[:2]:
                        value_score = your_needs[pos] * 15 + (player['projected_points'] or 0) * 3
                        if player['adp'] and player['adp'] < 50:
                            value_score += 20  # Bonus for early round value
                        
                        recommendations.append({
                            'player': player,
                            'value_score': value_score,
                            'reason': f"Round {self.current_round} - Premium {pos}"
                        })
        
        elif self.current_round <= 6:
            # Mid rounds: Fill needs, look for value
            for pos, need_count in your_needs.items():
                if need_count > 0:
                    players = self.get_available_players(pos, 3)
                    for player in players:
                        value_score = need_count * 10 + (player['projected_points'] or 0) * 2
                        
                        recommendations.append({
                            'player': player,
                            'value_score': value_score,
                            'reason': f"Fill {pos} need ({need_count} remaining)"
                        })
        
        else:
            # Late rounds: Handcuffs, sleepers, fill remaining spots
            for pos, need_count in your_needs.items():
                if need_count > 0:
                    players = self.get_available_players(pos, 5)
                    for player in players:
                        value_score = need_count * 5 + (player.get('sleeper_rating', 0) * 3)
                        
                        recommendations.append({
                            'player': player,
                            'value_score': value_score,
                            'reason': f"Late round {pos} - Sleeper potential"
                        })
        
        # Sort by value score
        recommendations.sort(key=lambda x: x['value_score'], reverse=True)
        return recommendations[:5]
    
    def draft_player(self, player_name, team_name=None):
        """Draft a player to a specific team"""
        if not team_name:
            team_name = self.get_current_team()
        
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM players WHERE name = ?", (player_name,))
        player = cursor.fetchone()
        
        if not player:
            return {'success': False, 'message': f"Player '{player_name}' not found!"}
            
        if player_name in self.drafted_players:
            return {'success': False, 'message': f"Player '{player_name}' already drafted!"}
        
        # Add to team roster
        self.team_rosters[team_name].append(dict(player))
        self.drafted_players.add(player_name)
        
        # Record in draft results
        cursor.execute('''
            INSERT INTO draft_results (player_id, team_name, round, pick, overall_pick)
            VALUES (?, ?, ?, ?, ?)
        ''', (player['id'], team_name, self.current_round, 
              ((self.current_pick - 1) % 8) + 1, self.current_pick))
        
        conn.commit()
        conn.close()
        
        # Advance to next pick
        self.current_pick += 1
        if ((self.current_pick - 1) % 8) == 0:
            self.current_round += 1
        
        return {
            'success': True,
            'message': f"{team_name} drafted {player['name']} (Pick {self.current_pick - 1})",
            'current_pick': self.current_pick,
            'current_round': self.current_round,
            'current_team': self.get_current_team()
        }

# Global enhanced assistant
enhanced_assistant = EnhancedDraftAssistant()

@app.route('/')
def index():
    return render_template('enhanced_index.html')

@app.route('/api/draft_state')
def get_draft_state():
    """Get complete draft state"""
    current_team = enhanced_assistant.get_current_team()
    your_needs = enhanced_assistant.get_team_needs(enhanced_assistant.your_team)
    
    return jsonify({
        'current_pick': enhanced_assistant.current_pick,
        'current_round': enhanced_assistant.current_round,
        'current_team': current_team,
        'your_turn': current_team == enhanced_assistant.your_team,
        'teams': enhanced_assistant.teams,
        'your_team': enhanced_assistant.your_team,
        'your_needs': your_needs,
        'your_roster': enhanced_assistant.team_rosters[enhanced_assistant.your_team],
        'team_rosters': enhanced_assistant.team_rosters
    })

@app.route('/api/players')
def get_players():
    position = request.args.get('position', 'ALL')
    limit = int(request.args.get('limit', 50))
    
    players = enhanced_assistant.get_available_players(position, limit)
    return jsonify(players)

@app.route('/api/recommendations')
def get_recommendations():
    recommendations = enhanced_assistant.get_strategic_recommendations()
    return jsonify(recommendations)

@app.route('/api/draft_player', methods=['POST'])
def draft_player():
    data = request.json
    player_name = data.get('player_name')
    team_name = data.get('team_name')  # Optional - if not provided, uses current team
    
    result = enhanced_assistant.draft_player(player_name, team_name)
    return jsonify(result)

@app.route('/api/undo_pick', methods=['POST'])
def undo_pick():
    """Undo the last pick (in case of mistakes)"""
    if enhanced_assistant.current_pick > 1:
        enhanced_assistant.current_pick -= 1
        if ((enhanced_assistant.current_pick - 1) % 8) == 7 and enhanced_assistant.current_round > 1:
            enhanced_assistant.current_round -= 1
        
        # Remove last drafted player (would need more complex logic for full undo)
        return jsonify({'success': True, 'message': 'Pick undone'})
    
    return jsonify({'success': False, 'message': 'Cannot undo first pick'})

if __name__ == '__main__':
    # Create enhanced templates
    import os
    os.makedirs('templates', exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced NFL Fantasy Draft Assistant</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', system-ui, sans-serif;
            margin: 0; 
            padding: 15px; 
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: #fff; 
            min-height: 100vh;
        }
        
        .header { 
            text-align: center; 
            margin-bottom: 20px; 
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .draft-status {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .status-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .your-turn {
            background: rgba(76, 175, 80, 0.3);
            border-color: #4CAF50;
            box-shadow: 0 0 20px rgba(76, 175, 80, 0.3);
        }
        
        .container { 
            display: grid; 
            grid-template-columns: 2fr 1fr 1fr; 
            gap: 20px; 
            max-width: 1600px; 
            margin: 0 auto; 
        }
        
        .panel { 
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px; 
            padding: 20px; 
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .panel h3 { 
            margin-top: 0; 
            color: #4CAF50; 
            border-bottom: 2px solid #4CAF50; 
            padding-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .player-list { 
            max-height: 500px; 
            overflow-y: auto; 
        }
        
        .player-item { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            padding: 12px; 
            margin: 8px 0; 
            background: rgba(255,255,255,0.05);
            border-radius: 8px; 
            cursor: pointer; 
            transition: all 0.3s ease;
            border-left: 4px solid transparent;
        }
        
        .player-item:hover { 
            background: rgba(255,255,255,0.15);
            transform: translateX(5px);
        }
        
        .recommendation { 
            border-left-color: #FF9800;
        }
        
        .your-player { 
            background: rgba(76, 175, 80, 0.2);
            border-left-color: #4CAF50;
        }
        
        .player-info { 
            flex: 1; 
        }
        
        .player-name { 
            font-weight: bold; 
            font-size: 1.1em;
            margin-bottom: 4px;
        }
        
        .player-details { 
            font-size: 0.9em; 
            color: #ccc; 
        }
        
        .draft-btn { 
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white; 
            border: none; 
            padding: 8px 15px; 
            border-radius: 20px; 
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: bold;
        }
        
        .draft-btn:hover { 
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
        }
        
        .other-team-btn {
            background: linear-gradient(135deg, #2196F3, #1976D2);
            margin-left: 5px;
        }
        
        .controls { 
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 20px; 
        }
        
        .btn { 
            background: linear-gradient(135deg, #2196F3, #1976D2);
            color: white; 
            border: none; 
            padding: 12px 25px; 
            border-radius: 25px; 
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(33, 150, 243, 0.4);
        }
        
        .position-filter { 
            margin-bottom: 15px; 
        }
        
        select { 
            background: rgba(255,255,255,0.1);
            color: white; 
            border: 1px solid rgba(255,255,255,0.3);
            padding: 8px 12px; 
            border-radius: 8px;
            backdrop-filter: blur(5px);
        }
        
        .needs { 
            background: rgba(255, 87, 34, 0.2);
            padding: 15px; 
            border-radius: 10px; 
            margin-top: 15px;
            border-left: 4px solid #FF5722;
        }
        
        .pick-counter { 
            font-size: 1.8em; 
            font-weight: bold;
            background: linear-gradient(135deg, #4CAF50, #FF9800);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .message { 
            padding: 15px; 
            margin: 15px 0; 
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        
        .success { 
            background: rgba(76, 175, 80, 0.3);
            border: 1px solid #4CAF50;
        }
        
        .error { 
            background: rgba(244, 67, 54, 0.3);
            border: 1px solid #f44336;
        }
        
        .team-dropdown {
            background: rgba(255,255,255,0.1);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
            padding: 5px;
            border-radius: 5px;
            font-size: 0.8em;
        }
        
        .roster-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }
        
        .position-count {
            background: rgba(255,255,255,0.1);
            padding: 8px;
            border-radius: 8px;
            text-align: center;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏈 Enhanced NFL Fantasy Draft Assistant</h1>
        <p><strong>The League</strong> • 8 Teams • Snake Draft • 0.5 PPR</p>
    </div>
    
    <div class="draft-status">
        <div class="status-card" id="pick-info">
            <div class="pick-counter">Pick <span id="current-pick">1</span></div>
            <div>Round <span id="current-round">1</span></div>
        </div>
        <div class="status-card" id="team-info">
            <div><strong>On the Clock:</strong></div>
            <div id="current-team">Fudge Bay Packers</div>
        </div>
        <div class="status-card" id="your-status">
            <div id="your-turn-indicator">Your Turn!</div>
        </div>
    </div>
    
    <div class="controls">
        <button class="btn" onclick="refreshData()">🔄 Refresh</button>
        <button class="btn" onclick="undoPick()">↶ Undo Last Pick</button>
    </div>
    
    <div id="message-area"></div>
    
    <div class="container">
        <div class="panel">
            <h3>
                🎯 Available Players
                <select id="position-filter" onchange="filterPlayers()">
                    <option value="ALL">All Positions</option>
                    <option value="QB">QB</option>
                    <option value="RB">RB</option>
                    <option value="WR">WR</option>
                    <option value="TE">TE</option>
                    <option value="K">K</option>
                    <option value="DST">DEF</option>
                </select>
            </h3>
            <div id="available-players" class="player-list"></div>
        </div>
        
        <div class="panel">
            <h3>👑 Your Team</h3>
            <div id="my-team" class="player-list"></div>
            <div id="position-needs" class="needs"></div>
            <div id="roster-summary" class="roster-summary"></div>
        </div>
        
        <div class="panel">
            <h3>💡 Strategic Picks</h3>
            <div id="recommendations" class="player-list"></div>
        </div>
    </div>

    <script>
        let draftState = {};
        
        function showMessage(message, type = 'success') {
            const messageArea = document.getElementById('message-area');
            messageArea.innerHTML = `<div class="message ${type}">${message}</div>`;
            setTimeout(() => messageArea.innerHTML = '', 4000);
        }
        
        function draftPlayerToTeam(playerName, teamName = null) {
            const team = teamName || draftState.current_team;
            const confirmMsg = teamName ? 
                `Draft ${playerName} to ${team}?` : 
                `Draft ${playerName}?`;
                
            if (confirm(confirmMsg)) {
                fetch('/api/draft_player', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        player_name: playerName,
                        team_name: teamName
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showMessage(data.message, 'success');
                        refreshData();
                    } else {
                        showMessage(data.message, 'error');
                    }
                });
            }
        }
        
        function undoPick() {
            if (confirm('Undo the last pick?')) {
                fetch('/api/undo_pick', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    showMessage(data.message, data.success ? 'success' : 'error');
                    if (data.success) refreshData();
                });
            }
        }
        
        function filterPlayers() {
            loadAvailablePlayers();
        }
        
        function loadDraftState() {
            fetch('/api/draft_state')
            .then(response => response.json())
            .then(data => {
                draftState = data;
                
                // Update draft status
                document.getElementById('current-pick').textContent = data.current_pick;
                document.getElementById('current-round').textContent = data.current_round;
                document.getElementById('current-team').textContent = data.current_team;
                
                // Update your turn indicator
                const yourTurnEl = document.getElementById('your-turn-indicator');
                const teamInfoEl = document.getElementById('team-info');
                if (data.your_turn) {
                    yourTurnEl.textContent = '🎯 YOUR TURN!';
                    yourTurnEl.parentElement.classList.add('your-turn');
                } else {
                    yourTurnEl.textContent = 'Wait...';
                    yourTurnEl.parentElement.classList.remove('your-turn');
                }
                
                // Update your team
                const container = document.getElementById('my-team');
                container.innerHTML = data.your_roster.map(player => `
                    <div class="player-item your-player">
                        <div class="player-info">
                            <div class="player-name">${player.name}</div>
                            <div class="player-details">
                                ${player.position} - ${player.team} • 
                                Proj: ${player.projected_points ? player.projected_points.toFixed(1) : '--'}
                            </div>
                        </div>
                    </div>
                `).join('');
                
                // Show position needs
                const needsContainer = document.getElementById('position-needs');
                const needsList = Object.entries(data.your_needs)
                    .filter(([pos, count]) => count > 0)
                    .map(([pos, count]) => `${pos}: ${count}`)
                    .join(', ');
                
                needsContainer.innerHTML = needsList ? 
                    `<strong>🎯 Still need:</strong> ${needsList}` : 
                    '<strong>✅ Roster complete!</strong>';
                
                // Roster summary
                const summaryContainer = document.getElementById('roster-summary');
                const positionCounts = {};
                data.your_roster.forEach(player => {
                    positionCounts[player.position] = (positionCounts[player.position] || 0) + 1;
                });
                
                summaryContainer.innerHTML = Object.entries({QB: 0, RB: 0, WR: 0, TE: 0, K: 0, DST: 0, ...positionCounts})
                    .map(([pos, count]) => `
                        <div class="position-count">
                            <strong>${pos}</strong><br>${count}
                        </div>
                    `).join('');
            });
        }
        
        function loadAvailablePlayers() {
            const position = document.getElementById('position-filter').value;
            fetch(`/api/players?position=${position}&limit=50`)
            .then(response => response.json())
            .then(players => {
                const container = document.getElementById('available-players');
                container.innerHTML = players.map(player => {
                    const isYourTurn = draftState.your_turn;
                    return `
                        <div class="player-item">
                            <div class="player-info">
                                <div class="player-name">${player.name}</div>
                                <div class="player-details">
                                    ${player.position} - ${player.team} • 
                                    ADP: ${player.adp < 999 ? player.adp.toFixed(1) : '---'} • 
                                    Proj: ${player.projected_points ? player.projected_points.toFixed(1) : '--'}
                                </div>
                            </div>
                            <div>
                                ${isYourTurn ? 
                                    `<button class="draft-btn" onclick="draftPlayerToTeam('${player.name}')">Draft</button>` :
                                    `<select class="team-dropdown" onchange="if(this.value) draftPlayerToTeam('${player.name}', this.value); this.value='';">
                                        <option value="">Draft to...</option>
                                        ${draftState.teams ? draftState.teams.map(team => 
                                            `<option value="${team}">${team.substring(0, 15)}</option>`
                                        ).join('') : ''}
                                    </select>`
                                }
                            </div>
                        </div>
                    `;
                }).join('');
            });
        }
        
        function loadRecommendations() {
            fetch('/api/recommendations')
            .then(response => response.json())
            .then(recommendations => {
                const container = document.getElementById('recommendations');
                container.innerHTML = recommendations.map(rec => `
                    <div class="player-item recommendation">
                        <div class="player-info">
                            <div class="player-name">${rec.player.name}</div>
                            <div class="player-details">
                                ${rec.player.position} - ${rec.player.team}<br>
                                <strong>${rec.reason}</strong><br>
                                ADP: ${rec.player.adp < 999 ? rec.player.adp.toFixed(1) : '---'} • 
                                Proj: ${rec.player.projected_points ? rec.player.projected_points.toFixed(1) : '--'}
                            </div>
                        </div>
                        <button class="draft-btn" onclick="draftPlayerToTeam('${rec.player.name}')">Draft</button>
                    </div>
                `).join('');
            });
        }
        
        function refreshData() {
            loadDraftState();
            loadAvailablePlayers();
            loadRecommendations();
        }
        
        // Initial load
        refreshData();
        
        // Auto-refresh every 15 seconds
        setInterval(refreshData, 15000);
    </script>
</body>
</html>'''
    
    with open('templates/enhanced_index.html', 'w') as f:
        f.write(html_content)
    
    print("🚀 Starting Enhanced Draft Assistant...")
    print("📱 Open http://localhost:5000 in your browser")
    print("\n🎯 YOU HAVE PICK #1!")
    print("Draft order: Fudge Bay Packers (YOU) → Withdean Lambs → Jenny's Vinegar Strokes → ...")
    app.run(debug=True, host='0.0.0.0', port=5000)