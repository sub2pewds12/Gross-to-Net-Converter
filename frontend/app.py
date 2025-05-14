# frontend/app.py

import streamlit as st
import pandas as pd
import io
import datetime
import logging
import os
from dotenv import load_dotenv
import textwrap
import requests # For making API calls

# Load environment variables from .env file (for local development)
load_dotenv()

# Local application imports
from core.models import GrossNetInput, SavedCalculationCreate # Import SavedCalculationCreate
from core.calculator import calculate_gross_to_net
from core.constants import REGIONAL_MINIMUM_WAGES
from core.exceptions import (
    CoreCalculationError, InvalidRegionError, InvalidInputDataError,
    NegativeGrossIncomeError, NegativeDependentsError, MissingConfigurationError
)

# --- Basic Logging Configuration ---
LOG_LEVEL_FROM_ENV = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL_FROM_ENV,
    format='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)
logger.info(f"Logging level set to: {LOG_LEVEL_FROM_ENV}")

# --- Application Environment ---
APP_ENVIRONMENT = os.getenv("API_ENV", "development")
logger.info(f"Streamlit application starting in '{APP_ENVIRONMENT}' environment.")

# --- API URL ---
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")
logger.info(f"API_BASE_URL for frontend calls: {API_BASE_URL}")


# --- Constants for UI ---
EXPECTED_COLUMNS_EXCEL_UPLOAD = {
    'gross': 'GrossIncome',
    'dependents': 'Dependents',
    'region': 'Region'
}
OUTPUT_COLUMNS_EXCEL_UPLOAD = [
    'NetIncome', 'PIT', 'TotalInsurance', 'TaxableIncome', 'PreTaxIncome',
    'BHXH', 'BHYT', 'BHTN', 'CalculationStatus', 'ErrorMessage'
]

# --- Helper Functions ---
def format_vnd(value):
    if pd.isna(value) or value is None:
        return ""
    try:
        return f"{float(value):,.0f} VND"
    except (ValueError, TypeError):
        logger.warning(f"Could not format value as VND: {value}", exc_info=False)
        return str(value)

@st.cache_data
def convert_df_to_csv(df_to_convert):
    logger.info("Converting DataFrame to CSV for download.")
    return df_to_convert.to_csv(index=False).encode('utf-8')

@st.cache_data
def convert_df_to_excel(df_to_convert):
    logger.info("Converting DataFrame to Excel for download.")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_to_convert.to_excel(writer, index=False, sheet_name='GrossNetResults')
    processed_data = output.getvalue()
    return processed_data

