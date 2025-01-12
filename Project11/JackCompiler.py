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
    pattern = r'"[^"]*"|[^\s";,.()\[\]~\-\/]+|[.,;(){}\[\]~\-\/]|[-~](?=\w)|\/'
    
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

def change_extension_to_vm(file_path):
     # Create a Path object
    path = Path(file_path)
    
    # Change the file extension to .xml
    new_path = path.with_suffix('.vm')
    
    return new_path

# Create tokenized files of each jack file and return a dictionary containing the tokenized files by path {'path' : tokens[(token, type)]}
def find_jack_files(directory_path):
    tokens_Dict = {} 
    VMPaths = {}

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
            VMPaths[output_file_path] = change_extension_to_vm(output)
            lines = read_and_parse_file(output)
            tokens = tokenize(lines)
            tXML = tokenFile(tokens, output_file_path)
            tokens_Dict[output_file_path] = tokens
    return tokens_Dict, VMPaths

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

def lookAheadType():
    global currentToken
    return tokenPairs[currentToken+1][1]

def vmPeekAhead(index):
    return tokenPairs[index+1][0]

def lookBack():
    global currentToken
    return tokenPairs[currentToken-1][0]

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
    print("Compile new file " + currentFile)
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
    
    # For symbol table
    pairs = []

    # Next element must be static or field
    while(tokenPairs[currentToken][0] != ";"):
        # Fill array for symbol table
        tokenP = tokenPairs[currentToken]
        if tokenP[0] not in symbols:
            pairs.append(tokenP)
        # Loop up until ;
        printXMLToken()
        advanceToken()
    process(";")

    varType = pairs[1][0] #int
    kind = pairs[0][0]   #field/static
    # Add class vars to symbol table
    global classSB
    for i in range(2, len(pairs)):
        classSB.define(pairs[i][0], varType, kind, "Dec")
        
    # Go back up to parent
    Parent.pop()
    compileClassVarDec()

def compileSubroutine():
    t = currToken()

    if (t!= "constructor" and t!= "function" and t!= "method"):
        return

    # Create new local symbol table
    if (t== "constructor" or t== "function" or t== "method"):
        global localSB
        localSB.reset()

    # Set new depth
    global Parent
    subroutineDec = ET.SubElement(Parent.peek(), "subroutineDec")
    Parent.push(subroutineDec)
    
    meth = []
    subInfo = [None] * 4 #name, type , localArgs, argCount
    subInfo[2] = currentFile
    # Print (method|function|constructor) type routineName
    for i in range(0,3):
        t = currToken()
        if i == 2: # if void
            subInfo[0] = t
        if i == 0:
            subInfo[1] = t
        meth.append(t)
        printXMLToken()
        advanceToken()

    # Add this to subroutine table if method
    if meth[0] == "method":
        localSB.define("this", meth[1], "argument")


    VMCode.append(subInfo)
    index_of_subroutine = len(VMCode) - 1

    process("(")
    compileParameterList()
    subInfo[3] = classSB.varCount("field")
    process(")")
    compileSubroutineBody()
    
    localVarCount = localSB.varCount("local")
    subInfo[2] = localVarCount

    writeFunction(index_of_subroutine, subInfo)

    Parent.pop()
    compileSubroutine()

# The is not currently in use anymore
def compileParameterList(count = 0, firstFlag = True):
    global localSB
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
        return count
    else:
        if currTokenType() == "identifier" and lookAheadType() != "identifier":
            localSB.define(t, lookBack(), "argument")
            count += 1
        process(t)
    return compileParameterList(count, False)

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
    
    # For symbol table
    global localSB
    vars = []

    # Next element must be a var declaration
    t = currToken()
    while(t != ";"):
        if t not in symbols:
            vars.append(t)
        # Loop up until ;
        process(t)
        t = currToken()
    process(";")

    # First two indeces of vars are 'var' and type
    varType = vars[1] #int, char, Class
    # Add class vars to symbol table
    global classSB
    for i in range(2, len(vars)):
        #print(vars[i])
        localSB.define(vars[i], varType, "local", "Dec")

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
    t = currToken() # varName
    isArray = False
    if lookAhead() == "[":
        isArray = True
        if classSB.kindOf(t) != "NONE":
            writePush(classSB.kindOf(t), classSB.indexOf(t))
        elif localSB.kindOf(t) != "NONE":
            writePush(localSB.kindOf(t), localSB.indexOf(t))
    process(t)
    variableUsed = t
    #check array
    if currToken() == "[":
        process("[")
        compileExpression()
        VMCode.append("add")
        process("]")
    process("=")
    compileExpression()
    if isArray:
        VMCode.append("pop temp 0")
        VMCode.append("pop pointer 1")
        VMCode.append("push temp 0")
        VMCode.append("pop that 0")
    elif classSB.kindOf(t) != "NONE":
        writePop(classSB.kindOf(variableUsed), classSB.indexOf(variableUsed))
    elif localSB.kindOf(t) != "NONE":
        writePop(localSB.kindOf(variableUsed), localSB.indexOf(variableUsed))
    process(";")
    Parent.pop()

