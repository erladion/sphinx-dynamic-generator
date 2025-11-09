import os
import re
import argparse
from typing import Dict, List, Any
import yaml # Required for YAML front matter in MyST Markdown

# --- Configuration (Relative to the script execution path) ---
# These paths are set relative to the root directory passed via the command line argument.
# We will define them dynamically in the main function based on the passed root.

PLACEHOLDER = '<<DYNAMIC_CHAPTER_LINKS>>'
CHAPTERS_SUB_DIR = 'chapters'

# --- Utility Functions for Metadata ---

def read_chapter_config(path: str) -> Dict[str, Any]:
    """Reads the .chapterconf for title and order."""
    config_path = os.path.join(path, '.chapterconf') 
    
    if not os.path.exists(config_path):
        # This is okay if a directory doesn't need to be part of the navigation
        return None
    
    config = {'order': 9999, 'title': None}
    order_pattern = re.compile(r'^order\s*=\s*(\d+)', re.MULTILINE)
    title_pattern = re.compile(r'^title\s*=\s*(.*)', re.MULTILINE)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            order_match = order_pattern.search(content)
            if order_match:
                config['order'] = int(order_match.group(1))
            else:
                print(f"⚠️ WARNING: Missing 'order=' in config file: {config_path}. Defaulting to 9999.")

            title_match = title_pattern.search(content)
            if title_match:
                config['title'] = title_pattern.search(content).group(1).strip()
            else:
                print(f"⚠️ WARNING: Missing 'title=' in config file: {config_path}. Using folder name.")

    except Exception as e:
        print(f"❌ ERROR: Failed to read config {config_path}: {e}")
        return None
        
    return config