# --- API Call Functions for Saved Calculations ---
def fetch_saved_calculations_from_api():
    items = []
    st.session_state.saved_calculations_error = None # Clear previous errors
    try:
        url = f"{API_BASE_URL}/saved-calculations/"
        logger.info(f"Fetching saved calculations from: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        logger.info(f"Successfully fetched {data.get('total', 0)} saved calculations. Displaying {len(items)}.")
    except requests.exceptions.RequestException as e:
        st.session_state.saved_calculations_error = f"Error fetching saved calculations: {e}"
        logger.error(f"API call error fetching saved calculations: {e}", exc_info=True)
    except Exception as e:
        st.session_state.saved_calculations_error = f"An unexpected error occurred: {str(e)}"
        logger.exception("Unexpected error fetching saved calculations.")
    return items

def save_calculation_to_api(calculation_data: SavedCalculationCreate):
    """Saves a calculation result to the API."""
    try:
        url = f"{API_BASE_URL}/saved-calculations/"
        logger.info(f"Saving calculation to API: {url} with data: {calculation_data.model_dump_json(exclude_none=True)}")
        response = requests.post(url, json=calculation_data.model_dump(), timeout=10)
        response.raise_for_status()
        saved_data = response.json()
        st.success(f"Calculation '{saved_data.get('calculation_name', 'Untitled')}' (ID: {saved_data.get('id')}) saved successfully!", icon="✅")
        logger.info(f"Successfully saved calculation with ID: {saved_data.get('id')}")
        # Clear and refresh the saved calculations list in session state
        if 'saved_calculations_data' in st.session_state:
            del st.session_state.saved_calculations_data
        st.session_state.initial_fetch_done_saved_calcs = False # Trigger re-fetch on Saved Calcs tab
        return True
    except requests.exceptions.HTTPError as e:
        error_detail = "Could not save calculation."
        try:
            error_detail = e.response.json().get("detail", error_detail)
        except ValueError: # Not a JSON response
            pass
        st.error(f"API Error saving calculation: {error_detail} (Status: {e.response.status_code})")
        logger.error(f"API HTTPError saving calculation: {error_detail}", exc_info=True)
    except requests.exceptions.RequestException as e:
        st.error(f"Network error saving calculation: {e}")
        logger.error(f"API Network error saving calculation: {e}", exc_info=True)
    except Exception as e:
        st.error(f"An unexpected error occurred while saving: {str(e)}")
        logger.exception("Unexpected error saving calculation.")
    return False


# --- Main App ---
st.set_page_config(
    page_title="VN Gross<=>Net Calculator",
    page_icon="🇻🇳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state variables if they don't exist
if 'single_calc_result' not in st.session_state:
    st.session_state.single_calc_result = None
if 'single_calc_input_data' not in st.session_state:
    st.session_state.single_calc_input_data = None
if 'saved_calculations_data' not in st.session_state:
    st.session_state.saved_calculations_data = []
if 'saved_calculations_error' not in st.session_state:
    st.session_state.saved_calculations_error = None
if 'initial_fetch_done_saved_calcs' not in st.session_state:
    st.session_state.initial_fetch_done_saved_calcs = False


current_date_str = datetime.date.today().strftime("%A, %B %d, %Y")

st.title("🇻🇳 Vietnam Gross↔️Net Income Calculator")
st.caption(
    f"Calculates Net income based on Gross salary, dependents, and region. "
    f"Based on regulations circa April 2025. Current date: {current_date_str} (Env: {APP_ENVIRONMENT})"
)

tab1, tab2, tab3 = st.tabs(["Single Calculation", "Batch Upload (Excel)", "Saved Calculations"])

# --- Tab 1: Single Calculation ---
with tab1:
    st.header("Single Income Calculation")
    col1_single, col2_single = st.columns(2)
    with col1_single:
        gross_income_single = st.number_input(
            "💰 Gross Monthly Income (VND)",
            min_value=0.0, step=100000.0, value=30000000.0, format="%.0f",
            help="Enter the total gross salary before any deductions.", key="gross_single"
        )
        num_dependents_single = st.number_input(
            "👨‍👩‍👧‍👦 Number of Dependents",
            min_value=0, step=1, value=1,
            help="Enter the number of registered dependents.", key="dep_single"
        )
    with col2_single:
        region_options_single = list(REGIONAL_MINIMUM_WAGES.keys())
        region_single = st.selectbox(
            "📍 Region (Vùng)", options=region_options_single,
            format_func=lambda r: f"Region {r} (Min Wage: {REGIONAL_MINIMUM_WAGES.get(r, 0):,} VND)",
            index=0, help="Select the region where you work.", key="region_single"
        )
        st.radio(
            "Mức lương đóng bảo hiểm (Insurance Base)",
            ("Based on Official Salary", "Other - Not Implemented"), index=0,
            help=(
                "Currently calculates based on Official Salary (Gross). "
                "'Other' option is not yet implemented."
            ),
            key="ins_base_single"
        )

    if st.button("Calculate Single / Tính Đơn", type="primary", key="calc_single", use_container_width=True):
        logger.info(
            f"Single calculation initiated with: Gross={gross_income_single}, "
            f"Dependents={num_dependents_single}, Region={region_single}"
        )
        st.session_state.single_calc_result = None # Reset previous result
        st.session_state.single_calc_input_data = None

        if gross_income_single <= 0:
            st.error("Gross Monthly Income must be greater than zero.", icon="⚠️")
            logger.warning("Single calculation: Invalid gross income <= 0.")
        else:
            try:
                input_data_single = GrossNetInput(
                    gross_income=gross_income_single,
                    num_dependents=num_dependents_single,
                    region=region_single
                )
                with st.spinner("Calculating..."):
                    result_single = calculate_gross_to_net(input_data_single)
                
                st.session_state.single_calc_result = result_single
                st.session_state.single_calc_input_data = input_data_single # Store input for saving

                st.success("Calculation Successful!", icon="✅")
                logger.info(f"Single calculation successful. Net income: {result_single.net_income}")

            except (InvalidRegionError, NegativeGrossIncomeError, NegativeDependentsError, InvalidInputDataError) as e:
                st.error(f"Input Error: {str(e)}", icon="⚠️")
                logger.warning(f"Single calculation input error: {str(e)}")
            except MissingConfigurationError as e:
                st.error(f"Configuration Error: {str(e)}. Please contact support.", icon="⚙️")
                logger.error(f"Single calculation configuration error: {str(e)}", exc_info=True)
            except CoreCalculationError as e:
                st.error(f"Calculation Error: {str(e)}", icon="❌")
                logger.error(f"Single calculation core error: {str(e)}", exc_info=True)
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}", icon="❌")
                logger.exception("Unexpected error during single calculation.")

    # Display results if available in session state
    if st.session_state.single_calc_result:
        result_single = st.session_state.single_calc_result
        st.subheader("📊 Calculation Result")
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            st.metric("💵 Net Income (Lương Net)", format_vnd(result_single.net_income))
            st.metric("💸 PIT (Thuế TNCN)", format_vnd(result_single.personal_income_tax))
            st.metric("🛡️ Total Insurance (Tổng BH)", format_vnd(result_single.total_insurance_contribution))
        with res_col2:
            st.metric("💰 Gross Income (Lương Gộp)", format_vnd(result_single.gross_income))
            st.metric("📉 Taxable Income (TNCT)", format_vnd(result_single.taxable_income))
            st.metric("📈 Pre-Tax Income (TNTT)", format_vnd(result_single.pre_tax_income))

        with st.expander("📋 View Insurance Breakdown"):
            ins_data = {
                "Social Insurance (BHXH)": format_vnd(result_single.insurance_breakdown.social_insurance),
                "Health Insurance (BHYT)": format_vnd(result_single.insurance_breakdown.health_insurance),
                "Unemployment Insurance (BHTN)": format_vnd(result_single.insurance_breakdown.unemployment_insurance),
                "**Total**": f"**{format_vnd(result_single.insurance_breakdown.total)}**"
            }
            st.table(ins_data)

        # --- Save Calculation Section ---
        st.markdown("---")
        st.subheader("💾 Save This Calculation")
        save_calc_name = st.text_input("Optional name for this calculation:", key="save_calc_name_input")
        if st.button("Save Calculation", key="save_single_calc_button"):
            if st.session_state.single_calc_input_data and st.session_state.single_calc_result:
                calc_to_save = SavedCalculationCreate(
                    calculation_name=save_calc_name if save_calc_name else f"Calculation from {datetime.date.today().isoformat()}",
                    gross_income=st.session_state.single_calc_input_data.gross_income,
                    num_dependents=st.session_state.single_calc_input_data.num_dependents,
                    region=st.session_state.single_calc_input_data.region,
                    net_income=st.session_state.single_calc_result.net_income,
                    personal_income_tax=st.session_state.single_calc_result.personal_income_tax,
                    total_insurance_contribution=st.session_state.single_calc_result.total_insurance_contribution
                )
                save_calculation_to_api(calc_to_save)
            else:
                st.warning("Please perform a calculation first before saving.")


# --- Tab 2: Batch Upload Calculation ---
# ... (Batch upload code remains the same as previous version) ...
with tab2:
    st.header("Batch Calculation via Excel Upload")
    with st.expander("Click here for detailed instructions on the Excel file format", expanded=False):
        st.markdown("**1. File Format:**")
        st.markdown("* Use standard Excel formats: `.xlsx` (recommended) or `.xls`.")
        st.markdown(
            "* Ensure the file is saved as a proper Excel workbook. If you "
            "encounter errors like 'File is not a zip file', try re-saving "
            "explicitly as `.xlsx`."
        )
        st.markdown("**2. Sheet:**")
        st.markdown(
            "* Place the data to be processed on the **first sheet** in the "
            "workbook."
        )
        st.markdown("**3. Header Row:**")
        st.markdown(
            "* The **very first row** must contain the column headers."
        )
        st.markdown(
            "* Headers must **exactly match** these names (case-sensitive):"
        )
        st.markdown(f"    * `{EXPECTED_COLUMNS_EXCEL_UPLOAD['gross']}`")
        st.markdown(f"    * `{EXPECTED_COLUMNS_EXCEL_UPLOAD['dependents']}`")
        st.markdown(f"    * `{EXPECTED_COLUMNS_EXCEL_UPLOAD['region']}`")
        st.markdown("**4. Data Types & Values:**")
        st.markdown(
            f"* `{EXPECTED_COLUMNS_EXCEL_UPLOAD['gross']}` column: **Numeric** values only "
            "(gross monthly income in VND). No currency symbols or commas. "
            "Must be > 0."
        )
        st.markdown(
            f"* `{EXPECTED_COLUMNS_EXCEL_UPLOAD['dependents']}` column: **Integer** (whole "
            "number) values only (number of registered dependents). Must be >= 0."
        )
        st.markdown(
            f"* `{EXPECTED_COLUMNS_EXCEL_UPLOAD['region']}` column: **Integer** values only: "
            "`1`, `2`, `3`, or `4`."
        )
        st.markdown("**5. Data Rows:**")
        st.markdown(
            "* Each row after the header represents one calculation case."
        )
        st.markdown("**6. Simplicity:**")
        st.markdown(
            "* Avoid merged cells, complex formatting, images, or formulas "
            "within the header and data rows."
        )
        st.markdown("**Example File Structure:**")
        example_data = {
            EXPECTED_COLUMNS_EXCEL_UPLOAD['gross']: [30000000, 20000000, 50000000],
            EXPECTED_COLUMNS_EXCEL_UPLOAD['dependents']: [1, 0, 2],
            EXPECTED_COLUMNS_EXCEL_UPLOAD['region']: [1, 1, 2]
        }
        st.table(pd.DataFrame(example_data))
        st.markdown("**Troubleshooting Upload Errors:**")
        st.markdown(
            "* `File is not a zip file`: Ensure you save as `.xlsx` properly."
        )
        st.markdown(
            "* `Missing required columns`: Check header spelling and "
            "capitalization exactly."
        )
        st.markdown(
            "* Processing errors: Check data types in each cell match the "
            "requirements."
        )

    uploaded_file = st.file_uploader(
        "Choose an Excel file for Batch Calculation",
        type=['xlsx', 'xls'],
        accept_multiple_files=False,
        key="excel_uploader_batch"
        )

    if uploaded_file is not None:
        logger.info(f"Excel file '{uploaded_file.name}' uploaded by user for batch processing.")
        st.info(f"File '{uploaded_file.name}' uploaded. Processing...")
        try:
            df_input = pd.read_excel(
                uploaded_file,
                engine='openpyxl' if uploaded_file.name.endswith('xlsx') else None
            )
            logger.info(f"Successfully read Excel file for batch. Shape: {df_input.shape}")
            st.dataframe(df_input.head())

            missing_cols = [col_val for col_key, col_val in EXPECTED_COLUMNS_EXCEL_UPLOAD.items() if col_val not in df_input.columns]
            if missing_cols:
                msg = f"Error: Missing required columns in Excel file: {', '.join(missing_cols)}"
                st.error(msg, icon="⚠️")
                logger.error(f"Batch upload: {msg}")
            else:
                results_list = []
                total_rows = len(df_input)
                progress_bar = st.progress(0, text="Processing rows...")
                logger.info(f"Starting batch processing for {total_rows} rows.")

                for index, row in df_input.iterrows():
                    status = "Success"
                    error_msg = ""
                    result_data_dict = {}

                    try:
                        gross = float(row[EXPECTED_COLUMNS_EXCEL_UPLOAD['gross']])
                        deps = int(row[EXPECTED_COLUMNS_EXCEL_UPLOAD['dependents']])
                        reg = int(row[EXPECTED_COLUMNS_EXCEL_UPLOAD['region']])

                        if gross <= 0: raise NegativeGrossIncomeError(gross_income=gross)
                        if deps < 0: raise NegativeDependentsError(num_dependents=deps)
                        if reg not in [1, 2, 3, 4]: raise InvalidRegionError(region_value=reg)

                        input_data = GrossNetInput(gross_income=gross, num_dependents=deps, region=reg)
                        result = calculate_gross_to_net(input_data)
                        result_data_dict = result.model_dump(exclude_none=True)

                    except (InvalidRegionError, NegativeGrossIncomeError, NegativeDependentsError, InvalidInputDataError, MissingConfigurationError, CoreCalculationError) as e:
                        status = "Error"; error_msg = f"Row {index + 2}: {type(e).__name__} - {str(e)}"
                        logger.warning(f"Batch processing error: {error_msg}")
                    except (TypeError, KeyError, ValueError) as e:
                        status = "Error"; error_msg = f"Row {index + 2}: Data Error - {type(e).__name__} - {str(e)}. Check column names and data types."
                        logger.warning(f"Batch processing data error: {error_msg}")
                    except Exception as e:
                        status = "Error"; error_msg = f"Row {index + 2}: Unexpected Error - {str(e)}"
                        logger.exception(f"Unexpected error during batch processing row {index + 2}.")

                    combined_row_data = row.to_dict()
                    combined_row_data['CalculationStatus'] = status
                    combined_row_data['ErrorMessage'] = error_msg.split(':')[-1].strip() if error_msg else ""
                    if result_data_dict:
                         combined_row_data.update(result_data_dict)
                    results_list.append(combined_row_data)

                    progress_text = f"Processing row {index + 1}/{total_rows}"
                    progress_bar.progress(
                        (index + 1) / total_rows, text=progress_text
                    )

                progress_bar.empty()
                logger.info("Batch processing completed.")

                df_output = pd.DataFrame(results_list)
                st.subheader("📊 Batch Calculation Results")
                st.dataframe(df_output)

                st.markdown("---"); st.subheader("⬇️ Download Results")
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    csv_data = convert_df_to_csv(df_output)
                    st.download_button("Download Results as CSV", csv_data, 'gross_net_results.csv', 'text/csv', use_container_width=True)
                with col_dl2:
                    excel_data = convert_df_to_excel(df_output)
                    st.download_button("Download Results as Excel", excel_data, 'gross_net_results.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', use_container_width=True)
        except Exception as e:
            st.error(f"Error reading or processing Excel file: {str(e)}", icon="❌")
            logger.exception("Critical error reading or processing uploaded Excel file.")

# --- Tab 3: Saved Calculations ---
with tab3:
    st.header("Saved Calculation Records")
    st.markdown("View your previously saved calculation results.")

    if st.button("Refresh Saved Calculations", key="refresh_saved_calcs_button", use_container_width=True):
        logger.info("User clicked refresh for saved calculations.")
        st.session_state.saved_calculations_data = fetch_saved_calculations_from_api()
        if st.session_state.saved_calculations_error:
            st.error(st.session_state.saved_calculations_error) # Show error if fetch failed
        elif not st.session_state.saved_calculations_data:
             st.info("No saved calculations found or the list is empty.")
        else:
            st.success(f"Fetched {len(st.session_state.saved_calculations_data)} records.")
        st.session_state.initial_fetch_done_saved_calcs = True # Mark that refresh was attempted

    # Fetch data on first load of the tab or if not already loaded
    if not st.session_state.get('initial_fetch_done_saved_calcs', False):
        with st.spinner("Loading saved calculations..."):
            st.session_state.saved_calculations_data = fetch_saved_calculations_from_api()
            st.session_state.initial_fetch_done_saved_calcs = True
            if st.session_state.saved_calculations_error:
                st.error(st.session_state.saved_calculations_error)
            elif not st.session_state.saved_calculations_data:
                st.info("No saved calculations found.")
            # No need to rerun if data is displayed below

    if st.session_state.saved_calculations_data:
        df_saved = pd.DataFrame(st.session_state.saved_calculations_data)
        display_cols = [
            'id', 'calculation_name', 'gross_income', 'num_dependents', 'region',
            'net_income', 'personal_income_tax', 'total_insurance_contribution',
            'created_at', 'updated_at'
        ]
        display_cols_present = [col for col in display_cols if col in df_saved.columns]

        if not display_cols_present:
            st.warning("No data to display or columns are misconfigured in the API response.")
        else:
            df_display = df_saved[display_cols_present].copy()
            for col in ['gross_income', 'net_income', 'personal_income_tax', 'total_insurance_contribution']:
                if col in df_display.columns:
                    df_display[col] = df_display[col].apply(lambda x: f"{float(x):,.0f}" if pd.notnull(x) else "")
            for col_date in ['created_at', 'updated_at']:
                 if col_date in df_display.columns:
                    df_display[col_date] = pd.to_datetime(df_display[col_date]).dt.strftime('%Y-%m-%d %H:%M:%S')

            st.dataframe(df_display, hide_index=True, use_container_width=True)
            # TODO: Add UI elements for Delete and Update (Rename) per row here
    elif not st.session_state.saved_calculations_error: # Only show this if no error and no data
        st.info("Click 'Refresh Saved Calculations' to load data or if the list is empty.")


# --- Footer ---
st.markdown("---")
disclaimer = f"""
**Disclaimer:** This calculator uses rates and allowances presumed current
for {current_date_str} (Hanoi, Vietnam) based on available public data
(e.g., Decree 74/2024/ND-CP, Resolution 954/2020/UBTVQH14, standard
insurance rates). Base salary (`Lương cơ sở`) for the BHXH/BHYT cap uses
2,340,000 VND based on UI hints/potential reforms. Always consult official
sources or a professional for financial decisions.
"""
st.caption(textwrap.dedent(disclaimer))