def compileIf():
    global ifWhileCounter
    L1 = ifWhileCounter
    L2 = L1+1
    ifWhileCounter += 2

    #print("If L1,L2 --" + str(L1) + "," + str(L2) )
    # Add depth
    global Parent
    ifStatement = ET.SubElement(Parent.peek(), "ifStatement")
    Parent.push(ifStatement)

    process("if")
    process("(")
    compileExpression()
    VMCode.append("not")
    writeIf("if-goto L" + str(L1))
    process(")")
    process("{")
    compileStatements()
    writeGoto("goto L" + str(L2))
    process("}")
    #check if there is an else statement
    t = currToken()
    writeLabel("L" + str(L1))
    if t == "else":
        process("else")
        process("{")
        compileStatements()
        process("}")
    writeLabel("L" + str(L2))
    Parent.pop()

def compileWhile():
    global ifWhileCounter
    L1 = ifWhileCounter
    L2 = L1+1
    ifWhileCounter += 2

    #print("While L1,L2 --" + str(L1) + "," + str(L2) )
    # Add depth
    global Parent
    whileStatement = ET.SubElement(Parent.peek(), "whileStatement")
    Parent.push(whileStatement)

    process("while")
    writeLabel("L" + str(L1))
    process("(")
    compileExpression()
    process(")")
    VMCode.append("not")
    process("{")
    writeIf("if-goto L" + str(L2))
    compileStatements()
    writeGoto("goto L" + str(L1))
    process("}")
    writeLabel("L" + str(L2))
    Parent.pop()

def compileDo():
    # Add depth
    global Parent
    doStatement = ET.SubElement(Parent.peek(), "doStatement")
    Parent.push(doStatement)

    # Going to be name(exp *,exp) or nameA.nameB(exp *,exp) or nameA.nameB.nameC etc
    call = []
    process("do")
    t = currToken()
    while (t !=  "("):
        call.append(t)
        process(t)
        t = currToken()
    process("(")
    count = compileExpressionList()
    #print("Do count: " + str(count))
    process(")")
    vmString = ""
    if len(call) == 1: #Method call that takes in the class. ie Math.double(this)
        vmString = currentFile + "." + call[0] 
        count = 1
        VMCode.append("push pointer 0")
    # if this is a method call on an obj variable ie square.new(); where field Square square
    elif classObj(call[0]):
        tab = whatTable(call[0])
        vmString = call[0].capitalize() + "." + call[2]
        tab = whatTable(call[0])
        if tab == "class":
            VMCode.append("push this " + str(classSB.indexOf(call[0])) )
            count = 1
        else:
            k = localSB.kindOf(call[0])
            VMCode.append("push " + k + " "+ str(localSB.indexOf(call[0])))
            vmString = localSB.typeOf(call[0]) + call[1] + call[2]
            count = 1
    else:
        for elem in call:
            vmString += elem
    writeCall(vmString, count)
    writePop("temp", 0)
    process(";")
    Parent.pop()

def whatTable(obj):
    if classSB.kindOf(obj) != "NONE":
        return "class"
    if localSB.kindOf(obj) != "NONE":
        return "local"

def classObj(obj):
    if classSB.kindOf(obj) != "NONE":
        return True
    if localSB.kindOf(obj) != "NONE":
        return True
    else:
        return False

def compileReturn():
    # Add depth
    global Parent
    returnStatement = ET.SubElement(Parent.peek(), "returnStatement")
    Parent.push(returnStatement)

    process("return")
    emptyReturn = True
    t = currToken()
    if t!= ";":
        emptyReturn = False
        compileExpression()
    process(";")
    writeReturn(emptyReturn)
    Parent.pop()

