#!/usr/bin/env python3
"""
Hack Computer Assembler (Nand to Tetris Part I Capstone Project)
Personal Custom Variable: K = 5 (K mod 3 = 2)

Extra Feature (K mod 3 = 2):
  Detect duplicate label declarations during Pass 1 and print a warning:
  "Warning: Label (LABEL_NAME) is defined more than once on line X"
  Duplicate handling policy: The assembler retains the FIRST definition's
  ROM address to keep earlier forward/backward jumps deterministic, while
  notifying the developer of the duplicate declaration.

Usage:
  python assembler.py <file.asm>
  python assembler.py Box.asm  --> Generates Box.hack
"""

import sys
import os
import re

# =====================================================================
# HACK ARCHITECTURE TABLES
# =====================================================================

PREDEFINED_SYMBOLS = {
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,
    "R0": 0,
    "R1": 1,
    "R2": 2,
    "R3": 3,
    "R4": 4,
    "R5": 5,
    "R6": 6,
    "R7": 7,
    "R8": 8,
    "R9": 9,
    "R10": 10,
    "R11": 11,
    "R12": 12,
    "R13": 13,
    "R14": 14,
    "R15": 15,
    "SCREEN": 16384,
    "KBD": 24576,
}

# 7-bit computation field (a c1 c2 c3 c4 c5 c6)
COMP_TABLE = {
    # a = 0 (operations using A register)
    "0":   "0101010",
    "1":   "0111111",
    "-1":  "0111010",
    "D":   "0001100",
    "A":   "0110000",
    "!D":  "0001101",
    "!A":  "0110001",
    "-D":  "0001111",
    "-A":  "0110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "D+A": "0000010",
    "A+D": "0000010",  # Commutative addition
    "D-A": "0010011",
    "A-D": "0000111",
    "D&A": "0000000",
    "A&D": "0000000",  # Commutative AND
    "D|A": "0010101",
    "A|D": "0010101",  # Commutative OR

    # a = 1 (operations using Memory M = RAM[A])
    "M":   "1110000",
    "!M":  "1110001",
    "-M":  "1110011",
    "M+1": "1110111",
    "M-1": "1110010",
    "D+M": "1000010",
    "M+D": "1000010",  # Commutative addition
    "D-M": "1010011",
    "M-D": "1000111",
    "D&M": "1000000",
    "M&D": "1000000",  # Commutative AND
    "D|M": "1010101",
    "M|D": "1010101",  # Commutative OR
}

# 3-bit destination field (d1 d2 d3: A D M)
DEST_TABLE = {
    None:  "000",
    "":    "000",
    "M":   "001",
    "D":   "010",
    "MD":  "011",
    "DM":  "011",
    "A":   "100",
    "AM":  "101",
    "AD":  "110",
    "DA":  "110",
    "AMD": "111",
    "ADM": "111",
}

