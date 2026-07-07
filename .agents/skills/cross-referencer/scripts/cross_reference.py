import os
import sys
import argparse
import re
import pandas as pd

def find_column_by_patterns(df, patterns):
    """
    Finds a column in the dataframe that matches any of the given patterns (case-insensitive).
    """
    cols = [str(c).strip().lower() for c in df.columns]
    for pattern in patterns:
        for i, col in enumerate(cols):
            if pattern == col or col.endswith(' ' + pattern) or col.startswith(pattern + ' '):
                return df.columns[i]
    return None

def extract_channel_id(val):
    """
    Extracts a YouTube channel ID (UC...) from a string or URL.
    """
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
    """
    Normalizes a string (lowercase, stripped) for comparison.
    """
    if pd.isna(val):
        return ""
    return str(val).strip().lower()

def is_smart_match(target_name, block_name, target_url=None, block_url=None):
    """
    Performs a smart match between target and block channels using names, words, and handles.
    """
    t_name = normalize_string(target_name)
    b_name = normalize_string(block_name)
    
    if not t_name or not b_name:
        return False, ""
        
    # 1. Direct exact name match
    if t_name == b_name:
        return True, f"Exact Name Match ('{target_name}')"
        
    # 2. Significant word overlap
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
            
    # 3. Handle overlap if URLs are provided
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
            # Only match if the word is at least 4 characters long and is a significant part of the handle (at least 35%)
            if len(bw) >= 4 and bw in t_handle and len(bw) >= len(t_handle) * 0.35:
                return True, f"Handle Match (Block word '{bw}' matched Target handle '@{t_handle}')"
        for tw in t_words:
            if len(tw) >= 4 and tw in b_handle and len(tw) >= len(b_handle) * 0.35:
                return True, f"Handle Match (Target word '{tw}' matched Block handle '@{b_handle}')"
                
    return False, ""

def main():
    parser = argparse.ArgumentParser(
        description="Cross-reference a YouTube channel target list with a block list and filter out matches."
    )
    parser.add_argument('--target-list', required=True, help="Path to the channel target list Excel file (.xlsx)")
    parser.add_argument('--block-list', required=True, help="Path to the YT channel block list Excel file (.xlsx)")
    parser.add_argument('--output-path', default="Cleaned Block List.xlsx", help="Path to save the cleaned block list Excel file (.xlsx)")
    
    args = parser.parse_args()
    
    # Verify input files exist
    if not os.path.exists(args.target_list):
        print(f"Error: Target list file not found at '{args.target_list}'", file=sys.stderr)
        sys.exit(1)
        
    block_list_path = args.block_list
    if not os.path.exists(block_list_path):
        print(f"Error: Block list file not found at '{block_list_path}'", file=sys.stderr)
        sys.exit(1)
        
    print(f"Reading target list: {args.target_list}")
    try:
        df_target = pd.read_excel(args.target_list)
    except Exception as e:
        print(f"Error reading target list: {e}", file=sys.stderr)
        sys.exit(1)
        
    print(f"Reading block list: {block_list_path}")
    try:
        df_block = pd.read_excel(block_list_path)
    except Exception as e:
        print(f"Error reading block list: {e}", file=sys.stderr)
        sys.exit(1)
        
    print(f"Target list shape: {df_target.shape[0]} rows, {df_target.shape[1]} columns")
    print(f"Block list shape: {df_block.shape[0]} rows, {df_block.shape[1]} columns")
    
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
        print(f"Warning: No standard columns found in target list. Using first column '{target_id_col}' as ID/URL.")
        
    if not block_id_col and not block_url_col and not block_name_col:
        block_id_col = df_block.columns[0]
        print(f"Warning: No standard columns found in block list. Using first column '{block_id_col}' as ID/URL.")
        
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
            
    print(f"Loaded target references:")
    print(f"  - Unique Channel IDs: {len(target_ids)}")
    print(f"  - Unique Channel URLs: {len(target_urls)}")
    print(f"  - Unique Channel Names: {len(target_names)}")
    
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
    
    # Save cleaned block list
    output_path = args.output_path
    if not output_path.endswith('.xlsx'):
        output_path += '.xlsx'
        
    print(f"Saving cleaned block list to: {output_path}")
    try:
        df_cleaned.to_excel(output_path, index=False)
        print("Successfully saved cleaned block list.")
    except Exception as e:
        print(f"Error saving cleaned block list: {e}", file=sys.stderr)
        sys.exit(1)
        
    # Save eliminated channels list
    output_dir = os.path.dirname(output_path) or '.'
    eliminated_path = os.path.join(output_dir, "Eliminated Channels.xlsx")
    print(f"Saving eliminated channels list to: {eliminated_path}")
    try:
        df_eliminated.to_excel(eliminated_path, index=False)
        print("Successfully saved eliminated channels list.")
    except Exception as e:
        print(f"Error saving eliminated channels list: {e}", file=sys.stderr)
        sys.exit(1)
        
    # Print summary table
    print("\n### Execution Summary")
    print("| Metric | Value |")
    print("|---|---|")
    print(f"| Original Block List Rows | {df_block.shape[0]} |")
    print(f"| Channels Filtered Out | {df_eliminated.shape[0]} |")
    print(f"| Cleaned Block List Rows | {df_cleaned.shape[0]} |")
    print(f"| Cleaned Output File | {output_path} |")
    print(f"| Eliminated Channels File | {eliminated_path} |")

if __name__ == '__main__':
    main()