def compileExpression(first_call=True):
    expression = ET.SubElement(Parent.peek(), "expression")
    expression.text = "\n"
    Parent.push(expression)

    t = currToken()
    #print("Expression t: " + t)
    compileTerm()
    # Check for (op term)*
    t = currToken()
    if t in operators:
       op = t 
       process(t) # Should be the op
       compileTerm()
       #VMCode.append((t, "op"))
       writeArithmetic(t)
    Parent.pop()

def compileTerm(firstFlag = True):
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
        # This will go ahead for a term like a[i] where we are at a
        if lookAhead() == "[":
            # b[j] push b, push j, add
            if classSB.kindOf(t) != "NONE":
                writePush(classSB.kindOf(t), classSB.indexOf(t))
            elif localSB.kindOf(t) != "NONE":
                writePush(localSB.kindOf(t), localSB.indexOf(t))
            process(t)
            process("[")
            compileExpression(False)
            process("]")
            VMCode.append("add")
            VMCode.append("pop pointer 1")
            VMCode.append("push that 0")
            Parent.pop()
            return
        if lookAhead() == ".": # example : Keyboard.readInt("ENTER THE NEXT NUMBER: ");
            callString = t
            process(t)
            process(".")
            t = currToken()
            process(t)
            callString += "." + t
            # (
            t = currToken()
            process(t)
            count = compileExpressionList()
            process(")")
            Parent.pop()
            writeCall(callString, count)
            return
        if lookAhead() == "(":
            pass
    process(t)
    if t == "(":
        compileExpression(False)
        process(")")
    if t == "-" or t == "~":
        compileTerm()
        writeArithmetic(t, True)
    elif t != "(":
        if classSB.kindOf(t) != "NONE":
            writePush(classSB.kindOf(t), classSB.indexOf(t))
        elif localSB.kindOf(t) != "NONE":
            if t == "this":
                writePush("pointer",0)
            else:
                writePush(localSB.kindOf(t), localSB.indexOf(t))
        else:
            if ty == "stringConstant":
                writeString(t)
            else:
                writePush("constant", t)
        # VMCode.append((t, ty))
    Parent.pop()

def compileExpressionList():
    # Set new depth
    global Parent
    expressionList = ET.SubElement(Parent.peek(), "expressionList")
    expressionList.text = "\n"
    Parent.push(expressionList)

    count = 0

    t = currToken()
    #print("Expression list = " + t)
    while(t != ")"):
        if t == ",":
            process(",")
        else:  
            count += 1  
            compileExpression()
        t = currToken()
    Parent.pop()
    return count

def compileTokens(tokens, output_file):
    # Make these variables global so no passing around
    global tree
    global Parent
    global tokenPairs
    global currentFile
    global currentToken
    global VMCurrentToken
    global VMStack
    global VMCode
    global ifWhileCounter
    global classSB
    global localSB

    # Init
    root = ET.Element("class")
    tree = ET.ElementTree(root)
    tokenPairs  = tokens
    Parent = Stack()
    Parent.push(root)

    currentToken = 0
    VMCurrentToken = 0
    ifWhileCounter = 0
    currentFile = output_file.stem
    VMStack = Stack()
    VMCode = []
    # Symbol Tables
    classSB = SymbolTable()
    localSB = SymbolTable() 
    
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

    #classSB.define("a", "int", "field")
    classSB.print_elements("Class")
    localSB.print_elements("Local")

