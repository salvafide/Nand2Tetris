-- VM Translator written for nand2tetris chapter 8
-- Takes in a .vm file and translates it into .asm
-- command line prompt: "lua VMTranslator.lua Filename.vm/DirectoryName"
-- Written by Sterling Salvaterra

local function filterContents(input)
    local lines = {}
    -- Iterate through content removing empty lines and comments
    for line in input:lines() do
        if not line:match("^%s*$") and not line:match("^%s*//") then
            lines[#lines + 1] = line
        end
    end
    return lines
end

-- Counts arithmetic operations to create unique labels.
counter = 0
local function arithmeticOp(instruction)
    counter = counter + 1
    local asm = ""
    asm = asm .. "//" .. instruction .. "\n"
    if instruction == "add" then
        asm = asm .. "@SP\n" .. "AM=M-1\n" .. "D=M\n" .. "@SP\n" .. "AM=M-1\n"
        asm = asm .. "M=D+M\n" .. "@SP\n" .. "M=M+1\n"
    elseif instruction == "sub" then
        asm = asm .. "@SP\n" .. "AM=M-1\n" .. "D=M\n" .. "@SP\n" .. "AM=M-1\n"
        asm = asm .. "M=M-D\n" .. "@SP\n" .. "M=M+1\n"
    elseif instruction == "neg" then
        asm = asm .. "@SP\n" .. "AM=M-1\n" .. "D=!M\n" .. "M=D+1\n" .. "@SP\n" .. "M=M+1\n" 
    elseif instruction == "lt" then
        asm = asm .. "@SP\nAM=M-1\nD=M\n@SP\nAM=M-1\nD=M-D\n"
        asm = asm .. "@SET_TRUE_" .. counter .. "\n" .. "D;JLT\n@SP\nA=M\nM=0\n"
        asm = asm .. "@END_"..counter .."\n" .. "0;JMP\n".."(SET_TRUE_".. counter..")\n"
        asm = asm .. "@SP\nA=M\nM=-1\n(END_" .. counter .. ")\n".. "@SP\nM=M+1\n"
    elseif instruction == "gt" then
        asm = asm .. "@SP\nAM=M-1\nD=M\n@SP\nAM=M-1\nD=M-D\n"
        asm = asm .. "@SET_TRUE_" .. counter .. "\n" .. "D;JGT\n@SP\nA=M\nM=0\n"
        asm = asm .. "@END_"..counter .."\n" .. "0;JMP\n".."(SET_TRUE_".. counter..")\n"
        asm = asm .. "@SP\nA=M\nM=-1\n(END_" .. counter .. ")\n".. "@SP\nM=M+1\n"
    elseif instruction == "eq" then
        asm = asm .. "@SP\nAM=M-1\nD=M\n@SP\nAM=M-1\nD=M-D\n"
        asm = asm .. "@SET_TRUE_" .. counter .. "\n" .. "D;JEQ\n@SP\nA=M\nM=0\n"
        asm = asm .. "@END_"..counter .."\n" .. "0;JMP\n".."(SET_TRUE_".. counter..")\n"
        asm = asm .. "@SP\nA=M\nM=-1\n(END_" .. counter .. ")\n".. "@SP\nM=M+1\n"   
    elseif instruction == "not" then
        asm = asm .. "@SP\n" .. "AM=M-1\n" .. "M=!M\n" .. "@SP\n" .. "M=M+1\n"
    elseif instruction == "and" then
        asm = asm .. "@SP\n" .. "AM=M-1\n" .. "D=M\n" .. "@SP\n".."AM=M-1\n"
        asm = asm .. "M=D&M\n" .. "@SP\n" .. "M=M+1\n"
    elseif instruction == "or" then
        asm = asm .. "@SP\n" .. "AM=M-1\n" .. "D=M\n" .. "@SP\n" .."AM=M-1\n"
        asm = asm .. "M=D|M\n" .. "@SP\n" .. "M=M+1\n"
    end
    return asm
end

local function pushConstant(value)
    local asm = ""
    asm = asm .. "//push constant " .. value .. "\n"
    asm = asm .. "@" .. value .. "\n"
    asm = asm .. "D=A\n".."@SP\n".."A=M\n".."M=D\n".."@SP\n".."M=M+1\n"
    return asm
end

local segments = {
    ["local"] = "LCL",
    ["argument"] = "ARG",
    ["this"] = "THIS",
    ["that"] = "THAT"
}

----- PUSH FUNCS -----
local function pushSegment(segment, value)
    local asm = "//push " .. segment .." " ..value .. "\n"
    asm = asm .. "@" .. value .. "\n" .. "D=A\n"
    asm = asm .. "@" ..segments[segment] .."\nA=D+M\n" .. "D=M\n".. "@SP\n"
    asm = asm .. "A=M\n" .."M=D\n".."@SP\n" .. "M=M+1\n"
    return asm
end

local function pushTemp(value)
    local tempAddr = 5 + tonumber(value)
    local asm = "//push temp " .. value .. "\n"
    asm = asm .. "@" .. tempAddr .. "\n" .. "D=M\n"
    asm = asm .. "@SP\n" .. "A=M\n" .. "M=D\n" .. "@SP\n" .. "M=M+1\n" 
    return asm
end

local function pushPointer(value)
    local pAddr = 3 + tonumber(value)
    local asm = "//push pointer " .. value .. "\n"
    asm = asm .. "@" .. pAddr .. "\n" .. "D=M\n"
    asm = asm .. "@SP\n" .. "A=M\n" .. "M=D\n" .. "@SP\n" .. "M=M+1\n" 
    return asm
end

local function pushStatic(value, fileName)
    local conversion = fileName .. "." ..value
    local asm = "//push static " .. value .. "\n"
    asm = asm .. "@" .. conversion .. "\n" .. "D=M\n"
    asm = asm .. "@SP\n" .. "A=M\n" .. "M=D\n" .. "@SP\n" .. "M=M+1\n"
    return asm
end

----- POP FUNCS -----
local function popSegment(segment, value)
    local asm = "//pop " .. segment .. " ".. value .. "\n"
    asm = asm .. "@"..value .. "\n" .. "D=A\n"
    asm = asm .. "@" .. segments[segment] .. "\n" .. "D=D+M\n"
    asm = asm .. "@SP\n" .. "AM=M-1\n" .. "D=D+M\n".."A=D-M\n".."M=D-A\n"
    return asm
end

local function popTemp(value)
    local tempAddr = 5 + tonumber(value)
    local asm = "//pop temp ".. value .. "\n"
    asm = asm .. "@" .. tempAddr .. "\n" .. "D=A\n"
    asm = asm .. "@SP\n" .. "AM=M-1\n".. "D=D+M\n".."A=D-M\n" .. "M=D-A\n"
    return asm
end

local function popPointer(value)
    local pAddr = 3 + tonumber(value)
    local asm = "//pop pointer ".. value .. "\n"
    asm = asm .. "@" .. pAddr .. "\n" .. "D=A\n"
    asm = asm .. "@SP\n" .. "AM=M-1\n".. "D=D+M\n".."A=D-M\n" .. "M=D-A\n"
    return asm
end

local function popStatic(value, fileName)
    local conversion = fileName .. "." ..value
    local asm = "//pop static " .. value .. "\n"
    asm = asm .. "@" .. conversion .. "\n" .. "D=A\n"
    asm = asm .. "@SP\n" .. "AM=M-1\n" .. "D=D+M\n" .. "A=D-M\n" .. "M=D-A\n"
    return asm
end

----- PUSH/POP DIRECTING -----
local function pushInstruction(line, fileName)
    -- Break down line into its 3 parts, 
    -- S parses char, s parses white space; inverses of each other
    instruction, segment, value = line:match("(%S+)%s+(%S+)%s+(%S+)")
    local asm = ""
    if segment == "constant" then
        asm = asm .. pushConstant(value)
    elseif segment == "local" or segment == "argument" or segment == "this" or segment == "that" then
        asm = asm .. pushSegment(segment, value)
    elseif segment == "temp" then
        asm = asm .. pushTemp(value)
    elseif segment == "pointer" then
        asm = asm .. pushPointer(value)
    elseif segment == "static" then
        asm = asm .. pushStatic(value, fileName)
    end
    return asm
end

local function popInstruction(line, fileName)
    -- Break down line into its 3 parts
    instruction, segment, value = line:match("(%S+)%s+(%S+)%s+(%S+)")
    local asm = ""
    if segment == "local" or segment == "argument" or segment == "this" or segment == "that" then
        asm = asm .. popSegment(segment, value)
    elseif segment == "temp" then
        asm = asm .. popTemp(value)
    elseif segment == "pointer" then
        asm = asm .. popPointer(value)
    elseif segment == "static" then
        asm = asm .. popStatic(value, fileName)
    end
    return asm
end

----- BRANCHING INSTRUCTIONS -----

--change label into (function$LABEL)
local function convertLabel(id)
    local nL = "$" .. id 
    if curr_func ~= "" then
        nL = curr_func .. nL
    end
    return nL
end

local function label(line)
    local instruction, id = line:match("(%S+)%s+(%S+)")
    local asm = "// " .. instruction .. " " .. id .. "\n"
    asm = asm .. "(" .. convertLabel(id) ..")".. "\n"
    return asm
end

local function goTo(line)
    local instruction, id = line:match("(%S+)%s+(%S+)")
    local asm = "// " .. instruction .. " " .. id .. "\n"
    asm = asm .. "@" .. convertLabel(id) .. "\n"
    asm = asm .. "0;JMP\n"
    return asm
end

local function ifGoTo(line)
    local instruction, id = line:match("(%S+)%s+(%S+)")
    local asm = "//" .. instruction .. " " .. id .. "\n"
    asm = asm .. "@SP\n".."AM=M-1\n" .. "D=M\n"
    asm = asm .. "@" .. convertLabel(id) .. "\n"
    asm = asm .. "D;JNE\n"
    return asm
end

----- FUNCTIONS -----

-- store function called by [id<string> : count]
functions_called = {}

-- store current function name to use for return label
curr_func = ""

-- call f nArgs command
local function functionCall(line)
    -- id is the function being called, curr_func is the caller
    local id, nArgs = line:match("%S+%s+(%S+)%s+(%S+)")
    if functions_called[curr_func] then
        functions_called[curr_func] = functions_called[curr_func] + 1
    else
        functions_called[curr_func] = 1
    end
    local ret_add =  curr_func .. "$" .. "RET$" .. functions_called[curr_func]
    local asm = "//call " .. id .. " " .. nArgs.. "\n"
    asm = asm .."@" .. ret_add.. "\n" .. "D=A\n" .. "@SP\n".."A=M\n" .."M=D\n"
    asm = asm .."@SP\n" .. "M=M+1\n"
    asm = asm .."@LCL\n".."D=M\n".."@SP\n".."A=M\n".."M=D\n".."@SP\n".."M=M+1\n"
    asm = asm .."@ARG\n".."D=M\n".."@SP\n".."A=M\n".."M=D\n".."@SP\n".."M=M+1\n"
    asm = asm .."@THIS\n".."D=M\n".."@SP\n".."A=M\n".."M=D\n".."@SP\n".."M=M+1\n"
    asm = asm .."@THAT\n".."D=M\n".."@SP\n".."A=M\n".."M=D\n".."@SP\n".."M=M+1\n"
    asm = asm .."@5\n".."D=A\n".."@"..nArgs.."\n".."D=D+A\n".."@SP\n".."D=M-D\n"
    asm = asm .. "@ARG\n" .. "M=D\n"
    asm = asm .. "@SP\n".."D=M\n".."@LCL\n".."M=D\n"
    asm = asm .. "@"..id .."\n".. "0;JMP\n"
    asm = asm .. "("..ret_add..")\n"
    return asm
end

-- function f nVars command
local function functionComm(line, fileName)
    local id, nVars = line:match("%S+%s+(%S+)%s+(%S+)")
    curr_func = id
    local asm = "//function " .. id  .. " " .. nVars .. "\n"
    asm = asm .. "(" .. id .. ")" .. "\n"
    asm = asm .. "@" .. nVars .. "\n" .. "D=A\n" .."@13\n".."M=D\n".."(" .. id .. ".pLOOP)\n"
    asm = asm .. "@13\n".. "MD=M-1\n" .. "@"..id..".BREAK\n" .. "D;JLT\n"
    asm = asm .. pushConstant("0")
    asm = asm .. "@" .. id .. ".pLOOP\n" .. "0;JMP\n"
    asm = asm .. "(" .. id .. ".BREAK)\n"
    return asm
end

-- return command
local function returnComm()
    local asm = "//return\n"
    asm = asm .. "@LCL\n".."D=M\n" .."@13\n" .. "M=D\n" .. "@14\n" .. "M=D\n"
    asm = asm .. "@5\n" .. "D=A\n".."@14\n" .. "AM=M-D\n" .."D=M\n".."@14\n".."M=D\n"
    asm = asm .. "@SP\n".. "AM=M-1\n" .. "D=M\n" .. "@ARG\n".. "A=M\n" .. "M=D\n"
    asm = asm .. "@ARG\n".."D=M+1\n".."@SP\n".."M=D\n"
    asm = asm .. "@13\n" .. "AM=M-1\n" .. "D=M\n" .. "@THAT\n".. "M=D\n"
    asm = asm .. "@13\n" .. "AM=M-1\n" .. "D=M\n" .. "@THIS\n".. "M=D\n"
    asm = asm .. "@13\n" .. "AM=M-1\n" .. "D=M\n" .. "@ARG\n" .. "M=D\n"
    asm = asm .. "@13\n" .. "AM=M-1\n" .. "D=M\n" .. "@LCL\n" .. "M=D\n"
    asm = asm .. "@14\n" .. "A=M\n".."0;JMP\n" 
    return asm
end

----- SORT INSTRUCTIONS -----
local function parseCode(input, fileName)
    local asm = ""
    -- For each line in VM file, translate into asm code
    for _, line in ipairs(input) do
        -- split line by white space
        local instruction = line:match("%S+")
        if instruction == "label" then
            asm = asm .. label(line)
        elseif instruction == "if-goto" then
            asm = asm .. ifGoTo(line)
        elseif instruction == "goto" then
            asm = asm .. goTo(line)
        elseif instruction == "push" then
            asm = asm .. pushInstruction(line, fileName)
        elseif instruction == "pop" then
            asm = asm .. popInstruction(line, fileName)
        elseif instruction == "function" then
            asm = asm .. functionComm(line, fileName)
        elseif instruction == "call" then
            asm = asm ..functionCall(line)
        elseif instruction == "return" then
            asm = asm .. returnComm()
        else
            asm = asm .. arithmeticOp(instruction)
        end
    end
    -- print("--Debug log--\n" .. asm .. "--End log--\n")
    return asm
end

----- FILE/IO -----

--check if arg is a file or directory
local function isFile(arg)
    if arg:find("%.") then
        return true
    else
        return false
    end
end

local og_path = arg[1]
local out_path = ""
print("Is " .. og_path .. " a file? ")
print(isFile(og_path))

local isFile = isFile(og_path)
local fileName = ""
local folderName = ""
local outputFileName = ""
if isFile then
    -- This matches strings that are in another folder
    fileName = og_path:match(".+/([^/]+)$"):gsub("%.vm$", "")
    out_path = og_path:gsub("%.vm$", "") .. ".asm"
    outputFileName = fileName .. ".asm"
else
    -- grab fileName from directory name
    folderName = og_path:match("([^/]+)$")
    out_path = og_path .. "/" .. folderName .. ".asm"
    outputFileName = folderName .. ".asm"
end

print("Input path: " .. og_path)
print("Output path: " .. out_path)

local asm = ""
if isFile then
    -- open input file
    local inputFile = io.open(og_path, "r")
    if not inputFile then
        error("Could not open input file: " .. og_path)
    end
    -- filter content into a table where each index is a line of VM code
    local contents = filterContents(inputFile)
    -- close input file
    inputFile:close()
    
    -- TURN VM INSTRUCTIONS INTO ASM
    asm = parseCode(contents, fileName)

-- Handle Folder
else
    -- Bootstrap Code
    asm = "//Bootstrap Code\n"
    asm = asm .. "@256\n" .. "D=A\n".."@SP\n" .. "M=D\n"
    asm = asm .. functionCall("call Sys.init 0")
    local handle = io.popen("ls " .. og_path .. " | grep '\\.vm$'")
    if handle then
        for file in handle:lines() do
            local filePath = og_path .. '/' .. file
            local name = file:match("^(.-)%.vm$")
            local inputFile = io.open(filePath, "r")
            local contents = filterContents(inputFile)
            inputFile:close()
            asm = asm .. parseCode(contents, name)
        end
    end
    handle:close()
end

-- open outputFile
local outputFile = io.open(out_path, "w")
-- write asm into the outputFile
outputFile:write(asm)
outputFile:close()

if isFile then
    print("VM file: '" .. fileName .. ".vm' has been translated into asm file: '" .. outputFileName .. "'")
else
    print("VM directory: '" .. folderName .. "' has been translated into asm file: '" .. outputFileName .. "'")
end
