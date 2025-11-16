from ensurepip import version
import os
import sys
from pathlib import Path
import glob

sys.path.append(str(Path('extensions').resolve()))

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'SphinxGen'
copyright = '2025, erladion'
author = 'erladion'
version = "1.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'myst_parser', 
    'sphinx.ext.duration',
    'sphinx.ext.ifconfig',
    'env_config',
    'dynamic_handling'
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

numfig = True

myst_heading_anchors = 3

templates_path = ['_templates']
exclude_patterns = ['index_template.rst']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_logo = "_static/logo.png"
html_favicon = html_logo
html_theme = 'furo' # 'alabaster'
html_show_sphinx = False
html_css_files = ['style.css']
html_show_sourcelink = False
html_theme_options = { 
    "sidebar_hide_name": True,
}

dynamic_handling_options = {
    "chapters_dir" : "chapters"
}

html_js_files = ["js/furo-toc-persistence.js"]

should_include = True
production_build = False

def setup(app):
    app.add_config_value('should_include', should_include, 'env')
    app.add_config_value('production_build', production_build, 'env')

def getDynamicStaticPaths():
    # --- Dynamic html_static_path Configuration ---
    conf_dir = Path(os.path.abspath(os.path.dirname(__file__)))
    # Define the names of subfolders you want to treat as static asset directories
    # e.g., 'images', 'assets', 'static'
    static_folder_names = ['images', 'assets']

    dynamic_static_paths = []
    # Search for the specified folder names recursively in all subdirectories
    for folder_name in static_folder_names:
        # Use glob to find all folders with the target name
        # '**/' means recursive search through subdirectories
        search_pattern = str(conf_dir / '**' / folder_name)
        
        # glob.glob returns absolute paths, so we convert them back to 
        # paths relative to conf_dir, as required by html_static_path
        for found_path_abs in glob.glob(search_pattern, recursive=True):
            found_path = Path(found_path_abs)
            if found_path.is_dir():
                # Get the path relative to conf_dir and add it as a string
                relative_path = found_path.relative_to(conf_dir)
                dynamic_static_paths.append(str(relative_path))
    
    return dynamic_static_paths

html_static_path = ['_static'] + getDynamicStaticPaths()
html_static_path = list(set(html_static_path))

print(f"Sphinx found static paths: {html_static_path}")

latex_elements = {
    'preamble': r'''
\usepackage{graphicx}
''',
    
    # Custom maketitle definition to place the logo precisely between author and date.
    # We now use the internal LaTeX macros (\@title, \@author, \@date).
    'maketitle': r'''
\makeatletter
\begin{titlepage}
    \centering
    
    % --- 1. TITLE ---
    \Huge \bfseries \@title \par % Document Title (using internal macro)
    \vskip 4em

    % --- 2. AUTHOR ---
    \Large \@author \par % Author (using internal macro)
    \vskip 2em
    
    % --- 3. LOGO INSERTION POINT (CENTERED) ---
    \includegraphics[width=10cm]{logo.png} \par
    \vskip 2em % Space after logo
    
    % --- 4. DATE ---
    \Large \@date \par % Date (using internal macro)
    \vskip 4em
    
    \vfill % Pushes content to the top
\end{titlepage}
\makeatother
'''
}

rst_prolog = f"""
.. |project| replace:: {project}
.. |copyright| replace:: {copyright}
"""