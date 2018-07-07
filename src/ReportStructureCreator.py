#!/usr/bin/env python

import sys
import os
import argparse
import re
import json
import shutil
from io import StringIO
from collections import OrderedDict
from jinja2 import Template
from argparse import RawDescriptionHelpFormatter as help_formatter
from time import sleep

# to get directory where the script is
dir_path = os.path.dirname(os.path.realpath(__file__))

# structure for JSON valid keys
class JSON_KEYS:
    DIRECTORY = 'directory'
    FILE = 'file'
    CHILDREN = 'children'

# structure for node elements
class NODE_MEMBERS:
    NAME = 'name'
    TOCNAME = 'toc_name'
    TYPE = 'type'
    CHILDREN = 'children'

# structure for different file names
class SORT_NAMES:
    FILENAME = 0
    TOCNAME = 1

# helper functions
def get_type(path):
    ''' Returns TYPE for path.
    get_type(folder): 'directory'
    get_type(file): 'file'
    '''
    if os.path.isdir(path):
        return JSON_KEYS.DIRECTORY
    return JSON_KEYS.FILE

def is_json(filename):
    return filename.endswith('.json')

def read_json(path):
    ''' Opens + loads .json file, returns dictionary.
    read_json('valid_path.json')

    Exits if fails to open. Does ensure valid structure.
    '''
    try:
        with open(path, 'r') as f:
            path_dict = json.load(f)
            return path_dict
    except IOError as errmsg:
        if errmsg.errno == 21:  # IsADirectoryError
            raise TypeError("Specified JSON, gave folder: {}".format(path))
        sys.exit('Cannot open. Error: {}'.format(errmsg))

def delete_if_dir_exists(path):
    if os.path.isdir(path):
        if input('WARNING: dest_file already exists. Overwrite? (y/n)') != 'y':
            print('Exiting.')
            sys.exit()
        try:
            shutil.rmtree(path)
            sleep(0.1) # give time for OS to clean
            print('\nWARNING: Existing directory deleted.\n')
        except:
            print('\nERROR: Could not overwrite:\n')
            sys.exit(sys.exc_info()[0].__name__)

# node is one element inside loaded JSON tree structure
class Node(object):
    ''' Node Instance Class.
    node = Node(path_data)
    path_data > node position

    : param : self.name
    : param : self.toc_name > name for template table of content
    : param : self.type > directory, file
    : param : self.children

    method : node.get_dict() > return sorted dictionary
    '''
    def __init__(self, path_data):
        self.parent = None # root does not have a parent
    
        def sort_name_and_type(path_data):
            configuration_error = False

            if JSON_KEYS.DIRECTORY in path_data: # sort types
                self.type = JSON_KEYS.DIRECTORY
                names = path_data.get(JSON_KEYS.DIRECTORY, None)
            elif JSON_KEYS.FILE in path_data:
                self.type = JSON_KEYS.FILE
                names = path_data.get(JSON_KEYS.FILE, None)
            else: # no valid key name
                configuration_error = True

            if len(names) == 2: # file name and TOC Name in the list
                self.name = names[SORT_NAMES.FILENAME]
                self.toc_name = names[SORT_NAMES.TOCNAME]
            elif len(names) == 1: # only file name in the list
                self.name = names[SORT_NAMES.FILENAME]
                self.toc_name = None
            else: # to many or to few elements in the list
                configuration_error = True

            if configuration_error: # check is JSON valid for the script
                print('ERROR: wrong configuration file (JSON) format')
                sys.exit()

        sort_name_and_type(path_data)
        self.children = [
            Node(child) # use recursion to generate all nodes inside a tree
            for child in path_data.get(JSON_KEYS.CHILDREN, []) # files have children[] added to the node element
        ]
        for child in self.children:
            child.parent = self

    def get_dict(self): # use it to get a complete dictionary of the structure
        d = OrderedDict()
        d[NODE_MEMBERS.NAME] = self.name
        d[NODE_MEMBERS.TOCNAME] = self.toc_name
        d[NODE_MEMBERS.TYPE] = self.type
        d[NODE_MEMBERS.CHILDREN] = [child.get_dict() for child in self.children]
        return d

    def __iter__(self):
        for child in self.children:
            yield child

    def __repr__(self):
        return '<NODE: {} | TYPE:{}>'.format(self.name, self.type)

