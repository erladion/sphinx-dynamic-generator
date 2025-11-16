import os
import re
import yaml # Required for YAML front matter in MyST Markdown
from docutils.parsers.rst import Directive
from docutils import nodes
from sphinx.util import logging
from typing import Dict, List, Any


class MetadataDirective(Directive):
    """
    Parses a YAML block of custom metadata (order, content destination, etc.)
    and stores it in a custom Docutils node for the generator script to read.
    """
    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False

    def run(self):
        try:
            # Parse the content block as YAML
            metadata = yaml.safe_load("\n".join(self.content))
            if not metadata:
                metadata = {}
        except Exception as e:
            error = self.state_machine.reporter.error(
                f'Error parsing custom metadata YAML: {e}',
                nodes.literal_block(self.block_text, self.block_text), line=self.lineno
            )
            return [error]

        # Create a custom Docutils node to hold the metadata data.
        # This node will be ignored by the final HTML builder but is visible 
        # to your Python script during the Sphinx environment build phase.
        metadata_node = metadata_node_class(metadata=metadata)
        
        # Ensure the node is included in the document structure
        return [metadata_node]

# Define a custom node class to hold the metadata dictionary
# This is a standard Docutils approach for custom data.
class metadata_node_class(nodes.General, nodes.Element):
    pass

class MetadataEndDirective(Directive):
    has_content = False
    required_arguments = 0
    optional_arguments = 0
    
    def run(self):
        return []

logger = logging.getLogger(__name__)

# We will define them dynamically in the main function based on the passed root.
MASTER_INDEX_FILE = 'index_template.rst'
PLACEHOLDER = '<<DYNAMIC_CHAPTER_LINKS>>'
CHAPTERS_SUB_DIR = 'chapters'
GENERATED_INCLUDES_EXTENSION = '.rst'
FILES_TO_CLEANUP=[]

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
                logger.warning(f"  ⚠️ WARNING: Missing 'order=' in config file: {config_path}. Defaulting to 9999.")

            title_match = title_pattern.search(content)
            if title_match:
                config['title'] = title_pattern.search(content).group(1).strip()
            else:
                logger.warning(f"  ⚠️ WARNING: Missing 'title=' in config file: {config_path}. Using folder name.")

    except Exception as e:
        logger.error(f"  ❌ ERROR: Failed to read config {config_path}: {e}")
        return None
        
    return config

