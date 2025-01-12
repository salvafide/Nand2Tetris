import xml.etree.ElementTree as ET
from xml.dom import minidom
from io import BytesIO
import argparse
import glob
import os
import re

from pathlib import Path

keywords = [
    "class",
    "constructor",
    "function",
    "method",
    "field",
    "static",
    "var",
    "int",
    "char",
    "boolean",
    "void",
    "true",
    "false",
    "null",
    "this",
    "let",
    "do",
    "if",
    "else",
    "while",
    "return"
]

symbols = [
    '{',
    '}',
    '(',
    ')',
    '[',
    ']',
    '.',
    ',',
    ';',
    '+',
    '-',
    '*',
    '/',
    '&',
    '|',
    '<',
    '>',
    '=',
    '~'
]

operators = [
    '+',
    '-',
    '*',
    '/',
    '&',
    '|',
    '<',
    '>',
    '='
]

# Reads through file, returns an array with filtered out code lines
def read_and_parse_file(file_path):
    """Read and parse the contents of the file, ignoring empty lines and comments."""
    in_multi_line_comment = False
    lines = []

    try:
        with open(file_path, 'r') as file:
            for line in file:
                stripped_line = line.strip()

                # Handle multi-line comments
                while '/*' in stripped_line or '*/' in stripped_line:
                    if in_multi_line_comment:
                        end_index = stripped_line.find('*/')
                        if end_index != -1:
                            in_multi_line_comment = False
                            stripped_line = stripped_line[end_index + 2:].strip()
                            if not stripped_line:
                                break  # Exit while loop if nothing left to process
                        else:
                            stripped_line = ''
                            break
                    else:
                        start_index = stripped_line.find('/*')
                        if start_index != -1:
                            end_index = stripped_line.find('*/', start_index)
                            if end_index != -1:
                                # Multi-line comment starts and ends on the same line
                                stripped_line = stripped_line[:start_index].strip()
                                stripped_line = stripped_line[end_index + 2:].strip()
                            else:
                                # Multi-line comment starts but does not end on this line
                                in_multi_line_comment = True
                                stripped_line = stripped_line[:start_index].strip()
                                if not stripped_line:
                                    break  # Skip this line as it contains only a comment

                if in_multi_line_comment:
                    continue  # Skip lines inside multi-line comments

                # Remove inline single-line comments
                if '//' in stripped_line:
                    stripped_line = stripped_line.split('//', 1)[0].strip()

                # Skip the line if it is empty after removing comments
                if stripped_line:
                    lines.append(stripped_line)

    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except IOError as e:
        print(f"Error: An I/O error occurred. Details: {e}")

    return lines

def is_integer(token):
    try:
        # Attempt to convert the token to an integer
        int(token)
        return True
    except ValueError:
        # If conversion fails, token is not an integer
        return False

# Return the token type, from the 5 base types
def tokenType(token):
    if token in symbols:
        return "symbol"
    elif token in keywords:
        return "keyword"
    elif is_integer(token):
        return "integerConstant"
    else:
        return "identifier"

# Tokenize array of code lines( (token, type) )
def tokenize(strings):
    """Tokenize an array of strings based on spaces, specific punctuation, and quoted elements, with special handling for parentheses and brackets."""
    # Regular expression to match quoted strings, words, and punctuation
    pattern = r'"[^"]*"|[^\s";,.()\[\]~\-]+|[.,;(){}\[\]~\-]|[-~](?=\w)'
    
    tokens = [] #(token, type)
    
    for string in strings:
        # Find all matches according to the pattern
        matches = re.findall(pattern, string)
        
        # Process each match
        for match in matches:
            if match.startswith('"') and match.endswith('"'):
                # Handle quoted strings by removing quotes
                tokens.append( (match[1:-1], "stringConstant") )  # Remove the surrounding quotes
            else:
                # Handle non-quoted strings and punctuation
                tokens.append( (match, tokenType(match)) )
    
    return tokens

