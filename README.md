## Templateorator

Small Python CLI script to create desired directory structure with empty files from a JSON file and use the structure in Jinja2 static html template.

Purpose:
Script can be used to create small static web page with "toc tree" and links. Good for all kinds of reporting representation and data gathering.

##### Preconditions:
    - python must be installed (Version 3.6.5)
    - read and write privileges must be available in execution folder
    - correct html template must be available (example: defaultTemplate.html)

##### Example
    Example contains result of the script run with default settings

    preconditions for example run:
        ReportStructureCreator.py in the same directory as default.json, defaultTemplate.json and img directory

    run from CLI:
        python ReportStructureCreator.py

    output:
        index.html and ProjectRoot directory
        output files together with img directory make a full product of this script

    what to check in example:
        check TOC tree in index.html, check directory structure under ProjectRoot and check the structure of default.json

##### Usage:
    1. Create JSON file with correct structure: (-h for CLA description or check default.json)
        { directory/file : ["dir_name"/"file_name" , "name of entry in index-page"] }
            -> in case of directory: add "children:[{}]" for subdirectories and subfiles
            -> "name of entry in index-page" can be left out, then folder/file is created but not shown in TOC tree of html output file

    2. Run python script (-h for CLA description)
        python ReportStructureCreator.py [--source_file ] [--template_file ] [--html_file ] [--dest_file ] [--help]

    3. Check output file (index.html)

    4. Replace created empty files with a valid version of files

    5. Enjoy in your new static web page and data structure

 Note: You can adjust the width of the sidebar manually by left-clicking  in the bottom right corner of the sidebar, holding the mouse button down and dragging the mouse left or right
