#!/usr/bin/env python3
"""
Final NFL Fantasy Draft Assistant
Perfect draft cycle with clear YOUR TURN vs OTHER TEAM workflows
"""

from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

class FinalDraftAssistant:
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
        self.draft_history = []  # Track all picks
        
        # Track each team's roster
        self.team_rosters = {team: [] for team in self.teams}
        
        # Load existing draft state if it exists
        self.load_draft_state()
    
    def get_db_connection(self):
        conn = sqlite3.connect('fantasy_draft_2025.db')
        conn.row_factory = sqlite3.Row
        return conn
    
    def load_draft_state(self):
        """Load existing draft state from database"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        # Create draft state table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS draft_state (
                id INTEGER PRIMARY KEY,
                current_pick INTEGER,
                current_round INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Load draft state
        cursor.execute("SELECT * FROM draft_state WHERE id = 1")
        state = cursor.fetchone()
        
        if state:
            self.current_pick = state['current_pick']
            self.current_round = state['current_round']
            print(f"📋 Loaded draft state: Pick {self.current_pick}, Round {self.current_round}")
        
        # Load all draft results to rebuild state
        cursor.execute("""
            SELECT dr.*, p.name, p.position, p.team, p.projected_points, p.adp, p.tier
            FROM draft_results dr 
            JOIN players p ON dr.player_id = p.id 
            ORDER BY dr.overall_pick
        """)
        
        draft_results = cursor.fetchall()
        
        for result in draft_results:
            # Rebuild drafted players set
            self.drafted_players.add(result['name'])
            
            # Rebuild team rosters
            player_dict = {
                'id': result['player_id'],
                'name': result['name'],
                'position': result['position'],
                'team': result['team'],
                'projected_points': result['projected_points'],
                'adp': result['adp'],
                'tier': result['tier']
            }
            self.team_rosters[result['team_name']].append(player_dict)
            
            # Rebuild draft history
            self.draft_history.append({
                'pick': result['overall_pick'],
                'round': result['round'],
                'team': result['team_name'],
                'player': player_dict
            })
        
        if draft_results:
            print(f"📋 Loaded {len(draft_results)} existing draft picks")
            print(f"🎯 Current team on clock: {self.get_current_team()}")
        
        conn.close()
    
    def save_draft_state(self):
        """Save current draft state to database"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO draft_state (id, current_pick, current_round)
            VALUES (1, ?, ?)
        ''', (self.current_pick, self.current_round))
        
        conn.commit()
        conn.close()
    
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
    
    def get_your_recommendations(self):
        """Get TOP recommendations for YOUR turn"""
        your_needs = self.get_team_needs(self.your_team)
        recommendations = []
        
        # Pick #1 overall strategy
        if self.current_pick == 1:
            top_players = self.get_available_players(limit=5)
            for i, player in enumerate(top_players):
                value_score = 100 + (player['projected_points'] or 0) * 5
                
                # Detailed explanation for #1 pick
                if i == 0:
                    explanation = f"🏆 TOP OVERALL VALUE: Highest projected points ({player['projected_points']:.1f}) with elite {player['position']} scarcity. In your 2QB/0.5PPR league, {player['position']}s like {player['name']} provide the best foundation for a championship team. ADP {player['adp']:.1f} confirms consensus #1 value."
                else:
                    explanation = f"🏆 PICK #1 OVERALL - Elite {player['position']} alternative"
                
                recommendations.append({
                    'player': player,
                    'value_score': value_score,
                    'reason': f"🏆 PICK #1 OVERALL - Elite {player['position']}",
                    'explanation': explanation
                })
        
        # Your turn in later rounds
        elif self.get_current_team() == self.your_team:
            # Early rounds (1-6): Premium positions
            if self.current_round <= 6:
                premium_positions = ['QB', 'RB', 'WR'] 
                for pos in premium_positions:
                    if your_needs.get(pos, 0) > 0:
                        players = self.get_available_players(pos, 3)
                        for i, player in enumerate(players):
                            value_score = your_needs[pos] * 20 + (player['projected_points'] or 0) * 3
                            if player['adp'] and player['adp'] < 100:
                                value_score += 15  # Bonus for good ADP
                            
                            # Detailed explanation for top recommendation
                            if i == 0:
                                explanation = f"🎯 PREMIUM POSITION VALUE: Best available {pos} with {player['projected_points']:.1f} projected points. You need {your_needs[pos]} more {pos}{'s' if your_needs[pos] > 1 else ''}. Round {self.current_round} is prime time for elite {pos}s - don't wait as quality drops fast. ADP {player['adp']:.1f} shows strong value here."
                            else:
                                explanation = f"🎯 Solid {pos} option for round {self.current_round}"
                            
                            recommendations.append({
                                'player': player,
                                'value_score': value_score,
                                'reason': f"🎯 Round {self.current_round} - Need {your_needs[pos]} {pos}{'s' if your_needs[pos] > 1 else ''}",
                                'explanation': explanation
                            })
            
            # Mid rounds (7-12): Fill needs  
            elif self.current_round <= 12:
                for pos, need_count in your_needs.items():
                    if need_count > 0:
                        players = self.get_available_players(pos, 3)
                        for i, player in enumerate(players):
                            value_score = need_count * 15 + (player['projected_points'] or 0) * 2
                            
                            if i == 0:
                                explanation = f"📋 ROSTER NEED PRIORITY: You still need {need_count} {pos}{'s' if need_count > 1 else ''}. {player['name']} projects {player['projected_points']:.1f} points and fills a critical roster hole. Mid-rounds are about building depth - grab reliable producers at needed positions."
                            else:
                                explanation = f"📋 Alternative {pos} to fill roster need"
                            
                            recommendations.append({
                                'player': player,
                                'value_score': value_score,
                                'reason': f"📋 Fill {pos} need - {need_count} remaining",
                                'explanation': explanation
                            })
            
            # Late rounds: Best available + sleepers
            else:
                top_available = self.get_available_players(limit=10)
                for i, player in enumerate(top_available[:5]):
                    value_score = (player['projected_points'] or 0) * 2
                    if player.get('sleeper_rating', 0) > 5:
                        value_score += 10
                    
                    if i == 0:
                        explanation = f"💎 LATE ROUND STRATEGY: Best available talent regardless of position. {player['name']} has upside potential with {player['projected_points']:.1f} projected points. Late rounds are about lottery tickets - swing for breakout candidates who could outperform ADP."
                    else:
                        explanation = f"💎 Upside play for late rounds"
                    
                    recommendations.append({
                        'player': player,
                        'value_score': value_score,
                        'reason': f"💎 Late round value - Best available {player['position']}",
                        'explanation': explanation
                    })
        
        # Sort by value score and return top 3
        recommendations.sort(key=lambda x: x['value_score'], reverse=True)
        return recommendations[:3]
    
    def draft_player(self, player_name, team_name=None):
        """Draft a player"""
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
        
        # Add to team roster and drafted set
        player_dict = dict(player)
        self.team_rosters[team_name].append(player_dict)
        self.drafted_players.add(player_name)
        
        # Add to draft history
        self.draft_history.append({
            'pick': self.current_pick,
            'round': self.current_round,
            'team': team_name,
            'player': player_dict
        })
        
        # Record in database
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
        
        # Save draft state to database
        self.save_draft_state()
        
        next_team = self.get_current_team()
        
        return {
            'success': True,
            'message': f"✅ {team_name} drafted {player['name']} (Pick {self.current_pick - 1})",
            'current_pick': self.current_pick,
            'current_round': self.current_round,
            'current_team': next_team,
            'your_turn': next_team == self.your_team
        }

@app.route('/')
def index():
    return render_template('final_index.html')

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
        'your_roster': assistant.team_rosters[assistant.your_team],
        'draft_history': assistant.draft_history[-10:],  # Last 10 picks
        'team_rosters': assistant.team_rosters
    })

@app.route('/api/players')
def get_players():
    position = request.args.get('position', 'ALL')
    limit = int(request.args.get('limit', 50))
    search = request.args.get('search', '').strip()
    
    if search:
        # Search functionality - get all available players and filter by name
        all_players = assistant.get_available_players(position, 500)  # Get more for search
        players = [p for p in all_players if search.lower() in p['name'].lower()][:limit]
    else:
        players = assistant.get_available_players(position, limit)
    
    return jsonify(players)

@app.route('/api/recommendations')
def get_recommendations():
    recommendations = assistant.get_your_recommendations()
    return jsonify(recommendations)

@app.route('/api/draft_player', methods=['POST'])
def draft_player():
    data = request.json
    player_name = data.get('player_name')
    team_name = data.get('team_name')
    
    print(f"🎯 DEBUG: Attempting to draft '{player_name}' to '{team_name or assistant.get_current_team()}'")
    print(f"🎯 DEBUG: Current team on clock: {assistant.get_current_team()}")
    print(f"🎯 DEBUG: Already drafted: {len(assistant.drafted_players)} players")
    print(f"🎯 DEBUG: Is '{player_name}' already drafted? {player_name in assistant.drafted_players}")
    
    result = assistant.draft_player(player_name, team_name)
    print(f"🎯 DEBUG: Draft result: {result}")
    return jsonify(result)

@app.route('/api/reset_draft', methods=['POST'])
def reset_draft():
    """Reset the entire draft - useful for testing"""
    global assistant
    
    conn = assistant.get_db_connection()
    cursor = conn.cursor()
    
    # Clear all draft data
    cursor.execute("DELETE FROM draft_results")
    cursor.execute("DELETE FROM draft_state")
    
    conn.commit()
    conn.close()
    
    # Reinitialize the assistant
    assistant = FinalDraftAssistant()
    
    return jsonify({
        'success': True,
        'message': 'Draft reset successfully',
        'current_pick': 1,
        'current_team': 'Fudge Bay Packers'
    })

# Global assistant - initialize after all functions are defined
assistant = FinalDraftAssistant()

if __name__ == '__main__':
    # Create final template
    import os
    os.makedirs('templates', exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>🏈 Fantasy Draft Assistant</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            margin: 0; padding: 15px; 
            background: linear-gradient(135deg, #0f0f23, #1a1a2e);
            color: #fff; min-height: 100vh;
        }
        
        .header { 
            text-align: center; margin-bottom: 25px;
            background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
            border-radius: 15px; padding: 20px; border: 1px solid rgba(255,255,255,0.2);
        }
        
        .draft-status {
            display: grid; grid-template-columns: 1fr 2fr 1fr; gap: 15px; margin-bottom: 20px;
        }
        
        .status-card {
            background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
            border-radius: 10px; padding: 15px; text-align: center;
            border: 1px solid rgba(255,255,255,0.2); transition: all 0.3s ease;
        }
        
        .your-turn-card {
            background: rgba(76, 175, 80, 0.3); border-color: #4CAF50;
            box-shadow: 0 0 30px rgba(76, 175, 80, 0.5); animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 30px rgba(76, 175, 80, 0.5); }
            50% { box-shadow: 0 0 50px rgba(76, 175, 80, 0.8); }
            100% { box-shadow: 0 0 30px rgba(76, 175, 80, 0.5); }
        }
        
        .other-turn-card {
            background: rgba(255, 152, 0, 0.3); border-color: #FF9800;
        }
        
        .current-team-name {
            font-size: 1.2em; font-weight: bold; margin-bottom: 10px;
        }
        
        .pick-info {
            font-size: 1.5em; font-weight: bold; color: #4CAF50;
        }
        
        .container { 
            display: grid; 
            grid-template-columns: 2fr 1fr 1fr; 
            gap: 20px; 
        }
        
        .panel { 
            background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
            border-radius: 15px; padding: 20px; 
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .panel h3 { 
            margin-top: 0; color: #4CAF50; 
            border-bottom: 2px solid #4CAF50; padding-bottom: 10px;
            display: flex; justify-content: space-between; align-items: center;
        }
        
        .recommendations-panel.your-turn {
            border: 3px solid #4CAF50; box-shadow: 0 0 20px rgba(76, 175, 80, 0.3);
        }
        
        .recommendations-panel.your-turn h3 {
            color: #4CAF50; font-size: 1.3em;
        }
        
        .player-list { 
            max-height: 450px; overflow-y: auto; 
        }
        
        .player-item { 
            display: flex; justify-content: space-between; align-items: center;
            padding: 12px; margin: 8px 0; 
            background: rgba(255,255,255,0.05); border-radius: 8px; 
            transition: all 0.3s ease; border-left: 4px solid transparent;
        }
        
        .player-item:hover { 
            background: rgba(255,255,255,0.15); transform: translateX(5px); 
        }
        
        .recommendation-item {
            border-left-color: #FF9800; background: rgba(255, 152, 0, 0.1);
        }
        
        .top-recommendation {
            border-left-color: #4CAF50; background: rgba(76, 175, 80, 0.2);
            border: 2px solid rgba(76, 175, 80, 0.5);
        }
        
        .your-player { 
            background: rgba(76, 175, 80, 0.2); border-left-color: #4CAF50; 
        }
        
        .player-info { flex: 1; }
        .player-name { font-weight: bold; font-size: 1.1em; margin-bottom: 4px; }
        .player-details { font-size: 0.9em; color: #ccc; }
        .recommendation-reason { 
            font-size: 0.85em; color: #FFB74D; font-weight: bold; 
            margin-top: 4px; 
        }
        
        .recommendation-explanation {
            font-size: 0.8em; color: #E0E0E0; line-height: 1.4;
            margin-top: 8px; padding: 8px; 
            background: rgba(0,0,0,0.3); border-radius: 6px;
            border-left: 3px solid #FFB74D;
        }
        
        .top-explanation {
            border-left-color: #4CAF50; background: rgba(76, 175, 80, 0.1);
        }
        
        .draft-btn { 
            background: linear-gradient(135deg, #4CAF50, #45a049);
            color: white; border: none; padding: 10px 20px; 
            border-radius: 20px; cursor: pointer; transition: all 0.3s ease;
            font-weight: bold; font-size: 1em;
        }
        
        .draft-btn:hover { 
            transform: scale(1.05); 
            box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4); 
        }
        
        .draft-btn.top-pick {
            background: linear-gradient(135deg, #4CAF50, #2E7D32);
            font-size: 1.1em; padding: 12px 25px;
            box-shadow: 0 0 20px rgba(76, 175, 80, 0.5);
        }
        
        .other-team-dropdown {
            background: rgba(255,255,255,0.1); color: white;
            border: 1px solid rgba(255,255,255,0.3); padding: 8px;
            border-radius: 8px; font-size: 0.9em;
        }
        
        select { 
            background: rgba(255,255,255,0.1); color: white; 
            border: 1px solid rgba(255,255,255,0.3); padding: 8px; border-radius: 8px;
        }
        
        .needs { 
            background: rgba(255, 87, 34, 0.2); padding: 15px; 
            border-radius: 10px; margin-top: 15px;
            border-left: 4px solid #FF5722;
        }
        
        .message { 
            padding: 15px; margin: 15px 0; border-radius: 10px;
            backdrop-filter: blur(10px); font-weight: bold;
        }
        
        .success { 
            background: rgba(76, 175, 80, 0.3); border: 1px solid #4CAF50; 
        }
        
        .error { 
            background: rgba(244, 67, 54, 0.3); border: 1px solid #f44336; 
        }
        
        .draft-history {
            max-height: 200px; overflow-y: auto; margin-top: 15px;
            background: rgba(0,0,0,0.3); border-radius: 8px; padding: 10px;
        }
        
        .draft-pick {
            display: flex; justify-content: space-between; padding: 5px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .your-pick { color: #4CAF50; font-weight: bold; }
        
        .instruction-banner {
            background: rgba(33, 150, 243, 0.3); border: 2px solid #2196F3;
            border-radius: 10px; padding: 15px; margin-bottom: 20px;
            text-align: center; font-weight: bold;
        }
        
        .your-turn-instruction {
            background: rgba(76, 175, 80, 0.3); border-color: #4CAF50;
            animation: pulse 3s infinite;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏈 Fantasy Draft Assistant</h1>
        <p><strong>The League</strong> • 8 Teams • Snake Draft • 0.5 PPR • 2 QB, 2 DEF</p>
    </div>
    
    <div id="instruction-banner" class="instruction-banner"></div>
    
    <div class="draft-status">
        <div class="status-card">
            <div class="pick-info">Pick <span id="current-pick">1</span></div>
            <div>Round <span id="current-round">1</span></div>
        </div>
        
        <div class="status-card" id="current-team-card">
            <div class="current-team-name">On the Clock:</div>
            <div id="current-team" style="font-size: 1.3em; font-weight: bold;">Fudge Bay Packers</div>
        </div>
        
        <div class="status-card" id="turn-indicator">
            <div id="turn-status">YOUR TURN!</div>
        </div>
    </div>
    
    <div id="message-area"></div>
    
    <div class="container">
        <div class="panel">
            <h3>🎯 Available Players</h3>
            <div style="display: flex; gap: 10px; margin-bottom: 15px; align-items: center;">
                <input type="text" id="player-search" placeholder="Search players..." 
                       style="flex: 1; padding: 8px; background: rgba(255,255,255,0.1); 
                              color: white; border: 1px solid rgba(255,255,255,0.3); 
                              border-radius: 8px;" 
                       onkeyup="searchPlayers()" />
                <select id="position-filter" onchange="loadPlayers()" 
                        style="padding: 8px; background: rgba(255,255,255,0.1); 
                               color: white; border: 1px solid rgba(255,255,255,0.3); 
                               border-radius: 8px;">
                    <option value="ALL">All Positions</option>
                    <option value="QB">QB</option>
                    <option value="RB">RB</option>
                    <option value="WR">WR</option>
                    <option value="TE">TE</option>
                    <option value="K">K</option>
                    <option value="DST">DEF</option>
                </select>
                <button onclick="clearSearch()" 
                        style="padding: 8px 12px; background: rgba(255,152,0,0.3); 
                               color: white; border: 1px solid #FF9800; border-radius: 8px; 
                               cursor: pointer;">Clear</button>
            </div>
            <div id="players-list" class="player-list"></div>
        </div>
        
        <div class="panel">
            <h3>👑 Your Team (Fudge Bay Packers)</h3>
            <div id="your-team" class="player-list"></div>
            <div id="needs" class="needs"></div>
            
            <h4>📋 Recent Picks</h4>
            <div id="draft-history" class="draft-history"></div>
        </div>
        
        <div class="panel recommendations-panel" id="recommendations-panel">
            <h3 id="recommendations-title">💡 Recommendations</h3>
            <div id="recommendations" class="player-list"></div>
        </div>
    </div>

    <script>
        let draftState = {};
        
        function showMessage(msg, type = 'success') {
            const area = document.getElementById('message-area');
            area.innerHTML = `<div class="message ${type}">${msg}</div>`;
            setTimeout(() => area.innerHTML = '', 4000);
        }
        
        function draftPlayer(playerName) {
            const team = draftState.current_team;
            const isYourTurn = draftState.your_turn;
            const confirmMsg = isYourTurn ? 
                `🎯 Draft ${playerName} to YOUR team?` : 
                `Draft ${playerName} to ${team}?`;
                
            if (confirm(confirmMsg)) {
                fetch('/api/draft_player', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({player_name: playerName})
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
                
                // Update pick info
                document.getElementById('current-pick').textContent = data.current_pick;
                document.getElementById('current-round').textContent = data.current_round;
                document.getElementById('current-team').textContent = data.current_team;
                
                // Update instruction banner and status
                const banner = document.getElementById('instruction-banner');
                const teamCard = document.getElementById('current-team-card');
                const turnIndicator = document.getElementById('turn-indicator');
                const recPanel = document.getElementById('recommendations-panel');
                const recTitle = document.getElementById('recommendations-title');
                
                if (data.your_turn) {
                    banner.className = 'instruction-banner your-turn-instruction';
                    banner.innerHTML = `
                        <div style="font-size: 1.2em;">🎯 YOUR TURN TO DRAFT! 🎯</div>
                        <div style="margin-top: 8px;">Pick ${data.current_pick} • Round ${data.current_round}</div>
                        <div style="margin-top: 8px; font-size: 0.9em;">Check recommendations below ⬇️</div>
                    `;
                    
                    teamCard.className = 'status-card your-turn-card';
                    turnIndicator.innerHTML = '<div style="color: #4CAF50; font-weight: bold; font-size: 1.2em;">🎯 YOUR TURN!</div>';
                    recPanel.classList.add('your-turn');
                    recTitle.textContent = '🎯 YOUR TOP PICKS';
                } else {
                    banner.className = 'instruction-banner';
                    banner.innerHTML = `
                        <div style="font-size: 1.1em;">⏰ ${data.current_team} is drafting...</div>
                        <div style="margin-top: 8px;">Watch your live draft, then select the player they chose from the list below</div>
                        <div style="margin-top: 8px; font-size: 0.9em;">Use the "Draft to..." dropdown to assign it to ${data.current_team}</div>
                    `;
                    
                    teamCard.className = 'status-card other-turn-card';
                    turnIndicator.innerHTML = '<div style="color: #FF9800;">⏳ Other Team</div>';
                    recPanel.classList.remove('your-turn');
                    recTitle.textContent = '💡 Info';
                }
                
                // Update your team
                const teamEl = document.getElementById('your-team');
                teamEl.innerHTML = data.your_roster.length > 0 ? 
                    data.your_roster.map(p => `
                        <div class="player-item your-player">
                            <div class="player-info">
                                <div class="player-name">${p.name}</div>
                                <div class="player-details">
                                    ${p.position} - ${p.team} • Proj: ${p.projected_points ? p.projected_points.toFixed(1) : '--'}
                                </div>
                            </div>
                        </div>
                    `).join('') : 
                    '<div style="text-align: center; color: #888; padding: 20px;">No players drafted yet</div>';
                
                // Update needs
                const needsList = Object.entries(data.your_needs)
                    .filter(([pos, count]) => count > 0)
                    .map(([pos, count]) => `${pos}: ${count}`)
                    .join(', ');
                document.getElementById('needs').innerHTML = needsList ? 
                    `<strong>🎯 Still need:</strong> ${needsList}` : 
                    '<strong>✅ Roster complete!</strong>';
                
                // Update draft history
                const historyEl = document.getElementById('draft-history');
                if (data.draft_history && data.draft_history.length > 0) {
                    historyEl.innerHTML = data.draft_history.slice(-8).reverse().map(pick => `
                        <div class="draft-pick ${pick.team === data.your_team ? 'your-pick' : ''}">
                            <span>${pick.pick}. ${pick.player.name} (${pick.player.position})</span>
                            <span>${pick.team === data.your_team ? 'YOU' : pick.team.substring(0, 12)}</span>
                        </div>
                    `).join('');
                } else {
                    historyEl.innerHTML = '<div style="text-align: center; color: #888;">No picks yet</div>';
                }
            });
        }
        
        function loadPlayers() {
            const position = document.getElementById('position-filter').value;
            const search = document.getElementById('player-search').value.trim();
            
            let url = `/api/players?position=${position}&limit=40`;
            if (search) {
                url += `&search=${encodeURIComponent(search)}`;
            }
            
            fetch(url)
            .then(r => r.json())
            .then(players => {
                const listEl = document.getElementById('players-list');
                listEl.innerHTML = players.map(p => `
                    <div class="player-item">
                        <div class="player-info">
                            <div class="player-name">${p.name}</div>
                            <div class="player-details">
                                ${p.position} - ${p.team} • ADP: ${p.adp < 999 ? p.adp.toFixed(1) : '---'} • Proj: ${p.projected_points ? p.projected_points.toFixed(1) : '--'}
                            </div>
                        </div>
                        <button class="draft-btn ${draftState.your_turn ? 'top-pick' : ''}" 
                                data-player-name="${p.name}" onclick="draftPlayer(this.dataset.playerName)">
                            ${draftState.your_turn ? '🎯 Draft' : 'Draft'}
                        </button>
                    </div>
                `).join('');
            });
        }
        
        function loadRecommendations() {
            fetch('/api/recommendations')
            .then(r => r.json())
            .then(recs => {
                const container = document.getElementById('recommendations');
                if (recs.length === 0) {
                    container.innerHTML = '<div style="text-align: center; color: #888; padding: 20px;">No specific recommendations right now</div>';
                    return;
                }
                
                container.innerHTML = recs.map((rec, index) => `
                    <div class="player-item recommendation-item ${index === 0 ? 'top-recommendation' : ''}">
                        <div class="player-info">
                            <div class="player-name">${rec.player.name}</div>
                            <div class="player-details">
                                ${rec.player.position} - ${rec.player.team} • 
                                ADP: ${rec.player.adp < 999 ? rec.player.adp.toFixed(1) : '---'} • 
                                Proj: ${rec.player.projected_points ? rec.player.projected_points.toFixed(1) : '--'}
                            </div>
                            <div class="recommendation-reason">${rec.reason}</div>
                            ${rec.explanation ? `<div class="recommendation-explanation ${index === 0 ? 'top-explanation' : ''}">${rec.explanation}</div>` : ''}
                        </div>
                        <button class="draft-btn ${index === 0 ? 'top-pick' : ''}" 
                                data-player-name="${rec.player.name}" onclick="draftPlayer(this.dataset.playerName)">
                            ${index === 0 ? '🎯 DRAFT' : 'Draft'}
                        </button>
                    </div>
                `).join('');
            });
        }
        
        function searchPlayers() {
            // Debounce search to avoid too many requests
            clearTimeout(window.searchTimeout);
            window.searchTimeout = setTimeout(() => {
                loadPlayers();
            }, 300);
        }
        
        function clearSearch() {
            document.getElementById('player-search').value = '';
            document.getElementById('position-filter').value = 'ALL';
            loadPlayers();
        }
        
        function resetDraft() {
            if (confirm('⚠️ This will RESET THE ENTIRE DRAFT and start over. Are you sure?')) {
                fetch('/api/reset_draft', {method: 'POST'})
                .then(r => r.json())
                .then(data => {
                    showMessage(data.message, data.success ? 'success' : 'error');
                    if (data.success) loadAll();
                });
            }
        }
        
        function loadAll() {
            loadDraftState();
            loadPlayers();
            loadRecommendations();
        }
        
        // Initial load and auto-refresh (but don't auto-refresh if user is searching)
        loadAll();
        setInterval(() => {
            // Only auto-refresh if no active search
            const hasSearch = document.getElementById('player-search').value.trim();
            if (!hasSearch) {
                loadAll();
            } else {
                // Still update draft state and recommendations during search
                loadDraftState();
                loadRecommendations();
            }
        }, 8000);
    </script>
</body>
</html>'''
    
    with open('templates/final_index.html', 'w') as f:
        f.write(html_content)
    
    print("🚀 Starting FINAL Draft Assistant...")
    print("📱 Open http://localhost:5000")
    print("\n🎯 PERFECT DRAFT WORKFLOW:")
    print("1. YOUR TURN: Big green banner + top recommendations")  
    print("2. OTHER TEAMS: Watch live draft, use dropdown to assign picks")
    print("3. CYCLE: Repeats perfectly through snake draft")
    print("\n🏆 YOU HAVE PICK #1 - Fudge Bay Packers!")
    app.run(debug=True, host='0.0.0.0', port=5000)