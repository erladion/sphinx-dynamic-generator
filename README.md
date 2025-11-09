<p align="center">
    <img src="source/_static/logo.png" width="400"/>
</p>

Testing out sphinx generation from dynamically available content.

The base of the project is the generator.py which builds up the necessary index.rst files expected by sphinx.
It does this based on metadata found in folders, subfolders and files in the chapters folder (which is assumed to exist).

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
:content_order: <Order of the content file in the chapter>
:content_title: <Title of the content>
```
and for a .md file:
```
---
content_order: <Order of the content file in the chapter>
content_title: <Title of the content>
---
```
