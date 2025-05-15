# frontend/app.py
import streamlit as st
import pandas as pd
import io
import datetime
import logging
import os
import json # Ensure json is imported for various uses
import textwrap
import requests # For making API calls
import sys # For sys.path modification if you keep it, and for __main__

# Add parent folder to sys.path if you were importing local modules differently
# For this self-contained example, direct core imports assume 'core' is in PYTHONPATH
# or in the same directory or a standard package location.
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# Helper conversion function (if not already in a shared utility)
def convert_excel_to_json(excel_stream, engine=None):
    # This import is fine here as it's specific to this function's utility scope
    # and avoids making pandas a top-level import if only used here.
    # However, since pandas is used elsewhere, it's better at the top.
    # For consistency with the rest of the file, pandas is imported at the top.
    df = pd.read_excel(excel_stream, engine=engine)
    df = df.where(pd.notnull(df), None) # Convert NaNs to None (to become JSON null)
    return json.dumps(df.to_dict(orient="records"))

from dotenv import load_dotenv
# Load environment variables from .env file (for local development)
load_dotenv()

# Local application imports (assuming 'core' is accessible)
from core.models import (
    GrossNetInput,
    SavedCalculationCreate,
)
from core.calculator import calculate_gross_to_net
from core.constants import REGIONAL_MINIMUM_WAGES
from core.exceptions import (
    CoreCalculationError,
    InvalidRegionError,
    InvalidInputDataError,
    NegativeGrossIncomeError,
    NegativeDependentsError,
    MissingConfigurationError,
)


# --- Basic Logging Configuration ---
LOG_LEVEL_FROM_ENV = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL_FROM_ENV,
    format="%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
logger.info(f"Logging level set to: {LOG_LEVEL_FROM_ENV}")

# --- Application Environment ---
APP_ENVIRONMENT = os.getenv("API_ENV", "development")
logger.info(f"Streamlit application starting in '{APP_ENVIRONMENT}' environment.")

# --- API URL ---
API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")  # Default for local API
logger.info(f"API_BASE_URL for frontend calls: {API_BASE_URL}")


