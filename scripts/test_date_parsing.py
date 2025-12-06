"""
Test script pour vérifier le parsing de dates naturelles
"""
from datetime import datetime, timedelta

def parse_natural_date(date_str: str) -> str:
    """Parse natural language dates to YYYY-MM-DD format"""
    import re
    
    date_str = date_str.lower().strip()
    today = datetime.now().date()
    
    print(f"📅 Aujourd'hui: {today} ({today.strftime('%A')})")
    print(f"🔍 Parsing: '{date_str}'")
    
    # Direct formats
    if date_str in ["aujourd'hui", "auj", "today"]:
        result = today.isoformat()
        print(f"✅ Résultat: {result}")
        return result
    elif date_str in ["demain", "tomorrow"]:
        result = (today + timedelta(days=1)).isoformat()
        print(f"✅ Résultat: {result}")
        return result
    elif date_str in ["après-demain", "apres-demain"]:
        result = (today + timedelta(days=2)).isoformat()
        print(f"✅ Résultat: {result}")
        return result
    
    # Days of week
    days_fr = {
        "lundi": 0, "mardi": 1, "mercredi": 2, "jeudi": 3,
        "vendredi": 4, "samedi": 5, "dimanche": 6
    }
    
    for day_name, day_num in days_fr.items():
        if day_name in date_str:
            # Find next occurrence of this day
            days_ahead = day_num - today.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            if "prochain" in date_str or "prochaine" in date_str:
                days_ahead += 7  # Next week
            result_date = today + timedelta(days=days_ahead)
            result = result_date.isoformat()
            print(f"✅ Résultat: {result} ({result_date.strftime('%A %d %B %Y')})")
            return result
    
    # Try to parse as YYYY-MM-DD
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        print(f"✅ Résultat: {date_str} (déjà au bon format)")
        return date_str
    except:
        pass
    
    # Default: return as-is
    print(f"⚠️  Format non reconnu, retour tel quel: {date_str}")
    return date_str


if __name__ == "__main__":
    test_cases = [
        "aujourd'hui",
        "demain",
        "lundi",
        "ce lundi",
        "lundi prochain",
        "vendredi",
        "2025-12-08"
    ]
    
    print("=" * 60)
    print("Test de parsing de dates naturelles")
    print("=" * 60 + "\n")
    
    for test in test_cases:
        print(f"\n{'='*60}")
        parse_natural_date(test)
