-- Assembler written for nand2tetris chapter 6
-- Takes in a .asm file and converts to .hack
-- Command line prompt: "lua assembler.lua Program.asm(input) Program.hack(output)
-- Written by Sterling Salvaterra

----- C INSTRUCTION TABLES -----

-- Destination
-- Added MD due to v1-v2 changes in book, MA, DA, AMD added just in case they show up
local destTable = {
    ["M"]   = "001",
    ["D"]   = "010",
    ["DM"]  = "011",
    ["A"]   = "100",
    ["AM"]  = "101",
    ["AD"]  = "110",
    ["ADM"] = "111",
    ["MD"]  = "011",
    ["MA"]  = "101",
    ["DA"]  = "110",
    ["AMD"] = "111"
}
-- Jump Table
local jumpTable = {
    ["JGT"] = "001",
    ["JEQ"] = "010",
    ["JGE"] = "011",
    ["JLT"] = "100",
    ["JNE"] = "101",
    ["JLE"] = "110",
    ["JMP"] = "111"
}

-- Computation table
local compTable = {
    ["0"]   = "0101010",
    ["1"]   = "0111111",
    ["-1"]  = "0111010",
    ["D"]   = "0001100",
    ["A"]   = "0110000",
    ["!D"]  = "0001111",
    ["!A"]  = "0110001",
    ["-D"]  = "0001111",
    ["-A"]  = "0110011",
    ["D+1"] = "0011111",
    ["A+1"] = "0110111",
    ["D-1"] = "0001110",
    ["A-1"] = "0110010",
    ["D+A"] = "0000010",
    ["D-A"] = "0010011",
    ["A-D"] = "0000111",
    ["D&A"] = "0000000",
    ["D|A"] = "0010101",
    ["M"]   = "1110000",
    ["!M"]  = "1110001",
    ["-M"]  = "1110011",
    ["M+1"] = "1110111",
    ["M-1"] = "1110010",
    ["D+M"] = "1000010",
    ["D-M"] = "1010011",
    ["M-D"] = "1000111",
    ["D&M"] = "1000000",
    ["D|M"] = "1010101"
}

----- SYMBOL TABLE -----
local symbolTab = {
    ["R0"]     = "0",
    ["R1"]     = "1",
    ["R2"]     = "2",
    ["R3"]     = "3",
    ["R4"]     = "4",
    ["R5"]     = "5",
    ["R6"]     = "6",
    ["R7"]     = "7",
    ["R8"]     = "8",
    ["R9"]     = "9",
    ["R10"]    = "10",
    ["R11"]    = "11",
    ["R12"]    = "12",
    ["R13"]    = "13",
    ["R14"]    = "14",
    ["R15"]    = "15",
    ["SCREEN"] = "16384",
    ["KDB"]    = "24576",
    ["SP"]     = "0",
    ["LCL"]    = "1",
    ["ARG"]    = "2",
    ["THIS"]   = "3",
    ["THAT"]   = "4"
}

----- FUNCTIONS -----

