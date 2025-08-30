# NFL Fantasy Draft Assistant 2025-2026

A comprehensive draft assistant for **The League** - your 8-team, 0.5 PPR fantasy football league.

## 📊 League Settings
- **Teams:** 8
- **Scoring:** 0.5 PPR  
- **Starting Lineup:** 2 QB, 3 RB, 3 WR, 1 TE, 3 FLEX, 1 K, 2 DEF, 9 Bench
- **Draft:** Friday, Aug 29, 2025 3:30pm EDT

## 🗄️ Database
Built from your "Cheat Sheet (Full) 25-26.xlsx" with 357 players including:
- Player rankings and ADP
- Projected points
- Team assignments
- Position depth

## 🚀 How to Use

### 1. Web Interface (Recommended for Draft Day)
```bash
python web_draft_assistant.py
```
Then open http://localhost:5000 in your browser

**Features:**
- Live draft board with available players
- Track your team and remaining position needs
- Smart recommendations based on your roster
- One-click drafting
- Auto-refresh during draft

### 2. Interactive Command Line
```bash
python draft_assistant.py
```

**Commands during draft:**
- `draft <player_name>` - Draft a player to your team
- `skip` - Skip a pick (another team drafted)  
- `search <name>` - Search for specific players
- `pos <QB|RB|WR|TE|K|DST>` - Show players by position
- `quit` - Exit

### 3. Quick Reference Tool
```bash
# Show overview and top players
python quick_draft.py

# Show top players by position
python quick_draft.py qb
python quick_draft.py rb 20  # Show top 20 RBs

# Search for specific players
python quick_draft.py search "Christian McCaffrey"

# Show sleeper picks
python quick_draft.py sleepers

# League settings and position scarcity
python quick_draft.py league
```

## 📈 Key Insights from Your Data

### Top Players by Position:
- **QB:** Ja'Marr Chase, Lamar Jackson, Josh Allen
- **RB:** Bijan Robinson, Saquon Barkley, Jahmyr Gibbs  
- **WR:** Justin Jefferson, CeeDee Lamb, Amon-Ra St. Brown
- **TE:** Brock Bowers, Trey McBride, George Kittle

### League-Specific Strategy:
- **2 QB League:** QBs more valuable - draft 2 early
- **2 DEF League:** Defense depth matters - don't wait too long
- **0.5 PPR:** Balance between rushing and receiving backs
- **3 FLEX spots:** Extra roster flexibility, depth crucial

### Position Scarcity:
- **QB:** 45 available (need 16 total) - Moderate scarcity
- **RB:** 100 available (need 48 total) - High competition  
- **WR:** 113 available (need 48 total) - Deepest position
- **TE:** 47 available (need 8 total) - Very top-heavy
- **DEF:** 30 available (need 16 total) - Limited quality options

## 📁 Files Created
- `fantasy_draft_2025.db` - SQLite database with all player data
- `web_draft_assistant.py` - Web interface for draft day
- `draft_assistant.py` - Interactive command-line assistant  
- `quick_draft.py` - Quick reference tool
- `parse_cheat_sheet.py` - Data extraction from Excel
- `create_draft_db.py` - Database setup

## 🎯 Draft Day Tips
1. **Start the web interface** before draft begins
2. **Focus on your positional needs** (highlighted in red)
3. **Use recommendations** - they factor in your roster gaps
4. **Don't forget 2 QBs and 2 DEFs** - unique to your league
5. **Target value picks** from the sleepers list

Good luck with your draft! 🏆