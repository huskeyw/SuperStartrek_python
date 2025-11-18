import os
import sys
import time

# --- 1. Import core functions and constants from utils.py ---
# NOTE: This assumes utils.py is accessible in the same directory and contains
# clear_screen, Colors, load_ascii_art, and translate_art_tags.
try:
    from utils import clear_screen, Colors, load_ascii_art, translate_art_tags
except ImportError:
    # Fallback/Error handling if utils.py is not found or is missing functions
    print("ERROR: Could not import functions from utils.py.")
    print("Please ensure utils.py is in the same directory and contains:")
    print("clear_screen, Colors, load_ascii_art, and translate_art_tags.")
    sys.exit(1)


# --- 2. Simplified Printer for Testing ---
# This function is designed to mimic the typewriter_print behavior (no delay)
# but it relies entirely on the imported translation logic.
def test_art_printer(text, color=None, newline=True):
    """
    Prints a string immediately, translating embedded tags.
    """
    # 1. Translate embedded tags (e.g., [RED] -> \033[91m)
    text_to_print = translate_art_tags(text)
    
    # 2. Add color override if specified
    if color:
        # Note: If a color is passed here, it overrides any embedded tags,
        # but the RESET ensures the terminal goes back to normal.
        text_to_print = color + text_to_print + Colors.RESET

    # 3. Print
    sys.stdout.write(text_to_print)
    sys.stdout.flush()

    if newline:
        print()


# --- 3. MAIN TESTING LOOP ---

def main_test_loop():
    clear_screen()
    print(f"{Colors.BOLD}{Colors.CYAN}--- ASCII ART & TAG TESTER ---{Colors.RESET}")
    print(f"Usage: Enter the name of your .txt art file (e.g., klingon.txt)")
    print(f"Test tags: [RED], [BLINK], [BOLD], etc.")
    print("-" * 40)
    
    while True:
        try:
            filename = input("Enter Filename (or 'q' to quit): ").strip()
            
            if filename.lower() == 'q':
                break
            
            # Clear below the header
            print("\033[5;1H\033[J", end="") 
            
            art_lines = load_ascii_art(filename)
            
            # Print the art starting at row 7
            current_row = 7
            for line in art_lines:
                # Use absolute cursor positioning to prevent wrapping/scrolling
                print(f"\033[{current_row};1H", end="")
                # Use the test printer, which handles the embedded tags
                test_art_printer(line, newline=False)
                current_row += 1
            
            # Move cursor safely down
            print(f"\033[{current_row + 2};1H", end="")
            print("-" * 40)
            print(f"File '{filename}' rendered successfully above.")
            print("-" * 40)
            
        except Exception as e:
            # Move to error area
            print("\033[5;1H\033[J", end="")
            print(f"\n{Colors.RED}An unexpected error occurred: {e}{Colors.RESET}")
            input("Press Enter to continue...")
            main_test_loop() # Restart the test loop

if __name__ == "__main__":
    main_test_loop()