from agents.decorators import tool

@tool
def calculate_percentage(
    value: float,
    percentage: float
) -> float:
    """
    Calculate a percentage of a numeric value.
    """

    return value * percentage / 100