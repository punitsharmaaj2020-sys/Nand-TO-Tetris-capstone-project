// This file is part of www.nand2tetris.org
// Capstone Project: Make the Computer Draw a Box
// Personal Custom Variable: K = 5
//
// Box Specifications for K = 5:
//   - Starting row:            5
//   - Starting column:         0 (left edge of the screen)
//   - Starting memory address: 16544 (SCREEN + 32 * 5 = 16384 + 160)
//   - Height:                  20 rows (screen rows 5 to 24 inclusive)
//   - Width:                   32 pixels (16 * ((5 mod 4) + 1) = 32 pixels)
//   - Screen words per row:    2 words (32 pixels / 16 pixels per word)
//   - Total screen words:      40 words (2 words/row * 20 rows)
//
// Program Operation:
//   - Continuously monitors memory address 24576 (KBD).
//   - If any key is pressed (KBD != 0), jumps to DRAW_BOX to paint the 32x20 box black (-1).
//   - If no key is pressed (KBD == 0), jumps to CLEAR_BOX to paint the 32x20 box white (0).
//   - Erases ONLY the 40 screen words belonging to the box; leaves all other pixels untouched.
//   - Runs infinitely in a responsive loop.

// =================================================================
// MAIN LOOP: Poll Keyboard
// =================================================================
(LOOP)
    @KBD
    D=M              // Read the current keycode from the keyboard memory map
    @DRAW_BOX
    D;JNE            // If D != 0 (key is pressed), branch to DRAW_BOX
    @CLEAR_BOX
    0;JMP            // Otherwise (D == 0, key released), branch to CLEAR_BOX

// =================================================================
// DRAW_BOX ROUTINE
// Draws 20 rows of 32 black pixels starting at row 5 (address 16544).
// Each 16-bit word is filled with -1 (0xFFFF / 16 black pixels).
// =================================================================
(DRAW_BOX)
    // Initialize screen pointer to row 5, col 0 (address 16544)
    @16544
    D=A
    @addr
    M=D              // addr = 16544

    // Initialize row counter to 20 rows
    @20
    D=A
    @rows
    M=D              // rows = 20

(DRAW_ROW_LOOP)
    // Check if all 20 rows have been drawn
    @rows
    D=M
    @LOOP
    D;JEQ            // If rows == 0, finished drawing -> return to MAIN LOOP

    // Word 0 of current row (pixels 0 to 15): write -1 (all black)
    @addr
    A=M
    M=-1

    // Word 1 of current row (pixels 16 to 31): write -1 (all black)
    A=A+1
    M=-1

    // Advance addr by 32 words to point to the start of the next screen row
    @32
    D=A
    @addr
    M=M+D

    // Decrement the row counter
    @rows
    M=M-1

    @DRAW_ROW_LOOP
    0;JMP            // Repeat for next row

// =================================================================
// CLEAR_BOX ROUTINE
// Clears 20 rows of 32 pixels starting at row 5 (address 16544).
// Each 16-bit word is filled with 0 (0x0000 / 16 white pixels).
// Only touches the 40 words occupied by the box.
// =================================================================
(CLEAR_BOX)
    // Initialize screen pointer to row 5, col 0 (address 16544)
    @16544
    D=A
    @addr
    M=D              // addr = 16544

    // Initialize row counter to 20 rows
    @20
    D=A
    @rows
    M=D              // rows = 20

(CLEAR_ROW_LOOP)
    // Check if all 20 rows have been cleared
    @rows
    D=M
    @LOOP
    D;JEQ            // If rows == 0, finished clearing -> return to MAIN LOOP

    // Word 0 of current row (pixels 0 to 15): write 0 (all white)
    @addr
    A=M
    M=0

    // Word 1 of current row (pixels 16 to 31): write 0 (all white)
    A=A+1
    M=0

    // Advance addr by 32 words to point to the start of the next screen row
    @32
    D=A
    @addr
    M=M+D

    // Decrement the row counter
    @rows
    M=M-1

    @CLEAR_ROW_LOOP
    0;JMP            // Repeat for next row
