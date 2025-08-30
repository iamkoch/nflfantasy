#!/usr/bin/env python3
"""
Web-based NFL Fantasy Draft Assistant
Simple Flask app for easier draft management
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import json

app = Flask(__name__)

class WebDraftAssistant:
    def __init__(self):
        self.drafted_players = set()
        self.my_team = []
        self.current_pick = 1
    
    def get_db_connection(self):
        conn = sqlite3.connect('fantasy_draft_2025.db')
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_available_players(self, position=None, limit=50):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        base_query = """
            SELECT * FROM players 
            WHERE name NOT IN ({})
        """.format(','.join(['?' for _ in self.drafted_players])) if self.drafted_players else "SELECT * FROM players"
        
        params = list(self.drafted_players)
        
        if position and position != 'ALL':
            base_query += " AND position = ?"
            params.append(position)
            
        base_query += " ORDER BY adp LIMIT ?"
        params.append(limit)
        
        cursor.execute(base_query, params)
        players = cursor.fetchall()
        conn.close()
        return [dict(player) for player in players]
    
    def get_position_needs(self):
        needs = {'QB': 2, 'RB': 6, 'WR': 6, 'TE': 1, 'K': 1, 'DST': 2}
        
        for player in self.my_team:
            pos = player['position']
            if pos in needs and needs[pos] > 0:
                needs[pos] -= 1
        
        return needs

# Global draft assistant instance
draft_assistant = WebDraftAssistant()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/players')
def get_players():
    position = request.args.get('position', 'ALL')
    limit = int(request.args.get('limit', 50))
    
    players = draft_assistant.get_available_players(position, limit)
    return jsonify(players)

@app.route('/api/my_team')
def get_my_team():
    needs = draft_assistant.get_position_needs()
    return jsonify({
        'team': draft_assistant.my_team,
        'needs': needs,
        'current_pick': draft_assistant.current_pick
    })

@app.route('/api/draft_player', methods=['POST'])
def draft_player():
    data = request.json
    player_name = data.get('player_name')
    
    conn = draft_assistant.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE name = ?", (player_name,))
    player = cursor.fetchone()
    
    if not player:
        return jsonify({'success': False, 'message': f"Player '{player_name}' not found!"})
        
    if player_name in draft_assistant.drafted_players:
        return jsonify({'success': False, 'message': f"Player '{player_name}' already drafted!"})
    
    # Add to team
    draft_assistant.my_team.append(dict(player))
    draft_assistant.drafted_players.add(player_name)
    
    # Record in draft results
    cursor.execute('''
        INSERT INTO draft_results (player_id, team_name, round, pick, overall_pick)
        VALUES (?, ?, ?, ?, ?)
    ''', (player['id'], 'My Team', 
          (draft_assistant.current_pick - 1) // 8 + 1, 
          ((draft_assistant.current_pick - 1) % 8) + 1, 
          draft_assistant.current_pick))
    
    conn.commit()
    conn.close()
    
    draft_assistant.current_pick += 1
    
    return jsonify({
        'success': True, 
        'message': f"Drafted {player['name']} at pick {draft_assistant.current_pick - 1}",
        'current_pick': draft_assistant.current_pick
    })

@app.route('/api/skip_pick', methods=['POST'])
def skip_pick():
    draft_assistant.current_pick += 1
    return jsonify({
        'success': True,
        'current_pick': draft_assistant.current_pick,
        'message': f"Skipped to pick {draft_assistant.current_pick}"
    })

@app.route('/api/recommendations')
def get_recommendations():
    needs = draft_assistant.get_position_needs()
    recommendations = []
    
    for pos, need_count in needs.items():
        if need_count > 0:
            players = draft_assistant.get_available_players(pos, 3)
            for player in players:
                value_score = need_count * 10 + (player['projected_points'] or 0)
                if player['adp'] and player['adp'] < 999:
                    value_score += max(0, 200 - player['adp']) / 20
                
                recommendations.append({
                    'player': player,
                    'value_score': value_score,
                    'reason': f"Need {need_count} {pos}{'s' if need_count > 1 else ''}"
                })
    
    recommendations.sort(key=lambda x: x['value_score'], reverse=True)
    return jsonify(recommendations[:5])

if __name__ == '__main__':
    # Create templates directory and HTML file
    import os
    os.makedirs('templates', exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NFL Fantasy Draft Assistant</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #1a1a1a; 
            color: #fff; 
        }
        .header { 
            text-align: center; 
            margin-bottom: 30px; 
            border-bottom: 2px solid #4CAF50; 
            padding-bottom: 20px; 
        }
        .container { 
            display: grid; 
            grid-template-columns: 1fr 1fr 1fr; 
            gap: 20px; 
            max-width: 1400px; 
            margin: 0 auto; 
        }
        .panel { 
            background: #2a2a2a; 
            border-radius: 8px; 
            padding: 20px; 
            border: 1px solid #444; 
        }
        .panel h3 { 
            margin-top: 0; 
            color: #4CAF50; 
            border-bottom: 1px solid #444; 
            padding-bottom: 10px; 
        }
        .player-list { 
            max-height: 400px; 
            overflow-y: auto; 
        }
        .player-item { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            padding: 10px; 
            margin: 5px 0; 
            background: #3a3a3a; 
            border-radius: 5px; 
            cursor: pointer; 
            transition: background 0.2s; 
        }
        .player-item:hover { 
            background: #4a4a4a; 
        }
        .player-info { 
            flex: 1; 
        }
        .player-name { 
            font-weight: bold; 
            color: #fff; 
        }
        .player-details { 
            font-size: 0.9em; 
            color: #ccc; 
        }
        .draft-btn { 
            background: #4CAF50; 
            color: white; 
            border: none; 
            padding: 5px 10px; 
            border-radius: 3px; 
            cursor: pointer; 
        }
        .draft-btn:hover { 
            background: #45a049; 
        }
        .controls { 
            text-align: center; 
            margin-bottom: 20px; 
        }
        .btn { 
            background: #2196F3; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            margin: 5px; 
            border-radius: 5px; 
            cursor: pointer; 
        }
        .btn:hover { 
            background: #1976D2; 
        }
        .position-filter { 
            margin-bottom: 15px; 
        }
        select { 
            background: #3a3a3a; 
            color: white; 
            border: 1px solid #555; 
            padding: 5px; 
            border-radius: 3px; 
        }
        .my-team-player { 
            background: #1a4a1a; 
            border-left: 4px solid #4CAF50; 
        }
        .needs { 
            background: #4a2a2a; 
            padding: 10px; 
            border-radius: 5px; 
            margin-top: 10px; 
        }
        .pick-counter { 
            font-size: 1.5em; 
            color: #4CAF50; 
            font-weight: bold; 
        }
        .message { 
            padding: 10px; 
            margin: 10px 0; 
            border-radius: 5px; 
        }
        .success { 
            background: #1a4a1a; 
            color: #4CAF50; 
        }
        .error { 
            background: #4a1a1a; 
            color: #f44336; 
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏈 NFL Fantasy Draft Assistant</h1>
        <p><strong>The League</strong> • 8 Teams • 0.5 PPR • 2 QB, 2 DEF</p>
        <div class="pick-counter">Current Pick: <span id="current-pick">1</span></div>
    </div>
    
    <div class="controls">
        <button class="btn" onclick="skipPick()">Skip Pick</button>
        <button class="btn" onclick="refreshData()">Refresh</button>
    </div>
    
    <div id="message-area"></div>
    
    <div class="container">
        <div class="panel">
            <h3>🎯 Available Players</h3>
            <div class="position-filter">
                <select id="position-filter" onchange="filterPlayers()">
                    <option value="ALL">All Positions</option>
                    <option value="QB">QB</option>
                    <option value="RB">RB</option>
                    <option value="WR">WR</option>
                    <option value="TE">TE</option>
                    <option value="K">K</option>
                    <option value="DST">DEF</option>
                </select>
            </div>
            <div id="available-players" class="player-list"></div>
        </div>
        
        <div class="panel">
            <h3>📋 My Team</h3>
            <div id="my-team" class="player-list"></div>
            <div id="position-needs" class="needs"></div>
        </div>
        
        <div class="panel">
            <h3>💡 Recommendations</h3>
            <div id="recommendations" class="player-list"></div>
        </div>
    </div>

    <script>
        let currentPick = 1;
        
        function showMessage(message, type = 'success') {
            const messageArea = document.getElementById('message-area');
            messageArea.innerHTML = `<div class="message ${type}">${message}</div>`;
            setTimeout(() => messageArea.innerHTML = '', 3000);
        }
        
        function updateCurrentPick(pick) {
            currentPick = pick;
            document.getElementById('current-pick').textContent = pick;
        }
        
        function draftPlayer(playerName) {
            if (confirm(`Draft ${playerName}?`)) {
                fetch('/api/draft_player', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({player_name: playerName})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showMessage(data.message, 'success');
                        updateCurrentPick(data.current_pick);
                        refreshData();
                    } else {
                        showMessage(data.message, 'error');
                    }
                });
            }
        }
        
        function skipPick() {
            fetch('/api/skip_pick', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                showMessage(data.message, 'success');
                updateCurrentPick(data.current_pick);
            });
        }
        
        function filterPlayers() {
            loadAvailablePlayers();
        }
        
        function loadAvailablePlayers() {
            const position = document.getElementById('position-filter').value;
            fetch(`/api/players?position=${position}&limit=30`)
            .then(response => response.json())
            .then(players => {
                const container = document.getElementById('available-players');
                container.innerHTML = players.map(player => `
                    <div class="player-item" onclick="draftPlayer('${player.name}')">
                        <div class="player-info">
                            <div class="player-name">${player.name}</div>
                            <div class="player-details">
                                ${player.position} - ${player.team} • 
                                ADP: ${player.adp < 999 ? player.adp.toFixed(1) : '---'} • 
                                Proj: ${player.projected_points ? player.projected_points.toFixed(1) : '--'}
                            </div>
                        </div>
                        <button class="draft-btn" onclick="event.stopPropagation(); draftPlayer('${player.name}')">Draft</button>
                    </div>
                `).join('');
            });
        }
        
        function loadMyTeam() {
            fetch('/api/my_team')
            .then(response => response.json())
            .then(data => {
                updateCurrentPick(data.current_pick);
                
                const container = document.getElementById('my-team');
                container.innerHTML = data.team.map(player => `
                    <div class="player-item my-team-player">
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
                const needsList = Object.entries(data.needs)
                    .filter(([pos, count]) => count > 0)
                    .map(([pos, count]) => `${pos}: ${count}`)
                    .join(', ');
                
                needsContainer.innerHTML = needsList ? 
                    `<strong>Still need:</strong> ${needsList}` : 
                    '<strong>Roster complete!</strong>';
            });
        }
        
        function loadRecommendations() {
            fetch('/api/recommendations')
            .then(response => response.json())
            .then(recommendations => {
                const container = document.getElementById('recommendations');
                container.innerHTML = recommendations.map(rec => `
                    <div class="player-item" onclick="draftPlayer('${rec.player.name}')">
                        <div class="player-info">
                            <div class="player-name">${rec.player.name}</div>
                            <div class="player-details">
                                ${rec.player.position} - ${rec.player.team} • ${rec.reason}
                                <br>ADP: ${rec.player.adp < 999 ? rec.player.adp.toFixed(1) : '---'} • 
                                Proj: ${rec.player.projected_points ? rec.player.projected_points.toFixed(1) : '--'}
                            </div>
                        </div>
                        <button class="draft-btn" onclick="event.stopPropagation(); draftPlayer('${rec.player.name}')">Draft</button>
                    </div>
                `).join('');
            });
        }
        
        function refreshData() {
            loadAvailablePlayers();
            loadMyTeam();
            loadRecommendations();
        }
        
        // Initial load
        refreshData();
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
    </script>
</body>
</html>'''
    
    with open('templates/index.html', 'w') as f:
        f.write(html_content)
    
    print("🚀 Starting web draft assistant...")
    print("📱 Open http://localhost:5000 in your browser")
    app.run(debug=True, host='0.0.0.0', port=5000)