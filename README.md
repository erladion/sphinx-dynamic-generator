<p align="center">
    <img src="source/_static/logo.png" width="400"/>
</p>

A project for dynamically creating table of contents for Sphinx based on available content.

The base of the project is the generator.py which builds up the necessary index.rst files expected by Sphinx.
It does this based on metadata found in folders, subfolders and files in the chapters folder (this is the default, can be specified).

A Sphinx extension has also been built from this general idea, the extension is located at extensions/dynamic_handling.py
It registers a metadata directive with Sphinx, allowing the use of .. metadata:: along with properties. It also does what the generator.py script does but it does this using a Sphinx event, more preciesly the build-inited event, causing the generation to be run just before the actual build.

---
## Dynamic toc tree generation
The chapters folder can contain any number of folders and with any name.
What sets the ordering and naming of each chapter is the content of the .chapterconf file that exists in each subfolder.
If it exists the folder is treated as a chapter.
It should look like the following
```
[Chapter]
title = <Name of the chapter>
order = <Order, lower number places the chapter higher up>
```

Every .rst or .md file in each folder will be used as content.
Each file should contain a content_order and a content_title

For a .rst file it should look like the following 
```
.. metadata::
   :content_order: <Order of the content file in the chapter>
   :content_title: <Title of the content>
   :content_destination: <path to result file>
```
and for a .md file:
```
---
content_order: <Order of the content file in the chapter>
content_title: <Title of the content>
---
```

---
## Dynamic include example
Specifying the :content_destination: allows for the dynamic creation of content to be used with a .. include:: directive

Example:
```
chapters/
├── chapter3/
│   ├── include-example.rst // contains the .. include:: directive
|   ├── fileA-to-be-included.rst // contains the :content_destination: property
│   └── sub-dir/
│       └── fileB-to-be-included.rst // contains the :content_destination: property

In this example the file include-example.rst contains the directive
.. include:: testing-include.rst

And both fileA-to-be-included.rst and fileB-to-be-included.rst
have the :content_destination: chapters/chapter3/testing-include

This will make it so that the generator.py script will exclude both 
fileA-to-be-included.rst and fileB-to-be-included.rst from the 
toc tree creation and use them for creation of a new file called 
testing-include.rst
containing two include directives like this:

.. include:: fileA-to-be-included.rst

.. include:: sub-dir/fileB-to-be-included.rst
```

---
## Specifying chapters directory
Using **--chapters-dir** when using generator.py, or setting the **chapters_dir** option for the extension in conf.py.  
Example:
```
dynamic_handling_options = {
    "chapters_dir" : "chapters"
} 
```

---
## Top level index template
By default a index template is used for the top level index.rst file.

The default template looks like the following:
```
|project| documentation
==================================

.. toctree::
   :maxdepth: 2
   :numbered:
   :caption: Chapters:

<<DYNAMIC_CHAPTER_LINKS>>
```

It is possible to specify another template to be used during toc generation. The only requirement is the existence of the tag <<DYNAMIC_CHAPTER_LINKS>>
To do this either use the **--index-template** for the generator.py or set the **master_index_file** variable for the extension