# --- Constants for UI ---
EXPECTED_COLUMNS_EXCEL_UPLOAD = {
    "gross": "GrossIncome",
    "dependents": "Dependents",
    "region": "Region",
}
OUTPUT_COLUMNS_EXCEL_UPLOAD = [
    "NetIncome", "PIT", "TotalInsurance", "TaxableIncome", "PreTaxIncome",
    "BHXH", "BHYT", "BHTN", "CalculationStatus", "ErrorMessage",
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


@st.cache_data(
    hash_funcs={
        pd.DataFrame: lambda df: hash(json.dumps(df.to_dict(), sort_keys=True)),
        dict: lambda d: hash(json.dumps(d, sort_keys=True)),
    }
)
def convert_df_to_csv(df_to_convert):
    logger.info("Converting DataFrame to CSV for download.")
    return df_to_convert.to_csv(index=False).encode("utf-8")


@st.cache_data(
    hash_funcs={
        pd.DataFrame: lambda df: hash(json.dumps(df.to_dict(), sort_keys=True)),
        dict: lambda d: hash(json.dumps(d, sort_keys=True)),
    }
)
def convert_df_to_excel(df_to_convert):
    logger.info("Converting DataFrame to Excel for download.")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_to_convert.to_excel(writer, index=False, sheet_name="GrossNetResults")
    processed_data = output.getvalue()
    return processed_data


# --- API Call Functions for Saved Calculations ---
def fetch_saved_calculations_from_api():
    items = []
    st.session_state.saved_calculations_error = None  # Clear previous errors
    try:
        url = f"{API_BASE_URL}/saved-calculations/"
        logger.info(f"Fetching saved calculations from: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        logger.info(
            f"Successfully fetched {data.get('total', 0)} saved calculations. Displaying {len(items)}."
        )
    except requests.exceptions.RequestException as e:
        st.session_state.saved_calculations_error = (
            f"Error fetching saved calculations: {e}"
        )
        logger.error(f"API call error fetching saved calculations: {e}", exc_info=True)
    except Exception as e:
        st.session_state.saved_calculations_error = (
            f"An unexpected error occurred: {str(e)}"
        )
        logger.exception("Unexpected error fetching saved calculations.")
    return items


def save_calculation_to_api(calculation_data: SavedCalculationCreate):
    """Saves a calculation result to the API."""
    try:
        url = f"{API_BASE_URL}/saved-calculations/"
        logger.info(
            f"Saving calculation to API: {url} with data: {calculation_data.model_dump_json(exclude_none=True)}"
        )
        response = requests.post(url, json=calculation_data.model_dump(), timeout=10)
        response.raise_for_status()
        saved_data = response.json()
        st.success(
            f"Calculation '{saved_data.get('calculation_name', 'Untitled')}' (ID: {saved_data.get('id')}) saved successfully!",
            icon="✅",
        )
        logger.info(f"Successfully saved calculation with ID: {saved_data.get('id')}")
        # Clear and refresh the saved calculations list in session state
        if "saved_calculations_data" in st.session_state:
            del st.session_state.saved_calculations_data
        st.session_state.initial_fetch_done_saved_calcs = False # Trigger re-fetch on Saved Calcs tab
        return True
    except requests.exceptions.HTTPError as e:
        error_detail = "Could not save calculation."
        try:
            error_detail = e.response.json().get("detail", error_detail)
        except ValueError:  # Not a JSON response
            pass
        st.error(
            f"API Error saving calculation: {error_detail} (Status: {e.response.status_code})"
        )
        logger.error(f"API HTTPError saving calculation: {error_detail}", exc_info=True)
    except requests.exceptions.RequestException as e:
        st.error(f"Network error saving calculation: {e}")
        logger.error(f"API Network error saving calculation: {e}", exc_info=True)
    except Exception as e:
        st.error(f"An unexpected error occurred while saving: {str(e)}")
        logger.exception("Unexpected error saving calculation.")
    return False


def update_calculation_name_in_api(calculation_id: int, new_name: str):
    """Updates the name of a saved calculation via the API."""
    try:
        url = f"{API_BASE_URL}/saved-calculations/{calculation_id}"
        payload = {"calculation_name": new_name} # Based on SavedCalculationUpdate model
        logger.info(f"Updating calculation ID {calculation_id} to new name: {new_name} at {url}")
        response = requests.put(url, json=payload, timeout=10)
        response.raise_for_status()
        updated_data = response.json()
        st.success(
            f"Calculation '{updated_data.get('calculation_name', 'Untitled')}' (ID: {updated_data.get('id')}) updated successfully!",
            icon="🔄",
        )
        logger.info(f"Successfully updated calculation ID: {updated_data.get('id')}")
        # Trigger re-fetch of saved calculations
        if "saved_calculations_data" in st.session_state:
            del st.session_state.saved_calculations_data
        st.session_state.initial_fetch_done_saved_calcs = False
        return True
    except requests.exceptions.HTTPError as e:
        error_detail = "Could not update calculation."
        try:
            error_detail = e.response.json().get("detail", error_detail)
        except ValueError:
            pass
        st.error(
            f"API Error updating calculation: {error_detail} (Status: {e.response.status_code})"
        )
        logger.error(f"API HTTPError updating calculation: {error_detail}", exc_info=True)
    except requests.exceptions.RequestException as e:
        st.error(f"Network error updating calculation: {e}")
        logger.error(f"API Network error updating calculation: {e}", exc_info=True)
    except Exception as e:
        st.error(f"An unexpected error occurred while updating: {str(e)}")
        logger.exception("Unexpected error updating calculation.")
    return False

def delete_calculation_from_api(calculation_id: int):
    """Deletes a saved calculation via the API."""
    try:
        url = f"{API_BASE_URL}/saved-calculations/{calculation_id}"
        logger.info(f"Deleting calculation ID {calculation_id} from API: {url}")
        response = requests.delete(url, timeout=10)
        response.raise_for_status()
        st.success(f"Calculation ID {calculation_id} deleted successfully!", icon="🗑️")
        logger.info(f"Successfully deleted calculation ID: {calculation_id}")
        # Trigger re-fetch of saved calculations
        if "saved_calculations_data" in st.session_state:
            del st.session_state.saved_calculations_data
        st.session_state.initial_fetch_done_saved_calcs = False
        return True
    except requests.exceptions.HTTPError as e:
        error_detail = "Could not delete calculation."
        try:
            error_detail = e.response.json().get("detail", error_detail)
        except ValueError:
            pass
        st.error(
            f"API Error deleting calculation: {error_detail} (Status: {e.response.status_code})"
        )
        logger.error(f"API HTTPError deleting calculation: {error_detail}", exc_info=True)
    except requests.exceptions.RequestException as e:
        st.error(f"Network error deleting calculation: {e}")
        logger.error(f"API Network error deleting calculation: {e}", exc_info=True)
    except Exception as e:
        st.error(f"An unexpected error occurred while deleting: {str(e)}")
        logger.exception("Unexpected error deleting calculation.")
    return False


# --- Main App ---
st.set_page_config(
    page_title="VN Gross<=>Net Calculator",
    page_icon="🇻🇳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Initialize session state variables if they don't exist
if "single_calc_result" not in st.session_state:
    st.session_state.single_calc_result = None
if "single_calc_input_data" not in st.session_state:
    st.session_state.single_calc_input_data = None
if "saved_calculations_data" not in st.session_state:
    st.session_state.saved_calculations_data = []
if "saved_calculations_error" not in st.session_state:
    st.session_state.saved_calculations_error = None
if "initial_fetch_done_saved_calcs" not in st.session_state:
    st.session_state.initial_fetch_done_saved_calcs = False


current_date_str = datetime.date.today().strftime("%A, %B %d, %Y")

st.title("🇻🇳 Vietnam Gross↔️Net Income Calculator")
st.caption(
    f"Calculates Net income based on Gross salary, dependents, and region. "
    f"Based on regulations circa April 2025. Current date: {current_date_str} (Env: {APP_ENVIRONMENT})"
)

tab1, tab2, tab3 = st.tabs(
    ["Single Calculation", "Batch Upload (Excel)", "Saved Calculations"]
)

# --- Tab 1: Single Calculation ---
with tab1:
    st.header("Single Income Calculation")
    col1_single, col2_single = st.columns(2)
    with col1_single:
        gross_income_single = st.number_input(
            "💰 Gross Monthly Income (VND)",
            min_value=0.0, step=100000.0, value=30000000.0, format="%.0f",
            help="Enter the total gross salary before any deductions.", key="gross_single",
        )
        num_dependents_single = st.number_input(
            "👨‍👩‍👧‍👦 Number of Dependents",
            min_value=0, step=1, value=1,
            help="Enter the number of registered dependents.", key="dep_single",
        )
    with col2_single:
        region_options_single = list(REGIONAL_MINIMUM_WAGES.keys())
        region_single = st.selectbox(
            "📍 Region (Vùng)",
            options=region_options_single,
            format_func=lambda r: f"Region {r} (Min Wage: {REGIONAL_MINIMUM_WAGES.get(r, 0):,} VND)",
            index=0, help="Select the region where you work.", key="region_single",
        )
        st.radio(
            "Mức lương đóng bảo hiểm (Insurance Base)",
            ("Based on Official Salary", "Other - Not Implemented"), index=0,
            help=(
                "Currently calculates based on Official Salary (Gross). "
                "'Other' option is not yet implemented."
            ), key="ins_base_single",
        )

    if st.button("Calculate Single / Tính Đơn", type="primary", key="calc_single", use_container_width=True):
        logger.info(
            f"Single calculation initiated with: Gross={gross_income_single}, "
            f"Dependents={num_dependents_single}, Region={region_single}"
        )
        st.session_state.single_calc_result = None  # Reset previous result
        st.session_state.single_calc_input_data = None

        if gross_income_single <= 0:
            st.error("Gross Monthly Income must be greater than zero.", icon="⚠️")
            logger.warning("Single calculation: Invalid gross income <= 0.")
        else:
            try:
                input_data_single = GrossNetInput(
                    gross_income=gross_income_single,
                    num_dependents=num_dependents_single,
                    region=region_single,
                )
                with st.spinner("Calculating..."):
                    result_single = calculate_gross_to_net(input_data_single)

                st.session_state.single_calc_result = result_single
                st.session_state.single_calc_input_data = input_data_single  # Store input for saving
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
                "**Total**": f"**{format_vnd(result_single.insurance_breakdown.total)}**",
            }
            st.table(ins_data)

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
                    total_insurance_contribution=st.session_state.single_calc_result.total_insurance_contribution,
                )
                if save_calculation_to_api(calc_to_save):
                    st.rerun() # Refresh the page to update saved list potentially
            else:
                st.warning("Please perform a calculation first before saving.")

