An attempt to create a simulation (of sorts) of a computer system :)

As of now we have main.py, this is the entry point to our StreamLt app. 

alu.py is the ALU - Arithmatic Logic Unit. Here, we have:
3 tabs: 
1 - ALU Operations

Enter two numbers: Operand A and Operand B
Pick an operation: ADD, SUB, MUL, AND, OR, XOR, NOT, SHL, SHR
Call r = alu_op(int(a), int(b), op) in our helper.py
Which return: decimal result, 32-bit result, hex + binary versions, CPU flags: Zero flag (Z), Negative flag (N), Carry (C), Overflow (V)

2 - Logic Gates
Pick a gate: AND, OR, NOT, NAND, NOR, XOR, XNOR
Each gate is defined as a Python function:
"AND": lambda a,b: a & b
"OR":  lambda a,b: a | b
"XOR": lambda a,b: a ^ b

Some are built from others:
NAND = NOT(AND)
NOR = NOT(OR)
XNOR = NOT(XOR)

Outputs:
Truth table (all input combinations)
Interactive toggle (A and B switches)
Big glowing result: 1 (HIGH) or 0 (LOW)

3 - 8-bit Ripple-Carry Adder
Input two numbers (0–255)
Convert to 8-bit binary:
a_bits = [int(b) for b in to_bin(a_val, 8)]

Full adder simulation (core CPU trick)
Each bit uses:
s  = ai ^ bi ^ ci
co = (ai & bi) | (bi & ci) | (ai & ci)

That is a full adder circuit:
XOR → sum
AND/OR → carry logic

The carry from each bit flows into the next:
bit0 → bit1 → bit2 → ... → bit7

Outputs:
step-by-step table of each bit stage
final sum
overflow detection (>255)
binary result visualisation
