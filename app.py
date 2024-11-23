import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from cashflow_calc import BCDebtSimulation

def main():
    st.title("BC Debt Simulation App")

    st.sidebar.header("Simulation Parameters")

    # User inputs
    initial_debt = st.sidebar.number_input("Initial Debt ($)", min_value=0.0, value=900000.0, step=10000.0)
    savings = st.sidebar.number_input("Total Savings ($)", min_value=0.0, value=500000.0, step=10000.0)

    # New slider for TFSA allocation percentage
    tfsa_allocation_percent = st.sidebar.slider("TFSA Allocation (%)", min_value=0, max_value=100, value=100, step=1)
    
    # Calculate TFSA amount based on allocation percentage
    tfsa_amount = (tfsa_allocation_percent / 100.0) * savings

    interest_rate = st.sidebar.number_input("Interest Rate on Debt (%)", min_value=0.0, max_value=100.0, value=5.5, step=0.1) / 100.0
    min_return = st.sidebar.number_input("Minimum Annual Investment Return (%)", min_value=-100.0, max_value=100.0, value=10.0, step=0.1) / 100.0
    max_return = st.sidebar.number_input("Maximum Annual Investment Return (%)", min_value=-100.0, max_value=100.0, value=30.0, step=0.1) / 100.0
    monthly_income_needed = st.sidebar.number_input("Monthly Income Needed ($)", min_value=0.0, value=3000.0, step=100.0)
    num_simulations = st.sidebar.number_input("Number of Simulations", min_value=1, max_value=100000, value=1000, step=100)
    max_years = st.sidebar.number_input("Maximum Years", min_value=1, max_value=100, value=30, step=1)
    inflation_rate = st.sidebar.number_input("Inflation Rate (%)", min_value=0.0, max_value=100.0, value=2.0, step=0.1) / 100.0
    dividend_yield = st.sidebar.number_input("Dividend Yield (%)", min_value=0.0, max_value=100.0, value=2.0, step=0.1) / 100.0

    # Add debt type selector and amortization period
    debt_type = st.sidebar.selectbox(
        "Debt Type",
        ["Line of Credit", "Mortgage"]
    )
    
    amortization_years = 25  # Default for mortgage
    if debt_type == "Mortgage":
        amortization_years = st.sidebar.number_input(
            "Amortization Period (years)", 
            min_value=1, 
            max_value=30, 
            value=25
        )

    # Add annual TFSA contribution input
    annual_tfsa_contribution = st.sidebar.number_input("Annual TFSA Contribution ($)", min_value=0.0, value=6500.0, step=500.0)

    run_sim = st.sidebar.button("Run Simulation")

    if run_sim:
        st.write("Running simulations...")
        simulator = BCDebtSimulation()
        params = {
            'initial_debt': initial_debt,
            'savings': savings,
            'tfsa_amount': tfsa_amount,
            'interest_rate': interest_rate,
            'min_return': min_return,
            'max_return': max_return,
            'monthly_income_needed': monthly_income_needed,
            'num_simulations': int(num_simulations),
            'max_years': int(max_years),
            'inflation_rate': inflation_rate,
            'dividend_yield': dividend_yield,
            'debt_type': debt_type,
            'amortization_years': amortization_years,
            'annual_tfsa_contribution': annual_tfsa_contribution,
        }

        # Run simulation
        simulations = simulator.run_simulation(**params)

        # Analyze results
        successful_sims = [sim for sim in simulations if sim['final_debt'] <= 0]
        failed_sims = len(simulations) - len(successful_sims)
        success_rate = len(successful_sims) / len(simulations) * 100

        st.subheader("Simulation Results")
        st.write(f"Success Rate: {success_rate:.2f}%")

        if successful_sims:
            years_to_repay = [sim['years'] for sim in successful_sims]
            avg_years = np.mean(years_to_repay)
            median_years = np.median(years_to_repay)
            avg_final_wealth = np.mean([sim['tfsa_savings'] + sim['taxable_savings'] for sim in successful_sims])
            avg_tax_paid = np.mean([sim['total_tax_paid'] for sim in successful_sims])

            st.write(f"Average Years to Repay Debt: {avg_years:.2f}")
            st.write(f"Median Years to Repay Debt: {median_years:.2f}")
            st.write(f"Average Final Wealth: ${avg_final_wealth:,.2f}")
            st.write(f"Average Total Tax Paid: ${avg_tax_paid:,.2f}")

            # Detailed breakdown for the first successful simulation
            st.subheader("Detailed Annual Breakdown for First Successful Simulation")
            df = pd.DataFrame(successful_sims[0]['annual_data'])
            st.dataframe(df)

            # Plotting Debt Over Time
            st.subheader("Debt Over Time")
            fig, ax = plt.subplots()
            ax.plot(df['Year'], df['Debt'])
            ax.set_xlabel('Year')
            ax.set_ylabel('Debt')
            ax.set_title('Debt Reduction Over Time')
            st.pyplot(fig)

            # Plotting Savings Over Time
            st.subheader("Savings Over Time")
            fig2, ax2 = plt.subplots()
            ax2.plot(df['Year'], df['TFSA Savings'], label='TFSA Savings')
            ax2.plot(df['Year'], df['Taxable Savings'], label='Taxable Savings')
            ax2.set_xlabel('Year')
            ax2.set_ylabel('Savings')
            ax2.set_title('Savings Growth Over Time')
            ax2.legend()
            st.pyplot(fig2)

        else:
            st.write("No successful simulations.")

if __name__ == "__main__":
    main()