# --- Tab 2: Batch Upload Calculation ---
with tab2:
    st.header("Batch Calculation via Excel Upload")
    with st.expander("Click here for detailed instructions on the Excel file format", expanded=False):
        st.markdown("**1. File Format:**")
        st.markdown("* Use standard Excel formats: `.xlsx` (recommended) or `.xls`.")
        st.markdown("* Ensure the file is saved as a proper Excel workbook...") # Truncated for brevity
        st.markdown(f"    * `{EXPECTED_COLUMNS_EXCEL_UPLOAD['gross']}`")
        st.markdown(f"    * `{EXPECTED_COLUMNS_EXCEL_UPLOAD['dependents']}`")
        st.markdown(f"    * `{EXPECTED_COLUMNS_EXCEL_UPLOAD['region']}`")
        # ... (rest of the instructions as in your provided code) ...
        example_data = {
            EXPECTED_COLUMNS_EXCEL_UPLOAD["gross"]: [30000000, 20000000, 50000000],
            EXPECTED_COLUMNS_EXCEL_UPLOAD["dependents"]: [1, 0, 2],
            EXPECTED_COLUMNS_EXCEL_UPLOAD["region"]: [1, 1, 2],
        }
        st.table(pd.DataFrame(example_data))
        st.markdown("**Troubleshooting Upload Errors:**")
        st.markdown("* `File is not a zip file`: Ensure you save as `.xlsx` properly.")
        st.markdown("* `Missing required columns`: Check header spelling and capitalization exactly.")
        st.markdown("* Processing errors: Check data types in each cell match the requirements.")

    uploaded_file = st.file_uploader(
        "Choose an Excel file for Batch Calculation", type=["xlsx", "xls"],
        accept_multiple_files=False, key="excel_uploader_batch"
    )

    if uploaded_file is not None:
        logger.info(f"Excel file '{uploaded_file.name}' uploaded by user for batch processing.")
        st.info(f"File '{uploaded_file.name}' uploaded. Processing...")
        try:
            contents = uploaded_file.getvalue()
            excel_stream = io.BytesIO(contents)
            engine_used = "openpyxl" if uploaded_file.name.endswith("xlsx") else None

            # This part was changed to use the local convert_excel_to_json and then re-read for df_input
            # For batch processing, we typically want to process df_input row by row
            # and then show results. The direct conversion to JSON might be for a different feature.
            # Reverting to direct pandas read for df_input for batch calculation.
            excel_stream.seek(0) # Reset stream before reading again for pandas
            df_input = pd.read_excel(excel_stream, engine=engine_used)
            df_input = df_input.where(pd.notnull(df_input), None) # Handle NaNs

            logger.info(f"Successfully read Excel file for batch. Shape: {df_input.shape}")
            st.dataframe(df_input.head())

            missing_cols = [
                col_val for col_key, col_val in EXPECTED_COLUMNS_EXCEL_UPLOAD.items()
                if col_val not in df_input.columns
            ]
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
                        gross = float(row[EXPECTED_COLUMNS_EXCEL_UPLOAD["gross"]])
                        deps = int(row[EXPECTED_COLUMNS_EXCEL_UPLOAD["dependents"]])
                        reg = int(row[EXPECTED_COLUMNS_EXCEL_UPLOAD["region"]])

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
                    combined_row_data["CalculationStatus"] = status
                    combined_row_data["ErrorMessage"] = error_msg.split(":")[-1].strip() if error_msg else ""
                    if result_data_dict:
                        combined_row_data.update(result_data_dict)
                    results_list.append(combined_row_data)
                    progress_text = f"Processing row {index + 1}/{total_rows}"
                    progress_bar.progress((index + 1) / total_rows, text=progress_text)

                progress_bar.empty()
                logger.info("Batch processing completed.")
                df_output = pd.DataFrame(results_list)
                st.subheader("📊 Batch Calculation Results")
                st.dataframe(df_output)

                st.markdown("---"); st.subheader("⬇️ Download Results") # PEP8 E702 fixed by ruff format
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    csv_data = convert_df_to_csv(df_output)
                    st.download_button("Download Results as CSV", csv_data, "gross_net_results.csv", "text/csv", use_container_width=True)
                with col_dl2:
                    excel_data = convert_df_to_excel(df_output)
                    st.download_button("Download Results as Excel", excel_data, "gross_net_results.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        except Exception as e:
            st.error(f"Error reading or processing Excel file: {str(e)}", icon="❌")
            logger.exception("Critical error reading or processing uploaded Excel file.")


# --- Tab 3: Saved Calculations ---
with tab3:
    st.header("Saved Calculation Records")
    st.markdown("View, rename, or delete your previously saved calculation results.")

    if st.button("🔄 Refresh Saved Calculations", key="refresh_saved_calcs_button_tab3"):
        logger.info("User clicked refresh for saved calculations.")
        if "saved_calculations_data" in st.session_state:
            del st.session_state.saved_calculations_data
        st.session_state.initial_fetch_done_saved_calcs = False
        st.rerun() # Rerun to trigger the fetch logic below

    if not st.session_state.get("initial_fetch_done_saved_calcs", False):
        with st.spinner("Loading saved calculations..."):
            st.session_state.saved_calculations_data = fetch_saved_calculations_from_api()
            st.session_state.initial_fetch_done_saved_calcs = True

    if st.session_state.get("saved_calculations_error"):
        st.error(st.session_state.saved_calculations_error)
    elif not st.session_state.get("saved_calculations_data"):
        st.info("No saved calculations found. Perform a calculation on Tab 1 and save it, or click 'Refresh'.")
    else:
        saved_calcs_list = st.session_state["saved_calculations_data"]
        st.subheader(f"Found {len(saved_calcs_list)} records")

        for i, record_dict in enumerate(saved_calcs_list):
            # Ensure record_dict is a dictionary, not a Pydantic model instance if API returns raw dicts
            record_id = record_dict.get("id")
            current_name = record_dict.get("calculation_name", f"Calculation {record_id}")

            st.markdown("---")
            # Using an expander for each record for better organization
            with st.expander(f"{current_name} (ID: {record_id})", expanded=False):
                details_cols = st.columns([2,2,1]) # 3 columns for details, edit, delete
                with details_cols[0]:
                    st.text(f"Gross: {format_vnd(record_dict.get('gross_income'))}")
                    st.text(f"Net: {format_vnd(record_dict.get('net_income'))}")
                    st.text(f"PIT: {format_vnd(record_dict.get('personal_income_tax'))}")
                with details_cols[1]:
                    st.text(f"Dependents: {record_dict.get('num_dependents')}")
                    st.text(f"Region: {record_dict.get('region')}")
                    st.text(f"Total Insurance: {format_vnd(record_dict.get('total_insurance_contribution'))}")
                    st.caption(f"Created: {pd.to_datetime(record_dict.get('created_at')).strftime('%Y-%m-%d %H:%M:%S') if record_dict.get('created_at') else 'N/A'}")
                    st.caption(f"Updated: {pd.to_datetime(record_dict.get('updated_at')).strftime('%Y-%m-%d %H:%M:%S') if record_dict.get('updated_at') else 'N/A'}")

                with details_cols[2]: # Column for buttons
                    # Update Button and Form (using unique keys for each form)
                    # Using st.popover for the edit form for a cleaner UI
                    with st.popover("✏️ Edit Name", use_container_width=True):
                        st.markdown(f"Edit name for ID: {record_id}")
                        with st.form(key=f"update_form_{record_id}_{i}"): # Added index for more uniqueness
                            new_name_input = st.text_input(
                                "New Calculation Name",
                                value=current_name, # Use current_name
                                key=f"new_name_{record_id}_{i}"
                            )
                            submit_update = st.form_submit_button("Save Name")

                            if submit_update:
                                if new_name_input and new_name_input != current_name:
                                    if update_calculation_name_in_api(record_id, new_name_input):
                                        st.rerun() # Refresh the list
                                elif not new_name_input:
                                    st.warning("New name cannot be empty.")
                                else:
                                    st.info("Name is unchanged.")
                    
                    # Delete Button
                    if st.button("🗑️ Delete", key=f"delete_btn_{record_id}_{i}", type="secondary", use_container_width=True):
                        # Simple confirmation, can be improved with a modal or checkbox
                        confirm_key = f"confirm_delete_{record_id}_{i}"
                        if confirm_key not in st.session_state:
                            st.session_state[confirm_key] = False

                        if st.session_state[confirm_key]: # If confirmed
                            if delete_calculation_from_api(record_id):
                                del st.session_state[confirm_key] # Reset confirmation state
                                st.rerun() # Refresh the list
                        else:
                            st.warning(f"Are you sure you want to delete '{current_name}' (ID: {record_id})? Click delete again to confirm.")
                            st.session_state[confirm_key] = True # Set to true, so next click on THIS button deletes
        st.markdown("---")


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


# The __main__ block for command-line Excel to JSON conversion can remain
# if you use this script directly for that purpose sometimes.
# If not, it can be removed.
if __name__ == "__main__":
    # This part is for command-line execution to convert Excel to JSON
    # It's separate from the Streamlit app functionality above.
    if len(sys.argv) < 2:
        print("Usage for CLI conversion: python app.py [excel_file_path]")
        sys.exit(1)

    excel_file_path = sys.argv[1]
    if not os.path.exists(excel_file_path):
        print(f"Error: '{excel_file_path}' not found. Please provide a valid file path.")
        sys.exit(1)
    
    try:
        with open(excel_file_path, 'rb') as ef:
            excel_stream_cli = io.BytesIO(ef.read())
        json_output_cli = convert_excel_to_json(excel_stream_cli)
        print(json_output_cli)
    except Exception as e:
        print(f"Error during CLI Excel to JSON conversion: {e}")
        sys.exit(1)
