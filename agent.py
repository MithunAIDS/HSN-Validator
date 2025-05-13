import pandas as pd
from google.adk.agents import Agent

def determine_gst_rate(hsn_code: str) -> str:
    """Determine GST rate based on HSN code ranges with specific exceptions."""
    try:
        # Handle specific exceptions first
        specific_exceptions = {
            "01": "0%",  # LIVE ANIMALS
            "0101": "0%",  # Live horses, asses, mules and hinnies
            "0102": "0%",  # Live bovine animals
            # Add more specific exceptions as needed
        }
        
        # Check if the code matches any specific exception
        if hsn_code in specific_exceptions:
            return specific_exceptions[hsn_code]
        
        # Handle cases where HSN code might be less than 4 digits
        hsn_code = hsn_code.zfill(4)  # Pad with leading zeros if needed
        
        # Check again in case padding created a match
        if hsn_code in specific_exceptions:
            return specific_exceptions[hsn_code]
            
        hsn_num = int(hsn_code[:4])  # Take first 4 digits
        
        if hsn_num < 1000:
            return "0%"
        elif 1001 <= hsn_num <= 2200:  # Agricultural products
            return "5%"
        elif 2201 <= hsn_num <= 2400:  # Tobacco products
            return "28%"
        elif 2401 <= hsn_num <= 4000:  # Various manufactured goods
            return "18%"
        elif 4001 <= hsn_num <= 5000:  # Textiles
            return "5%"
        elif 5001 <= hsn_num <= 7000:  # Other manufactured goods
            return "12%"
        elif 7001 <= hsn_num <= 9000:  # Machinery, electronics
            return "18%"
        elif hsn_num >= 9001:  # Services and other
            return "18%"
        else:
            return "18%"  # Default rate
    except:
        return "18%"  # Default if any error in processing

def load_hsn_data_from_excel(file_path: str) -> dict:
    """Load HSN data from Excel file into dictionary format."""
    try:
        df = pd.read_excel("D:\Task\HSN_SAC.xlsx")
        
        # Find the correct column names (case-insensitive)
        hsn_col = next(col for col in df.columns if 'hsn' in col.lower())
        desc_col = next(col for col in df.columns if 'desc' in col.lower())
        
        # Convert DataFrame to dictionary
        hsn_data = {}
        for _, row in df.iterrows():
            hsn_code = str(row[hsn_col]).strip()
            if hsn_code:  # Only add if HSN code exists
                hsn_data[hsn_code] = {
                    "description": row[desc_col],
                    "gst": determine_gst_rate(hsn_code)
                }
        return hsn_data
    except Exception as e:
        print(f"Error loading HSN data: {e}")
        print("Please ensure your Excel file has columns containing 'HSN' and 'Description'")
        return {}

# Load HSN data from your specific Excel file
HSN_DATA = load_hsn_data_from_excel(r"D:\Task\HSN_SAC.xlsx")

def get_hsn_info(hsn_code: str) -> dict:
    """Fetch HSN info based on code."""
    # Clean the input HSN code
    original_code = hsn_code
    hsn_code = str(hsn_code).strip()
    
    # First try exact match
    info = HSN_DATA.get(hsn_code)
    if info:
        return {
            "status": "success",
            "report": (
                f"HSN Code {hsn_code}: {info['description']}. "
                f"Applicable GST: {info['gst']}."
            )
        }
    
    # Try with leading zeros if code is short
    if len(hsn_code) < 4:
        padded_code = hsn_code.zfill(4)
        info = HSN_DATA.get(padded_code)
        if info:
            return {
                "status": "success",
                "report": (
                    f"HSN Code {padded_code}: {info['description']}. "
                    f"Applicable GST: {info['gst']}. "
                    f"(Note: Matched with padded code {padded_code} for your input {original_code})"
                )
            }
    
    # Try finding similar codes (handles cases where leading zeros were omitted)
    similar_codes = [code for code in HSN_DATA.keys() if code.endswith(hsn_code)]
    if similar_codes:
        info = HSN_DATA[similar_codes[0]]
        return {
            "status": "success",
            "report": (
                f"HSN Code {similar_codes[0]}: {info['description']}. "
                f"Applicable GST: {info['gst']}. "
                f"(Note: Found similar code {similar_codes[0]} for your input {original_code})"
            )
        }
    
    return {
        "status": "error",
        "error_message": f"No data found for HSN code '{original_code}'. Please verify the code."
    }

# Agent definition
root_agent = Agent(
    name="hsn_lookup_agent",
    model="gemini-2.0-flash",
    description="Agent to provide information about HSN codes and tax rates.",
    instruction="You are a helpful assistant who provides GST details for HSN codes.",
    tools=[get_hsn_info],
)