# 3-bit jump condition field (j1 j2 j3)
JUMP_TABLE = {
    None:  "000",
    "":    "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}


# =====================================================================
# ASSEMBLER IMPLEMENTATION
# =====================================================================

class HackAssembler:
    """
    Two-pass assembler for the Hack computer architecture.
    """

    def __init__(self):
        # Initialize symbol table with predefined symbols
        self.symbol_table = dict(PREDEFINED_SYMBOLS)
        # Tracking declared labels to detect duplicates (K mod 3 = 2 feature)
        self.declared_labels = {}
        # Next available RAM address for user variables starts at 16
        self.next_variable_address = 16

    def clean_line(self, line: str) -> str:
        """
        Removes comments (// ...) and all surrounding and internal whitespace.
        """
        # Strip inline comment
        comment_idx = line.find("//")
        if comment_idx != -1:
            line = line[:comment_idx]
        # Remove all whitespace
        return "".join(line.split())

    def pass_one(self, lines: list[str]) -> None:
        """
        PASS 1: Symbol Resolution
        Scans through the file, strips comments/whitespace, and identifies
        (LABEL) pseudocommands. Associates label names with ROM addresses.
        Labels do NOT advance the ROM instruction address counter.
        Detects duplicate labels and issues a warning (K mod 3 = 2 requirement).
        """
        rom_address = 0

        for original_line_num, raw_line in enumerate(lines, start=1):
            cleaned = self.clean_line(raw_line)
            if not cleaned:
                continue

            # Check if this line is a label declaration: (LABEL)
            if cleaned.startswith("(") and cleaned.endswith(")"):
                label_name = cleaned[1:-1].strip()

                if not label_name:
                    print(f"Error at line {original_line_num}: Empty label declaration '()' encountered.",
                          file=sys.stderr)
                    sys.exit(1)

                # Check for duplicate label declaration (K mod 3 = 2)
                if label_name in self.declared_labels:
                    first_line = self.declared_labels[label_name]
                    print(
                        f"Warning: Label ({label_name}) is defined more than once "
                        f"(first on line {first_line}, re-defined on line {original_line_num}). "
                        f"Retaining original ROM address {self.symbol_table[label_name]}.",
                        file=sys.stderr
                    )
                else:
                    self.declared_labels[label_name] = original_line_num
                    self.symbol_table[label_name] = rom_address
            else:
                # Regular A-instruction or C-instruction advances ROM address
                rom_address += 1

    def assemble_a_instruction(self, instruction: str, line_num: int) -> str:
        """
        Translates an A-instruction (@value or @symbol) into 16-bit binary.
        Format: 0 vvvvvvvvvvvvvvv (15-bit address)
        """
        symbol = instruction[1:]  # Strip '@'

        if not symbol:
            print(f"Error at line {line_num}: Empty @ instruction.", file=sys.stderr)
            sys.exit(1)

        # Case 1: Numeric constant (e.g., @16544 or @0)
        if symbol.isdigit():
            address_val = int(symbol)
            if address_val < 0 or address_val > 32767:
                print(f"Error at line {line_num}: Address '{address_val}' out of 15-bit range (0-32767).",
                      file=sys.stderr)
                sys.exit(1)
        else:
            # Case 2: Symbol (predefined, label, or user variable)
            # Validate symbol naming convention
            if re.match(r"^[0-9]", symbol):
                print(f"Error at line {line_num}: Malformed symbol '{symbol}' cannot start with a digit.",
                      file=sys.stderr)
                sys.exit(1)

            if symbol in self.symbol_table:
                address_val = self.symbol_table[symbol]
            else:
                # Allocate new variable at next available RAM address
                address_val = self.next_variable_address
                self.symbol_table[symbol] = address_val
                self.next_variable_address += 1

        # Format as 16-bit binary with MSB 0
        return f"{address_val:016b}"

    def assemble_c_instruction(self, instruction: str, line_num: int) -> str:
        """
        Translates a C-instruction (dest=comp;jump) into 16-bit binary.
        Format: 1 1 1 a c1 c2 c3 c4 c5 c6 d1 d2 d3 j1 j2 j3
        """
        dest_part = None
        jump_part = None
        comp_part = instruction

        # Check for destination: dest=comp
        if "=" in comp_part:
            dest_part, comp_part = comp_part.split("=", 1)

        # Check for jump: comp;jump
        if ";" in comp_part:
            comp_part, jump_part = comp_part.split(";", 1)

        # Lookup computation bits
        if comp_part not in COMP_TABLE:
            print(f"Error at line {line_num}: Invalid comp mnemonic '{comp_part}' in instruction '{instruction}'.",
                  file=sys.stderr)
            sys.exit(1)
        comp_bits = COMP_TABLE[comp_part]

        # Lookup destination bits
        if dest_part not in DEST_TABLE:
            print(f"Error at line {line_num}: Invalid dest mnemonic '{dest_part}' in instruction '{instruction}'.",
                  file=sys.stderr)
            sys.exit(1)
        dest_bits = DEST_TABLE[dest_part]

        # Lookup jump bits
        if jump_part not in JUMP_TABLE:
            print(f"Error at line {line_num}: Invalid jump mnemonic '{jump_part}' in instruction '{instruction}'.",
                  file=sys.stderr)
            sys.exit(1)
        jump_bits = JUMP_TABLE[jump_part]

        # C-instruction prefix is always '111'
        binary_instruction = "111" + comp_bits + dest_bits + jump_bits

        if len(binary_instruction) != 16:
            print(f"Internal Error at line {line_num}: Generated instruction is not 16 bits: {binary_instruction}",
                  file=sys.stderr)
            sys.exit(1)

        return binary_instruction

    def pass_two(self, lines: list[str]) -> list[str]:
        """
        PASS 2: Code Generation
        Translates each cleaned instruction line into 16-bit binary machine code.
        """
        machine_code = []

        for original_line_num, raw_line in enumerate(lines, start=1):
            cleaned = self.clean_line(raw_line)
            if not cleaned or (cleaned.startswith("(") and cleaned.endswith(")")):
                # Skip blank lines, comment-only lines, and label declarations
                continue

            if cleaned.startswith("@"):
                # A-instruction
                binary_line = self.assemble_a_instruction(cleaned, original_line_num)
            else:
                # C-instruction
                binary_line = self.assemble_c_instruction(cleaned, original_line_num)

            machine_code.append(binary_line)

        return machine_code

    def assemble(self, input_filepath: str, output_filepath: str) -> None:
        """
        Executes Pass 1 and Pass 2 on the input assembly file and writes the
        resulting machine code to the output .hack file.
        """
        if not os.path.exists(input_filepath):
            print(f"Error: Input file '{input_filepath}' not found.", file=sys.stderr)
            sys.exit(1)

        with open(input_filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        print(f"Assembling '{input_filepath}'...")
        # Pass 1: Resolve all labels and note their ROM addresses
        self.pass_one(lines)

        # Pass 2: Translate instructions into binary
        machine_code = self.pass_two(lines)

        # Write machine instructions to .hack file
        with open(output_filepath, "w", encoding="utf-8", newline="\n") as f:
            for instruction in machine_code:
                f.write(instruction + "\n")

        print(f"Assembly completed successfully.")
        print(f"Output written to '{output_filepath}' ({len(machine_code)} instructions).")


# =====================================================================
# COMMAND-LINE ENTRY POINT
# =====================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python assembler.py <input_file.asm> [output_file.hack]")
        sys.exit(1)

    input_path = sys.argv[1]
    if not input_path.endswith(".asm"):
        print(f"Warning: Expected input file with .asm extension, got '{input_path}'.")

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        # Default: replace .asm extension with .hack in the same directory
        base_name, _ = os.path.splitext(input_path)
        output_path = base_name + ".hack"

    assembler = HackAssembler()
    assembler.assemble(input_path, output_path)


if __name__ == "__main__":
    main()