# Write xml token file, takes in an array of pairs(token, type)
def tokenFile(tokens, output_file):
    # Create the root element
    root = ET.Element("tokens")

    # Iterate over the array and create a child element for each token
    for token in tokens:
        token_element = ET.SubElement(root, token[1])
        token_element.text = f" {token[0]} "

    # Create an ElementTree object from the root element
    tree = ET.ElementTree(root)

    # Root here is the root name, not tree root
    root, ext = os.path.splitext(output_file)
    # Create the new file name with 'T' before the extension
    new_name = f"{root}T{ext}"

    # THIS CODE IS TO MAKE THE XML PRINT WITH INDENTS("PRETTY")
    # Use a BytesIO buffer to capture the XML bytes
    buffer = BytesIO()
    tree.write(buffer, encoding='utf-8', xml_declaration=False)

    # Get the XML string from the buffer and decode it to a string
    xml_bytes = buffer.getvalue()
    xml_str = xml_bytes.decode('utf-8')

    # Pretty-print the XML
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="    ")

    # Remove the XML declaration from the pretty-printed string
    pretty_xml_lines = pretty_xml.splitlines()
    if pretty_xml_lines[0].startswith('<?xml'):
        pretty_xml_lines.pop(0)  # Remove the first line if it's the declaration
    pretty_xml_final = "\n".join(pretty_xml_lines)

    # Write the pretty-printed XML to a file
    with open(new_name, "w", encoding="utf-8") as fh:
        print(f"Writing file: {new_name}")
        fh.write(pretty_xml_final)

def change_extension_to_xml(file_path):
    # Create a Path object
    path = Path(file_path)
    
    # Change the file extension to .xml
    new_path = path.with_suffix('.xml')
    
    return new_path

# Create tokenized files of each jack file and return a dictionary containing the tokenized files by path {'path' : tokens[(token, type)]}
def find_jack_files(directory_path):
    tokens_Dict = {} 

    # Ensure the provided path is a directory
    if not os.path.isdir(directory_path):
        print(f"Error: The path '{directory_path}' is not a valid directory.")
        return
    
    # Create a pattern to match all .jack files in the directory
    pattern = os.path.join(directory_path, '*.jack')
    
    # Use glob to find all .jack files
    jack_files = glob.glob(pattern)
    
    if not jack_files:
        print("No .jack files found.")
    else:
        print("\nFound .jack files and writing token.xml files...")
        for file in jack_files:
            print(file)
            output = os.path.abspath(file)
            output_file_path = change_extension_to_xml(output)
            lines = read_and_parse_file(output)
            tokens = tokenize(lines)
            tXML = tokenFile(tokens, output_file_path)
            tokens_Dict[output_file_path] = tokens
    return tokens_Dict

def printXMLToken():
    global currentToken
    val = tokenPairs[currentToken][0]
    type = tokenPairs[currentToken][1]
    element = ET.SubElement(Parent.peek(), type)
    element.text = f" {val} "

def advanceToken():
    global currentToken
    currentToken += 1

def lookAhead():
    global currentToken
    return tokenPairs[currentToken+1][0]

def currToken():
    global currentToken
    t = tokenPairs[currentToken][0]
    return t

def currTokenType():
    global currentToken
    t = tokenPairs[currentToken][1]
    return t

def process(str):
    if (currToken() == str):
        printXMLToken()
    else:
        print("Syntax Error at " + str)
    # Get the next token
    advanceToken()

def compileClass():
    # <class> </class> is already added from init
    process("class")
    # Print ClassName and advance 1 token
    printXMLToken()
    advanceToken()
    process("{")
    compileClassVarDec()
    compileSubroutine()
    #This will error until other functions are completed.
    process("}")

def compileClassVarDec():
    t = currToken()
    if (t != "static" and t != "field"):
        return

    # Set new depth
    global Parent
    classVarDec = ET.SubElement(Parent.peek(), "classVarDec")
    Parent.push(classVarDec)
    
    # Next element must be static or field
    while(tokenPairs[currentToken][0] != ";"):
        # Loop up until ;
        printXMLToken()
        advanceToken()
    process(";")

    # Go back up to parent
    Parent.pop()
    compileClassVarDec()

