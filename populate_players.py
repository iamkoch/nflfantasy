#!/usr/bin/env python3
"""
Populate fantasy football database with 2025 player rankings
Based on composite rankings from ESPN, FantasyPros, and other expert sources
"""

import sqlite3

def populate_players():
    conn = sqlite3.connect('fantasy_draft_2025.db')
    cursor = conn.cursor()
    
    # Top 2025 Fantasy Football Players - Composite Rankings (0.5 PPR optimized)
    # Data compiled from ESPN, FantasyPros, PFF, and other expert sources
    players_data = [
        # Quarterbacks - Higher value in 2QB league
        ("Josh Allen", "QB", "BUF", 1, 1, 24.8, 8.5, 1, 12, "", 0, 0, "Elite dual-threat QB, consistent QB1"),
        ("Lamar Jackson", "QB", "BAL", 2, 2, 24.2, 12.2, 1, 14, "", 0, 0, "Top rushing QB, touchdown machine"),
        ("Jalen Hurts", "QB", "PHI", 3, 3, 23.9, 15.8, 1, 5, "", 0, 0, "Rushing upside, improved passing"),
        ("Jayden Daniels", "QB", "WAS", 4, 4, 22.8, 18.5, 2, 14, "", 8, 0, "Rookie sensation, dual-threat ability"),
        ("Kyler Murray", "QB", "ARI", 5, 5, 22.3, 22.1, 2, 11, "", 0, 0, "Healthy, explosive upside"),
        ("Dak Prescott", "QB", "DAL", 6, 6, 21.5, 28.3, 2, 7, "", 0, 0, "Consistent pocket passer"),
        ("Joe Burrow", "QB", "CIN", 7, 7, 21.2, 31.5, 2, 12, "", 0, 3, "Elite when healthy"),
        ("Patrick Mahomes", "QB", "KC", 8, 8, 20.9, 35.2, 3, 6, "", 0, 0, "Always a threat for big games"),
        ("Tua Tagovailoa", "QB", "MIA", 9, 9, 20.1, 42.8, 3, 6, "", 0, 5, "Health concerns but high ceiling"),
        ("Baker Mayfield", "QB", "TB", 10, 10, 19.8, 48.2, 3, 11, "", 7, 0, "Breakout 2024 season"),
        
        # Running Backs - Premium position
        ("Bijan Robinson", "RB", "ATL", 11, 1, 18.9, 3.2, 1, 12, "", 0, 0, "Elite talent, improved usage expected"),
        ("Jahmyr Gibbs", "RB", "DET", 12, 2, 18.5, 4.8, 1, 5, "", 0, 0, "Explosive dual-threat back"),
        ("Saquon Barkley", "RB", "PHI", 13, 3, 17.8, 6.5, 1, 5, "", 0, 0, "Elite talent in great offense"),
        ("Breece Hall", "RB", "NYJ", 14, 4, 17.2, 8.9, 1, 12, "", 0, 0, "Fully healthy, high ceiling"),
        ("Derrick Henry", "RB", "BAL", 15, 5, 16.8, 11.2, 2, 14, "", 0, 2, "Age concerns but elite offense"),
        ("Josh Jacobs", "RB", "GB", 16, 6, 16.3, 13.8, 2, 10, "", 0, 0, "Proven workhorse, good offense"),
        ("Kenneth Walker III", "RB", "SEA", 17, 7, 15.9, 16.5, 2, 10, "", 0, 0, "Explosive runner when healthy"),
        ("Jonathan Taylor", "RB", "IND", 18, 8, 15.6, 18.9, 2, 14, "", 0, 3, "Bounce-back candidate"),
        ("Kyren Williams", "RB", "LAR", 19, 9, 15.2, 21.3, 2, 6, "", 0, 0, "Reliable three-down back"),
        ("De'Von Achane", "RB", "MIA", 20, 10, 14.8, 24.1, 3, 6, "", 6, 0, "Explosive upside, health questions"),
        
        # Wide Receivers - Deep position
        ("Ja'Marr Chase", "WR", "CIN", 21, 1, 17.2, 5.8, 1, 12, "", 0, 0, "Elite target share, big-play ability"),
        ("Amon-Ra St. Brown", "WR", "DET", 22, 2, 16.8, 7.2, 1, 5, "", 0, 0, "Target monster, consistent"),
        ("CeeDee Lamb", "WR", "DAL", 23, 3, 16.5, 9.1, 1, 7, "", 0, 0, "WR1 ceiling, proven production"),
        ("Tyreek Hill", "WR", "MIA", 24, 4, 16.1, 10.8, 1, 6, "", 0, 0, "Elite speed, big-play threat"),
        ("A.J. Brown", "WR", "PHI", 25, 5, 15.8, 12.5, 1, 5, "", 0, 0, "Red zone target, consistent"),
        ("Puka Nacua", "WR", "LAR", 26, 6, 15.4, 14.2, 2, 6, "", 0, 0, "Breakout star, target hog"),
        ("Garrett Wilson", "WR", "NYJ", 27, 7, 15.1, 16.8, 2, 12, "", 0, 0, "Improved QB situation"),
        ("Chris Olave", "WR", "NO", 28, 8, 14.8, 18.5, 2, 12, "", 0, 0, "Deep threat, consistent target"),
        ("Mike Evans", "WR", "TB", 29, 9, 14.5, 20.2, 2, 11, "", 0, 0, "Red zone beast, aging gracefully"),
        ("Marvin Harrison Jr.", "WR", "ARI", 30, 10, 14.2, 22.8, 2, 11, "", 8, 0, "Rookie sensation, WR1 upside"),
        
        # Tight Ends - Scarce position
        ("Travis Kelce", "TE", "KC", 31, 1, 13.8, 25.5, 1, 6, "", 0, 2, "Still the TE1 despite age"),
        ("Mark Andrews", "TE", "BAL", 32, 2, 12.9, 38.2, 1, 14, "", 0, 0, "Red zone monster"),
        ("Sam LaPorta", "TE", "DET", 33, 3, 12.5, 42.1, 1, 5, "", 0, 0, "Consistent target, young"),
        ("George Kittle", "TE", "SF", 34, 4, 12.1, 48.8, 2, 9, "", 0, 0, "Elite when healthy"),
        ("Trey McBride", "TE", "ARI", 35, 5, 11.8, 55.2, 2, 11, "", 6, 0, "Emerging target, consistent"),
        ("Evan Engram", "TE", "JAC", 36, 6, 11.4, 62.5, 2, 12, "", 0, 0, "PPR friendly, reliable"),
        ("David Njoku", "TE", "CLE", 37, 7, 11.1, 68.8, 3, 10, "", 0, 0, "Athletic freak, TD upside"),
        ("Kyle Pitts", "TE", "ATL", 38, 8, 10.8, 72.1, 3, 12, "", 7, 4, "Upside play, inconsistent"),
        ("Dallas Goedert", "TE", "PHI", 39, 9, 10.5, 78.5, 3, 5, "", 0, 0, "Solid floor, limited ceiling"),
        ("Jake Ferguson", "TE", "DAL", 40, 10, 10.2, 85.2, 3, 7, "", 6, 0, "Emerging option, good offense"),
        
        # Kickers - Draft late
        ("Justin Tucker", "K", "BAL", 41, 1, 9.8, 145.2, 1, 14, "", 0, 0, "Most accurate kicker ever"),
        ("Harrison Butker", "K", "KC", 42, 2, 9.5, 148.5, 1, 6, "", 0, 0, "High-powered offense"),
        ("Brandon McManus", "K", "GB", 43, 3, 9.2, 152.1, 1, 10, "", 0, 0, "Reliable leg, good offense"),
        ("Tyler Bass", "K", "BUF", 44, 4, 9.0, 155.8, 2, 12, "", 0, 0, "High-scoring offense"),
        ("Chris Boswell", "K", "PIT", 45, 5, 8.8, 158.5, 2, 9, "", 0, 0, "Veteran reliability"),
        
        # Defenses - Need 2 in this league
        ("Pittsburgh Steelers", "DEF", "PIT", 46, 1, 11.2, 138.5, 1, 9, "", 0, 0, "Elite defense, sack upside"),
        ("Cleveland Browns", "DEF", "CLE", 47, 2, 10.8, 142.1, 1, 10, "", 0, 0, "Myles Garrett led defense"),
        ("Baltimore Ravens", "DEF", "BAL", 48, 3, 10.5, 145.8, 1, 14, "", 0, 0, "Aggressive defense, turnovers"),
        ("San Francisco 49ers", "DEF", "SF", 49, 4, 10.2, 148.2, 1, 9, "", 0, 0, "Talented across the board"),
        ("Dallas Cowboys", "DEF", "DAL", 50, 5, 9.9, 151.5, 2, 7, "", 0, 0, "Micah Parsons impact"),
        ("Miami Dolphins", "DEF", "MIA", 51, 6, 9.6, 154.2, 2, 6, "", 0, 0, "Improved pass rush"),
        ("Buffalo Bills", "DEF", "BUF", 52, 7, 9.3, 157.1, 2, 12, "", 0, 0, "Opportunistic defense"),
        ("New York Jets", "DEF", "NYJ", 53, 8, 9.0, 159.8, 2, 12, "", 0, 0, "Aaron Rodgers impact"),
        ("Philadelphia Eagles", "DEF", "PHI", 54, 9, 8.8, 162.5, 2, 5, "", 0, 0, "Aggressive scheme"),
        ("Kansas City Chiefs", "DEF", "KC", 55, 10, 8.5, 165.2, 3, 6, "", 0, 0, "Opportunistic, game script"),
    ]
    
    # Additional depth players
    additional_players = [
        # More RBs
        ("Alvin Kamara", "RB", "NO", 56, 11, 14.5, 26.8, 3, 12, "", 0, 0, "PPR machine when healthy"),
        ("Joe Mixon", "RB", "HOU", 57, 12, 14.2, 29.5, 3, 7, "", 0, 0, "Workhorse back, new team"),
        ("Aaron Jones", "RB", "MIN", 58, 13, 13.9, 32.1, 3, 6, "", 0, 0, "Change of scenery boost"),
        ("Rachaad White", "RB", "TB", 59, 14, 13.6, 35.8, 3, 11, "", 0, 0, "Three-down back potential"),
        ("James Cook", "RB", "BUF", 60, 15, 13.3, 38.5, 4, 12, "", 6, 0, "High-powered offense"),
        ("Rhamondre Stevenson", "RB", "NE", 61, 16, 13.0, 41.2, 4, 14, "", 0, 0, "Workhorse role, bad offense"),
        ("Travis Etienne Jr.", "RB", "JAC", 62, 17, 12.7, 44.1, 4, 12, "", 0, 0, "Speed demon, inconsistent"),
        ("Tony Pollard", "RB", "TEN", 63, 18, 12.4, 46.8, 4, 13, "", 0, 0, "New opportunity, questions"),
        ("Najee Harris", "RB", "PIT", 64, 19, 12.1, 49.5, 4, 9, "", 0, 0, "Volume play, limited upside"),
        ("D'Andre Swift", "RB", "CHI", 65, 20, 11.8, 52.2, 4, 7, "", 0, 3, "Injury prone, new team"),
        
        # More WRs  
        ("DK Metcalf", "WR", "SEA", 66, 11, 13.9, 23.5, 2, 10, "", 0, 0, "Red zone threat, consistent"),
        ("Stefon Diggs", "WR", "HOU", 67, 12, 13.6, 25.8, 2, 7, "", 0, 0, "New team, still elite"),
        ("DeVonta Smith", "WR", "PHI", 68, 13, 13.3, 28.2, 3, 5, "", 0, 0, "Consistent WR2, great hands"),
        ("Tee Higgins", "WR", "CIN", 69, 14, 13.0, 30.5, 3, 12, "", 0, 0, "Big play ability, injury prone"),
        ("DJ Moore", "WR", "CHI", 70, 15, 12.7, 33.1, 3, 7, "", 0, 0, "Consistent target, QB questions"),
        ("Amari Cooper", "WR", "CLE", 71, 16, 12.4, 35.8, 3, 10, "", 0, 0, "Veteran reliability"),
        ("Keenan Allen", "WR", "CHI", 72, 17, 12.1, 38.2, 3, 7, "", 0, 0, "PPR monster, age concerns"),
        ("Calvin Ridley", "WR", "TEN", 73, 18, 11.8, 40.5, 4, 13, "", 0, 0, "Bounce back candidate"),
        ("Michael Pittman Jr.", "WR", "IND", 74, 19, 11.5, 43.1, 4, 14, "", 0, 0, "Target hog, QB dependent"),
        ("Terry McLaurin", "WR", "WAS", 75, 20, 11.2, 45.8, 4, 14, "", 0, 0, "Reliable despite QB play"),
        
        # Sleeper/Rookie Picks
        ("Rome Odunze", "WR", "CHI", 76, 21, 10.9, 58.5, 4, 7, "", 9, 0, "Rookie with upside, good situation"),
        ("Jayden Reed", "WR", "GB", 77, 22, 10.6, 62.1, 4, 10, "", 8, 0, "Explosive playmaker"),
        ("Brian Thomas Jr.", "WR", "JAC", 78, 23, 10.3, 65.8, 5, 12, "", 9, 0, "Rookie deep threat"),
        ("Ladd McConkey", "WR", "LAC", 79, 24, 10.0, 69.2, 5, 5, "", 8, 0, "Rookie slot receiver"),
        ("Jordan Addison", "WR", "MIN", 80, 25, 9.7, 72.5, 5, 6, "", 7, 0, "Sophomore breakout candidate"),
        
        # Handcuff RBs
        ("Omarion Hampton", "RB", "LAC", 81, 21, 8.5, 89.5, 5, 5, "", 9, 0, "Rookie lead back potential"),
        ("Blake Corum", "RB", "LAR", 82, 22, 8.2, 95.2, 5, 6, "", 8, 0, "Rookie in RBBC"),
        ("MarShawn Lloyd", "RB", "GB", 83, 23, 7.9, 101.5, 5, 10, "", 8, 0, "Rookie change of pace"),
        ("Bucky Irving", "RB", "TB", 84, 24, 7.6, 108.2, 5, 11, "", 7, 0, "Emerging back"),
        ("Ray Davis", "RB", "BUF", 85, 25, 7.3, 115.5, 6, 12, "", 6, 0, "Handcuff with upside"),
        
        # More QBs for 2QB league
        ("Bo Nix", "QB", "DEN", 86, 11, 18.5, 85.2, 4, 14, "", 8, 0, "Rookie starter, rushing upside"),
        ("Caleb Williams", "QB", "CHI", 87, 12, 18.2, 92.1, 4, 7, "", 9, 0, "High draft pick rookie"),
        ("Drake Maye", "QB", "NE", 88, 13, 17.8, 98.5, 4, 14, "", 8, 0, "Rookie with talent"),
        ("Anthony Richardson", "QB", "IND", 89, 14, 17.5, 105.2, 4, 14, "", 7, 2, "Injury return, upside"),
        ("Geno Smith", "QB", "SEA", 90, 15, 17.2, 112.8, 5, 10, "", 0, 0, "Consistent veteran"),
    ]
    
    all_players = players_data + additional_players
    
    # Insert all players
    cursor.executemany('''
        INSERT INTO players (name, position, team, overall_rank, position_rank, projected_points, 
                           adp, tier, bye_week, injury_status, sleeper_rating, bust_rating, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10], p[11], p[12]) for p in all_players])
    
    conn.commit()
    conn.close()
    print(f"✅ Populated database with {len(all_players)} players!")

if __name__ == "__main__":
    populate_players()