# Now, create a Python script to read the PDF
# import os
# import pdfplumber

# script_dir = os.path.dirname(__file__) 

# # pdf_path = os.path.join(script_dir,"../../assets/linkedin/Profile.pdf")
# # pdf_path = os.path.abspath(pdf_path) 

# # print(f"Looking for PDF at: {pdf_path}")
# # full_text = ""

# # try:
# #     with pdfplumber.open(pdf_path) as pdf:
# #         print("success")
# # except FileNotFoundError:
# #     print(f"Error: Could not find the PDF file at the specified path.")
    
# # with pdfplumber.open(pdf_path) as pdf:
# #     for page in pdf.pages:
# #         full_text += page.extract_text() + "\n"

# # print(full_text)


# pdf_path2 = os.path.join(script_dir,"../../assets/linkedin/linkedin_projects.pdf")
# pdf_path2 = os.path.abspath(pdf_path2) 

# full_text2 = ""

# try:
#     with pdfplumber.open(pdf_path2) as pdf:
#         print("success")
# except FileNotFoundError:
#     print(f"Error: Could not find the PDF file at the specified path.")
    
# with pdfplumber.open(pdf_path2) as pdf:
#     for page in pdf.pages:
#         full_text2 += page.extract_text() + "\n"

# print(full_text2)


import fitz  # PyMuPDF
import easyocr
import io
import os
from PIL import Image
import json
import urllib.request

# --- CONFIGURATION ---
# Initialize the EasyOCR reader. This will download the model on the first run.
print("Initializing EasyOCR reader... (This may take a moment on the first run)")
reader = easyocr.Reader(['en']) # Specify English language
print("EasyOCR reader initialized successfully.")

# Use the robust method to define the path to your PDF
script_dir = os.path.dirname(os.path.abspath(__file__))
# IMPORTANT: Adjust this path based on your actual folder structure.
pdf_path = os.path.join(script_dir, "../../assets/linkedin/linkedin_projects.pdf")

# --- LLM Analysis Function ---
def analyze_text_with_llm(text_content):
    """
    Sends the extracted text to the Gemini LLM and returns its analysis.
    """
    # API key provided by the user.
    api_key = "AIzaSyA3oL10YVTzXGjmVJh-902_X9wAX5VB0aU" 
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    # The prompt instructs the LLM on how to process the text, as updated by the user.
    prompt = f"""
    Based *only* on the following text extracted from a document, please provide a concise summary.
    Describe the main subject and the likely purpose of the document.
    Also write about all the projects and the purpose of those projects as it will be used to write resume of the individual in question.
    Do not add any information that is not present in the text.

    Extracted Text:
    ---
    {text_content}
    ---
    """
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    print("\n--- Sending extracted text to LLM for analysis... ---")
    
    try:
        # Create and send the request
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                response_body = json.loads(response.read().decode('utf-8'))
                # Navigate through the response JSON to find the generated text
                if (response_body.get('candidates') and 
                    response_body['candidates'][0].get('content') and
                    response_body['candidates'][0]['content'].get('parts')):
                    
                    llm_response = response_body['candidates'][0]['content']['parts'][0]['text']
                    return llm_response
                else:
                    return "LLM response format was unexpected."
            else:
                return f"LLM API request failed with status code: {response.status}. Response: {response.read().decode('utf-8')}"
                
    except Exception as e:
        return f"An error occurred while contacting the LLM API: {e}"


# --- SCRIPT ---
print(f"Opening PDF: {pdf_path}")
all_extracted_text = []

try:
    # 1. OPEN THE PDF AND EXTRACT TEXT FROM IMAGES
    doc = fitz.open(pdf_path)
    print(f"PDF has {doc.page_count} pages.")

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        image_list = page.get_images(full=True)

        if not image_list:
            print(f"Page {page_num + 1}: No images found.")
            continue

        print(f"Page {page_num + 1}: Found {len(image_list)} images. Processing...")

        for image_index, img_info in enumerate(image_list, start=1):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            # 3. PERFORM OCR ON THE IMAGE USING EasyOCR
            try:
                # EasyOCR's readtext method can handle the raw image bytes directly
                results = reader.readtext(image_bytes)
                
                # Concatenate all the detected text fragments into a single string
                text = "\n".join([res[1] for res in results])

                if text.strip():
                    all_extracted_text.append(text.strip())
            except Exception as ocr_error:
                print(f"Could not perform OCR on image {image_index} on page {page_num + 1}. Reason: {ocr_error}")

    doc.close()

    # 4. COMBINE TEXT, SEND TO LLM, AND PRINT RESULTS
    if all_extracted_text:
        final_text = "\n".join(all_extracted_text)
        
        print("\n\n--- All Combined Text from Images (EasyOCR) ---")
        print(final_text)
        print("-------------------------------------------------")
        
        # Call the function to get the LLM's analysis
        llm_analysis = analyze_text_with_llm(final_text)
        
        # Print the analysis received from the LLM
        print("\n\n--- LLM Analysis of the Document ---")
        print(llm_analysis)
        print("------------------------------------")
        
    else:
        print("\nNo text was detected in any images, so no analysis was performed.")

except FileNotFoundError:
    print(f"ERROR: PDF file not found at {pdf_path}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")



