// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
// The algorithm is based on repetitive addition.

// create i
@i
M=0

// create product
@product
M=0

(LOOP)
// if i = R1, goto STOP
@i
D=M
@R1
D=M-D
@STOP
D;JEQ

// product = product + R0
@R0
D=M
@product
M=D+M

// i++
@i
M=M+1

// goto LOOP
@LOOP
0;JMP

(STOP)
@product
D=M
@R2
M=D

(END)
@END
0;JMP

