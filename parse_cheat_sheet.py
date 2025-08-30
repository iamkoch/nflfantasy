#!/usr/bin/env python3
"""
Parse the fantasy cheat sheet Excel file and populate the database
"""

import pandas as pd
import sqlite3
import numpy as np

def parse_and_populate():
    try:
        # Read the Excel file
        print("📊 Reading Excel cheat sheet...")
        df = pd.read_excel('Cheat Sheet (Full) 25-26.xlsx')
        
        # The data starts from row 1 (index 1) since row 0 is headers
        # Let's clean up the DataFrame and extract the key columns
        data_df = df.iloc[1:].copy()  # Skip the header row
        
        # Map the key columns we need (based on the column structure we saw)
        # Column 0: Player names
        # Column 1: Age  
        # Column 2: Team
        # Column 3: Position rank (WR1, RB1, etc)
        # Column 4: Position (WR, RB, etc)
        # Column 4: ADP
        # Other columns contain various stats and projections
        
        players_data = []
        
        for idx, row in data_df.iterrows():
            try:
                # Extract basic player info
                player_name = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
                age = row.iloc[1] if pd.notna(row.iloc[1]) else None
                team = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""
                pos_rank = str(row.iloc[3]) if pd.notna(row.iloc[3]) else ""
                position = str(row.iloc[4]) if pd.notna(row.iloc[4]) else ""
                
                # Skip if we don't have a valid player name or position
                if not player_name or player_name == "nan" or not position or position == "nan":
                    continue
                
                # Extract ADP (column 4, but there might be some formatting issues)
                adp = None
                try:
                    adp_val = row.iloc[5] if len(row) > 5 else None
                    if pd.notna(adp_val):
                        adp = float(adp_val)
                except:
                    adp = 999.0  # Default high ADP for players without data
                
                # Extract projected points (around column 37 based on the headers)
                proj_points = None
                try:
                    if len(row) > 37:
                        proj_val = row.iloc[37]
                        if pd.notna(proj_val):
                            proj_points = float(proj_val)
                except:
                    proj_points = 0.0
                
                # Extract team (column 57)
                actual_team = team
                if len(row) > 57:
                    team_val = row.iloc[57]
                    if pd.notna(team_val) and str(team_val) != "nan":
                        actual_team = str(team_val)
                
                # Extract injury status (column 59)
                injury_status = ""
                if len(row) > 59:
                    inj_val = row.iloc[59]
                    if pd.notna(inj_val):
                        injury_status = str(inj_val)
                
                # Parse position rank to get numeric rank
                position_rank = 999
                if pos_rank and pos_rank != "nan":
                    try:
                        # Extract number from strings like "WR1", "RB12", etc.
                        import re
                        match = re.search(r'(\d+)', str(pos_rank))
                        if match:
                            position_rank = int(match.group(1))
                    except:
                        pass
                
                # Determine overall rank based on ADP
                overall_rank = int(adp) if adp and adp < 999 else 999
                
                # Default values
                tier = 1 if overall_rank <= 24 else (2 if overall_rank <= 60 else 3)
                bye_week = 0  # Would need additional data for this
                
                players_data.append({
                    'name': player_name,
                    'position': position,
                    'team': actual_team,
                    'overall_rank': overall_rank,
                    'position_rank': position_rank,
                    'projected_points': proj_points if proj_points else 0.0,
                    'adp': adp if adp else 999.0,
                    'tier': tier,
                    'bye_week': bye_week,
                    'injury_status': injury_status,
                    'sleeper_rating': 0,
                    'bust_rating': 0,
                    'notes': f"Age: {age}" if age else ""
                })
                
            except Exception as e:
                print(f"⚠️  Error processing row {idx}: {e}")
                continue
        
        print(f"📈 Extracted {len(players_data)} players from Excel file")
        
        # Connect to database and populate
        conn = sqlite3.connect('fantasy_draft_2025.db')
        cursor = conn.cursor()
        
        # Clear existing players
        cursor.execute('DELETE FROM players')
        
        # Insert players
        for player in players_data:
            cursor.execute('''
                INSERT INTO players (name, position, team, overall_rank, position_rank, projected_points,
                                   adp, tier, bye_week, injury_status, sleeper_rating, bust_rating, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                player['name'], player['position'], player['team'], player['overall_rank'],
                player['position_rank'], player['projected_points'], player['adp'], player['tier'],
                player['bye_week'], player['injury_status'], player['sleeper_rating'],
                player['bust_rating'], player['notes']
            ))
        
        conn.commit()
        
        # Show some stats
        cursor.execute("SELECT COUNT(*) FROM players")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT position, COUNT(*) FROM players GROUP BY position ORDER BY COUNT(*) DESC")
        position_counts = cursor.fetchall()
        
        print(f"✅ Successfully populated database with {total} players!")
        print("\n📊 Players by position:")
        for pos, count in position_counts:
            print(f"  {pos}: {count}")
        
        # Show top 20 players by ADP
        cursor.execute("""
            SELECT name, position, team, adp, projected_points 
            FROM players 
            WHERE adp < 999 
            ORDER BY adp 
            LIMIT 20
        """)
        top_players = cursor.fetchall()
        
        print("\n🏆 Top 20 players by ADP:")
        for i, (name, pos, team, adp, proj) in enumerate(top_players, 1):
            print(f"  {i:2d}. {name:<20} ({pos:<2} - {team:<3}) ADP: {adp:5.1f} Proj: {proj:5.1f}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parse_and_populate()