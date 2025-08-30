#!/usr/bin/env python3
"""
Quick Draft Assistant - Command Line Version
Simple and fast for draft day use
"""

import sqlite3
import sys

def get_db_connection():
    conn = sqlite3.connect('fantasy_draft_2025.db')
    conn.row_factory = sqlite3.Row
    return conn

def show_top_players(position=None, limit=10):
    """Show top available players"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if position:
        cursor.execute("""
            SELECT name, position, team, adp, projected_points 
            FROM players 
            WHERE position = ? 
            ORDER BY adp 
            LIMIT ?
        """, (position.upper(), limit))
    else:
        cursor.execute("""
            SELECT name, position, team, adp, projected_points 
            FROM players 
            ORDER BY adp 
            LIMIT ?
        """, (limit,))
    
    players = cursor.fetchall()
    conn.close()
    
    print(f"\n🏆 Top {limit} {position or 'Overall'} Players:")
    print("-" * 60)
    for i, player in enumerate(players, 1):
        proj = f"{player['projected_points']:4.1f}" if player['projected_points'] else "  --"
        adp = f"{player['adp']:5.1f}" if player['adp'] < 999 else "  ---"
        print(f"{i:2d}. {player['name']:<20} ({player['position']} - {player['team']}) ADP:{adp} Proj:{proj}")

def search_player(name):
    """Search for a specific player"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name, position, team, adp, projected_points, notes
        FROM players 
        WHERE name LIKE ? 
        ORDER BY adp
    """, (f"%{name}%",))
    
    players = cursor.fetchall()
    conn.close()
    
    if not players:
        print(f"❌ No players found matching '{name}'")
        return
    
    print(f"\n🔍 Search results for '{name}':")
    print("-" * 60)
    for player in players:
        proj = f"{player['projected_points']:4.1f}" if player['projected_points'] else "  --"
        adp = f"{player['adp']:5.1f}" if player['adp'] < 999 else "  ---"
        print(f"• {player['name']:<25} ({player['position']} - {player['team']}) ADP:{adp} Proj:{proj}")
        if player['notes']:
            print(f"  Notes: {player['notes']}")

def show_league_info():
    """Show league settings"""
    print("\n🏈 LEAGUE: The League")
    print("📊 8 Teams • 0.5 PPR • 2 QB • 2 DEF")
    print("📅 Draft: Friday, Aug 29, 2025 3:30pm EDT")
    print("\n🏁 Starting Lineup: 2 QB, 3 RB, 3 WR, 1 TE, 3 FLEX, 1 K, 2 DEF, 9 Bench")

def show_positional_scarcity():
    """Show position depth analysis"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
    
    print("\n📈 POSITIONAL DEPTH ANALYSIS:")
    print("-" * 50)
    
    for pos in positions:
        cursor.execute("""
            SELECT COUNT(*) as total,
                   AVG(projected_points) as avg_proj
            FROM players 
            WHERE position = ? AND adp < 200
        """, (pos,))
        
        stats = cursor.fetchone()
        need = {'QB': 16, 'RB': 48, 'WR': 48, 'TE': 8, 'K': 8, 'DST': 16}[pos]  # 8 teams
        
        print(f"{pos:3}: {stats['total']:3d} players available (need {need:2d}) - Avg Proj: {stats['avg_proj']:4.1f}")
    
    conn.close()

def show_sleepers():
    """Show potential sleepers (high projected points, low ADP)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name, position, team, adp, projected_points
        FROM players 
        WHERE adp > 50 AND projected_points > 10 
        ORDER BY (projected_points - (200 - adp) / 20) DESC
        LIMIT 15
    """)
    
    sleepers = cursor.fetchall()
    conn.close()
    
    print("\n💎 POTENTIAL SLEEPERS:")
    print("-" * 60)
    for i, player in enumerate(sleepers, 1):
        proj = f"{player['projected_points']:4.1f}" if player['projected_points'] else "  --"
        adp = f"{player['adp']:5.1f}" if player['adp'] < 999 else "  ---"
        print(f"{i:2d}. {player['name']:<20} ({player['position']} - {player['team']}) ADP:{adp} Proj:{proj}")

def main():
    if len(sys.argv) == 1:
        print("🏈 NFL FANTASY DRAFT ASSISTANT - Quick Mode")
        print("=" * 50)
        show_league_info()
        show_positional_scarcity()
        show_top_players(limit=20)
        show_sleepers()
        
        print("\n💡 USAGE:")
        print("  python quick_draft.py top [position] [limit]  - Show top players")
        print("  python quick_draft.py search <name>          - Search for player")
        print("  python quick_draft.py qb|rb|wr|te|k|dst      - Show position players")
        print("  python quick_draft.py sleepers               - Show sleeper picks")
        print("  python quick_draft.py league                 - Show league info")
        
    elif len(sys.argv) >= 2:
        command = sys.argv[1].lower()
        
        if command == 'league':
            show_league_info()
            show_positional_scarcity()
            
        elif command == 'sleepers':
            show_sleepers()
            
        elif command == 'search' and len(sys.argv) >= 3:
            search_player(' '.join(sys.argv[2:]))
            
        elif command == 'top':
            position = sys.argv[2].upper() if len(sys.argv) >= 3 else None
            limit = int(sys.argv[3]) if len(sys.argv) >= 4 else 15
            show_top_players(position, limit)
            
        elif command in ['qb', 'rb', 'wr', 'te', 'k', 'dst']:
            show_top_players(command, 20)
            
        else:
            print("❓ Unknown command. Run without arguments to see usage.")

if __name__ == "__main__":
    main()