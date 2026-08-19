"""FIFA 2026 3rd place matchup rules - simplified for our simulation."""

def get_third_place_assignments(third_place_teams):
    """
    Given the 8 best 3rd place teams (sorted best to worst),
    return their match assignments.
    
    Match 74: 1E vs 3rd (from A/B/C/D/F)
    Match 77: 1I vs 3rd (from C/D/F/G/H)
    Match 79: 1A vs 3rd (from C/E/F/H/I)
    Match 80: 1L vs 3rd (from E/H/I/J/K)
    Match 81: 1D vs 3rd (from B/E/F/I/J)
    Match 82: 1G vs 3rd (from A/E/H/I/J)
    Match 85: 1B vs 3rd (from E/F/G/I/J)
    Match 87: 1K vs 3rd (from D/E/I/J/L)
    """
    # The 8 match slots in order
    slots = [
        ('M74', 'A/B/C/D/F'),
        ('M77', 'C/D/F/G/H'),
        ('M79', 'C/E/F/H/I'),
        ('M80', 'E/H/I/J/K'),
        ('M81', 'B/E/F/I/J'),
        ('M82', 'A/E/H/I/J'),
        ('M85', 'E/F/G/I/J'),
        ('M87', 'D/E/I/J/L'),
    ]
    
    assignments = []
    used = []
    
    for match_id, allowed_groups in slots:
        for group in allowed_groups.split('/'):
            # Find best 3rd place team from this group not yet used
            for tp in third_place_teams:
                if tp['group'] == group and tp['team'] not in used:
                    assignments.append((match_id, tp['team']))
                    used.append(tp['team'])
                    break
            else:
                continue
            break
    
    return assignments
