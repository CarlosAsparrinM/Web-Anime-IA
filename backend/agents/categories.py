from datetime import datetime

# Categories
CATEGORIES = ['novedades', 'curiosidades', 'analisis', 'resenas']

def get_category_for_today() -> str:
    # 0 = Monday, ..., 6 = Sunday in Python's weekday()
    day = datetime.now().weekday()
    
    if day == 0 or day == 3: # Mon, Thu
        return 'novedades'
    elif day == 1 or day == 5: # Tue, Sat
        return 'curiosidades'
    elif day == 2 or day == 6: # Wed, Sun
        return 'resenas'
    elif day == 4: # Fri
        return 'analisis'
    
    return 'novedades'
