#!/usr/bin/env python3
"""
Extract data from Excel cheat sheet and populate database
"""

import pandas as pd
import sqlite3

def extract_and_populate():
    try:
        # Read the Excel file
        print("📊 Reading Excel cheat sheet...")
        df = pd.read_excel('Cheat Sheet (Full) 25-26.xlsx')
        
        # Display basic info about the sheet
        print(f"📋 Found {len(df)} rows and {len(df.columns)} columns")
        print("🔍 Column names:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")
        
        # Display first few rows to understand structure
        print("\n📝 First 10 rows:")
        print(df.head(10).to_string())
        
        # Show data types
        print("\n📊 Data types:")
        print(df.dtypes)
        
        # Connect to database
        conn = sqlite3.connect('fantasy_draft_2025.db')
        cursor = conn.cursor()
        
        # Clear existing players
        cursor.execute('DELETE FROM players')
        
        # Map Excel columns to database fields (will need to adjust based on actual column names)
        # Let's first see what columns we have and then map them appropriately
        
        conn.commit()
        conn.close()
        
        print("✅ Excel data extracted successfully!")
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        print("Make sure you have pandas and openpyxl installed:")
        print("pip install pandas openpyxl")

if __name__ == "__main__":
    extract_and_populate()