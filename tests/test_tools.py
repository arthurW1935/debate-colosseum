import pytest
from src.tools.financial_calc import (
    calculate_roi,
    calculate_npv,
    calculate_irr,
    calculate_breakeven,
    financial_calculator
)

def test_calculate_roi():
    assert calculate_roi(1000, 200) == 20.0
    assert calculate_roi(0, 200) == 0.0

def test_calculate_npv():
    cash_flows = [-1000, 500, 500, 500]
    rate = 0.1
    npv = calculate_npv(rate, cash_flows)
    assert round(npv, 2) == 243.43

def test_calculate_irr():
    cash_flows = [-1000, 500, 500, 500]
    irr = calculate_irr(cash_flows)
    assert round(irr, 4) == 0.2338

def test_calculate_breakeven():
    assert calculate_breakeven(1000, 50, 30) == 50.0
    assert calculate_breakeven(1000, 20, 30) == float('inf')

def test_financial_calculator_tool():
    res = financial_calculator.invoke({
        "principal": 1000,
        "rate": 0.1,
        "periods": 3,
        "cash_flows": [-1000, 500, 500, 500],
        "net_profit": 200,
        "fixed_costs": 1000,
        "price_per_unit": 50,
        "variable_cost_per_unit": 30
    })
    assert res["roi_percentage"] == 20.0
    assert round(res["npv"], 2) == 243.43
    assert round(res["irr_decimal"], 4) == 0.2338
    assert res["breakeven_units"] == 50.0
