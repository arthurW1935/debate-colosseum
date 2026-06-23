from typing import List, Dict, Any
from langchain_core.tools import tool
import scipy.optimize

def calculate_roi(principal: float, net_profit: float) -> float:
    """Calculate Return on Investment (ROI)"""
    if principal == 0:
        return 0.0
    return (net_profit / principal) * 100.0

def calculate_npv(rate: float, cash_flows: List[float]) -> float:
    """Calculate Net Present Value (NPV). 
    Assume cash_flows[0] is at time 0.
    rate is expected as a decimal, e.g., 0.1 for 10%.
    """
    npv = sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows))
    return npv

def calculate_irr(cash_flows: List[float]) -> float:
    """Calculate Internal Rate of Return (IRR).
    Finds the rate at which NPV equals 0. Returns value as a decimal.
    """
    # Using scipy.optimize.newton to find the root
    try:
        res = scipy.optimize.newton(lambda r: calculate_npv(r, cash_flows), 0.1)
        return float(res)
    except (RuntimeError, TypeError):
        return 0.0 # Return 0 if it fails to converge

def calculate_breakeven(fixed_costs: float, price_per_unit: float, variable_cost_per_unit: float) -> float:
    """Calculate Breakeven point in units."""
    contribution_margin = price_per_unit - variable_cost_per_unit
    if contribution_margin <= 0:
        return float('inf')
    return fixed_costs / contribution_margin

@tool
def financial_calculator(principal: float, rate: float, periods: int, cash_flows: List[float], net_profit: float = 0.0, fixed_costs: float = 0.0, price_per_unit: float = 0.0, variable_cost_per_unit: float = 0.0) -> Dict[str, Any]:
    """Calculate key financial metrics: ROI, NPV, IRR, and Breakeven point.
    
    Args:
        principal: The initial investment amount.
        rate: Discount rate as a decimal (e.g., 0.1 for 10%).
        periods: Number of periods.
        cash_flows: List of cash flows, starting with the initial investment as a negative number at index 0.
        net_profit: The net profit for ROI calculation.
        fixed_costs: Total fixed costs for breakeven calculation.
        price_per_unit: Price per unit for breakeven calculation.
        variable_cost_per_unit: Variable cost per unit for breakeven calculation.
        
    Returns:
        A dictionary containing the calculated financial metrics.
    """
    metrics = {}
    if principal != 0 and net_profit != 0:
        metrics["roi_percentage"] = calculate_roi(principal, net_profit)
        
    if cash_flows:
        metrics["npv"] = calculate_npv(rate, cash_flows)
        metrics["irr_decimal"] = calculate_irr(cash_flows)
        
    if price_per_unit > variable_cost_per_unit and fixed_costs > 0:
        metrics["breakeven_units"] = calculate_breakeven(fixed_costs, price_per_unit, variable_cost_per_unit)
        
    return metrics