-- Function that removes white space and empty lines 
local function removeWhitespace(input)
    -- Split the input string into lines
    local lines = {}
	
    -- matching lines up to carriage return or newline
    for line in input:gmatch("[^\r\n]+") do
        -- remove white space including tabs and newlines
        modified = string.gsub(line, "%s+", "")
        lines[#lines + 1] = modified
    end
 
    -- Concatenate lines back into a single string seperated by newline characters
    return table.concat(lines, "\n")
end

-- Function that removes comments
local function removeComments(input)
    -- Pattern to match comments starting with //
    local pattern = "//.-\n"  -- Matches // followed by anything (.-) until end of line (\n)

    -- Remove comments from input string
    local modifiedContent = input:gsub(pattern, "")

    return modifiedContent
end

-- Function that returns type of instruction
local function instructionType(instr)
    if instr:sub(1,1) == '@' then
        local secondChar = instr:sub(2,2)
	    -- Check if instruction has a symbol
        if secondChar:match('%a') then 
	        return "L"
        else
	        return "A"
        end
    else
        return "C"
    end
end

-- Function that takes an A instruction and returns the machine code conversion
-- Assumes that it is a @# and no longer symbolic
local function convertAInstruction(line)
    -- Remove first character from string("@")
    -- variable:sub(start, default=end), string.sub(variable,start,default=end)
    local numberSegment = line:sub(2)
    local num = tonumber(numberSegment)
    local binary_str = ""

    -- Convert nunber to 15-bit binary string
    for i = 0,14,1 do
        bit_value = num % 2 -- gives LSB
	    binary_str = bit_value .. binary_str
	    num = math.floor(num/2) -- bitshift
    end
    return "0"..binary_str
end

-- Function that takes a C instruction and returns the machine code conversion
local function convertCInstruction(line)
    local dest = "000"
    local comp = ""
    local jump = "000"
    -- Split line into its parts by ';' and '=', if no ';' or '=' keep line as is
    local parts = {}
    -- If there is no '=' then destination is null 
    local hasEquals = line:find("=") ~= nil
    -- DEBUG print(hasEquals)
    -- track progess of loop 
    firstLoop = true
    for part in line:gmatch("[^;=]+") do
       -- DEBUG print("Part: " .. part)
        if hasEquals == false then
            if firstLoop then
                comp = compTable[part]
            else
                jump = jumpTable[part]
            end
        elseif hasEquals == true then
            if firstLoop then
                if destTable[part] == nil then 
                    print(part .. " is not a valid destination")
                else
                    dest = destTable[part]
                end
            else
                comp = compTable[part]
            end
        end
        firstLoop = false
    end
    -- DEBUG print("Comp: " .. comp .." Dest: ".. dest.." Jump: " ..jump.. "\n")
    return "111".. comp .. dest .. jump
end

-- Function that leads the conversion from assembly to machine code
local function assembleBits(assembly)
    local lines = {}
    local type = ""
    for line in assembly:gmatch("[^\r\n]+") do
        type = instructionType(line)
        if type == "A" then
	        lines[#lines + 1] = convertAInstruction(line)
        elseif type == "C" then
            lines[#lines + 1] = convertCInstruction(line)
        else
	        lines[#lines + 1] = line
        end
    end
    -- Concatenate lines back into a single string seperated by newline characters
    return table.concat(lines, "\n")
end

-- Function that takes (LABELS) and assigns adds them to table, 
-- also removes (LABELS) from the input assembly code
local function firstPass(input)
    -- DEBUG print("First Pass")
    local lines = {}
    local line_number = 0
    for line in input:gmatch("[^\r\n]+") do
        if line:sub(1, 1) == '(' then
            -- Take (name) from inside Label
            local label = string.match(line, "%((.-)%)")
            if symbolTab[label] == nil then
                symbolTab[label] = line_number
            end
        else
            lines[#lines + 1] = line
            line_number = line_number + 1
        end
    end
    return table.concat(lines, "\n")
end

-- Function that takes sumbolic @Variable instructions and adds them to symbol table
-- Essentially adding the address(#) to a variable, a.k.a pointer
-- [Symbol] = address, @R0 == @0(memory address 0), user created variables start @16->
local function secondPass(input)
    -- DEBUG print("Second Pass")
    local lines = {}
    local address_num = 16
    for line in input:gmatch("[^\r\n]+") do
        if line:sub(1, 1) == '@' then
            -- Remove @
            local var = line:sub(2)
            -- if not in symbol table and is not @0, must be something like @R0 or @i
            if symbolTab[var] == nil then 
                if var:match('%a') then
                    symbolTab[var] = address_num
                    lines[#lines + 1] = "@"..symbolTab[var]
                    address_num = address_num + 1
                else
                    lines[#lines + 1] = line
                end
            else
                lines[#lines + 1] = "@"..symbolTab[var]
            end
        else
            lines[#lines + 1] = line
        end
    end
    return table.concat(lines, "\n")
end

----- FILE I/O -----

-- Input and output file names
local inputFileName = arg[1]
local outputFileName = arg[2]

-- Open the input file in read mode
local inputFile = io.open(inputFileName, "r")
if not inputFile then
    error("Could not open input file: " .. inputFileName)
end

-- Read all content from input file
local content = inputFile:read("*all")

-- Close the input file
inputFile:close()

-- Run asm file contents through functions
local noWhitespaces = removeWhitespace(content)
local noComments = removeComments(noWhitespaces)
-- Add (LABELS) into symbol table
local fp = firstPass(noComments)
-- Add @variables into symbol table 
local sp = secondPass(fp)

local assembled = assembleBits(sp)
local modifiedContent = assembled

-- Open the output file in write mode
local outputFile = io.open(outputFileName, "w")
if not outputFile then
    error("Could not open output file: " .. outputFileName)
end

-- Write modified content to the output file
outputFile:write(modifiedContent)

-- Close the output file
outputFile:close()

print("'Assembly file: " .. inputFileName .. " -> has been assembled into machine code: "  .. outputFileName .. "'")

