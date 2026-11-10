# CAPSTONE PROJECT REPORT: MAKE THE COMPUTER DRAW A BOX
**Course:** Nand to Tetris – I (ETCCNT301)  
**School of Engineering & Technology, K.R. Mangalam University**  

---

## Student Details
- **Student Name:** [Punit Kumar]
- **Roll Number:** [2501730205]
- **Personal Number (K):** **5** (05)
- **Course Outcomes Covered:** CO1 – CO4

---

## 1. Project Specifications & Parameter Derivation

### A. Assembler Custom Feature ($K \bmod 3$)
- Calculation: $5 \bmod 3 = 2$
- **Assigned Feature:** *Print a warning if the same label is written twice.*
- **Policy Implementation:** When duplicate `(LABEL)` pseudocommands appear in Pass 1:
  1. The assembler outputs:  
     `Warning: Label (LABEL_NAME) is defined more than once (first on line X, re-defined on line Y). Retaining original ROM address Z.`
  2. The assembler preserves the **first** definition's ROM address so that earlier forward/backward jumps remain deterministic and do not get overwritten.

### B. Screen Geometry and Address Derivation ($K = 5$)
- **Starting Row:** Row $K = 5$.
- **Starting Column:** Column $0$ (left edge).
- **Height:** $20$ rows (Row $5$ through Row $24$ inclusive).
- **Width:**
  $$\text{Width} = 16 \times ((K \bmod 4) + 1) = 16 \times ((5 \bmod 4) + 1) = 16 \times (1 + 1) = 32 \text{ pixels}$$
- **Words per Row:** $32 \text{ pixels} / 16 \text{ pixels per word} = 2 \text{ words}$.
- **Total Words Affected:** $20 \text{ rows} \times 2 \text{ words/row} = 40 \text{ words}$.
- **Memory Base for Row 5:**
  $$\text{Starting Address} = \text{SCREEN} + (32 \times 5) = 16384 + 160 = 16544 \ (0\text{x}40\text{A}0)$$
- **Ending Word Address:**
  $$\text{Ending Address} = 16544 + (32 \times 19) + 1 = 17153$$
- **Color Values:**
  - Drawing: Write `-1` (`0xFFFF`, all 16 bits set to 1 $\rightarrow$ solid black).
  - Clearing: Write `0` (`0x0000`, all 16 bits set to 0 $\rightarrow$ solid white).

---

## 2. Hardware Implementation Summary (Part A)

### A. `Memory.hdl`
- Routes 15-bit addresses across three functional regions:
  - RAM16K ($0$ to $16383$): Selected when `address[14] == 0`.
  - Screen ($16384$ to $24575$): Selected when `address[14..13] == 10`.
  - Keyboard ($24576$): Selected when `address[14..13] == 11`.
- Uses a `DMux4Way` to route the `load` signal and an `Or` gate to unite the two 8K slices of `RAM16K`.
- Multiplexes the output via `Mux4Way16`.

### B. `CPU.hdl`
- Decodes A-instructions (`instruction[15] == 0`) and C-instructions (`instruction[15] == 1`).
- Directs inputs to `ARegister`, `DRegister`, and the Hack `ALU`.
- Evaluates the three jump condition bits (`j1, j2, j3`) against the ALU output flags (`zr`, `ng`, and positive) to assert `pcLoad`.
- The `PC` chip loads the target address from `aOut` on jump conditions; otherwise, it increments sequentially.

### C. `Computer.hdl`
- Integrates `ROM32K`, `CPU`, and `Memory`.
- Connects the `reset` input to restart the program counter at ROM address 0.
- Successfully passes `ComputerAdd.tst`, `ComputerMax.tst`, and `ComputerRect.tst`.

---

## 3. Assembler Implementation (Part B)

The custom assembler (`assembler.py`) follows a robust two-pass design:
1. **Pass 1 (Symbol Resolution):**
   - Strips comments and whitespace.
   - Detects `(LABEL)` declarations.
   - Checks for duplicate label definitions and issues a warning while retaining the first occurrence.
   - Counts real instructions to assign accurate ROM addresses without inflating instruction count.
2. **Pass 2 (Code Generation):**
   - Populates predefined symbols (`SP, LCL, ARG, THIS, THAT, R0-R15, SCREEN, KBD`).
   - Dynamically allocates user variables starting at RAM address 16 (`@addr` $\rightarrow$ 16, `@rows` $\rightarrow$ 17).
   - Generates exact 16-bit binary strings for all A- and C-instructions.
   - Verified against test programs `Add.asm`, `Max.asm`, and `Box.asm`.

---

## 4. Hack Assembly Program (`Box.asm`) & Screen Output (Part C)

### A. Program Structure
- **Main Loop:** Continually reads `RAM[KBD]`. If non-zero (key pressed), jumps to `DRAW_BOX`; if zero, jumps to `CLEAR_BOX`.
- **DRAW_BOX Routine:**
  - Loads starting address $16544$ into `@addr` and initializes `@rows` to $20$.
  - Writes `-1` to `RAM[addr]` and `RAM[addr+1]`.
  - Adds $32$ to `@addr` to reach the next row.
  - Decrements `@rows` and loops until all 20 rows are black.
  - Returns to the main polling loop.
- **CLEAR_BOX Routine:**
  - Identical loop structure as DRAW_BOX, but writes `0` to erase only the 40 screen words of the box.

### B. Screen Geometry Verification Table
| Row Number | Screen Row | Word 0 Address | Word 1 Address | Value When Drawn | Value When Cleared |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | 5 | 16544 | 16545 | -1 | 0 |
| 2 | 6 | 16576 | 16577 | -1 | 0 |
| 3 | 7 | 16608 | 16609 | -1 | 0 |
| ... | ... | ... | ... | -1 | 0 |
| 19 | 23 | 17120 | 17121 | -1 | 0 |
| 20 | 24 | 17152 | 17153 | -1 | 0 |

---

## 5. One Mistake I Encountered and How I Fixed It

> **Mistake Report Paragraph:**  
> During the initial development of the `Box.asm` drawing loop, I attempted to write to the second 16-bit word of each row using the instruction `A=M+1`. However, because `@addr` had just been dereferenced with `A=M`, the A-register was pointing to screen memory ($16544$), which caused `M` to evaluate to the current pixel value ($-1$) rather than the address. When `-1 + 1` was evaluated, the A-register was corrupted to `0`, resulting in incorrect memory writes to RAM[0] instead of the second screen word. I fixed this by using the Hack ALU's register increment instruction `A=A+1` immediately after writing the first word. Because `A=A+1` operates strictly on the internal A-register without reading memory operand `M`, the address advanced cleanly from $16544$ to $16545$, accurately drawing the contiguous 32-pixel row without any memory corruption.

---

## 6. Viva Voce Preparation Quick Reference

1. **How to move the box down by $N$ rows?**  
   Add $32 \times N$ to the starting address. For instance, to move the box down by 5 rows (to start at row 10), change `@16544` to `@16704` ($16544 + 160$).
2. **How to change the width of the box?**  
   To make the box 48 pixels wide (3 words), add another `A=A+1` and `M=-1` (or `M=0`) before advancing the row address.
3. **Why does Keyboard not have a load signal?**  
   The keyboard memory map (`RAM[24576]`) is a physical input device. Writing to it is electrically invalid, so its load line is intentionally discarded in `Memory.hdl`.
