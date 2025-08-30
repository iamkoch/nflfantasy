#!/usr/bin/env python3
"""
NFL Fantasy Draft Database Creator
Creates SQLite database optimized for specific league settings
"""

import sqlite3
import json
from datetime import datetime

def create_database():
    conn = sqlite3.connect('fantasy_draft_2025.db')
    cursor = conn.cursor()
    
    # League settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS league_settings (
            id INTEGER PRIMARY KEY,
            name TEXT,
            teams INTEGER,
            qb_slots INTEGER,
            rb_slots INTEGER,
            wr_slots INTEGER,
            te_slots INTEGER,
            flex_slots INTEGER,
            k_slots INTEGER,
            def_slots INTEGER,
            bench_slots INTEGER,
            ppr_scoring REAL,
            passing_yards_per_point INTEGER,
            passing_td_points INTEGER,
            rushing_yards_per_point INTEGER,
            rushing_td_points INTEGER,
            receiving_yards_per_point INTEGER,
            receiving_td_points INTEGER,
            td_bonus_40 INTEGER,
            td_bonus_50 INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Players table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position TEXT NOT NULL,
            team TEXT,
            overall_rank INTEGER,
            position_rank INTEGER,
            projected_points REAL,
            adp REAL,
            tier INTEGER,
            bye_week INTEGER,
            injury_status TEXT,
            sleeper_rating INTEGER DEFAULT 0,
            bust_rating INTEGER DEFAULT 0,
            notes TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Draft results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS draft_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            team_name TEXT,
            round INTEGER,
            pick INTEGER,
            overall_pick INTEGER,
            drafted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players(id)
        )
    ''')
    
    # User team roster tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS my_team (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            position TEXT,
            starter BOOLEAN DEFAULT FALSE,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players(id)
        )
    ''')
    
    # Target players wishlist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            priority INTEGER DEFAULT 1,
            target_round INTEGER,
            notes TEXT,
            FOREIGN KEY (player_id) REFERENCES players(id)
        )
    ''')
    
    # Insert league settings
    cursor.execute('''
        INSERT OR REPLACE INTO league_settings 
        (id, name, teams, qb_slots, rb_slots, wr_slots, te_slots, flex_slots, k_slots, def_slots, bench_slots,
         ppr_scoring, passing_yards_per_point, passing_td_points, rushing_yards_per_point, rushing_td_points,
         receiving_yards_per_point, receiving_td_points, td_bonus_40, td_bonus_50)
        VALUES (1, 'The League', 8, 2, 3, 3, 1, 3, 1, 2, 9,
                0.5, 25, 6, 10, 6, 10, 6, 1, 1)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Fantasy draft database created successfully!")

if __name__ == "__main__":
    create_database()