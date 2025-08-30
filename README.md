# NFL Fantasy Draft Application 2025-2026

A comprehensive web-based fantasy football draft application with real-time ESPN API integration, mock drafts, and advanced analytics.

## 📊 Features
- **Real-time ESPN League Integration** - Sync with your actual ESPN league
- **Mock Draft Simulator** - Practice with AI-driven opponents
- **Advanced Player Analytics** - Comprehensive scoring and ranking system
- **Live Draft Board** - Real-time draft tracking with team analysis
- **Export Functionality** - Save draft results and analysis
- **Responsive Design** - Works on desktop and mobile

## 🗄️ Database
Built from "Cheat Sheet (Full) 25-26.xlsx" with 357 players including:
- Player rankings and ADP
- Projected points
- Team assignments
- Position depth analysis
- Advanced metrics and scoring

## 🚀 How to Use

### Start the Application
```bash
python final_draft_app.py
```
Then open http://localhost:5000 in your browser

### Main Features:
1. **ESPN League Integration** - Connect to your live ESPN league
2. **Mock Draft Mode** - Practice drafting against AI opponents
3. **Player Database** - Browse and analyze all available players
4. **Draft Analytics** - Real-time team analysis and recommendations
5. **Export Tools** - Save your draft results and team analysis

### Draft Interface:
- View available players sorted by value and position
- See real-time team composition and needs analysis
- Get intelligent draft recommendations
- Track all teams' rosters and remaining picks
- Export final results with detailed analytics

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

## 📁 Key Files
- `final_draft_app.py` - Main Flask application with full functionality
- `fantasy_draft_2025.db` - SQLite database with all player data
- `templates/final_index.html` - Modern responsive web interface
- `parse_cheat_sheet.py` - Data extraction from Excel
- `create_draft_db.py` - Database setup and initialization
- `quick_draft.py` - Command-line reference tool

## 🎯 Draft Tips
1. **Use Mock Draft Mode** to practice before your real draft
2. **Connect ESPN League** for live draft tracking
3. **Monitor team analysis** - system shows positional needs
4. **Follow recommendations** - based on value and roster composition
5. **Export results** after draft for league analysis

Good luck with your draft! 🏆