def extract_md_metadata(filepath: str) -> Dict[str, Any]:
    """Reads metadata (order and title) from YAML front matter in a Markdown file."""
    metadata = {
        'order': 9999,
        'title': None,
        'valid': True # Flag to track successful extraction of ORDER
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Regex to find the YAML front matter block (must be at the start)
        yaml_match = re.match(r'---\s*\n(.*?)\n---', content, re.DOTALL)
        
        if not yaml_match:
            print(f"⚠️ WARNING: Missing or malformed YAML front matter in {filepath}. Skipping.")
            metadata['valid'] = False
            return metadata
        
        # Parse the YAML content
        data = yaml.safe_load(yaml_match.group(1)) or {}
        
        order = data.get('content_order')
        title = data.get('content_title')

        if isinstance(order, int):
            metadata['order'] = order
        else:
            print(f"⚠️ WARNING: Missing or non-integer 'content_order' in {filepath}. Defaulting to 9999.")
            metadata['valid'] = False # Must have order to be linked

        if isinstance(title, str):
            metadata['title'] = title.strip()
            
    except Exception as e:
        print(f"❌ ERROR: Failed to read Markdown metadata from {filepath}: {e}")
        metadata['valid'] = False

    return metadata

def extract_rst_metadata(filepath: str) -> Dict[str, Any]:
    """Reads metadata (order and title) from the field list at the top of an RST file."""
    metadata = {
        'order': 9999,  # Default to last position if missing
        'title': None,
        'valid': True  # Flag to track successful extraction of ORDER
    }
    
    order_pattern = re.compile(r'^:content_order:\s*(\d+)', re.MULTILINE)
    title_pattern = re.compile(r'^:content_title:\s*(.*)', re.MULTILINE)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Read first 1000 characters (should cover metadata block)
            head_content = f.read(1000)
            
            # Extract Order (MANDATORY CHECK)
            order_match = order_pattern.search(head_content)
            if order_match:
                metadata['order'] = int(order_match.group(1))
            else:
                print(f"⚠️ WARNING: Missing ':content_order:' in {filepath}. Defaulting to order 9999.")
                metadata['valid'] = False

            # Extract Title (OPTIONAL CHECK)
            title_match = title_pattern.search(head_content)
            if title_match:
                metadata['title'] = title_match.group(1).strip()
            # If title is missing, the toctree will use the document's internal title.
                
    except Exception as e:
        print(f"❌ ERROR: Failed to read RST metadata from {filepath}: {e}")
        metadata['valid'] = False

    return metadata


def process_directory(root_dir: str, directory_path: str, chapter_relative_path: str = '') -> List[Dict[str, Any]]:
    """
    Recursively scans a directory for content files (.md/.rst) and sub-chapter 
    directories (.chapterconf), generates the index.rst for the current 
    directory, and returns the sorted list of items.
    """
    if not os.path.isdir(directory_path):
        return []

    print(f"\nProcessing directory: {directory_path}")
    
    items_to_link = []
    
    # 1. SCAN DIRECTORY and COLLECT METADATA
    for item in sorted(os.listdir(directory_path)):
        full_path = os.path.join(directory_path, item)
        relative_path_name = os.path.join(chapter_relative_path, item)

        item_data = {
            'order': 9999,
            'title': None,
            'link_path': None,  # What to put in the toctree link
            'issues': False
        }

        # Case A: SUB-CHAPTER FOLDER (Requires .chapterconf)
        if os.path.isdir(full_path):
            config = read_chapter_config(full_path)
            
            # Recursively process the sub-chapter first
            sub_chapter_content = process_directory(root_dir, full_path, relative_path_name)

            if config:    
                # Use the config data for linking in the parent index
                item_data.update({
                    'order': config['order'],
                    'title': config['title'] or item,
                    # Link to the generated index file inside the folder
                    'link_path': f"{item}/index"
                })
                items_to_link.append(item_data)
            else:
                print(f"  📂 Merging content from container folder: {full_path}")
                # Append all files found in the subfolder (which are returned by the recursive call)
                # The 'link_path' for these items must be made RELATIVE TO THE CURRENT INDEX.RST.
                
                for sub_item in sub_chapter_content:
                    # Adjust the link_path to be relative to the *current* directory_path index.rst
                    # e.g., if current index is chapter_A/index.rst, and the sub_item link is chapter_A_Sub/file,
                    # the new link path must be chapter_A_Sub/file
                    if sub_item['link_path']:
                        sub_item['link_path'] = os.path.join(item, sub_item['link_path'])
                        items_to_link.append(sub_item)

        # Case B: CONTENT FILE (.md or .rst)
        elif item != 'index.rst':
            file_extension = os.path.splitext(item)[1].lower()
            
            metadata = None
            if file_extension == '.md':
                metadata = extract_md_metadata(full_path)
            elif file_extension == '.rst':
                metadata = extract_rst_metadata(full_path)
                
            if metadata:
                if not metadata['valid']:
                    item_data['issues'] = True

                # Link to the filename base (no extension, relative to current index)
                filename_base = os.path.splitext(item)[0]
                item_data.update({
                    'order': metadata['order'],
                    'title': metadata['title'] or filename_base,
                    'link_path': filename_base
                })
                items_to_link.append(item_data)
        
    # 2. SORT ITEMS
    items_to_link.sort(key=lambda x: x['order'])

    # 3. GENERATE TOCTREE CONTENT
    toctree_entries = []
    issues_found = False
    
    for item in items_to_link:
        if item['issues']:
            issues_found = True
            
        display_title = item['title']
        link_path = item['link_path']

        # CORRECT SYNTAX: Custom Title <path> 
        # Note: Indentation (3 spaces) for links inside chapter index is added here
        if display_title and display_title != link_path:
            toctree_entries.append(f"   {display_title} <{link_path}>")
        else:
            # Simple syntax: just the path (Sphinx uses the document's internal title)
            toctree_entries.append(f"   {link_path}")
            
    # 4. WRITE THE INDEX.RST FILE
    
    # Get the title for the index file from the last part of the path
    chapter_title = os.path.basename(directory_path)
    # Read the title from the chapterconf if it exists (for prettier header)
    root_config = read_chapter_config(directory_path)
    if root_config and root_config['title']:
        chapter_title = root_config['title']
    
    # The parent index file path (e.g., source/chapters/my_chapter/index.rst)
    index_path = os.path.join(directory_path, 'index.rst')
    
    # Create header and toctree content
    header = f"{chapter_title}\n{'=' * len(chapter_title)}\n\n"

    # Ensure a blank line separates the options from the links
    toctree_content = (
        ".. toctree::\n"
        "   :maxdepth: 2\n"
        f"   :caption: {chapter_title} Content:\n\n"
        + "\n".join(toctree_entries) + "\n"
    )

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(toctree_content)

    print(f"  > Index generated: {os.path.relpath(index_path, root_dir)} ({len(items_to_link)} links)")
    if issues_found:
        print(f"‼️ REVIEW REQUIRED: Issues found in files in {directory_path}.")
        
    return items_to_link

# --- Master Index (Top-Level) Generation ---

def update_master_index(root_dir: str, all_chapters: List[Dict[str, Any]]):
    """
    Reads the master index template, substitutes the top-level chapter links, 
    and writes the final live index.rst.
    """
    # Define paths relative to the passed root_dir
    MASTER_INDEX_TEMPLATE_PATH = os.path.join(root_dir, 'index_template.rst') 
    MASTER_INDEX_PATH = os.path.join(root_dir, 'index.rst')
    
    # Links point to the index.rst files we generated in each top-level chapter folder.
    # We use the chapter folder name (path_name) and the constant CHAPTERS_SUB_DIR
    master_toctree_entries = "\n".join([
        # Indentation for links under the toctree directive in index.rst
        f"   {CHAPTERS_SUB_DIR}/{chap['path_name']}/index" 
        for chap in all_chapters
    ])
    
    try:
        # 1. READ from the template file
        with open(MASTER_INDEX_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        # The substitution must occur after the existing toctree directive in the template.
        # We ensure a leading newline to separate options from links if not already present 
        # in the template content before the placeholder.
        if PLACEHOLDER in content:
            # We prepend a newline if needed, and substitute the content
            new_content = content.replace(PLACEHOLDER, f"\n{master_toctree_entries}\n")
        else:
            print(f"❌ Error: Placeholder {PLACEHOLDER} not found in template '{MASTER_INDEX_TEMPLATE_PATH}'. Skipping master index update.")
            return

        # 2. WRITE to the live index file
        with open(MASTER_INDEX_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"✅ Successfully updated master index at {os.path.relpath(MASTER_INDEX_PATH, root_dir)}.")

    except IOError as e:
        print(f"❌ Fatal Error: Could not access or write files: {e}")
        
# --- Main Execution ---

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate Sphinx TOCTREE indices recursively.")
    parser.add_argument('--root-dir', type=str, default='.', 
                        help="The root directory containing the source files (e.g., '.' or '/tmp/source').")
    args = parser.parse_args()
    
    ROOT_DIR = args.root_dir
    CHAPTERS_ROOT = os.path.join(ROOT_DIR, CHAPTERS_SUB_DIR)
    
    print(f"--- Sphinx Dynamic Chapter Generator Initiated (Root: {ROOT_DIR}) ---")
    
    if not os.path.isdir(CHAPTERS_ROOT):
        print(f"❌ Fatal Error: Chapter root directory not found: {CHAPTERS_ROOT}")
        exit(1)
        
    top_level_chapters = []
    
    # Scan only the top level of the chapters root
    for item in os.listdir(CHAPTERS_ROOT):
        full_path = os.path.join(CHAPTERS_ROOT, item)
        
        # Only process directories that contain a .chapterconf file
        if os.path.isdir(full_path):
            config = read_chapter_config(full_path)
            if config:
                top_level_chapters.append({
                    'path_name': item,
                    'order': config['order'],
                    'title': config['title'] or item
                })
    
    # Sort top-level chapters
    top_level_chapters.sort(key=lambda x: x['order'])

    # Process all chapters recursively and generate their index files
    for chapter in top_level_chapters:
        chapter_path = os.path.join(CHAPTERS_ROOT, chapter['path_name'])
        process_directory(ROOT_DIR, chapter_path, chapter['path_name'])
        
    # Final step: Update the master index
    update_master_index(ROOT_DIR, top_level_chapters)
    
    print("\n--- Generator Complete. ---")