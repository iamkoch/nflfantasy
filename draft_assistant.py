#!/usr/bin/env python3
"""
NFL Fantasy Draft Assistant App
Optimized for your league settings: 8 teams, 0.5 PPR, 2 QB, 2 DEF
"""

import sqlite3
import os
from datetime import datetime

class DraftAssistant:
    def __init__(self):
        self.conn = sqlite3.connect('fantasy_draft_2025.db')
        self.conn.row_factory = sqlite3.Row
        self.current_pick = 1
        self.my_team = []
        self.drafted_players = set()
        
    def display_league_settings(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM league_settings WHERE id = 1")
        settings = cursor.fetchone()
        
        print("🏈 LEAGUE SETTINGS")
        print("=" * 50)
        print(f"League: {settings['name']}")
        print(f"Teams: {settings['teams']}")
        print(f"Scoring: {settings['ppr_scoring']} PPR")
        print(f"Starting Lineup:")
        print(f"  QB: {settings['qb_slots']}")
        print(f"  RB: {settings['rb_slots']}")
        print(f"  WR: {settings['wr_slots']}")
        print(f"  TE: {settings['te_slots']}")
        print(f"  FLEX: {settings['flex_slots']}")
        print(f"  K: {settings['k_slots']}")
        print(f"  DEF: {settings['def_slots']}")
        print(f"  Bench: {settings['bench_slots']}")
        print("=" * 50)
        
    def get_available_players(self, position=None, limit=20):
        cursor = self.conn.cursor()
        
        base_query = """
            SELECT * FROM players 
            WHERE name NOT IN ({})
        """.format(','.join(['?' for _ in self.drafted_players]))
        
        params = list(self.drafted_players)
        
        if position:
            base_query += " AND position = ?"
            params.append(position)
            
        base_query += " ORDER BY adp LIMIT ?"
        params.append(limit)
        
        cursor.execute(base_query, params)
        return cursor.fetchall()
    
    def get_position_needs(self):
        """Calculate remaining position needs based on league settings"""
        needs = {
            'QB': 2, 'RB': 6, 'WR': 6, 'TE': 1, 'K': 1, 'DST': 2
        }
        
        # Count current positions on my team
        for player in self.my_team:
            pos = player['position']
            if pos in needs and needs[pos] > 0:
                needs[pos] -= 1
        
        return needs
    
    def draft_player(self, player_name):
        """Draft a player to my team"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM players WHERE name = ?", (player_name,))
        player = cursor.fetchone()
        
        if not player:
            print(f"❌ Player '{player_name}' not found!")
            return False
            
        if player_name in self.drafted_players:
            print(f"❌ Player '{player_name}' already drafted!")
            return False
            
        # Add to my team and drafted players
        self.my_team.append(dict(player))
        self.drafted_players.add(player_name)
        
        # Record in draft results
        cursor.execute('''
            INSERT INTO draft_results (player_id, team_name, round, pick, overall_pick)
            VALUES (?, ?, ?, ?, ?)
        ''', (player['id'], 'My Team', 
              (self.current_pick - 1) // 8 + 1, 
              ((self.current_pick - 1) % 8) + 1, 
              self.current_pick))
        
        self.conn.commit()
        self.current_pick += 1
        
        print(f"✅ Drafted {player['name']} ({player['position']} - {player['team']}) at pick {self.current_pick - 1}")
        return True
    
    def show_draft_board(self):
        """Show top available players by position"""
        print("\n🎯 DRAFT BOARD - Top Available Players")
        print("=" * 80)
        
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
        needs = self.get_position_needs()
        
        for pos in positions:
            players = self.get_available_players(pos, 8)
            need_indicator = f"(NEED {needs[pos]})" if needs[pos] > 0 else ""
            print(f"\n{pos} {need_indicator}:")
            print("-" * 40)
            
            for i, player in enumerate(players[:5], 1):
                proj = f"{player['projected_points']:4.1f}" if player['projected_points'] else "  --"
                adp = f"{player['adp']:5.1f}" if player['adp'] < 999 else "  ---"
                print(f"  {i}. {player['name']:<20} {player['team']:<3} ADP:{adp} Proj:{proj}")
    
    def show_my_team(self):
        """Display current team roster"""
        if not self.my_team:
            print("\n📋 MY TEAM: Empty")
            return
            
        print("\n📋 MY TEAM")
        print("=" * 50)
        
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
        for pos in positions:
            pos_players = [p for p in self.my_team if p['position'] == pos]
            if pos_players:
                print(f"\n{pos}:")
                for player in pos_players:
                    proj = f"{player['projected_points']:4.1f}" if player['projected_points'] else "  --"
                    print(f"  • {player['name']:<20} {player['team']:<3} Proj:{proj}")
        
        # Show position needs
        needs = self.get_position_needs()
        remaining_needs = [f"{pos}:{count}" for pos, count in needs.items() if count > 0]
        if remaining_needs:
            print(f"\n🎯 Still need: {', '.join(remaining_needs)}")
    
    def get_recommendations(self):
        """Get draft recommendations based on team needs and value"""
        needs = self.get_position_needs()
        recommendations = []
        
        # Get top players for positions we need
        for pos, need_count in needs.items():
            if need_count > 0:
                players = self.get_available_players(pos, 5)
                for player in players:
                    value_score = 0
                    # Higher value for positions we need more of
                    value_score += need_count * 10
                    # Higher value for better projected points
                    value_score += (player['projected_points'] or 0)
                    # Lower ADP = higher value (inverse relationship)
                    if player['adp'] and player['adp'] < 999:
                        value_score += max(0, 200 - player['adp']) / 20
                    
                    recommendations.append({
                        'player': player,
                        'value_score': value_score,
                        'reason': f"Need {need_count} {pos}{'s' if need_count > 1 else ''}"
                    })
        
        # Sort by value score
        recommendations.sort(key=lambda x: x['value_score'], reverse=True)
        return recommendations[:10]
    
    def show_recommendations(self):
        """Display draft recommendations"""
        recs = self.get_recommendations()
        
        print("\n💡 DRAFT RECOMMENDATIONS")
        print("=" * 60)
        
        for i, rec in enumerate(recs[:5], 1):
            player = rec['player']
            proj = f"{player['projected_points']:4.1f}" if player['projected_points'] else "  --"
            adp = f"{player['adp']:5.1f}" if player['adp'] < 999 else "  ---"
            print(f"{i}. {player['name']:<20} ({player['position']} - {player['team']}) "
                  f"ADP:{adp} Proj:{proj}")
            print(f"   Reason: {rec['reason']}")
    
    def run_interactive_draft(self):
        """Main interactive draft loop"""
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("🏈 NFL FANTASY DRAFT ASSISTANT")
        print("Draft Date: Friday, Aug 29, 2025 3:30pm EDT")
        self.display_league_settings()
        
        while True:
            print(f"\n📍 CURRENT PICK: {self.current_pick}")
            self.show_my_team()
            self.show_recommendations()
            self.show_draft_board()
            
            print("\n" + "=" * 80)
            print("COMMANDS:")
            print("  draft <player_name>  - Draft a player")
            print("  skip                 - Skip a pick (other team drafted)")
            print("  search <name>        - Search for a player")
            print("  pos <position>       - Show players by position")
            print("  quit                 - Exit draft")
            print("=" * 80)
            
            command = input(f"Pick {self.current_pick} > ").strip()
            
            if command.lower() == 'quit':
                break
            elif command.lower() == 'skip':
                self.current_pick += 1
                print(f"⏭️  Skipped pick {self.current_pick - 1}")
            elif command.startswith('draft '):
                player_name = command[6:].strip()
                self.draft_player(player_name)
            elif command.startswith('search '):
                search_term = command[7:].strip()
                self.search_players(search_term)
            elif command.startswith('pos '):
                position = command[4:].strip().upper()
                self.show_position(position)
            else:
                print("❓ Unknown command. Type 'quit' to exit.")
            
            input("Press Enter to continue...")
            os.system('clear' if os.name == 'posix' else 'cls')
    
    def search_players(self, search_term):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM players 
            WHERE name LIKE ? AND name NOT IN ({})
            ORDER BY adp 
            LIMIT 10
        """.format(','.join(['?' for _ in self.drafted_players])), 
        ['%' + search_term + '%'] + list(self.drafted_players))
        
        players = cursor.fetchall()
        print(f"\n🔍 Search results for '{search_term}':")
        for player in players:
            proj = f"{player['projected_points']:4.1f}" if player['projected_points'] else "  --"
            adp = f"{player['adp']:5.1f}" if player['adp'] < 999 else "  ---"
            print(f"  {player['name']:<25} ({player['position']} - {player['team']}) "
                  f"ADP:{adp} Proj:{proj}")
    
    def show_position(self, position):
        players = self.get_available_players(position, 15)
        print(f"\n📊 Available {position} players:")
        for i, player in enumerate(players, 1):
            proj = f"{player['projected_points']:4.1f}" if player['projected_points'] else "  --"
            adp = f"{player['adp']:5.1f}" if player['adp'] < 999 else "  ---"
            print(f"  {i:2d}. {player['name']:<20} {player['team']:<3} "
                  f"ADP:{adp} Proj:{proj}")

def main():
    assistant = DraftAssistant()
    assistant.run_interactive_draft()

if __name__ == "__main__":
    main()