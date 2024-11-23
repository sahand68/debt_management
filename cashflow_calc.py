import numpy as np
import pandas as pd
from typing import Dict, List
import matplotlib.pyplot as plt

class BCDebtSimulation:
    def __init__(self):
        # Federal brackets for 2024
        self.federal_brackets = [
            (0, 55867, 0.15),
            (55867, 111733, 0.205),
            (111733, 173205, 0.26),
            (173205, 246752, 0.29),
            (246752, float('inf'), 0.33)
        ]
        
        # BC Provincial brackets for 2024
        self.bc_brackets = [
            (0, 45654, 0.0506),
            (45654, 91308, 0.077),
            (91308, 104835, 0.105),
            (104835, 127299, 0.1229),
            (127299, 172602, 0.147),
            (172602, 240716, 0.168),
            (240716, float('inf'), 0.205)
        ]
        
        # BC dividend tax credit rates
        self.bc_dividend_credit_rate = 0.12
        self.federal_dividend_credit_rate = 0.150198
        
    def calculate_tax(self, income: float, income_type: str = 'regular') -> float:
        """Calculate total tax based on income type for BC"""
        if income <= 0:
            return 0.0
            
        if income_type == 'capital_gains':
            taxable_income = income * 0.5  # 50% inclusion rate
        elif income_type == 'eligible_dividends':
            taxable_income = income * 1.38  # 38% gross-up
        else:
            taxable_income = income
            
        federal_tax = self._calculate_bracket_tax(taxable_income, self.federal_brackets)
        provincial_tax = self._calculate_bracket_tax(taxable_income, self.bc_brackets)
        
        total_tax = federal_tax + provincial_tax
        
        if income_type == 'eligible_dividends':
            federal_credit = taxable_income * self.federal_dividend_credit_rate
            provincial_credit = taxable_income * self.bc_dividend_credit_rate
            total_tax -= (federal_credit + provincial_credit)
            
        return max(0, total_tax)
        
    def _calculate_bracket_tax(self, income: float, brackets: List) -> float:
        """Calculate bracket-specific tax"""
        total_tax = 0
        remaining_income = income
        
        for lower, upper, rate in brackets:
            if remaining_income <= 0:
                break
            taxable_in_bracket = min(remaining_income, upper - lower)
            tax_in_bracket = taxable_in_bracket * rate
            total_tax += tax_in_bracket
            remaining_income -= taxable_in_bracket
            
        return total_tax

    def calculate_gross_income(self, net_income_needed, income_type='regular'):
        """Calculate the gross income required to achieve the net income after taxes."""
        gross_income = net_income_needed / 0.8  # Initial guess
        for _ in range(10):  # Iterative approach
            tax = self.calculate_tax(gross_income, income_type)
            net_income = gross_income - tax
            difference = net_income_needed - net_income
            if abs(difference) < 1e-2:
                break
            gross_income += difference
        return gross_income

    def calculate_mortgage_payment(self, principal, annual_rate, years):
        """Calculate monthly mortgage payment"""
        monthly_rate = annual_rate / 12
        num_payments = years * 12
        if monthly_rate == 0:
            return principal / num_payments
        return principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)

    def run_simulation(self, 
                      initial_debt: float,
                      savings: float,
                      tfsa_amount: float,
                      interest_rate: float,
                      min_return: float,
                      max_return: float,
                      monthly_income_needed: float,
                      num_simulations: int = 1000,
                      max_years: int = 30,
                      inflation_rate: float = 0.02,
                      dividend_yield: float = 0.02,
                      debt_type: str = "Line of Credit",
                      amortization_years: int = 25,
                      annual_tfsa_contribution: float = 6500.0) -> Dict:
        
        all_simulations = []

        for sim in range(num_simulations):
            # Initialize simulation variables
            current_debt = initial_debt
            tfsa_savings = min(tfsa_amount, savings)  # Prioritize TFSA
            taxable_savings = max(0, savings - tfsa_amount)
            taxable_cost_basis = taxable_savings  # Initial cost basis equals initial investment
            years = 0
            total_tax_paid = 0
            yearly_income_needed = monthly_income_needed * 12
            annual_data = []

            while current_debt > 0 and years < max_years:
                # Adjust for inflation
                if years > 0:
                    yearly_income_needed *= (1 + inflation_rate)
                
                # Calculate gross income needed to net the after-tax income
                gross_income_needed = self.calculate_gross_income(yearly_income_needed)
                personal_tax = gross_income_needed - yearly_income_needed
                
                # Generate random return for the year
                annual_return = np.random.uniform(min_return, max_return)
                
                # Calculate TFSA returns (tax-free)
                tfsa_return = tfsa_savings * annual_return
                tfsa_savings += tfsa_return  # Reinvest returns
                tfsa_savings += annual_tfsa_contribution  # Add annual contribution
                
                # Calculate taxable account returns
                taxable_return = taxable_savings * annual_return
                taxable_savings += taxable_return  # Reinvest returns
                
                # Calculate dividends and capital gains
                dividend_income = taxable_savings * dividend_yield
                capital_gains = taxable_return - dividend_income
                
                # Adjust cost basis for capital gains
                taxable_cost_basis += taxable_savings - taxable_cost_basis  # Reinvested amounts
                
                # Taxes on dividends and capital gains
                dividend_tax = self.calculate_tax(dividend_income, 'eligible_dividends')
                capital_gains_tax = self.calculate_tax(capital_gains, 'capital_gains')
                investment_tax = dividend_tax + capital_gains_tax
                
                # Total taxes paid this year
                total_tax = personal_tax + investment_tax
                total_tax_paid += total_tax
                
                # Calculate debt payment based on type
                if debt_type == "Mortgage":
                    # Calculate fixed monthly payment
                    monthly_payment = self.calculate_mortgage_payment(
                        initial_debt, interest_rate, amortization_years)
                    annual_debt_payment = monthly_payment * 12
                    # Split payment into principal and interest
                    annual_interest = current_debt * interest_rate
                    principal_payment = min(current_debt, annual_debt_payment - annual_interest)
                else:  # Line of Credit
                    annual_interest = current_debt * interest_rate
                    principal_payment = 0  # Only interest is required

                # Total expenses (personal income needs and debt payments)
                total_expenses = gross_income_needed + annual_interest + principal_payment
                
                # Total available funds from investments
                total_available = tfsa_return + taxable_return
                
                # Remaining proceeds after expenses
                remaining_proceeds = total_available - total_expenses - investment_tax
                
                # Handle surplus or shortfall
                if remaining_proceeds >= 0:
                    # Pay down additional principal with surplus
                    if debt_type == "Line of Credit":
                        debt_payment = min(current_debt, remaining_proceeds)
                        current_debt -= debt_payment
                        remaining_proceeds -= debt_payment
                    else:  # Mortgage - principal already paid in fixed payment
                        current_debt -= principal_payment
                else:
                    if debt_type == "Mortgage":
                        current_debt -= principal_payment  # Still reduce by scheduled principal

                # Record annual data
                annual_data.append({
                    'Year': years + 1,
                    'Debt': current_debt,
                    'TFSA Savings': tfsa_savings,
                    'Taxable Savings': taxable_savings,
                    'Total Tax Paid': total_tax_paid,
                    'Annual Return': annual_return,
                    'Gross Income Needed': gross_income_needed,
                    'Personal Tax': personal_tax,
                    'Investment Tax': investment_tax,
                    'Total Expenses': total_expenses
                })
                
                years += 1

                # Break if investments are depleted before debt is paid
                if tfsa_savings <= 0 and taxable_savings <= 0:
                    break  # Scenario fails

            # Append simulation results
            all_simulations.append({
                'years': years,
                'final_debt': current_debt,
                'tfsa_savings': tfsa_savings,
                'taxable_savings': taxable_savings,
                'total_tax_paid': total_tax_paid,
                'annual_data': annual_data
            })

        return all_simulations

