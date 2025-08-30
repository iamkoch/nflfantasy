#!/usr/bin/env python3
"""
Working NFL Fantasy Draft Assistant
Fixed version with proper 8-team tracking
"""

from flask import Flask, render_template, request, jsonify
import sqlite3
import json

app = Flask(__name__)

class DraftAssistant:
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
            if position and position != 'ALL':
                query = f"SELECT * FROM players WHERE name NOT IN ({placeholders}) AND position = ? ORDER BY adp LIMIT ?"
                params = list(self.drafted_players) + [position, limit]
            else:
                query = f"SELECT * FROM players WHERE name NOT IN ({placeholders}) ORDER BY adp LIMIT ?"
                params = list(self.drafted_players) + [limit]
        else:
            if position and position != 'ALL':
                query = "SELECT * FROM players WHERE position = ? ORDER BY adp LIMIT ?"
                params = [position, limit]
            else:
                query = "SELECT * FROM players ORDER BY adp LIMIT ?"
                params = [limit]
        
        cursor.execute(query, params)
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
    
    def get_recommendations(self):
        """Get recommendations for your team"""
        your_needs = self.get_team_needs(self.your_team)
        recommendations = []
        
        # Get top players for positions we need
        for pos, need_count in your_needs.items():
            if need_count > 0:
                players = self.get_available_players(pos, 5)
                for player in players[:3]:
                    value_score = need_count * 10 + (player['projected_points'] or 0)
                    if player['adp'] and player['adp'] < 999:
                        value_score += max(0, 200 - player['adp']) / 20
                    
                    recommendations.append({
                        'player': player,
                        'value_score': value_score,
                        'reason': f"Need {need_count} {pos}{'s' if need_count > 1 else ''}"
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

# Global assistant
assistant = DraftAssistant()

@app.route('/')
def index():
    return render_template('working_index.html')

@app.route('/api/draft_state')
def get_draft_state():
    """Get complete draft state"""
    current_team = assistant.get_current_team()
    your_needs = assistant.get_team_needs(assistant.your_team)
    
    return jsonify({
        'current_pick': assistant.current_pick,
        'current_round': assistant.current_round,
        'current_team': current_team,
        'your_turn': current_team == assistant.your_team,
        'teams': assistant.teams,
        'your_team': assistant.your_team,
        'your_needs': your_needs,
        'your_roster': assistant.team_rosters[assistant.your_team]
    })

@app.route('/api/players')
def get_players():
    position = request.args.get('position', 'ALL')
    limit = int(request.args.get('limit', 50))
    
    players = assistant.get_available_players(position, limit)
    return jsonify(players)

@app.route('/api/recommendations')
def get_recommendations():
    recommendations = assistant.get_recommendations()
    return jsonify(recommendations)

@app.route('/api/draft_player', methods=['POST'])
def draft_player():
    data = request.json
    player_name = data.get('player_name')
    team_name = data.get('team_name')
    
    result = assistant.draft_player(player_name, team_name)
    return jsonify(result)

if __name__ == '__main__':
    # Create working template
    import os
    os.makedirs('templates', exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Working Fantasy Draft Assistant</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
        .header { text-align: center; margin-bottom: 30px; }
        .container { display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 20px; }
        .panel { background: #2a2a2a; padding: 20px; border-radius: 10px; }
        .panel h3 { color: #4CAF50; margin-top: 0; }
        .player-item { 
            display: flex; justify-content: space-between; align-items: center;
            padding: 10px; margin: 5px 0; background: #3a3a3a; border-radius: 5px;
        }
        .player-item:hover { background: #4a4a4a; }
        .your-turn { background: rgba(76, 175, 80, 0.3); border: 2px solid #4CAF50; }
        .draft-btn { 
            background: #4CAF50; color: white; border: none; 
            padding: 8px 15px; border-radius: 5px; cursor: pointer; 
        }
        .draft-btn:hover { background: #45a049; }
        .team-dropdown { 
            background: #3a3a3a; color: white; border: 1px solid #555; 
            padding: 5px; border-radius: 3px; 
        }
        select { background: #3a3a3a; color: white; border: 1px solid #555; padding: 5px; }
        .message { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: rgba(76, 175, 80, 0.3); }
        .error { background: rgba(244, 67, 54, 0.3); }
        .needs { background: #4a2a2a; padding: 10px; margin-top: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏈 Fantasy Draft Assistant</h1>
        <p><strong>Pick <span id="current-pick">1</span></strong> • Round <span id="current-round">1</span></p>
        <p><strong>On the Clock:</strong> <span id="current-team">Fudge Bay Packers</span></p>
        <div id="your-turn-status"></div>
    </div>
    
    <div id="message-area"></div>
    
    <div class="container">
        <div class="panel">
            <h3>🎯 Available Players 
                <select id="position-filter" onchange="loadPlayers()">
                    <option value="ALL">All</option>
                    <option value="QB">QB</option>
                    <option value="RB">RB</option>
                    <option value="WR">WR</option>
                    <option value="TE">TE</option>
                    <option value="K">K</option>
                    <option value="DST">DEF</option>
                </select>
            </h3>
            <div id="players-list" style="max-height: 500px; overflow-y: auto;"></div>
        </div>
        
        <div class="panel">
            <h3>👑 Your Team</h3>
            <div id="your-team"></div>
            <div id="needs" class="needs"></div>
        </div>
        
        <div class="panel">
            <h3>💡 Recommendations</h3>
            <div id="recommendations"></div>
        </div>
    </div>

    <script>
        let draftState = {};
        
        function showMessage(msg, type = 'success') {
            const area = document.getElementById('message-area');
            area.innerHTML = `<div class="message ${type}">${msg}</div>`;
            setTimeout(() => area.innerHTML = '', 3000);
        }
        
        function draftPlayer(playerName, teamName = null) {
            const team = teamName || draftState.current_team;
            if (confirm(`Draft ${playerName} to ${team}?`)) {
                fetch('/api/draft_player', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({player_name: playerName, team_name: teamName})
                })
                .then(r => r.json())
                .then(data => {
                    showMessage(data.message, data.success ? 'success' : 'error');
                    if (data.success) loadAll();
                });
            }
        }
        
        function loadDraftState() {
            fetch('/api/draft_state')
            .then(r => r.json())
            .then(data => {
                draftState = data;
                document.getElementById('current-pick').textContent = data.current_pick;
                document.getElementById('current-round').textContent = data.current_round;
                document.getElementById('current-team').textContent = data.current_team;
                
                const statusEl = document.getElementById('your-turn-status');
                if (data.your_turn) {
                    statusEl.innerHTML = '<div class="your-turn">🎯 YOUR TURN!</div>';
                } else {
                    statusEl.innerHTML = '<div>Wait for your turn...</div>';
                }
                
                // Your team
                const teamEl = document.getElementById('your-team');
                teamEl.innerHTML = data.your_roster.map(p => `
                    <div class="player-item">
                        <div>
                            <strong>${p.name}</strong><br>
                            ${p.position} - ${p.team} • Proj: ${p.projected_points ? p.projected_points.toFixed(1) : '--'}
                        </div>
                    </div>
                `).join('');
                
                // Needs
                const needsList = Object.entries(data.your_needs)
                    .filter(([pos, count]) => count > 0)
                    .map(([pos, count]) => `${pos}: ${count}`)
                    .join(', ');
                document.getElementById('needs').innerHTML = needsList ? 
                    `<strong>Still need:</strong> ${needsList}` : 
                    '<strong>Roster complete!</strong>';
            });
        }
        
        function loadPlayers() {
            const position = document.getElementById('position-filter').value;
            fetch(`/api/players?position=${position}&limit=30`)
            .then(r => r.json())
            .then(players => {
                const listEl = document.getElementById('players-list');
                listEl.innerHTML = players.map(p => `
                    <div class="player-item">
                        <div>
                            <strong>${p.name}</strong><br>
                            ${p.position} - ${p.team} • ADP: ${p.adp < 999 ? p.adp.toFixed(1) : '---'} • Proj: ${p.projected_points ? p.projected_points.toFixed(1) : '--'}
                        </div>
                        <div>
                            ${draftState.your_turn ? 
                                `<button class="draft-btn" onclick="draftPlayer('${p.name}')">Draft</button>` :
                                `<select class="team-dropdown" onchange="if(this.value) { draftPlayer('${p.name}', this.value); this.value=''; }">
                                    <option value="">Draft to...</option>
                                    ${draftState.teams ? draftState.teams.map(t => 
                                        `<option value="${t}">${t.substring(0, 20)}</option>`
                                    ).join('') : ''}
                                </select>`
                            }
                        </div>
                    </div>
                `).join('');
            });
        }
        
        function loadRecommendations() {
            fetch('/api/recommendations')
            .then(r => r.json())
            .then(recs => {
                document.getElementById('recommendations').innerHTML = recs.map(rec => `
                    <div class="player-item">
                        <div>
                            <strong>${rec.player.name}</strong><br>
                            ${rec.player.position} - ${rec.player.team}<br>
                            <em>${rec.reason}</em>
                        </div>
                        <button class="draft-btn" onclick="draftPlayer('${rec.player.name}')">Draft</button>
                    </div>
                `).join('');
            });
        }
        
        function loadAll() {
            loadDraftState();
            loadPlayers();
            loadRecommendations();
        }
        
        // Initial load and auto-refresh
        loadAll();
        setInterval(loadAll, 10000);
    </script>
</body>
</html>'''
    
    with open('templates/working_index.html', 'w') as f:
        f.write(html_content)
    
    print("🚀 Starting Working Draft Assistant...")
    print("📱 Open http://localhost:5000")
    print("\n🎯 YOU HAVE PICK #1 - Fudge Bay Packers!")
    app.run(debug=True, host='0.0.0.0', port=5000)