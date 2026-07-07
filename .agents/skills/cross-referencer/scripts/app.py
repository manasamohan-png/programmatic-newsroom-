import streamlit as st
import pandas as pd
import io
import os
import re
import sys

# Add the current directory to path so we can import cross_reference
sys.path.append(os.path.dirname(__file__))
try:
    from cross_reference import (
        find_column_by_patterns,
        extract_channel_id,
        normalize_string,
        is_smart_match
    )
except ImportError:
    # Fallback definitions if import fails
    def find_column_by_patterns(df, patterns):
        cols = [str(c).strip().lower() for c in df.columns]
        for pattern in patterns:
            for i, col in enumerate(cols):
                if pattern == col or col.endswith(' ' + pattern) or col.startswith(pattern + ' '):
                    return df.columns[i]
        return None

    def extract_channel_id(val):
        if pd.isna(val):
            return None
        val_str = str(val).strip()
        if re.match(r'^UC[a-zA-Z0-9_-]{22}$', val_str):
            return val_str
        match = re.search(r'youtube\.com/channel/(UC[a-zA-Z0-9_-]{22})', val_str, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def normalize_string(val):
        if pd.isna(val):
            return ""
        return str(val).strip().lower()

    def is_smart_match(target_name, block_name, target_url=None, block_url=None):
        t_name = normalize_string(target_name)
        b_name = normalize_string(block_name)
        if not t_name or not b_name:
            return False, ""
        if t_name == b_name:
            return True, f"Exact Name Match ('{target_name}')"
        stop_words = {
            'dr', 'the', 'lab', 'university', 'of', 'and', 'with', 'md', 'doctor', 'medicine', 
            'health', 'science', 'org', 'net', 'com', 'channel', 'youtube', 'yt', 'club', 'show', 
            'podcast', 'tv', 'vlog', 'vlogs', 'blog', 'blogs', 'official', 'network', 'media', 
            'group', 'center', 'clinic', 'hospital', 'institute', 'association', 'society', 
            'foundation', 'school', 'college', 'dept', 'department', 'division', 'program', 
            'project', 'system', 'systems', 'service', 'services', 'support', 'care', 'wellness', 
            'fitness', 'nutrition', 'diet', 'food', 'gut', 'stomach', 'digestive', 'gastro'
        }
        t_words = [w for w in re.findall(r'[a-z0-9]+', t_name) if len(w) >= 3 and w not in stop_words]
        b_words = [w for w in re.findall(r'[a-z0-9]+', b_name) if len(w) >= 3 and w not in stop_words]
        for tw in t_words:
            if tw in b_words:
                return True, f"Significant Word Match ('{tw}' found in both '{target_name}' and '{block_name}')"
        t_handle = ""
        if target_url:
            t_url_str = normalize_string(target_url)
            match = re.search(r'@([a-z0-9_-]+)', t_url_str)
            if match:
                t_handle = match.group(1)
        b_handle = ""
        if block_url:
            b_url_str = normalize_string(block_url)
            match = re.search(r'@([a-z0-9_-]+)', b_url_str)
            if match:
                b_handle = match.group(1)
        if t_handle:
            for bw in b_words:
                if len(bw) >= 4 and bw in t_handle and len(bw) >= len(t_handle) * 0.35:
                    return True, f"Handle Match (Block word '{bw}' matched Target handle '@{t_handle}')"
            for tw in t_words:
                if len(tw) >= 4 and tw in b_handle and len(tw) >= len(b_handle) * 0.35:
                    return True, f"Handle Match (Target word '{tw}' matched Block handle '@{b_handle}')"
        return False, ""

# Set page config
st.set_page_config(
    page_title="YouTube Channel Cross-Referencer",
    page_icon="📺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background-color: #FF0000;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #CC0000;
        box-shadow: 0 4px 12px rgba(255, 0, 0, 0.2);
    }
    .card {
        background-color: white;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .title-container {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    .title-icon {
        font-size: 40px;
        margin-right: 15px;
    }
    .title-text {
        font-size: 32px;
        font-weight: 800;
        color: #1a1a1a;
    }
    .subtitle-text {
        font-size: 16px;
        color: #666;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg", width=150)
    st.markdown("### About")
    st.markdown("""
    This tool cross-references a **YouTube Channel Target List** with a **Weekly YouTube Channel Block List** to filter out any target channels from the block list.
    
    It uses smart matching algorithms to detect matches by:
    1. **Channel ID** (direct or extracted from URL)
    2. **Channel URL**
    3. **Smart Name Match** (exact name or significant word overlap)
    4. **Handle Match** (matching words to handles)
    """)
    st.markdown("---")
    st.markdown("Created for **Alli Platform**")

# Main Content
st.markdown("""
    <div class="title-container">
        <span class="title-icon">📺</span>
        <span class="title-text">YouTube Channel Cross-Referencer</span>
    </div>
    <div class="subtitle-text">
        Clean your weekly YouTube channel block lists by removing target channels with smart matching.
    </div>
""", unsafe_allow_html=True)

# File Uploaders
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🎯 1. Target List")
    st.markdown("Upload the Excel file containing your target YouTube channels.")
    target_file = st.file_uploader("Choose Target List Excel file", type=["xlsx"], key="target")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🚫 2. Block List")
    st.markdown("Upload the weekly Excel file containing channels to be blocked.")
    block_file = st.file_uploader("Choose Block List Excel file", type=["xlsx"], key="block")
    st.markdown('</div>', unsafe_allow_html=True)

if target_file and block_file:
    st.markdown('<div class="card" style="text-align: center;">', unsafe_allow_html=True)
    st.markdown("### ⚙️ Process Files")
    st.markdown("Click the button below to run the smart cross-referencing and filtering algorithm.")
    run_button = st.button("Run Cross-Reference", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if run_button:
        with st.spinner("Processing files and running smart matching..."):
            try:
                # Read files
                df_target = pd.read_excel(target_file)
                df_block = pd.read_excel(block_file)

                # Identify columns in Target List
                target_id_col = find_column_by_patterns(df_target, ['channel id', 'channelid', 'id', 'youtube id', 'yt id'])
                target_url_col = find_column_by_patterns(df_target, ['channel url', 'channelurl', 'url', 'link', 'youtube url', 'yt url'])
                target_name_col = find_column_by_patterns(df_target, ['channel name', 'channelname', 'name', 'title', 'channel title'])
                
                # Identify columns in Block List
                block_id_col = find_column_by_patterns(df_block, ['channel id', 'channelid', 'id', 'youtube id', 'yt id', 'placement'])
                block_url_col = find_column_by_patterns(df_block, ['channel url', 'channelurl', 'url', 'link', 'youtube url', 'yt url'])
                block_name_col = find_column_by_patterns(df_block, ['channel name', 'channelname', 'name', 'title', 'channel title', 'placement name'])
                
                # Fallbacks if columns are not explicitly named
                if not target_id_col and not target_url_col and not target_name_col:
                    target_id_col = df_target.columns[0]
                    
                if not block_id_col and not block_url_col and not block_name_col:
                    block_id_col = df_block.columns[0]

                # Build target sets for matching
                target_ids = set()
                target_urls = set()
                target_names = set()
                
                # Populate target sets
                for _, row in df_target.iterrows():
                    if target_id_col and not pd.isna(row[target_id_col]):
                        val = str(row[target_id_col]).strip()
                        target_ids.add(val.lower())
                        extracted = extract_channel_id(val)
                        if extracted:
                            target_ids.add(extracted.lower())
                            
                    if target_url_col and not pd.isna(row[target_url_col]):
                        val = str(row[target_url_col]).strip()
                        target_urls.add(val.lower())
                        extracted = extract_channel_id(val)
                        if extracted:
                            target_ids.add(extracted.lower())
                            
                    if target_name_col and not pd.isna(row[target_name_col]):
                        target_names.add(normalize_string(row[target_name_col]))

                # Filter block list and track eliminated rows
                eliminated_rows = []
                cleaned_rows = []
                
                for _, row in df_block.iterrows():
                    matched = False
                    match_reason = ""
                    
                    # 1. Check Channel ID
                    if block_id_col and not pd.isna(row[block_id_col]):
                        val = str(row[block_id_col]).strip().lower()
                        extracted = extract_channel_id(row[block_id_col])
                        extracted_lower = extracted.lower() if extracted else None
                        
                        if val in target_ids:
                            matched = True
                            match_reason = f"Channel ID match ('{row[block_id_col]}')"
                        elif extracted_lower and extracted_lower in target_ids:
                            matched = True
                            match_reason = f"Extracted Channel ID match ('{extracted}')"
                            
                    # 2. Check Channel URL
                    if not matched and block_url_col and not pd.isna(row[block_url_col]):
                        val = str(row[block_url_col]).strip().lower()
                        extracted = extract_channel_id(row[block_url_col])
                        extracted_lower = extracted.lower() if extracted else None
                        
                        if val in target_urls or val in target_ids:
                            matched = True
                            match_reason = f"Channel URL match ('{row[block_url_col]}')"
                        elif extracted_lower and extracted_lower in target_ids:
                            matched = True
                            match_reason = f"Extracted ID from URL match ('{extracted}')"
                            
                    # 3. Check Smart Name/Word/Handle Match
                    if not matched:
                        # Iterate through target list to find any smart match
                        for _, target_row in df_target.iterrows():
                            t_name = target_row[target_name_col] if target_name_col else ""
                            b_name = row[block_name_col] if block_name_col else ""
                            t_url = target_row[target_url_col] if target_url_col else ""
                            b_url = row[block_url_col] if block_url_col else ""
                            
                            is_match, reason = is_smart_match(t_name, b_name, t_url, b_url)
                            if is_match:
                                matched = True
                                match_reason = reason
                                break
                                
                    if matched:
                        row_dict = row.to_dict()
                        row_dict['Elimination Reason'] = match_reason
                        eliminated_rows.append(row_dict)
                    else:
                        cleaned_rows.append(row)
                        
                df_cleaned = pd.DataFrame(cleaned_rows) if cleaned_rows else pd.DataFrame(columns=df_block.columns)
                df_eliminated = pd.DataFrame(eliminated_rows) if eliminated_rows else pd.DataFrame(columns=list(df_block.columns) + ['Elimination Reason'])

                # Display Metrics
                st.markdown("### 📊 Execution Summary")
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("Original Block List Rows", len(df_block))
                with m2:
                    st.metric("Channels Filtered Out", len(df_eliminated), delta=f"-{len(df_eliminated)}" if len(df_eliminated) > 0 else "0", delta_color="inverse")
                with m3:
                    st.metric("Cleaned Block List Rows", len(df_cleaned))

                # Create Excel files in memory for download
                cleaned_buffer = io.BytesIO()
                with pd.ExcelWriter(cleaned_buffer, engine='openpyxl') as writer:
                    df_cleaned.to_excel(writer, index=False)
                cleaned_data = cleaned_buffer.getvalue()

                eliminated_buffer = io.BytesIO()
                with pd.ExcelWriter(eliminated_buffer, engine='openpyxl') as writer:
                    df_eliminated.to_excel(writer, index=False)
                eliminated_data = eliminated_buffer.getvalue()

                # Download Buttons
                st.markdown("### 📥 Download Results")
                d1, d2 = st.columns(2)
                with d1:
                    st.download_button(
                        label="Download Cleaned Block List (.xlsx)",
                        data=cleaned_data,
                        file_name="Cleaned_Block_List.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                with d2:
                    st.download_button(
                        label="Download Eliminated Channels (.xlsx)",
                        data=eliminated_data,
                        file_name="Eliminated_Channels.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

                # Tabs for Previews
                st.markdown("### 🔍 Data Preview")
                tab1, tab2 = st.tabs(["Cleaned Block List Preview", "Eliminated Channels Preview"])
                
                with tab1:
                    st.dataframe(df_cleaned.head(100), use_container_width=True)
                    
                with tab2:
                    st.dataframe(df_eliminated.head(100), use_container_width=True)

            except Exception as e:
                st.error(f"An error occurred during processing: {e}")
else:
    # Show instructions when files are not uploaded
    st.markdown("""
    <div class="card" style="border-left: 5px solid #FF0000;">
        <h4>💡 How to use:</h4>
        <ol>
            <li>Upload your <b>Target List</b> Excel file in the left box.</li>
            <li>Upload your weekly <b>Block List</b> Excel file in the right box.</li>
            <li>Click the <b>Run Cross-Reference</b> button that appears.</li>
            <li>Download the cleaned block list and review the eliminated channels.</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
