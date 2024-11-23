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

    def calculate_gross_income(self, net_income_needed: float, income_type: str = 'regular') -> float:
        """Calculate gross income needed to achieve desired net income after taxes"""
        gross_income = net_income_needed / 0.7  # Initial guess
        for _ in range(10):  # Iterative approach
            tax = self.calculate_tax(gross_income, income_type)
            net_income = gross_income - tax
            difference = net_income_needed - net_income
            if abs(difference) < 1e-2:
                break
            gross_income += difference
        return gross_income

    def calculate_mortgage_payment(self, principal: float, annual_rate: float, years: int) -> float:
        """Calculate monthly mortgage payment"""
        if principal <= 0 or years <= 0:
            return 0.0
        
        monthly_rate = annual_rate / 12
        num_payments = years * 12
        
        if monthly_rate == 0:
            return principal / num_payments
            
        return principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)

    def calculate_mortgage_principal_payment(self, principal: float, payment: float, annual_rate: float) -> float:
        """Calculate the principal portion of a mortgage payment"""
        if principal <= 0 or payment <= 0:
            return 0.0
            
        monthly_rate = annual_rate / 12
        interest_payment = principal * monthly_rate
        return payment - interest_payment

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
                      annual_tfsa_contribution: float = 6500.0) -> List[Dict]:
        """
        Run debt repayment simulations with investment returns
        
        Parameters:
        initial_debt (float): Starting debt amount
        savings (float): Total initial savings
        tfsa_amount (float): Amount of savings allocated to TFSA
        interest_rate (float): Annual interest rate on debt
        min_return (float): Minimum annual investment return
        max_return (float): Maximum annual investment return
        monthly_income_needed (float): Required monthly after-tax income
        num_simulations (int): Number of simulation runs
        max_years (int): Maximum simulation years
        inflation_rate (float): Annual inflation rate
        dividend_yield (float): Annual dividend yield
        debt_type (str): "Line of Credit" or "Mortgage"
        amortization_years (int): Years for mortgage amortization
        annual_tfsa_contribution (float): Yearly TFSA contribution
        
        Returns:
        List[Dict]: Results of all simulations
        """
        
        all_simulations = []

        for sim in range(num_simulations):
            # Initialize simulation variables
            current_debt = initial_debt
            tfsa_savings = min(tfsa_amount, savings)
            taxable_savings = max(0, savings - tfsa_amount)
            taxable_cost_basis = taxable_savings
            years = 0
            total_tax_paid = 0
            yearly_income_needed = monthly_income_needed * 12
            annual_data = []

            # Calculate fixed monthly mortgage payment if applicable
            monthly_mortgage_payment = 0
            if debt_type == "Mortgage":
                monthly_mortgage_payment = self.calculate_mortgage_payment(
                    initial_debt, interest_rate, amortization_years)

            while current_debt > 0 and years < max_years:
                # Adjust for inflation
                if years > 0:
                    yearly_income_needed *= (1 + inflation_rate)
                
                # Calculate investment returns
                annual_return = np.random.uniform(min_return, max_return)
                
                # TFSA returns and contribution
                tfsa_return = tfsa_savings * annual_return
                tfsa_savings += tfsa_return
                tfsa_savings += annual_tfsa_contribution
                
                # Taxable account returns
                taxable_return = taxable_savings * annual_return
                taxable_savings += taxable_return
                
                # Calculate investment income
                dividend_income = taxable_savings * dividend_yield
                capital_gains = taxable_return - dividend_income
                
                # Update cost basis
                taxable_cost_basis += taxable_return  # Reinvested returns
                
                # Calculate taxes
                gross_income_needed = self.calculate_gross_income(yearly_income_needed)
                personal_tax = gross_income_needed - yearly_income_needed
                
                dividend_tax = self.calculate_tax(dividend_income, 'eligible_dividends')
                capital_gains_tax = self.calculate_tax(capital_gains, 'capital_gains')
                investment_tax = dividend_tax + capital_gains_tax
                total_tax = personal_tax + investment_tax
                total_tax_paid += total_tax

                # Handle debt payments based on type
                annual_interest = 0
                principal_payment = 0
                total_payment = 0
                
                if debt_type == "Mortgage":
                    # Process monthly mortgage payments
                    annual_mortgage_payment = monthly_mortgage_payment * 12
                    remaining_debt = current_debt
                    
                    for month in range(12):
                        if remaining_debt <= 0:
                            break
                            
                        month_interest = remaining_debt * (interest_rate / 12)
                        month_principal = min(remaining_debt, 
                                           self.calculate_mortgage_principal_payment(
                                               remaining_debt, monthly_mortgage_payment, interest_rate))
                        
                        annual_interest += month_interest
                        principal_payment += month_principal
                        remaining_debt -= month_principal
                    
                    current_debt = remaining_debt
                    total_payment = annual_mortgage_payment
                    
                else:  # Line of Credit
                    annual_interest = current_debt * interest_rate
                    total_payment = annual_interest  # Only required to pay interest
                
                # Calculate total expenses and available funds
                total_expenses = gross_income_needed + total_payment
                total_available = tfsa_return + taxable_return
                remaining_proceeds = total_available - total_expenses - investment_tax

                # Handle surplus for Line of Credit
                if remaining_proceeds > 0 and debt_type == "Line of Credit":
                    additional_payment = min(current_debt, remaining_proceeds)
                    current_debt -= additional_payment
                    principal_payment = additional_payment
                    remaining_proceeds -= additional_payment

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
                    'Total Expenses': total_expenses,
                    'Principal Payment': principal_payment,
                    'Interest Payment': annual_interest,
                    'Total Payment': total_payment
                })
                
                years += 1

                # Check if investments are depleted
                if tfsa_savings <= 0 and taxable_savings <= 0:
                    break

            # Store simulation results
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
    """Analyze and print simulation results"""
    successful_sims = [sim for sim in simulations if sim['final_debt'] <= 0]
    success_rate = len(successful_sims) / len(simulations) * 100

    print(f"\n{scenario_name} Results:")
    print(f"Success Rate: {success_rate:.2f}%")

    if successful_sims:
        years_to_repay = [sim['years'] for sim in successful_sims]
        avg_years = np.mean(years_to_repay)
        median_years = np.median(years_to_repay)
        avg_final_wealth = np.mean([sim['tfsa_savings'] + sim['taxable_savings'] 
                                  for sim in successful_sims])
        avg_tax_paid = np.mean([sim['total_tax_paid'] for sim in successful_sims])

        print(f"Average Years to Repay: {avg_years:.2f}")
        print(f"Median Years to Repay: {median_years:.2f}")
        print(f"Average Final Wealth: ${avg_final_wealth:,.2f}")
        print(f"Average Total Tax Paid: ${avg_tax_paid:,.2f}")

        # Show detailed breakdown of first successful simulation
        print("\nDetailed Annual Breakdown for First Successful Simulation:")
        df = pd.DataFrame(successful_sims[0]['annual_data'])
        print(df.to_string(index=False))
    else:
        print("No successful simulations.")

# Example usage
if __name__ == "__main__":
    simulator = BCDebtSimulation()
    
    # Example parameters
    params = {
        'initial_debt': 900000,
        'savings': 500000,
        'tfsa_amount': 300000,
        'interest_rate': 0.055,
        'min_return': 0.1,
        'max_return': 0.3,
        'monthly_income_needed': 0,
        'num_simulations': 1000,
        'debt_type': "Mortgage",
        'amortization_years': 5
    }
    
    # Run simulation
    results = simulator.run_simulation(**params)
    
    # Analyze results
    analyze_simulations(results, "Mortgage Simulation")