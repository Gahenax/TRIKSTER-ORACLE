import math

def calculate_win_probability(
    home_rating: float,
    away_rating: float,
    home_advantage: float = 100
) -> tuple[float, float, float]:
    """
    Calculate win probabilities using ELO formula.
    
    Returns:
        (prob_home, prob_draw, prob_away) - All probabilities sum to 1.0
    """
    
    # Constants for Elo and Draw model
    SCALE = 400.0
    DRAW_BASE_PROB = 0.25 # Probability of draw when ratings are equal
    
    # Calculate expected rating difference
    diff = home_rating + home_advantage - away_rating
    
    # Calculate expected score (standard Elo)
    # expected_home = 1 / (1 + 10^(diff/400)) <-- This is for AWAY win if diff is (Away - Home)
    # Standard Elo: E_A = 1 / (1 + 10^((R_B - R_A)/400))
    # Here diff is (Home - Away).
    # expected_home = 1 / (1 + 10^(-diff/400))
    
    # Using Logistic Distribution logic to support Draw
    # We define a threshold T such that P(Draw|Equal) = 0.25
    # The logistic scale parameter 's' corresponds to 400 / ln(10)
    # s = 400 / math.log(10)
    s = SCALE / math.log(10)
    
    # Threshold derivation:
    # P(draw) = P(-T < X < T) for X ~ Logistic(0, s)
    # = CDF(T) - CDF(-T)
    # = (1 / (1 + exp(-T/s))) - (1 / (1 + exp(T/s)))
    # ...
    # T = -s * ln((1-P)/(1+P))
    
    threshold = -s * math.log((1 - DRAW_BASE_PROB) / (1 + DRAW_BASE_PROB))
    
    def logistic_cdf(x, loc, scale):
        return 1 / (1 + math.exp(-(x - loc) / scale))
        
    # P(Away Win) = P(Performance Diff < -threshold)
    prob_away = logistic_cdf(-threshold, loc=diff, scale=s)
    
    # P(Home Win) = P(Performance Diff > threshold)
    prob_home = 1 - logistic_cdf(threshold, loc=diff, scale=s)
    
    # P(Draw)
    prob_draw = 1.0 - prob_home - prob_away
    
    # Ensure non-negative and normalize
    prob_draw = max(0.0, prob_draw)
    total = prob_home + prob_draw + prob_away
    
    return (prob_home / total, prob_draw / total, prob_away / total)