# object which links all nodes
class Tree(object):
    ''' Create a Tree Object from a valid json.
    tree = Tree(pathToJson)
    path_to_json: a valid path to a JSON file with a directory structure

    : param : self.root > returns tree root node
    : param : self.path > returns the absolute path were tree will be created

    Methods:
    tree.write_tree(destination) > creates direcotry structure on the disk
    tree.print_tree > console print of a tree and all nodes
    tree.print_django > stream tree html output to a correct template

    Properties:
    tree.as_dict > self.root.get_dict()
    '''

    def __init__(self, path_to_json):
        path_dict = read_json(path_to_json)
        self.root = Node(path_dict)
        self.path = None

    def write_tree(self, dest_path): # assume that the directoryes are not existing
        ''' Creates directory tree from root node.
        write_tree(dest_path)
        Will delete tree if exists.
        '''

        def make(dest_path, node):
            dest_path = os.path.join(dest_path, node.name)
            if node.type == JSON_KEYS.DIRECTORY:
                try:
                    os.makedirs(dest_path)
                except:
                    raise
            elif node.type == JSON_KEYS.FILE:
                with open(dest_path, 'a') as f: # 'a' is for creating a file
                    pass

            for child in node.children:
                make(dest_path, child)
        make(dest_path, self.root)
        self.path = dest_path
        print('''Directoryes and files located at:''')
        print(dest_path + '\n')

    @property
    def as_dict(self):
        return self.root.get_dict()

    def print_tree(self):
        print('=' * 40)
        print(self)

        def print_node(node, level=0):
            print('{level} {name}'.format(level='|' * level or '|', name=node.name))
            level += 1
            for child in node.children:
                print_node(child, level)

        print_node(self.root)

    def print_django(self): # this can be done better "a quick hack"
        string_stream = StringIO()
        default_space_offset = '        '
        number_of_spaces = '  '
        def print_node(node, level=1, dest_path=self.path):
            dest_path = os.path.join(dest_path, node.name)
            if node.type == JSON_KEYS.DIRECTORY and node.toc_name != None:
                print('{spaces}<li>'.format(
                    spaces= (number_of_spaces * level) + default_space_offset), 
                    file = string_stream)
                print('{spaces}<a href="./img/Default.htm" target="ContentFrame">{name}</a>'.format(
                    spaces= (number_of_spaces * level) + default_space_offset, 
                    name=node.toc_name), 
                    file = string_stream)
                print('{spaces}<ul>'.format(
                    spaces= (number_of_spaces * level) + default_space_offset),
                    file = string_stream)
                level += 1
            elif node.type == JSON_KEYS.FILE and node.toc_name != None:
                path_to_node_file = os.path.relpath(dest_path, dir_path).replace('\\', '/')
                print('{spaces}<li>'.format(
                    spaces= (number_of_spaces * level) + default_space_offset), 
                    file = string_stream)
                print('{spaces}<a href="{link}" target="ContentFrame">{name}</a>'.format(
                    spaces= (number_of_spaces * level) + default_space_offset, 
                    link=path_to_node_file, name = node.toc_name), 
                    file = string_stream)
                level += 1

            for child in node.children:
                print_node(child, level, dest_path)

            level -= 1
            if node.type == JSON_KEYS.DIRECTORY and node.toc_name != None:
                print('{spaces}</ul>'.format(
                    spaces= (number_of_spaces * level) + default_space_offset), 
                    file = string_stream)
                print('{spaces}</li>'.format(
                    spaces= (number_of_spaces * level) + default_space_offset), 
                    file = string_stream)
            elif node.type == JSON_KEYS.FILE and node.toc_name != None:
                print('{spaces}</li>'.format(
                    spaces= (number_of_spaces * level) + default_space_offset), 
                    file = string_stream)

        print_node(self.root)

        data = string_stream.getvalue()
        string_stream.close()
        return data

    def __repr__(self):
        return '<TREE: {}>'.format(self.root.name)


def main():
    usage = 'python ReportStructureCreator.py sourceFile.json [--source_file ] [--template_file ] [--html_file ] [--dest_file ] [--help]'
    description = '''
    ====================================================================================
    ReportStructureCreator - Tool for generating Report folder structure and html
    Version: {version}
    Author: {author}
    Project: {projectName}
    ProjectVersion: {projectVersion}

    small json input Example:
    "directory": ["Root Folder", "TOC RootName"],
    "children": ["file": ["File A-A-1", "checkExample.txt"]]
   ====================================================================================
    '''.format(version='V01.00.00', author='mate.vukic@gmail.com', projectName='Terminator', projectVersion='N/A')

    # command line arguments handeling
    parser = argparse.ArgumentParser(prog='ReportStructureCreator', description=description,
                                     usage=usage,
                                     formatter_class=help_formatter,
                                     )

    parser.add_argument("-i", "--source_file", type=str, default=os.path.join(dir_path, "default.json"), nargs='?',
                        help='file path to .json which contains directory structure, default: "default.json')

    parser.add_argument("-t", "--template_file", type=str, default=os.path.join(dir_path, "defaultTemplate.html"), nargs='?',
                        help='Jinja2-Template for creation of html index page, default: "defaultTemplate.html')

    parser.add_argument("-o", "--html_file", type=str, default=os.path.join(dir_path, "index.html"), nargs='?',
                        help='html to be created, default: index.html')

    parser.add_argument("-p", "--dest_file", type=str, nargs='?', default=os.path.join(dir_path, "ProjectRoot"),
                        help='file path to a directory where structure will be created, default: Path were script is executed + "ProjectRoot"')

    args_dict = vars(parser.parse_args())
    globals().update(args_dict)

    # ensure source_file exists, if not exit.
    exists = os.path.exists
    if not exists(source_file):
        print('=' * 40)
        parser.print_help()
        print('=' * 40)
        print('\nERROR: configuration file does not exist.\n')
        sys.exit()

    # if dest_file exists, prompt for overwrite before continuing.
    if exists(dest_file):
        delete_if_dir_exists(dest_file)

    # make a tree from JSON file with node elements
    tree = Tree(source_file)

    # create directory structure inside destitnation directory
    tree.write_tree(dest_file)

    with open(template_file) as f:
        template = Template(f.read())

    render = template.render(tree = tree)

    tree.print_tree()

    Html_file= open(html_file,"w")
    Html_file.write(render)
    Html_file.close

    print('Done.')

if __name__ == '__main__':
    main()
