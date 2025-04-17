
import streamlit as st
import requests
import datetime
from core.models import GrossNetInput, GrossNetResult
from core.calculator import calculate_gross_to_net
from core.constants import REGIONAL_MINIMUM_WAGES


current_date_str = "Thursday, April 17, 2025"


st.set_page_config(
    page_title="VN Gross<=>Net Calculator",
    page_icon="🇻🇳",
    layout="wide",
    initial_sidebar_state="collapsed"
    )


st.title("🇻🇳 Vietnam Gross↔️Net Income Calculator (April 2025)")
st.caption(f"Calculates Net income based on Gross salary, dependents, and region. Based on regulations for: {current_date_str}")


col1, col2 = st.columns(2)

with col1:
    gross_income = st.number_input(
        "💰 Gross Monthly Income (Thu Nhập - VND)",
        min_value=0.0,
        step=100000.0,
        value=30000000.0,
        format="%.0f",
        help="Enter your total gross salary before any deductions."
    )
    num_dependents = st.number_input(
        "👨‍👩‍👧‍👦 Number of Registered Dependents (Số người phụ thuộc)",
        min_value=0,
        step=1,
        value=1,
        help="Enter the number of dependents officially registered for tax relief."
    )

with col2:
    region_options = list(REGIONAL_MINIMUM_WAGES.keys())
    region = st.selectbox(
        "📍 Region (Vùng)",
        options=region_options,
        format_func=lambda r: f"Region {r} (Min Wage: {REGIONAL_MINIMUM_WAGES[r]:,} VND)",
        index=0,
        help="Select the region where you work, affecting Unemployment Insurance cap and minimum insurance base."
    )

    st.radio(
        " Mức lương đóng bảo hiểm (Insurance Contribution Base)",
        ("Trên Lương chính thức (Based on Official Salary)", "Khác (Other) - Not Implemented"),
        index=0,
        help="Currently calculates based on Official Salary (Gross). 'Other' option is not yet implemented."
    )



if st.button("Calculate Net Income / Tính Lương Net", type="primary", use_container_width=True):

    input_valid = True
    if gross_income <= 0:
        st.error("Please enter a valid Gross Monthly Income greater than zero.", icon="⚠️")
        input_valid = False


    if input_valid:

        input_data = GrossNetInput(
            gross_income=gross_income,
            num_dependents=num_dependents,
            region=region

        )


        try:
            with st.spinner("Calculating..."):
                result = calculate_gross_to_net(input_data)

            st.success("Calculation Successful!", icon="✅")


            st.subheader("📊 Calculation Results / Kết quả tính toán")
            res_col1, res_col2 = st.columns(2)


            def format_vnd(value):
                return f"{value:,.0f} VND"

            with res_col1:
                st.metric(label="💵 Net Income (Lương Net)", value=format_vnd(result.net_income))
                st.metric(label="💸 Personal Income Tax (Thuế TNCN)", value=format_vnd(result.personal_income_tax))
                st.metric(label="🛡️ Total Employee Insurance (Tổng BH người LĐ)", value=format_vnd(result.total_insurance_contribution))

            with res_col2:
                st.metric(label="💰 Gross Income (Lương Gộp)", value=format_vnd(result.gross_income))
                st.metric(label="📉 Taxable Income (Thu nhập tính thuế)", value=format_vnd(result.taxable_income))
                st.metric(label="📈 Pre-Tax Income (Thu nhập trước thuế)", value=format_vnd(result.pre_tax_income))


            with st.expander("📋 View Insurance Contribution Breakdown / Chi tiết Bảo hiểm"):
                ins_data = {
                    "Social Insurance (BHXH)": format_vnd(result.insurance_breakdown.social_insurance),
                    "Health Insurance (BHYT)": format_vnd(result.insurance_breakdown.health_insurance),
                    "Unemployment Insurance (BHTN)": format_vnd(result.insurance_breakdown.unemployment_insurance),
                    "**Total**": f"**{format_vnd(result.insurance_breakdown.total)}**"
                 }

                st.table(ins_data)


        except ValueError as e:
            st.error(f"Input Error: {e}", icon="⚠️")
        except Exception as e:
            st.error(f"An unexpected error occurred during calculation: {e}", icon="❌")
            print(f"Calculation Error in Streamlit: {e}")




st.markdown("---")
st.caption(f"""
**Disclaimer:** This calculator uses rates and allowances presumed current for {current_date_str} (Hanoi, Vietnam) based on available public data
(e.g., Decree 74/2024/ND-CP, Resolution 954/2020/UBTVQH14, standard insurance rates). Base salary (`Lương cơ sở`) for the BHXH/BHYT cap uses 2,340,000 VND
based on UI hints/potential reforms. Always consult official sources or a professional for financial decisions.
""")