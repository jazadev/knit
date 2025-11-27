def get_demo_profiles():
    return {
        'mexicano': {
            'oid': 'demo_jorge_mx',
            'name': 'Jorge Ramírez',
            'preferred_username': 'jorge@demo.com',
            'platformLang': 'es',
            'dbProfile': {
                'name': 'Jorge Ramírez',
                'email': 'jorge@demo.com',
                'country': 'MX',
                'state': 'MX-CMX',
                'platformLang': 'es',
                'age': 30,
                'gender': 'male'
            },
            'dbPreferences': { 'notifications': { 'email': True, 'sms': True } },
            'dbTopics': {
                'procedures': { 'enabled': True, 'subs': { 'licenses': True } },
                'services': { 'enabled': True, 'subs': { 'water': True } }
            }
        },
        'americano': {
            'oid': 'demo_ana_us',
            'name': 'Ana Smith',
            'preferred_username': 'ana@demo.com',
            'platformLang': 'en',
            'dbProfile': {
                'name': 'Ana Smith',
                'email': 'ana@demo.com',
                'country': 'MX',
                'state': 'MX-CMX',
                'platformLang': 'en',
                'age': 28,
                'gender': 'female'
            },
            'dbPreferences': { 'notifications': { 'email': True, 'sms': False } },
            'dbTopics': {
                'civic': { 'enabled': True, 'subs': {} },
                'community': { 'enabled': True, 'subs': {} }
            }
        },
        'frances': {
            'oid': 'demo_alice_fr',
            'name': 'Alice Dubois',
            'preferred_username': 'alice@demo.com',
            'platformLang': 'fr',
            'dbProfile': {
                'name': 'Alice Dubois',
                'email': 'alice@demo.com',
                'country': 'MX',
                'state': 'MX-CMX',
                'platformLang': 'fr',
                'age': 24,
                'gender': 'female'
            },
            'dbPreferences': { 'notifications': { 'email': False, 'sms': False } },
            'dbTopics': {
                'events': { 'enabled': True, 'subs': { 'cultural': True, 'arts': True } }
            }
        }
    }

def get_profile_by_key(key):
    profiles = get_demo_profiles()
    return profiles.get(key)