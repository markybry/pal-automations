import pandas as pd

def check_unsigned_staff(file_path, sheet_name, document_name):
    staff_list = [
        "Craig Bryant", "Mark Bryant", "Sini Bryant", "Terhi Bryant", "Lita Crouch",
        "Patrick Donyina", "Philomena Freeman", "Albertinah Mbaza Malambo", "Dorothy Mukuka",
        "Yetta Pain", "Jack Shaw", "Emma Wilkes", "Rebecca Ward", "Kasey Young", "Albert Nwuzoh"
    ]
    
    try:
        # Ensure openpyxl is used for .xlsx files
        df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
        
        # Clean column names (strip spaces and convert to lowercase)
        df.columns = df.columns.str.strip().str.lower()

        # Normalize the document name for comparison
        document_name_normalized = document_name.strip().lower()

        # Check if 'document name' column exists
        if 'document name' not in df.columns:
            print("Column 'Document Name' is not found in the spreadsheet.")
            return []

        # Normalize the 'document name' column values
        df['document name'] = df['document name'].str.strip().str.lower()

        # Filter rows where 'document name' matches the desired document
        df_filtered = df[df['document name'] == document_name_normalized]
        
        # Check if 'your name' column exists
        if "your name" not in df_filtered.columns:
            print("Column 'Your Name' is not found in the spreadsheet.")
            return []

        # Identify the final column
        final_column = df_filtered.columns[-1]
        
        # Ensure the final column is treated as a string to avoid errors
        df_filtered[final_column] = df_filtered[final_column].astype(str).str.lower()
        
        # Normalize the values in the final column to ensure consistent comparison
        df_filtered[final_column] = df_filtered[final_column].str.strip().str.lower()

        # Filter staff who have signed (expecting "yes" in the final column)
        signed_staff = df_filtered[df_filtered[final_column] == "yes"]["your name"].str.strip().str.lower().tolist()

        # Normalize the names in staff_list by stripping spaces and converting to lowercase
        normalized_staff_list = [name.strip().lower() for name in staff_list]
        
        # Finding unsigned staff
        unsigned_staff = [name for name in normalized_staff_list if name not in signed_staff]
        
        # Sort the unsigned staff list by name
        unsigned_staff_sorted = sorted(unsigned_staff)

        # Print sorted unsigned staff
        print("Staff who have not signed the document:", document_name)
        for name in unsigned_staff_sorted:
            print(name)

        return unsigned_staff_sorted
    except Exception as e:
        print(f"Error reading the spreadsheet: {e}")
        return []
    
print("Ensure you open the file first to ensure it has the latest changes synced.")

# Example usage:
file_path = "F:\pal files\OneDrive\Acknowledgement of Document Change.xlsx"  # Ensure correct file extension
document_name = "James Russon - Communication Passport"
sheet_name = "Sheet1"  # Update this if needed

check_unsigned_staff(file_path, sheet_name, document_name)