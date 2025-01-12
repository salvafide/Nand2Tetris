// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

@KBD
D=A
@keys
M=D //value of keys is 24576

(LOOP)
@SCREEN
D=A
@addr
M=D //addr = RAM['some #'] = 16384

@KBD
D=M
@FILL
D;JGT   //if key pressed fill black

@FWhite //else fill white
D;JEQ

@LOOP
0;JMP

(FILL)
@addr
A=M
M=-1    //Ram[addr] = -1 a.k.a RAM[ RAM['some #'] ]

@addr
M=M+1   //add 1 to address starting at 16384
D=M     //current address in loop
@keys
D=M-D   //subtract current from max address
@LOOP
D;JEQ   // Break out of inner loop when at end of screen addresses

@KBD
D=M
@LOOP
D;JEQ   //break out if no key pressed

@FILL   // continue setting pixels
0;JMP

(FWhite)
@addr
A=M
M=0    //Ram[addr] = -1 a.k.a RAM[ RAM['some #'] ]

@addr
M=M+1   //add 1 to address starting at 16384
D=M     //current address in loop
@keys
D=M-D   //subtract current from max address
@LOOP
D;JEQ   // Break out of inner loop when at end of screen addresses

@FWhite // continue setting pixels
0;JMP

(END)
@END
0;JMP