import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from cashflow_calc import BCDebtSimulation

def analyze_debt_simulations(simulations):
    successful_sims = [sim for sim in simulations if sim['final_debt'] <= 0]
    failed_sims = len(simulations) - len(successful_sims)
    success_rate = len(successful_sims) / len(simulations) * 100

    st.subheader("Debt Repayment Simulation Results")
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

def analyze_tfsa_simulations(simulations):
    st.subheader("TFSA Growth Simulation Results")

    final_balances = [sim['tfsa_balance'] for sim in simulations]
    avg_final_balance = np.mean(final_balances)
    median_final_balance = np.median(final_balances)

    st.write(f"Average Final TFSA Balance: ${avg_final_balance:,.2f}")
    st.write(f"Median Final TFSA Balance: ${median_final_balance:,.2f}")

    # Detailed breakdown for the first simulation
    st.subheader("Detailed Annual Breakdown for First Simulation")
    df = pd.DataFrame(simulations[0]['annual_data'])
    st.dataframe(df)

    # Plotting TFSA Balance Over Time
    st.subheader("TFSA Balance Over Time")
    fig, ax = plt.subplots()
    ax.plot(df['Year'], df['TFSA Balance'])
    ax.set_xlabel('Year')
    ax.set_ylabel('TFSA Balance')
    ax.set_title('TFSA Growth Over Time')
    st.pyplot(fig)

    # Histogram of Final Balances
    st.subheader("Distribution of Final TFSA Balances Across Simulations")
    fig2, ax2 = plt.subplots()
    ax2.hist(final_balances, bins=20, edgecolor='black')
    ax2.set_xlabel('Final TFSA Balance')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Histogram of Final TFSA Balances')
    st.pyplot(fig2)

    # Add Monte Carlo paths visualization
    st.subheader("Monte Carlo Simulation Paths")
    fig3, ax3 = plt.subplots(figsize=(10, 6))
    
    # Plot first 100 simulation paths
    max_paths = min(100, len(simulations))
    for sim in simulations[:max_paths]:
        df = pd.DataFrame(sim['annual_data'])
        ax3.plot(df['Year'], df['TFSA Balance'], alpha=0.1, color='blue')
    
    # Plot median path with higher opacity
    median_sim = simulations[len(simulations)//2]
    df_median = pd.DataFrame(median_sim['annual_data'])
    ax3.plot(df_median['Year'], df_median['TFSA Balance'], 
             color='red', linewidth=2, label='Median Path')
    
    ax3.set_xlabel('Year')
    ax3.set_ylabel('TFSA Balance ($)')
    ax3.set_title('Monte Carlo Simulation Paths')
    ax3.legend()
    st.pyplot(fig3)

    # Add percentile analysis
    st.subheader("Percentile Analysis of Final TFSA Balances")
    percentiles = [10, 25, 50, 75, 90]
    final_balance_percentiles = np.percentile(final_balances, percentiles)
    
    percentile_df = pd.DataFrame({
        'Percentile': [f"{p}th" for p in percentiles],
        'Final Balance': final_balance_percentiles
    })
    percentile_df['Final Balance'] = percentile_df['Final Balance'].map('${:,.2f}'.format)
    st.table(percentile_df)

def main():
    st.title("BC Debt and TFSA Simulation App")

    st.sidebar.header("Simulation Parameters")

    # Add mode selection
    simulation_mode = st.sidebar.selectbox(
        "Select Simulation Mode",
        ["Debt Repayment Simulation", "TFSA Growth Simulation"]
    )

    # Common inputs for both modes
    savings = st.sidebar.number_input("Total Savings ($)", min_value=0.0, value=500000.0, step=10000.0)

    tfsa_allocation_percent = st.sidebar.slider("TFSA Allocation (%)", min_value=0, max_value=100, value=100, step=1)
    tfsa_amount = (tfsa_allocation_percent / 100.0) * savings

    min_return = st.sidebar.number_input(
        "Minimum Annual Investment Return (%)",
        min_value=-100.0,
        max_value=100.0,
        value=5.0,
        step=0.1
    ) / 100.0
    max_return = st.sidebar.number_input(
        "Maximum Annual Investment Return (%)",
        min_value=-100.0,
        max_value=100.0,
        value=8.0,
        step=0.1
    ) / 100.0
    num_simulations = st.sidebar.number_input(
        "Number of Simulations",
        min_value=1,
        max_value=100000,
        value=1000,
        step=100
    )
    max_years = st.sidebar.number_input(
        "Maximum Years",
        min_value=1,
        max_value=100,
        value=30,
        step=1
    )
    inflation_rate = st.sidebar.number_input(
        "Inflation Rate (%)",
        min_value=0.0,
        max_value=100.0,
        value=2.0,
        step=0.1
    ) / 100.0
    dividend_yield = st.sidebar.number_input(
        "Dividend Yield (%)",
        min_value=0.0,
        max_value=100.0,
        value=2.0,
        step=0.1
    ) / 100.0

    if simulation_mode == "Debt Repayment Simulation":
        # Debt-specific inputs
        initial_debt = st.sidebar.number_input(
            "Initial Debt ($)",
            min_value=0.0,
            value=900000.0,
            step=10000.0
        )
        interest_rate = st.sidebar.number_input(
            "Interest Rate on Debt (%)",
            min_value=0.0,
            max_value=100.0,
            value=5.5,
            step=0.1
        ) / 100.0
        monthly_income_needed = st.sidebar.number_input(
            "Monthly Income Needed ($)",
            min_value=0.0,
            value=3000.0,
            step=100.0
        )

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

        # Include annual TFSA contribution input here if needed
        annual_tfsa_contribution = st.sidebar.number_input(
            "Annual TFSA Contribution ($)",
            min_value=0.0,
            value=6500.0,
            step=500.0
        )

    else:
        # TFSA-only inputs
        st.sidebar.markdown("**TFSA Growth Simulation Selected**")
        monthly_income_needed = 0.0  # No income needed in this mode
        initial_debt = 0.0
        interest_rate = 0.0
        debt_type = None
        amortization_years = None

        # Add annual TFSA contribution input here
        annual_tfsa_contribution = st.sidebar.number_input(
            "Annual TFSA Contribution ($)",
            min_value=0.0,
            value=6500.0,
            step=500.0
        )

    # Run simulation button
    run_sim = st.button("Run Simulation")

    if run_sim:
        st.write("Running simulations...")
        simulator = BCDebtSimulation()

        if simulation_mode == "Debt Repayment Simulation":
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

            # Run debt repayment simulation
            simulations = simulator.run_simulation(**params)

            # Analyze results
            analyze_debt_simulations(simulations)
        else:
            params = {
                'tfsa_savings': tfsa_amount,
                'min_return': min_return,
                'max_return': max_return,
                'num_simulations': int(num_simulations),
                'max_years': int(max_years),
                'inflation_rate': inflation_rate,
                'dividend_yield': dividend_yield,
                'annual_tfsa_contribution': annual_tfsa_contribution,
            }

            # Run TFSA growth simulation
            simulations = simulator.run_tfsa_simulation(**params)

            # Analyze TFSA simulation results
            analyze_tfsa_simulations(simulations)
    else:
        st.write("Please adjust the parameters and click 'Run Simulation' to start the calculation.")

if __name__ == "__main__":
    main()