def writeVMFile(file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
    # Write each element of the array to the file
        global VMCode
        #file.write("***** My compile VM code, remove for submission *****\n")
        for item in VMCode:
            file.write(f"{item}\n") 

def writeString(s):
    for index, char in enumerate(s):
        if index == 0:
            VMCode.append("push constant " + str(len(s)))
            VMCode.append("call String.new 1")
        else:
            VMCode.append("call String.appendChar 2")
        VMCode.append("push constant " + str(ord(char)))
    VMCode.append("call String.appendChar 2")


def writePush(segment, index):
    if index == "this":
        VMCode.append("push pointer 0")
    elif segment == "field":
        VMCode.append("push this " + str(index))
    elif index == "true":
       VMCode.append("push constant 1")
       VMCode.append("neg")
    elif index == "false" or index == "null":
        VMCode.append("push constant 0")
    else:
        VMCode.append("push " + str(segment) + " " + str(index))

def writePop(segment, index):
    if segment == "field":
        VMCode.append("pop this " +  str(index))
    else:
        VMCode.append("pop " + segment +  " " +  str(index))

def writeArithmetic(command, term = False):
    if command == "*":
        VMCode.append("call Math.multiply 2")
    elif command == "/":
        VMCode.append("call Math.divide 2")
    elif command == "+":
        VMCode.append("add")
    elif command == "-":
        if term:
             VMCode.append("neg")
        else:
            VMCode.append("sub")
    elif command == "~":
        VMCode.append("not")
    elif command == "<":
        VMCode.append("lt")
    elif command == ">":
        VMCode.append("gt")
    elif command == "=":
        VMCode.append("eq")
    elif command == "&":
        VMCode.append("and")
    elif command == "|":
        VMCode.append("or")

def writeLabel(label):
    VMCode.append("label " + label)

def writeGoto(label):
    VMCode.append(label)

def writeIf(label):
    VMCode.append(label)

def writeCall(name, nArgs):
    VMCode.append("call " + name + " " + str(nArgs))


def writeFunction(index, subinfo):
    # Subinfo = [name, type , localArgs, size]
    if subinfo[1] == "constructor":
        print()
        VMCode[index] = ("function " + currentFile + "." + subinfo[0] + " " + str(subinfo[2]))
        VMCode.insert(index+1, "push constant " + str(subinfo[3]))
        VMCode.insert(index+2, "call Memory.alloc 1")
        VMCode.insert(index+3, "pop pointer 0")
    elif subinfo[1] == "method":
        VMCode[index] = ("function " + currentFile + "." + subinfo[0] + " " + str(subinfo[2]))
        VMCode.insert(index+1, "push argument 0")
        VMCode.insert(index+2, "pop pointer 0")
    else:
        VMCode[index] = (subinfo[1] + " " + currentFile + "." + subinfo[0] + " " + str(subinfo[2]))

def writeReturn(empty):
    if empty:
        writePush("constant", 0)
    VMCode.append("return")

class SymbolTable:
    def __init__(self):
        # Name: element
        self.elements = {}
        self.varIndex = 0
        self.argIndex = 0
        self.fieldIndex = 0
        self.staticIndex = 0

    def reset(self):
        self.elements = {}
        self.localIndex = 0
        self.argIndex = 0
        self.fieldIndex = 0
        self.staticIndex = 0

    def define(self, name, type, kind, usage = "Used"):
        index = self.varCount(kind)
        self.elements[name] = SBElement(name, type, kind, index, usage)
        self.increaseVarCount(kind)

    def varCount(self, kind):
        if kind == "local":
            return self.localIndex
        elif kind == "argument":
            return self.argIndex
        elif kind == "field":
            return self.fieldIndex
        elif kind == "static":
            return self.staticIndex

    def increaseVarCount(self, kind):
        if kind == "local":
            self.localIndex += 1
        elif kind == "argument":
            self.argIndex += 1
        elif kind == "field":
            self.fieldIndex += 1
        elif kind == "static":
            self.staticIndex += 1      

    def kindOf(self, name):
        if name in self.elements:
            return self.elements[name].kind
        else:
            return "NONE"

    def typeOf(self, name):
        return self.elements[name].type

    def indexOf(self, name):
        return self.elements[name].index

    def print_elements(self, which):
        print(f"\n\n***** {which} Symbol Table *****")
        for key, value in self.elements.items():
            print(f"{value}")
        print()

class SBElement:
    def __init__(self, name, type, kind, index, usage):
        self.name = name
        self.type = type   # int, char, bool, Class
        self.kind = kind   # static, field, arg, var, none
        self.index = index 
        self.usage = usage # Used OR Declared

    def __str__(self):
        return (f"Name: {self.name:<10}, "
                    f"Type: {self.type:<10}, "
                    f"Kind: {self.kind:<10}, "
                    f"Index: {self.index:<10}, "
                    f"Usage: {self.usage:<10}")

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
    vm_file_path = change_extension_to_vm(path)

    # Check if the path is a file or directory and process accordingly
    if os.path.isfile(path):
        print(f"Reading file: {path}")
        # Read and print file contents, filtered out to lines of code in an array
        lines = read_and_parse_file(path)
        tokens = tokenize(lines)
        tXML = tokenFile(tokens, output_file_path)
        print("Compiling file now...")
        compileTokens(tokens, output_file_path)
        print("Writing VM file now...")
        writeVMFile(vm_file_path)
    elif os.path.isdir(path):
        tDict, VMPaths = find_jack_files(path)
        print("Compiling files now...")
        # tDict = xml path : [tokens, vmpath]
        for key, value in tDict.items():
            compileTokens(value, key)
            writeVMFile(VMPaths[key])
    else:
        print(f"Error: The path {path} is neither a file nor a directory.")

if __name__ == "__main__":
    main()