def analyze_simulations(simulations: List[Dict], scenario_name: str) -> None:
    successful_sims = [sim for sim in simulations if sim['final_debt'] <= 0]
    failed_sims = len(simulations) - len(successful_sims)
    success_rate = len(successful_sims) / len(simulations) * 100

    if successful_sims:
        years_to_repay = [sim['years'] for sim in successful_sims]
        avg_years = np.mean(years_to_repay)
        median_years = np.median(years_to_repay)
        avg_final_wealth = np.mean([sim['tfsa_savings'] + sim['taxable_savings'] for sim in successful_sims])
        avg_tax_paid = np.mean([sim['total_tax_paid'] for sim in successful_sims])

        print(f"\n{scenario_name} Results:")
        print(f"Success Rate: {success_rate:.2f}%")
        print(f"Average Years to Repay: {avg_years:.2f}")
        print(f"Median Years to Repay: {median_years:.2f}")
        print(f"Average Final Wealth: ${avg_final_wealth:,.2f}")
        print(f"Average Total Tax Paid: ${avg_tax_paid:,.2f}")
    else:
        print(f"\n{scenario_name} Results:")
        print("No successful simulations.")

    # Detailed breakdown for the first successful simulation
    if successful_sims:
        print("\nDetailed Annual Breakdown for First Successful Simulation:")
        df = pd.DataFrame(successful_sims[0]['annual_data'])
        print(df.to_string(index=False))

# Run simulations
simulator = BCDebtSimulation()

# Scenario parameters
params = {
    'initial_debt': 900000,
    'savings': 500000,
    'interest_rate': 0.055,
    'min_return': 0.1,
    'max_return': 0.3,
    'monthly_income_needed': 3000,
    'num_simulations': 10000
}

# Scenario 1: All money in TFSA
scenario1_results = simulator.run_simulation(tfsa_amount=500000, **params)

# Scenario 2: Only $300,000 in TFSA
scenario2_results = simulator.run_simulation(tfsa_amount=300000, **params)

# Analyze results
analyze_simulations(scenario1_results, "Scenario 1 (Full TFSA)")
analyze_simulations(scenario2_results, "Scenario 2 ($300,000 in TFSA)")
