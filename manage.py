import os
import numpy as np
import cv2
import pytesseract
import streamlit as st
from PIL import Image

# Path for Tesseract executable
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# Function to detect text regions
def text_detect(img, ele_size=(8, 2)):
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    img_sobel = cv2.Sobel(img, cv2.CV_8U, 1, 0)
    _, img_threshold = cv2.threshold(img_sobel, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY)
    
    element = cv2.getStructuringElement(cv2.MORPH_RECT, ele_size)
    img_threshold = cv2.morphologyEx(img_threshold, cv2.MORPH_CLOSE, element)
    
    contours, hierarchy = cv2.findContours(img_threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    Rect = [cv2.boundingRect(i) for i in contours if i.shape[0] > 100]
    RectP = [(int(i[0] - i[2] * 0.08), int(i[1] - i[3] * 0.08), 
              int(i[0] + i[2] * 1.1), int(i[1] + i[3] * 1.1)) for i in Rect]
    return RectP

# Streamlit UI with styling enhancements
st.set_page_config(page_title="📝 AI-Powered Text Detection Tool", layout="centered", page_icon="🔍")
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Text Detection & Extraction</h1>", unsafe_allow_html=True)

st.sidebar.header("📂 Upload Files")
st.sidebar.write("Upload your image to begin text detection and extraction!")

uploaded_file = st.sidebar.file_uploader("Choose an image file", type=["png", "jpg", "jpeg", "bmp", "tiff", "webp"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if img is None:
        st.error("Invalid image format or file not found.")
    else:
        with st.spinner("Analyzing image and detecting text regions..."):
            rect = text_detect(img)

        extracted_text = ""
        rect_sorted = sorted(rect, key=lambda x: x[1])  # Sort regions from top to bottom

        # Progress indicator
        progress_bar = st.progress(0)
        total_regions = len(rect_sorted)

        for i, (x1, y1, x2, y2) in enumerate(rect_sorted, start=1):
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(img.shape[1], x2)
            y2 = min(img.shape[0], y2)
            
            roi = img[y1:y2, x1:x2]
            text = pytesseract.image_to_string(roi, config='--psm 6')
            extracted_text += text  # Concatenate text in order of appearance
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

            progress_bar.progress(i / total_regions)

        st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption="🔍 Text Regions Detected", use_column_width=True)
        
        st.subheader("Extracted Text")
        st.markdown("<pre style='background-color: #f5f5f5; padding: 15px; border-radius: 5px;'>"
                    f"{extracted_text}</pre>", unsafe_allow_html=True)

        # Download button with custom style
        st.download_button("📥 Download Extracted Text", extracted_text, file_name="extracted_text.txt")

        st.balloons()  # Celebratory effect after extraction!
else:
    st.info("Please upload an image file to begin text extraction.")