def extract_md_metadata(filepath: str) -> Dict[str, Any]:
    """Reads metadata (order and title) from YAML front matter in a Markdown file."""
    metadata = {
        'order': 9999,
        'title': None,
        'destination_file': None,
        'valid': True # Flag to track successful extraction of ORDER
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Regex to find the YAML front matter block (must be at the start)
        yaml_match = re.match(r'---\s*\n(.*?)\n---', content, re.DOTALL)
        
        if not yaml_match:
            logger.verbose(f"  ℹ️ INFO: Could not find a YAML style metadata block, trying rst style {filepath}.")        
            metadata = extract_rst_metadata(filepath)
        else:
            # Parse the YAML content
            data = yaml.safe_load(yaml_match.group(1)) or {}

            if isinstance(data.get('content_order'), int):
                metadata['order'] = data.get('content_order')
                metadata['valid'] = True
            else:
                logger.warning(f"  ⚠️ WARNING: Missing or non-integer 'content_order' in {filepath}. Defaulting to 9999.")
                metadata['valid'] = False # Must have order to be linked

            if isinstance(data.get('content_title'), str):
                metadata['title'] = data.get('content_title').strip()

            if isinstance(data.get('content_destination'), str):
                metadata['destination_file'] = data.get('content_destination').strip()       
    except Exception as e:
        logger.error(f"  ❌ ERROR: Failed to read Markdown metadata from {filepath}: {e}")
        metadata['valid'] = False

    return metadata    

def extract_rst_metadata(filepath: str) -> Dict[str, Any]:
    """Reads metadata (order and title) from the field list at the top of an RST file."""
    metadata = {
        'order': 9999,  # Default to last position if missing
        'title': None,
        'destination_file': None,
        'valid': True  # Flag to track successful extraction of ORDER
    }

    metadata_yaml_pattern = re.compile(
        r'^\.\.\s*metadata::\s*\n'
        r'(.*?)'
        r'(?=\n\S|\Z)',
        re.DOTALL | re.MULTILINE
    )

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            head_content = f.read(1000)

            yaml_match = metadata_yaml_pattern.search(head_content)

            if yaml_match:
                yaml_content = yaml_match.group(1)

                first_line = [line for line in yaml_content.splitlines() if line.strip()][0]
                indent = len(first_line) - len(first_line.lstrip())

                unindented_content = re.sub(r'^\s{' + str(indent) + '}', '', yaml_content, flags=re.MULTILINE)
                data = yaml.safe_load(unindented_content) or {}
                data = {key.lstrip(':'): value for key, value in data.items()}

                metadata['order'] = data.get('content_order', 9999)
                metadata['title'] = data.get('content_title')
                metadata['destination_file'] = data.get('content_destination')

                if metadata['order'] == 9999:
                    logger.warning(f"  ⚠️ WARNING: Missing ':content_order:' in {filepath}. Defaulting to order 9999.")
                    metadata['valid'] = False
    except Exception as e:
        logger.error(f"  ❌ ERROR: Failed to read RST metadata from {filepath}: {e}")
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

    logger.verbose(f"🔨 Processing directory: {directory_path}")
    
    items_to_link = []
    
    # Scan directory and collect metadata
    for item in sorted(os.listdir(directory_path)):
        full_path = os.path.join(directory_path, item)
        relative_path_name = os.path.join(chapter_relative_path, item)

        item_data = {
            'order': 9999,
            'title': None,
            'link_path': None,  # What to put in the toctree link
            'issues': False
        }

        # Sub chapter folders (Requires .chapterconf)
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
                logger.verbose(f"  📂 Merging content from container folder: {full_path}")

                # Append all files found in the subfolder (which are returned by the recursive call)
                # The 'link_path' for these items must be made RELATIVE TO THE CURRENT INDEX.RST.                
                for sub_item in sub_chapter_content:
                    # Adjust the link_path to be relative to the *current* directory_path index.rst
                    # e.g., if current index is chapter_A/index.rst, and the sub_item link is chapter_A_Sub/file,
                    # the new link path must be chapter_A_Sub/file
                    if sub_item['link_path']:
                        sub_item['link_path'] = os.path.join(item, sub_item['link_path'])
                        items_to_link.append(sub_item)

        # Content file (.md or .rst)
        elif item != 'index.rst':
            file_extension = os.path.splitext(item)[1].lower()
            
            metadata = None
            if file_extension == '.md':
                metadata = extract_md_metadata(full_path)
            elif file_extension == '.rst':
                metadata = extract_rst_metadata(full_path)
                
            if metadata:
                if metadata.get('destination_file'):
                    logger.verbose(f"  ⏩ Skipping {item}: Tagged for inclusion (:content_destination: found).")
                    continue

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
        
    # Sort items
    items_to_link.sort(key=lambda x: x['order'])

    # Generate toctree content
    toctree_entries = []
    issues_found = False
    
    for item in items_to_link:
        if item['issues']:
            issues_found = True
            
        display_title = item['title']
        link_path = item['link_path']

        # Note: Indentation (3 spaces) for links inside chapter index is added here
        if display_title and display_title != link_path:
            toctree_entries.append(f"   {display_title} <{link_path}>")
        else:
            # Simple syntax: just the path (Sphinx uses the document's internal title)
            toctree_entries.append(f"   {link_path}")
            
    # Write index.rst file
    # Read the title from the chapterconf if it exists (for prettier header)
    root_config = read_chapter_config(directory_path)

    if root_config:
        # Get the title for the index file from the last part of the path
        chapter_title = os.path.basename(directory_path)
        if root_config['title']:
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

        logger.verbose(f"  ✨ Index generated: {os.path.relpath(index_path, root_dir)} ({len(items_to_link)} links)")
        if issues_found:
            logger.info(f"  ⚠️ REVIEW REQUIRED: Issues found in files in {directory_path}.")
    else:
        logger.verbose(f"  ⏩ Skipping index generation for container directory: {directory_path}")

    return items_to_link

def update_master_index(root_dir: str, all_chapters: List[Dict[str, Any]]):
    """
    Reads the master index template, substitutes the top-level chapter links, 
    and writes the final live index.rst.
    """
    # Define paths relative to the passed root_dir
    index_file_exists = False
    if MASTER_INDEX_FILE is None:
        MASTER_INDEX_TEMPLATE_PATH = os.path.join(root_dir, MASTER_INDEX_FILE) 
        index_file_exists = os.path.exists(MASTER_INDEX_TEMPLATE_PATH)    
    
    MASTER_INDEX_PATH = os.path.join(root_dir, 'index.rst')
    
    # Links point to the index.rst files we generated in each top-level chapter folder.
    # We use the chapter folder name (path_name) and the constant CHAPTERS_SUB_DIR
    master_toctree_entries = "\n".join([
        # Indentation for links under the toctree directive in index.rst
        f"   {CHAPTERS_SUB_DIR}/{chapter['path_name']}/index" 
        for chapter in all_chapters
    ])
    
    try:
        # Read template file
        content = ""
        if index_file_exists:
            with open(MASTER_INDEX_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = f"""
|project| documentation
==================================

.. toctree::
   :maxdepth: 2
   :numbered:
   :caption: Chapters:

   <<DYNAMIC_CHAPTER_LINKS>>
"""

        # The substitution must occur after the existing toctree directive in the template.
        # We ensure a leading newline to separate options from links if not already present 
        # in the template content before the placeholder.
        if PLACEHOLDER in content:
            # We prepend a newline if needed, and substitute the content
            new_content = content.replace(PLACEHOLDER, f"\n{master_toctree_entries}\n")
        else:
            logger.error(f"❌ Error: Placeholder {PLACEHOLDER} not found in template '{MASTER_INDEX_TEMPLATE_PATH}'. Skipping master index update.")
            return

        # Write index file
        with open(MASTER_INDEX_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        logger.verbose(f"✅ Successfully updated master index at {os.path.relpath(MASTER_INDEX_PATH, root_dir)}.")

    except IOError as e:
        logger.error(f"❌ Fatal Error: Could not access or write files: {e}")


def generate_combined_includes(root_dir: str):
    """
    Scans recursively for RST files, reads their ':content_destination:' metadata, and 
    generates the inclusion list file at the designated location with 
    correct relative paths.
    """

    combined_files_map = {}

    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            # We only look at RST files for the dynamic include feature
            metadata = None
            if filename.endswith(GENERATED_INCLUDES_EXTENSION) and filename != 'index.rst':
                filepath = os.path.join(dirpath, filename)
                metadata = extract_rst_metadata(filepath)
            elif filename.endswith(".md") and filename != 'index.md':
                filepath = os.path.join(dirpath, filename)
                metadata = extract_md_metadata(filepath)

            if metadata is not None:
                dest_file_base = metadata.get('destination_file')
                order = metadata.get('order')

                if dest_file_base:
                    if dest_file_base not in combined_files_map:
                        combined_files_map[dest_file_base] = []
                    
                    # Store the FULL path to the source content file    
                    combined_files_map[dest_file_base].append({
                        'full_path': filepath,
                        'order': order
                    })

    logger.verbose("\n🔨 Generating dynamic include files...")
    if not combined_files_map:
        logger.verbose("⏩ No :content_destination: tags found in RST files. Skipping combined include generation.")
        return

    for dest_file_base, files_to_include in combined_files_map.items():
        files_to_include.sort(key=lambda x: x['order'])

        # Determine the full path of the generated inclusion list file
        output_file_path = os.path.join(root_dir, f"{dest_file_base}{GENERATED_INCLUDES_EXTENSION}")

        FILES_TO_CLEANUP.append(output_file_path)

        # Ensure the destination directory exists
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        include_directives = []

        # Define the starting directory for relative path calculation
        relative_start_dir = os.path.dirname(output_file_path)

        for file_data in files_to_include:
            source_content_path = file_data['full_path']

            # Calculate the path from the generated file's location to the source content file
            relative_include_path = os.path.relpath(source_content_path, relative_start_dir)

            include_directives.append(
                f".. include:: {relative_include_path}\n"
            )

        # Write the list of include directives to the new destination file
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write("\n\n".join(include_directives) + "\n")

        logger.verbose(f"✅ Generated inclusion list: {os.path.relpath(output_file_path, root_dir)} ({len(files_to_include)} content files)")    

def generate_files(app):
    logger.info("Generating dynamic indices and includes")
    ROOT_DIR = app.srcdir
    CHAPTERS_SUB_DIR = app.config.dynamic_handling_options.get("chapters_dir", "chapters")
    MASTER_INDEX_FILE = app.config.dynamic_handling_options.get("master_index_file", None)
    CHAPTERS_ROOT = os.path.join(ROOT_DIR, CHAPTERS_SUB_DIR)
    
    logger.verbose(f"▶️ Sphinx Dynamic Chapter Generator Initiated (Root: {ROOT_DIR})")
    
    if not os.path.isdir(CHAPTERS_ROOT):
        logger.error(f"❌ Error: Chapter root directory not found: {CHAPTERS_ROOT}")
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

    # Generate the combined inclusion files based on the :content_destination: tag
    generate_combined_includes(ROOT_DIR)
        
    # Final step: Update the master index
    update_master_index(ROOT_DIR, top_level_chapters)
    
    logger.verbose("\n✅ Generator Complete. ")

def cleanup(app, exception):
    for file in FILES_TO_CLEANUP:
        if os.path.exists(file):
            try:
                os.remove(file)
            except OSError as e:
                logger.warning(f"Could not delete generated file {file}")

def setup(app):
    def skip_node(self, node):
        """Standard handler that skips the node and all its children."""
        raise nodes.SkipNode

    def noop(self, node):
        """No-op handler for visiting/departing the node."""
        pass

    app.add_config_value('dynamic_handling_options', {}, 'env')

    # Add custom node and directive roles
    app.add_node(metadata_node_class, html=(skip_node, None), latex=(skip_node, None), text=(skip_node, None))
    
    # Register the directives
    app.add_directive('metadata', MetadataDirective)
    app.add_directive('metadata-end', MetadataEndDirective)

    app.connect('builder-inited', generate_files)
    app.connect('build-finished', cleanup)

    return {
        'version': '1.0',
        'parallel_read_safe': True,
        'parallel_write_safe': True
    }