def compileSubroutine():
    t = currToken()

    if (t!= "constructor" and t!= "function" and t!= "method"):
        return

    # Set new depth
    global Parent
    subroutineDec = ET.SubElement(Parent.peek(), "subroutineDec")
    Parent.push(subroutineDec)
    
    # Print (method|function|constructor) type routineName
    for i in range(0,3):
        t = currToken()
        printXMLToken()
        advanceToken()

    process("(")
    compileParameterList()
    process(")")
    compileSubroutineBody()

    Parent.pop()
    compileSubroutine()


def compileParameterList(firstFlag = True):
    # Set new depth
    global Parent
    if firstFlag:
        paramList = ET.SubElement(Parent.peek(), "parameterList")
        paramList.text = "\n"
        Parent.push(paramList)

    t = currToken()
    # If next token is ) return
    if (t == ")"):
        Parent.pop()
        return
    else:
        process(t)
    
    compileParameterList(False)

def compileSubroutineBody():
    # Set new depth
    global Parent
    subBody = ET.SubElement(Parent.peek(), "subroutineBody")
    Parent.push(subBody)

    process("{") 
    compileVarDec()
    compileStatements()
    process("}")
    Parent.pop()

def compileVarDec():
    t = currToken()
    if (t != "var"):
        return

    # Set new depth
    global Parent
    varDec = ET.SubElement(Parent.peek(), "varDec")
    Parent.push(varDec)
    
    # Next element must be a var declaration
    t = currToken()
    while(t != ";"):
        # Loop up until ;
        process(t)
        t = currToken()
    process(";")

    # Go back up to parent
    Parent.pop()
    compileVarDec()

def compileStatements(firstFlag = True):
    # Set new depth
    global Parent
    if firstFlag:
        statements = ET.SubElement(Parent.peek(), "statements")
        statements.text = "\n"
        Parent.push(statements)
    t = currToken()
    #print("Statement t: " + t)
    if(t=="let"):
        compileLet()
    elif(t=="do"):
        compileDo()
    elif(t=="if"):
        compileIf()
    elif(t=="while"):
        compileWhile()
    elif(t=="return"):
        compileReturn()
    else:
        Parent.pop()
        return
    
    compileStatements(False)

def compileLet():
    # Add depth
    global Parent
    letStatement = ET.SubElement(Parent.peek(), "letStatement")
    Parent.push(letStatement)

    # Print let and varName
    printXMLToken()
    advanceToken()
    printXMLToken()
    advanceToken()
    if currToken() == "[":
        process("[")
        compileExpression()
        process("]")
    process("=")
    compileExpression()
    process(";")
    Parent.pop()

def compileIf():
    # Add depth
    global Parent
    ifStatement = ET.SubElement(Parent.peek(), "ifStatement")
    Parent.push(ifStatement)

    process("if")
    process("(")
    compileExpression()
    process(")")
    process("{")
    compileStatements()
    process("}")
    #check if there is an else statement
    t = currToken()
    if t == "else":
        process("else")
        process("{")
        compileStatements()
        process("}")

    Parent.pop()

def compileWhile():
    # Add depth
    global Parent
    whileStatement = ET.SubElement(Parent.peek(), "whileStatement")
    Parent.push(whileStatement)

    process("while")
    process("(")
    compileExpression()
    process(")")
    process("{")
    compileStatements()
    process("}")

    Parent.pop()

def compileDo():
    # Add depth
    global Parent
    doStatement = ET.SubElement(Parent.peek(), "doStatement")
    Parent.push(doStatement)

    # Going to be name(exp *,exp) or nameA.nameB(exp *,exp) or nameA.nameB.nameC etc
    process("do")
    t = currToken()
    while (t !=  "("):
        process(t)
        t = currToken()
    process("(")
    compileExpressionList()
    process(")")
    process(";")
    Parent.pop()

def compileReturn():
    # Add depth
    global Parent
    returnStatement = ET.SubElement(Parent.peek(), "returnStatement")
    Parent.push(returnStatement)

    process("return")
    
    t = currToken()
    if t!= ";":
        compileExpression()
    process(";")
    Parent.pop()

def compileExpression():
    expression = ET.SubElement(Parent.peek(), "expression")
    expression.text = "\n"
    Parent.push(expression)

    t = currToken()
    #print("Expression t: " + t)
    compileTerm()
    # Check for (op term)*
    t = currToken()
    if t in operators:
       process(t) # Should be the op
       compileTerm()
    Parent.pop()

def compileTerm(firstFlag = True):
    # TODO lookahead to match the type of term
    global Parent
    if firstFlag:
        term = ET.SubElement(Parent.peek(), "term")
        term.text = "\n"
        Parent.push(term)

    t = currToken()
    #print("Term t: " + t)
    ty = currTokenType()
    #print("Type is: " + ty)

    if ty == "identifier":
        if lookAhead() == "[":
            process(t)
            process("[")
            compileExpression()
            process("]")
            Parent.pop()
            return
        if lookAhead() == ".": # example : Keyboard.readInt("ENTER THE NEXT NUMBER: ");
            process(t)
            process(".")
            t = currToken()
            process(t)
            # (
            t = currToken()
            process(t)
            count = compileExpressionList()
            process(")")
            Parent.pop()
            return
        if lookAhead() == "(":
            pass
    process(t)
    
    if t == "(":
        compileExpression()
        process(")")
    if t == "-" or t == "~":
        compileTerm()

    Parent.pop()


def compileExpressionList():
    # Set new depth
    global Parent
    expressionList = ET.SubElement(Parent.peek(), "expressionList")
    expressionList.text = "\n"
    Parent.push(expressionList)

    count = 1
    t = currToken()
    #print("Expression list = " + t)
    while(t != ")"):
        if t == ",":
            count += 1
            process(",")
        else:    
            compileExpression()
        t = currToken()
    Parent.pop()
    return count

def compileTokens(tokens, output_file):
    # Make these variables global so no passing around
    global tree
    global Parent
    global tokenPairs
    global currentToken

    # Init
    root = ET.Element("class")
    tree = ET.ElementTree(root)
    tokenPairs  = tokens
    Parent = Stack()
    Parent.push(root)
    currentToken = 0
    
    compileClass()

    # THIS CODE IS TO MAKE THE XML PRINT WITH INDENTS("PRETTY")
    # Use a BytesIO buffer to capture the XML bytes
    buffer = BytesIO()
    tree.write(buffer, encoding='utf-8', xml_declaration=False)

    # Get the XML string from the buffer and decode it to a string
    xml_bytes = buffer.getvalue()
    xml_str = xml_bytes.decode('utf-8')

    # Pretty-print the XML
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="    ")

    # Remove the XML declaration from the pretty-printed string
    pretty_xml_lines = pretty_xml.splitlines()
    if pretty_xml_lines[0].startswith('<?xml'):
        pretty_xml_lines.pop(0)  # Remove the first line if it's the declaration
    
    # Join the lines back together, filtering out empty lines
    pretty_xml_final = "\n".join(line for line in pretty_xml_lines if line.strip())

    # Write the pretty-printed XML to a file
    with open(output_file, "w", encoding="utf-8") as fh:
        print(f"Writing file: {output_file}")
        fh.write(pretty_xml_final)

class Stack:
    def __init__(self):
        self.items = []

    def is_empty(self):
        return len(self.items) == 0

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        else:
            raise IndexError("pop from empty stack")

    def peek(self):
        if not self.is_empty():
            return self.items[-1]
        else:
            raise IndexError("peek from empty stack")

    def size(self):
        return len(self.items)

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Open and read the contents of a file.")
    
    # Add argument for path (File or dir)
    parser.add_argument(
        'path', 
        type=str, 
        help="Path to the file or dir."
    )
    
    # Parse the arguments
    args = parser.parse_args()
    path = args.path
    
    # Change the file extension
    output_file_path = change_extension_to_xml(path)

    # Check if the path is a file or directory and process accordingly
    if os.path.isfile(path):
        print(f"Reading file: {path}")
        # Read and print file contents, filtered out to lines of code in an array
        lines = read_and_parse_file(path)
        tokens = tokenize(lines)
        tXML = tokenFile(tokens, output_file_path)
        print("Compiling xml files now...")
        compileTokens(tokens, output_file_path)
    elif os.path.isdir(path):
        tDict = find_jack_files(path)
        print("Compiling xml files now...")
        for key, value in tDict.items():
            compileTokens(value, key)
    else:
        print(f"Error: The path {path} is neither a file nor a directory.")


if __name__ == "__main__":
    main()
