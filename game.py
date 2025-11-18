import random
#import math
import time
#import os
import sys
import textwrap

# --- Import all our helpers and colors ---
from utils import (clear_screen, get_quadrant_name, Colors, load_ascii_art,
                   get_visible_length,translate_art_tags,
                   get_course_and_distance,get_distance,
                   get_device_name,Difficulty, DIFFICULTIES, EASY, STANDARD, HARD)
class SuperStarTrek:
    """
    A Python implementation of the Super Star Trek BASIC game.
    """
    # This maps Course (1-8) to a (dRow, dCol) vector
        # Based on lines 530, 540, and 600 of the BASIC code
    COURSE_VECTORS = {
         1: (0, 1),   # Right
         2: (-1, 1),  # Up-Right
         3: (-1, 0),  # Up
         4: (-1, -1), # Up-Left
         5: (0, -1),  # Left
         6: (1, -1),  # Down-Left
         7: (1, 0),   # Down
         8: (1, 1)    # Down-Right
    }

    def __init__(self):
        


        """
        Initialize the game state.
        This translates the DIM and variable setup from lines 260-1100.
        """
        # Note: We use 9x9 arrays (indexed 1-8) to match the BASIC code's
        # 1-based indexing. This makes translation much easier.
        self.galaxy = [[0 for _ in range(9)] for _ in range(9)] # G(8,8)
        self.galaxy_known = [[False for _ in range(9)] for _ in range(9)] # Z(8,8)
        
        # Quadrant (q1, q2) and Sector (s1, s2) coordinates
        self.q1 = 0
        self.q2 = 0
        self.s1 = 0
        self.s2 = 0
        
        # Enterprise stats
        self.stardate = 0       # T
        self.stardate_start = 0 # T0
        self.stardate_end = 0   # T0+T9
        self.time_remaining = 0 # T9
        
        self.energy = 3000      # E
        self.energy_start = 3000 # E0
        self.shields = 0        # S
        self.torpedoes = 10     # P
        
        self.klingons_total = 0 # K9
        self.klingons_start = 0 #<-- Ensure this is 0 (Total Klingons at the start of the mission)
        self.starbases_total = 0 # B9
        
        # Tracks Klingons/Bases/Stars in the *current* quadrant
        self.quadrant_klingons = [] # Replaces K(3,3)
        self.quadrant_starbase = None # Replaces B4, B5
        self.quadrant_stars = []
        
        # Damage array (translates D(8))
        self.damage = {
            "WARP_ENGINES": 0.0,
            "SHORT_RANGE_SENSORS": 0.0,
            "LONG_RANGE_SENSORS": 0.0,
            "PHASER_CONTROL": 0.0,
            "PHOTON_TUBES": 0.0,
            "DAMAGE_CONTROL": 0.0,
            "SHIELD_CONTROL": 0.0,
            "LIBRARY_COMPUTER": 0.0
        }
        
        self.is_running = True
        self.is_docked = False
        self.message_queue = [] # message que to help control text placement
        self.klingons_start = 0 # Total Klingons at the start of the mission
        self.game_over_reason = "" # Tracks why the game ended
        self.hostile_action_taken = False
        # --- ADD THESE UI CONSTANTS ---
        self.msg_box_col = 40     # Col to start the message box (must match _draw_right_panel)
        self.msg_box_width = 40    # Width of the box
        self.msg_box_top = 12       # Top row of the message area
        self.msg_box_bottom = 29   # Last row for messages
        self.cmd_box_top = 31      # Row for the "COMMAND?" prompt
        # This will hold a *function* to call for input,
        # instead of the main "COMMAND?" prompt.
        self.input_handler = None
        # This will store temporary data between input steps
        self.command_data = {}
        self.pause_after_messages = False
        
    def print_help(self):
        """
        Takes over the map area to display the command list.
        Translates lines 2150-2260.
        """
        # --- FIX: Move to Row 1 and clear screen from there down ---
       # print("\033[1;1H\033[J", end="")
        
        # --- FIX: Use typewriter_print (with 0 delay) ---
        self.queue_message_instant("ENTER ONE OF THE FOLLOWING:", color=Colors.CYAN)
        self.queue_message_instant("--------------------------")
        self.queue_message_instant("  NAV  (TO SET COURSE)")
        self.queue_message_instant("  SRS  (FOR SHORT RANGE SENSOR SCAN)")
        self.queue_message_instant("  LRS  (FOR LONG RANGE SENSOR SCAN)")
        self.queue_message_instant("  PHA  (TO FIRE PHASERS)")
        self.queue_message_instant("  TOR  (TO FIRE PHOTON TORPEDOES)")
        self.queue_message_instant("  SHE  (TO RAISE OR LOWER SHIELDS)")
        self.queue_message_instant("  DAM  (FOR DAMAGE CONTROL REPORTS)")
        self.queue_message_instant("  COM  (TO CALL ON LIBRARY-COMPUTER)")
        self.queue_message_instant("  XXX  (TO RESIGN YOUR COMMAND)")
        
        # --- ADD: A pause so the user can see the help ---
     
    def setup_game(self):
        """
        Populates the galaxy. This translates lines 820-1200.
        """
     
        self.queue_message_instant("Setting up the galaxy...",color=Colors.BOLD)
        # A simplified setup
        self.klingons_total = 0 # K9
        self.starbases_total = 0 # B9
        self.time_remaining = 30 # T9
        self.stardate = 2000     # T0
        self.stardate_end = self.stardate + self.time_remaining
        #self.klingons_start = self.klingons_total  # Set starting K count
        self.game_over_reason = ""
        self.is_running = True
        
        # --- Place Klingons, Starbases, and Stars (Simplified Setup) ---
        
        # 1. Distribute Starbases (B9 total) across the 64 quadrants
        remaining_starbases = self.starbases_total
        
        for r in range(1, 9):
            for c in range(1, 9):
                k = 0
                b = 0
                s = random.randint(1, 8) # Stars

                # --- 2. Place Klingons (still randomized within the total) ---
                if random.random() > 0.8:
                    # Place 1-3 Klingons
                    k = random.randint(1, 3) 
                    
                # --- 3. Place Starbases (Bases are now placed exactly 'B9' times) ---
                # Check if we still have bases to place AND randomize placement
                if remaining_starbases > 0 and random.random() > 0.95: 
                    b = 1
                    remaining_starbases -= 1
                
                self.galaxy[r][c] = k * 100 + b * 10 + s
        
        # If we didn't place all bases randomly, force the placement of the remainder
        while remaining_starbases > 0:
            r = random.randint(1, 8)
            c = random.randint(1, 8)
            # Check if this quadrant already has a base
            if (self.galaxy[r][c] % 100) // 10 == 0:
                # Add a base (10 is the base multiplier)
                self.galaxy[r][c] += 10 
                remaining_starbases -= 1


        # Place the Enterprise (lines 490)
        self.q1 = random.randint(1, 8)
        self.q2 = random.randint(1, 8)
        self.s1 = random.randint(1, 8)
        self.s2 = random.randint(1, 8)
        
    def show_intro_animation(self):
        """
        Recreates the introductory animation using ANSI escape codes,
        just like the original BASIC file for a flicker-free animation.
        """
        # Load the art from the file instead of a hardcoded list
        enterprise_art = load_ascii_art("enterprise.txt")
        
        # --- ANSI Escape Codes ---
        # '\033' is the Python equivalent of CHR$(27)
        
        # [2J = Clear entire screen (from line 210)
        CLEAR_SCREEN = "\033[2J" 
        
        # [3;1H = Move cursor to Row 3, Column 1 (from line 210)
        CURSOR_TITLE = "\033[3;1H" 
        
        # Move cursor to Row 7, Column 1 (a good place for the ship)
        CURSOR_SHIP = "\033[7;1H"

        # 1. Clear the screen and self.queue_message_instant the title ONCE
        # We use end="" to prevent Python from adding extra newlines
        print(CLEAR_SCREEN, end="")
        print(CURSOR_TITLE, end="")
        print(f"{Colors.BOLD}{Colors.BLUE}THE USS ENTERPRISE --- NCC-1701{Colors.RESET}") # (from line 211)

        # 2. The animation loop (from line 222)
        for yy in range(1, 41, 2):
            # ... (print CURSOR_SHIP) ...
            print(CURSOR_SHIP, end="")
            for line in enterprise_art:
                clear_line = "\033[K"
                # --- FIX: Translate tags before printing ---
                translated_line = translate_art_tags(line)
                print(" " * yy + translated_line + clear_line)
            
            time.sleep(0.05)

        # 3. Clear the screen at the end before the game starts
        time.sleep(1)
    
   
        
    def _show_art(self, filename,color=None):
        """
        Loads and prints a specific art file to the message area.
        """
        # --- FIX: Clear the *message box* (Rows 12-29) ---
        message_row = self.msg_box_top
        for r in range(self.msg_box_top, self.msg_box_bottom + 1):
            print(f"\033[{r};{self.msg_box_col}H\033[K", end="")
        print(f"\033[{message_row};{self.msg_box_col}H", end="") # Move cursor to top of box
        
        art_lines = load_ascii_art(filename)
        for line in art_lines:
            translated_line = translate_art_tags(line)
            # Move to the correct row and column
            print(f"\033[{message_row};{self.msg_box_col}H", end="")
            self.typewriter_print(translated_line, delay=0, color=color, newline=False)
            message_row += 1
    
    def show_mission_briefing(self):
        """print the mission briefing. (Lines 1230-1271)"""
        # Logic for plural/singular (lines 1100, 1200)
        starbase_s = 'S' if self.starbases_total != 1 else ''
        starbase_is = 'ARE' if self.starbases_total != 1 else 'IS'

        self.queue_message("   YOUR ORDERS ARE AS FOLLOWS:",0.05,Colors.GREEN)
        self.queue_message("   ----------------Classified--------------------------",0.05,Colors.GREEN)
        self.queue_message(f"   DESTROY THE {self.klingons_total} KLINGON WARSHIPS WHICH HAVE INVADED",0.05,Colors.GREEN)
        self.queue_message("   THE GALAXY BEFORE THEY CAN ATTACK FEDERATION HEADQUARTERS",0.05,Colors.GREEN)
        self.queue_message(f"   ON STARDATE {self.stardate_end}.",0.05,Colors.GREEN)
        self.queue_message(f"   THIS GIVES YOU {self.time_remaining} DAYS. THERE {starbase_is}",0.05,Colors.GREEN)
        self.queue_message(f"   {self.starbases_total} STARBASE{starbase_s} IN THE GALAXY FOR RESUPPLYING YOUR SHIP.",0.05,Colors.GREEN)
        self.queue_message("   ----------------Classified--------------------------",0.05,Colors.GREEN)
        self.queue_message("")
    
    def show_instructions(self):
        """
        Displays the instructions by loading and parsing 'instructions.txt'.
        """
        clear_screen()
        
        try:
            with open("instructions.txt", 'r') as f:
                for line in f:
                    # Strip the newline character
                    cleaned_line = line.rstrip('\n')
                    
                    if cleaned_line == "[PAUSE]":
                        # This was an input() line
                        print() # Add a space
                        input("[ENTER] TO CONTINUE")
                        clear_screen()
                    else:
                        # Just print the line of text
                        print(cleaned_line)
                        
        except FileNotFoundError:
            # Handle error if file is missing
            print("ERROR: instructions.txt file not found.")
            print("Please make sure it's in the same directory as main.py.")
            input("[ENTER] TO CONTINUE")
        except Exception as e:
            print(f"ERROR: Could not read instructions file: {e}")
            input("[ENTER] TO CONTINUE")
        
        # When done, clear screen and return to the main Y/N/I prompt
        clear_screen() 
        
 
    def handle_difficulty_select(self):
        """Displays the difficulty menu and sets the handler for input."""
        
        # Clear any messages queued by a failed attempt (if any)
        self.message_queue.clear() 
        
        # Clear the entire screen content before printing the menu.
        print("\033[1;1H\033[J", end="")
        
        # --- Print the menu directly to ensure it appears before input ---
        self.typewriter_print("--- SELECT DIFFICULTY ---", delay=0, color=Colors.CYAN)
        
        # Print options using the instant typewriter print
        for i, diff in enumerate(DIFFICULTIES):
            self.typewriter_print(f"   {i + 1} - {diff.name} (Klingons: {diff.initial_klingons}, Shields: {diff.shield_multiplier}x)", delay=0)
        
        self.typewriter_print("\n" * 2, delay=0) # Add spacing before prompt
        
        try:
            # The input prompt is now placed directly after the printed menu text.
            choice = int(input("ENTER CHOICE (1-3): ").strip())
            
            if 1 <= choice <= len(DIFFICULTIES):
                # Set variables
                self.difficulty = DIFFICULTIES[choice - 1]
                self.klingons_total = self.difficulty.initial_klingons
                self.klingons_start = self.klingons_total
                self.starbases_total = self.difficulty.initial_starbases
                
                self.queue_message_instant(f"DIFFICULTY SET TO: {self.difficulty.name}", color=Colors.GREEN)
                
            else:
                self.queue_message_instant(f"   {Colors.RED}INVALID CHOICE. ENTER 1, 2, or 3.{Colors.RESET}")
                self.input_handler = self.handle_difficulty_select # Restart
                
        except ValueError:
            self.queue_message_instant(f"   {Colors.RED}INVALID INPUT. ENTER A NUMBER.{Colors.RESET}")
            self.input_handler = self.handle_difficulty_select # Restart
          
        
    def handle_y_n_i_input(self):
        """Handles the final Y/N/I input after the mission briefing."""
        # Use the new centralized function for setup messages
        self._process_message_queue(use_full_width=True,start_row=30) 
        #print(f"\033[35;1H\033[K", end="")
        response = input("PRESS Y TO ACCEPT COMMAND, N TO QUIT, I FOR INSTRUCTIONS: ").strip().upper()
        if response == "I":
            self.show_instructions() 
            clear_screen()
            self.show_mission_briefing() # Re-queue the briefing after instructions
            self.input_handler = self.handle_y_n_i_input # Loop back to this prompt
        elif response == "Y":
            clear_screen()
            self.enter_quadrant() # Start the game!
            # The input_handler is cleared here, ending the setup loop in run()
        elif response == "N":
            clear_screen()
            self.typewriter_print("Coward",delay=0.2,color=Colors.RED)
            self.is_running = False
            self.game_over_reason = "QUIT" 
            # The input_handler is cleared here, ending the setup loop in run()
    
    def klingons_fire_back(self):
        """
        Klingons in the quadrant fire back at the Enterprise.
        This function now takes over the message area and pauses.
        """
        active_klingons = [k for k in self.quadrant_klingons if k['shields'] > 0]
        if not active_klingons:
            return # No Klingons to fire

        if self.is_docked:
            self.queue_message_instant("   STARBASE SHIELDS PROTECT THE ENTERPRISE.")
            return

        # --- FIX: Take over the message area ---
        print("\033[11;1H\033[J", end="") # Clear message area
        
        # Draw the Klingon art
        art_lines = load_ascii_art("klingon.txt")
        for line in art_lines:
            self.typewriter_print(line, delay=0)

        # Print damage reports
        for k in active_klingons:
            distance = get_distance(self.s1, self.s2, k['s1'], k['s2'])
            if distance == 0: distance = 0.1 

            hit_strength = int((k['shields'] / distance) * (2 + random.random()) / self.difficulty.energy_divisor) # <-- NEW DIVISION
            self.shields -= hit_strength
            
            self.typewriter_print(f"   {hit_strength} UNIT HIT ON ENTERPRISE FROM SECTOR {k['s1']},{k['s2']}", delay=0, color=Colors.RED)

            if self.shields <= 0:
                self.typewriter_print("\n\n*** THE ENTERPRISE HAS BEEN DESTROYED ***", delay=0, color=Colors.RED)
                self.typewriter_print("THE FEDERATION WILL BE CONQUERED.", delay=0, color=Colors.RED)
                self.is_running = False 
                self.game_over_reason = "DESTROYED"
                break # Stop the loop
            
            self.typewriter_print(f"      <SHIELDS DOWN TO {self.shields:.0f} UNITS>", delay=0, color=Colors.YELLOW)

            # Check for random additional damage
            if hit_strength < 20 or \
               random.random() > 0.6 or \
               (self.shields > 0 and (hit_strength / self.shields) <= 0.02):
                continue
                
            device_index = int(random.random() * 7.98 + 1.01) 
            device_key = list(self.damage.keys())[device_index - 1]
            device_name_str = get_device_name(device_index)
            damage_amount = (hit_strength / self.shields if self.shields > 0 else 1) + (0.5 * random.random())
            self.damage[device_key] -= damage_amount
            
            self.typewriter_print(f"   DAMAGE CONTROL: '{device_name_str} DAMAGED BY THE HIT'", delay=0, color=Colors.MAGENTA)

        # --- FIX: Add the pause ---
        if self.is_running: # Don't pause if the game is over
            input("\nPress Enter to continue...")
            clear_screen() # <-- ADD THIS LINE
            
    def _get_random_sector(self, occupied_sectors):
        """
        Helper function to find an empty sector (1-8, 1-8).
        This replaces the GOSUB 8590 logic.
        """
        while True:
            # FNR(1) = INT(RND(1)*7.98+1.01)
            r1 = int(random.random() * 7.98 + 1.01) # Row
            r2 = int(random.random() * 7.98 + 1.01) # Col
            if (r1, r2) not in occupied_sectors:
                occupied_sectors.add((r1, r2))
                return r1, r2

    def enter_quadrant(self):
        """
        Populates the current quadrant with objects.
        This translates lines 1320-1910.
        """
        
        self.queue_message(f"NOW ENTERING {get_quadrant_name(self.q1, self.q2)} QUADRANT . . .",delay=0.05,color=Colors.GREEN)
        # Keep track of where we've placed objects
        occupied_sectors = set()
        occupied_sectors.add((self.s1, self.s2)) # Enterprise's location
        
        # Mark quadrant as visited (line 1320, Z(Q1,Q2)=G(Q1,Q2))
        self.galaxy_known[self.q1][self.q2] = True
        
        # Decode quadrant data from galaxy map (line 1500)
        quadrant_data = self.galaxy[self.q1][self.q2]
        k_count = quadrant_data // 100
        b_count = (quadrant_data % 100) // 10
        s_count = quadrant_data % 10
        
        # Place Klingons (lines 1720-1780)
        self.quadrant_klingons = []
        for _ in range(k_count):
            r1, r2 = self._get_random_sector(occupied_sectors)
            # K(I,3)=S9*(.5+RND(1)) -> shields = 200 * (0.5 + RND)
            shields_base = self.difficulty.base_klingon_shields
            shields = shields_base * (0.5 + random.random())
            self.quadrant_klingons.append({'s1': r1, 's2': r2, 'shields': shields})
            
        # Place Starbase (line 1880)
        self.quadrant_starbase = None
        if b_count > 0:
            r1, r2 = self._get_random_sector(occupied_sectors)
            self.quadrant_starbase = {'s1': r1, 's2': r2}
        
        # Place Stars (line 1910)
        self.quadrant_stars = []
        for _ in range(s_count):
            r1, r2 = self._get_random_sector(occupied_sectors)
            self.quadrant_stars.append({'s1': r1, 's2': r2})

        # Check for "Condition Red" (lines 1560-1580)
        if k_count > 0:
            self.queue_message_instant(f"\n   {Colors.RED}{Colors.BOLD}COMBAT AREA      CONDITION RED{Colors.RESET}")
            if self.shields <= 200:
                self.queue_message_instant(f"      {Colors.YELLOW}SHIELDS DANGEROUSLY LOW{Colors.RESET}")
        else:
            self.queue_message_instant("") # Add a blank line
            
    def _get_vector(self, course):
        """
        Calculates the (dRow, dCol) vector for a given course.
        Used by both NAV and TOR commands.
        """
        # Get the integer part of the course for vector lookup
        course_int = int(course)
        # Get the fractional part for interpolation
        course_frac = course - course_int
        
        # Get the two vectors for interpolation (e.g., for course 1.5)
        vec1 = self.COURSE_VECTORS[course_int]
        vec2 = self.COURSE_VECTORS[course_int + 1] if course_int < 8 else self.COURSE_VECTORS[1]

        # Interpolate the vector (line 3110)
        dRow = vec1[0] + (vec2[0] - vec1[0]) * course_frac
        dCol = vec1[1] + (vec2[1] - vec1[1]) * course_frac
        
        return dRow, dCol
    
    def typewriter_print(self, text="", delay=0.05, color=None, newline=True):
        """
        Prints a string with a typewriter effect and optional color.
        Can be controlled to not add a newline.
        """
        
        # Start the color if one was provided
        if color:
            sys.stdout.write(color)
            sys.stdout.flush()

        # --- THIS IS THE UPGRADED LOGIC ---
        if delay == 0:
            # If no delay, print the whole string at once.
            # This allows pre-embedded ANSI codes to work.
            sys.stdout.write(text)
            sys.stdout.flush()
        else:
            # If there's a delay, iterate char by char
            for char in text:
                sys.stdout.write(char)
                sys.stdout.flush()
                time.sleep(delay)
        
        # Reset the color if one was used
        if color:
            sys.stdout.write(Colors.RESET)
            sys.stdout.flush()

        # --- FIX: Only print a newline if requested ---
        if newline:
            print() # Move to the next line
    
    def queue_message(self, text, delay=0.05, color=Colors.GREEN):
        """
        Adds a message to the queue to be self.queue_message_instanted with typewriter effect.
        """
        # Store a dictionary with all the arguments for typewriter_print
        self.message_queue.append({
            "text": text,
            "delay": delay,
            "color": color
        })
    
    def queue_message_instant(self, text, color=None):
        """
        Adds a message to the queue that will self.queue_message_instant instantly.
        (A typewriter with zero delay).
        """
        self.message_queue.append({
            "text": text,
            "delay": 0,
            "color": color
        })
    
    def _draw_status_panel(self):
        """
        Draws the 8-line status report in the top-right panel.
        """
        # --- Logic moved from _draw_current_srs_map ---
        self.is_docked = False
        condition = ""
        if self.quadrant_starbase:
            if abs(self.s1 - self.quadrant_starbase['s1']) <= 1 and \
               abs(self.s2 - self.quadrant_starbase['s2']) <= 1:
                self.is_docked = True
                condition = f"{Colors.CYAN}DOCKED{Colors.RESET}"
                self.energy = self.energy_start * self.difficulty.shield_multiplier
                self.torpedoes = 10
                self.shields = 0
                self.queue_message_instant(f"{Colors.CYAN}SHIELDS DROPPED FOR DOCKING.{Colors.RESET}")
        
        if not self.is_docked:
            if len(self.quadrant_klingons) > 0:
                condition = f"{Colors.RED}*RED*{Colors.RESET}"
            elif self.energy < self.energy_start * 0.1:
                condition = f"{Colors.YELLOW}YELLOW{Colors.RESET}"
            else:
                condition = f"{Colors.GREEN}GREEN{Colors.RESET}"
        # --- End of moved logic ---
        
        # --- Print the 8 status lines ---
        col = self.msg_box_col # Start at the same column
        
        # Helper to clear line and print
        def print_status(row, text):
            print(f"\033[{row};{col}H\033[K{text}", end="")

        print_status(1, f"STARDATE          {int(self.stardate * 10) / 10}")
        print_status(2, f"CONDITION         {condition}")
        print_status(3, f"QUADRANT          {self.q1},{self.q2}")
        print_status(4, f"SECTOR            {self.s1},{self.s2}")
        print_status(5, f"PHOTON TORPEDOES  {self.torpedoes}")
        print_status(6, f"TOTAL ENERGY      {int(self.energy + self.shields)}")
        print_status(7, f"SHIELDS           {int(self.shields)}")
        print_status(8, f"KLINGONS REMAINING {self.klingons_total}")
    
    def _draw_current_srs_map(self):
        """
        Helper function to draw the SRS map in the top-left pane.
        """
        # --- ANSI: Move cursor to Row 1, Col 1 ---
        print("\033[1;1H", end="")

        # 2. Sensor Damage Check
        if self.damage["SHORT_RANGE_SENSORS"] < 0:
            self.queue_message_instant(f"\n{Colors.RED}*** SHORT RANGE SENSORS ARE OUT ***{Colors.RESET}\n")
            quadrant_map = [["???" for _ in range(9)] for _ in range(9)]
        else:
            # 3. Build the 2D map data
            quadrant_map = [["   " for _ in range(9)] for _ in range(9)]
            quadrant_map[self.s1][self.s2] = f"{Colors.CYAN}<E>{Colors.RESET}"
            for k in self.quadrant_klingons:
                if k['shields'] > 0:
                    quadrant_map[k['s1']][k['s2']] = f"{Colors.RED}+K+{Colors.RESET}"
            if self.quadrant_starbase:
                quadrant_map[self.quadrant_starbase['s1']][self.quadrant_starbase['s2']] = f"{Colors.GREEN}>B<{Colors.RESET}"
            for s in self.quadrant_stars:
                quadrant_map[s['s1']][s['s2']] = f"{Colors.YELLOW} * {Colors.RESET}"

        # 4. Print Map (No status)
        top_bottom_border = "  +--1---2---3---4---5---6---7---8-+"
        print(top_bottom_border)

        for r in range(1, 9):
            row_str = f"{r} |"
            for c in range(1, 9):
                row_str += f" {quadrant_map[r][c]}" 
            row_str += f"|{r}"
            print(row_str)

        print(top_bottom_border)

    def _draw_console_art(self):
        """
        Draws the console art in the bottom-left pane.
        """
        # Move cursor to line 11 to start drawing
        print("\033[11;1H", end="")
        
        art_lines = load_ascii_art("console.txt")
        for line in art_lines:
            # --- FIX: Translate tags before printing ---
            translated_line = translate_art_tags(line)
            print(translated_line)
    
    def _draw_right_panel(self):
        """
        Draws the static UI for the right-hand message/command box.
        """
        col_start = self.msg_box_col - 1 # Start 1 column left for the border
        box_width = self.msg_box_width + 1 # Add 1 for the border
        
        # --- Draw Top Border (at Row 11) ---
        print(f"\033[11;{col_start}H+", end="")
        print("-" * box_width, end="")
        print("+", end="")
        
        # --- Draw Side Borders (from Row 12 to 31) ---
        for r in range(self.msg_box_top, self.cmd_box_top + 1): # Use constants
            print(f"\033[{r};{col_start}H|", end="")
            print(f"\033[{r};{col_start + box_width + 1}H|", end="")
        
        # --- Draw Middle Separator (at Row 30) ---
        print(f"\033[30;{col_start}H+", end="")
        print("-" * box_width, end="")
        print("+", end="")
        
        # --- Draw Bottom Border (at Row 32) ---
        print(f"\033[32;{col_start}H+", end="")
        print("-" * box_width, end="")
        print("+", end="")
            
    def _move_to_map_sector(self, r, c):
            """
            Moves the cursor to the center of a given map sector (r,c)
            on the map drawn by _draw_current_srs_map.
            """
            # Map row `r` is on screen row `r + 1` (border is on 1)
            screen_row = r + 1
            
            # Map col `c` starts at screen col 5, plus 4 for each preceding col
            # "r |" (3) + " " (1) + (c-1)*4 + " " (1, to be in the middle)
            screen_col = 5 + (c - 1) * 4 + 1 
            
            print(f"\033[{screen_row};{screen_col}H", end="")
        
    def run(self):
        """The main game loop. Now uses the new two-pane layout."""
        
        # --- REPLAY LOOP ---
        while True:
            # --- 1. SETUP ---
                  
            # Move cursor to message area (Line 15) and clear for text
            print("\033[15;1H\033[J", end="")
            self.setup_game()
            # --- STEP 2: SELECT DIFFICULTY (First thing asked) ---
            self.input_handler = self.handle_difficulty_select 
            
            # Run the input handler sequence for setup
            while self.input_handler:
                
                # --- FIX: DO NOT DRAW FULL UI YET ---
                # self._draw_full_ui() # <--- REMOVE/SKIP THIS
                
                # 2.1 Process Messages on the FULL SCREEN
                self._process_message_queue(use_full_width=True) # <-- USE FULL WIDTH
                
                # 2.2 Clear command prompt line and get input
                # Move cursor to a consistent location below the messages (e.g., line 25)
                #print(f"\033[25;1H\033[K", end="") # <-- MOVE PROMPT TO FULL-SCREEN LOCATION
                handler = self.input_handler
                self.input_handler = None
                handler() # Execute the current handler (Difficulty Select)
            
            # If the user quit during the setup phase, exit the replay loop
            if not self.is_running: 
                 break 
            
            # --- STEP 3: PLAY ANIMATION AND BRIEFING (AFTER difficulty is set) ---
            self.show_intro_animation() # Animation will clear screen
            self.show_mission_briefing() # Briefing uses queue_message
            
            # --- STEP 4: ACCEPT COMMAND (Y/N/I) ---
            self.input_handler = self.handle_y_n_i_input
            
            # Run the Y/N/I loop (Uses full screen for instructions/briefing display)
            while self.input_handler:
                # We still need the process message queue for instructions/briefing updates
                self._process_message_queue(use_full_width=True) 
                
                # Move cursor to a consistent location below the messages
               # print(f"\033[25;1H\033[K", end="") # <-- USE FULL-SCREEN LOCATION
                handler = self.input_handler
                self.input_handler = None
                handler()
            
            # If the user quit, exit
            if not self.is_running: 
                 break 
            
            # --- 5. MAIN GAME LOOP ---
            clear_screen() # Clear final setup text before drawing UI
            self.enter_quadrant() # Now start the game
            while self.is_running:
                # --- DRAW THE FULL UI ---
                self._draw_full_ui() 
                
                # 4. Print queued messages (using centralized function)
                self._process_message_queue() 
                
                # --- NEW PAUSE LOGIC ---
                if self.pause_after_messages:
                    self.pause_after_messages = False 
                    
                    active_klingons = [k for k in self.quadrant_klingons if k['shields'] > 0]
                    will_klingons_fire = self.hostile_action_taken and len(active_klingons) > 0
                    
                    if not will_klingons_fire:
                        # No Klingons will fire, so we must pause.
                        print(f"\033[{self.cmd_box_top};{self.msg_box_col}H\033[K", end="")
                        input("Press Enter to continue...")
                
                # 5. Handle Klingon Attacks (if any)
                if self.hostile_action_taken:
                    self.klingons_fire_back()
                    self.hostile_action_taken = False 
                    continue 
                    
                # 6. Move to prompt *inside* the box
                print(f"\033[{self.cmd_box_top};{self.msg_box_col}H\033[K", end="")
                # --- NEW INPUT LOGIC ---
                if self.input_handler:
                    handler = self.input_handler
                    self.input_handler = None
                    handler()
                else:
                    command = input("COMMAND? ").strip().upper()
                    self.handle_command(command)
                
                
                    
                # 7. Check for end-game conditions
                if self.klingons_total <= 0 and self.game_over_reason == "":
                    self.queue_message_instant("Congratulations, you have destroyed all Klingons!")
                    self.is_running = False
                    self.game_over_reason = "WIN"
                if self.stardate > self.stardate_end and self.game_over_reason == "":
                    self.queue_message_instant("Your time is up. The Federation has been conquered.")
                    self.is_running = False
                    self.game_over_reason = "TIME"
            
            # --- 4. GAME ENDS ---
            
            # Clear screen from the console art start point
            print("\033[11;1H\033[J", end="")
            
            # Print any final queued messages (e.g., "Congratulations...")
            self._process_message_queue(use_full_width=True)
            
            play_again = self._end_game()
            
            if play_again:
                self.__init__() 
                clear_screen()
            else:
                break
    
    def handle_command(self, command):
        """Routes the user's command to the correct function."""
        if command == "NAV":
            self.nav_command()
        elif command == "SRS":
            pass # Already drawn, so we do nothing
        elif command == "LRS":
            self.lrs_command()
        elif command == "PHA":
            self.pha_command()
        elif command == "TOR":
            self.tor_command()
        elif command == "SHE":
            self.she_command()
        elif command == "DAM":
            self.dam_command()
        elif command == "COM":
            self.com_command()
        elif command == "XXX":
            self.xxx_command()
        else:
            self.print_help()
    
    def nav_command(self):
        """
        Handles the NAV command. Queues the first prompt
        and sets the input handler.
        """
        self.queue_message_instant("'NAV' COMMAND = WARP ENGINE CONTROL --", color=Colors.CYAN)
        self.queue_message_instant("      4  3  2")
        self.queue_message_instant("       . . .")
        self.queue_message_instant("        ...")
        self.queue_message_instant("    5 ---*--- 1")
        self.queue_message_instant("        ...")
        self.queue_message_instant("      . . .")
        self.queue_message_instant("      6  7  8")
        self.input_handler = self.handle_nav_course

    def _process_message_queue(self, use_full_width=False,start_row = 15):
        """
        Processes and prints all queued messages.
        
        Args:
            use_full_width (bool): If True, messages are printed across the full 
                                   screen width (for setup/end game).
                                   If False (default), they are printed inside 
                                   the message box (main game loop).
        """
        if use_full_width:
           # start_row = 15
            current_row = start_row
            max_width = 78
            
            # Clear screen from the start row down
            print(f"\033[{start_row};1H\033[J", end="") 
            
            for msg_args in self.message_queue:
                # Wrap the text using full width
                lines = textwrap.wrap(msg_args["text"], width=max_width)
                if not lines: lines = [""] # Handle blank lines

                for line in lines:
                    print(f"\033[{current_row};1H", end="") # Move to the line
                    self.typewriter_print(
                        text=line,
                        delay=msg_args["delay"],
                        color=msg_args["color"],
                        newline=False
                    )
                    current_row += 1 # Move to next line
        
        else:
            # Main game UI box logic
            message_row = self.msg_box_top
            
            # Clear the message box
            for r in range(self.msg_box_top, self.msg_box_bottom + 1):
                print(f"\033[{r};{self.msg_box_col}H\033[K", end="")
            print(f"\033[{message_row};{self.msg_box_col}H", end="") # Move cursor to top of box

            # Print queued messages
            for msg_args in self.message_queue:
                if message_row > self.msg_box_bottom:
                    break # Stop printing if we run out of space
                
                # ANSI-AWARE TEXT WRAP LOGIC
                lines = []
                # First, split by any manual newlines
                for line in msg_args["text"].split('\n'):
                    if get_visible_length(line) <= self.msg_box_width:
                        lines.append(line)
                    else:
                        current_line = ""
                        words = line.split(' ')
                        for word in words:
                            if get_visible_length(word) > self.msg_box_width:
                                if current_line: lines.append(current_line)
                                lines.append(word)
                                current_line = ""
                                continue
                            
                            test_line = current_line + " " + word if current_line else word
                            if get_visible_length(test_line) <= self.msg_box_width:
                                current_line = test_line
                            else:
                                lines.append(current_line)
                                current_line = word
                        
                        if current_line: lines.append(current_line)
                
                if not lines: lines = [""] 

                for line in lines:
                    if message_row > self.msg_box_bottom:
                        break
                    # Move to the correct row AND column, and clear the line
                    print(f"\033[{message_row};{self.msg_box_col}H\033[K", end="")
                    self.typewriter_print(
                        text=line,
                        delay=msg_args["delay"],
                        color=msg_args["color"],
                        newline=False
                    )
                    message_row += 1 
                    
        self.message_queue.clear() # Clear queue for next turn


    def _draw_full_ui(self):
        """Draws the entire two-pane UI: Map, Status, Console Art, and Message Box border."""
        self.srs_command()          # Draws map at [1;1]
        self._draw_status_panel()   # Draws status lines
        self._draw_console_art()    # Draws art at [11;1]
        self._draw_right_panel()    # Draws the message box border

    def handle_nav_course(self):
        """Gets the COURSE input for NAV."""
        try:
            course = float(input("COURSE (1-8): "))
            if course == 9: course = 1
            if not 1 <= course < 9:
                self.queue_message_instant("   LT. SULU: 'INCORRECT COURSE DATA, SIR!'", color=Colors.RED)
                return
            
            # Store course and set next handler
            self.command_data = {'course': course}
            self.input_handler = self.handle_nav_warp
            
        except ValueError:
            self.queue_message_instant("   LT. SULU: 'INCORRECT COURSE DATA, SIR!'", color=Colors.RED)

    def handle_nav_warp(self):
        """Gets the WARP input and executes the NAV command."""
        try:
            course = self.command_data['course']
            
            max_warp = 8.0
            if self.damage["WARP_ENGINES"] < 0:
                max_warp = 0.2
                self.queue_message_instant(f"   CHIEF ENGINEER SCOTT: 'WARP ENGINES DAMAGED. MAX = {max_warp}'")
            
            warp = float(input(f"WARP FACTOR (0-{max_warp}): "))
            if warp <= 0: return
            if warp > max_warp:
                self.queue_message_instant(f"   CHIEF ENGINEER SCOTT: 'THE ENGINES WON'T TAKE WARP {warp}!'")
                return
            
            # --- All input is gathered, now execute the command ---
            self.execute_nav_move(course, warp)

        except ValueError:
            self.queue_message_instant("   CHIEF ENGINEER SCOTT: 'INVALID WARP FACTOR!'")
        
        self.command_data = {} # Clear temp data
        self.pause_after_messages = True
        
    def execute_nav_move(self, course, warp):
        """The actual logic for the NAV move, separated from the input."""
        # --- STEP 3: CALCULATE MOVEMENT ---
        distance_sectors = int(warp * 8 + 0.5)

        # Check energy
        if self.energy < distance_sectors:
            self.queue_message_instant("   ENGINEERING: 'INSUFFICIENT ENERGY FOR MANEUVER.'", color=Colors.RED)
            energy_deficit = distance_sectors - self.energy
            if self.shields < energy_deficit or self.damage["SHIELD_CONTROL"] < 0:
                return 
            else:
                self.queue_message_instant("   DEFLECTOR CONTROL ROOM:", color=Colors.CYAN)
                self.queue_message_instant(f"     '{self.shields:.0f} UNITS OF ENERGY PRESENTLY DEPLOYED TO SHIELDS.'", color=Colors.CYAN)
                self.queue_message_instant("   (USE 'SHE' COMMAND TO TRANSFER ENERGY)", color=Colors.YELLOW)
                return

        dRow, dCol = self._get_vector(course)
        
        # --- KLINGON MOVEMENT (Lines 2610-2700) ---
        occupied_sectors = set()
        occupied_sectors.add((self.s1, self.s2)) # Enterprise
        if self.quadrant_starbase:
            occupied_sectors.add((self.quadrant_starbase['s1'], self.quadrant_starbase['s2']))
        for s in self.quadrant_stars:
            occupied_sectors.add((s['s1'], s['s2']))
        
        klingon_positions = set()
        for k in self.quadrant_klingons:
            if k['shields'] > 0:
                klingon_positions.add((k['s1'], k['s2']))
        occupied_sectors.update(klingon_positions)

        for k in self.quadrant_klingons:
            if k['shields'] <= 0:
                continue
            occupied_sectors.remove((k['s1'], k['s2']))
            new_s1, new_s2 = self._get_random_sector(occupied_sectors)
            k['s1'] = new_s1
            k['s2'] = new_s2
            occupied_sectors.add((new_s1, new_s2))
            
        # --- STEP 4 & 5: EXECUTE MOVE ---
        quadrant_map = [["   " for _ in range(9)] for _ in range(9)]
        for k in self.quadrant_klingons:
            if k['shields'] > 0: quadrant_map[k['s1']][k['s2']] = "+K+"
        if self.quadrant_starbase:
            quadrant_map[self.quadrant_starbase['s1']][self.quadrant_starbase['s2']] = ">B<"
        for s in self.quadrant_stars:
            quadrant_map[s['s1']][s['s2']] = " * "

        final_row_f = self.s1 + distance_sectors * dRow
        final_col_f = self.s2 + distance_sectors * dCol
        
        quadrant_changed = False
        time_elapsed = 0.0

        if 1 <= final_row_f <= 8.99 and 1 <= final_col_f <= 8.99:
            self.queue_message_instant("   LT. SULU: 'MANEUVERING WITHIN QUADRANT.'")
            
            for i in range(1, distance_sectors + 1):
                new_row = int(self.s1 + i * dRow + 0.5)
                new_col = int(self.s2 + i * dCol + 0.5)

                if not (1 <= new_row <= 8 and 1 <= new_col <= 8):
                    continue 

                if quadrant_map[new_row][new_col] != "   ":
                    self.queue_message_instant("   LT. SULU: 'WARP ENGINES SHUT DOWN AT SECTOR")
                    self.queue_message_instant(f"             {new_row},{new_col} DUE TO OBSTACLE!'")
                    self.s1 = int(self.s1 + (i - 1) * dRow + 0.5)
                    self.s2 = int(self.s2 + (i - 1) * dCol + 0.5)
                    break
                
                self.s1 = new_row
                self.s2 = new_col
                
            time_elapsed = 1.0 if warp >= 1.0 else warp

        else:
            # --- Inter-Quadrant Move (Lines 3500-3870) ---
            self.queue_message_instant("   LT. UHURA: 'MANEUVERING, PREPARING FOR QUADRANT CHANGE.'")
            quadrant_changed = True
            
            global_row_start = (self.q1 - 1) * 8 + (self.s1 - 1)
            global_col_start = (self.q2 - 1) * 8 + (self.s2 - 1)
            
            global_row_end = global_row_start + distance_sectors * dRow
            global_col_end = global_col_start + distance_sectors * dCol

            if global_row_end < 0 or global_row_end > 63 or \
               global_col_end < 0 or global_col_end > 63:
                
                self.queue_message_instant("   LT. UHURA: 'MESSAGE FROM STARFLEET COMMAND --", color=Colors.YELLOW)
                self.queue_message_instant("     'PERMISSION TO ATTEMPT CROSSING OF GALACTIC PERIMETER", color=Colors.YELLOW)
                self.queue_message_instant("     IS HEREBY *DENIED*.'", color=Colors.YELLOW)

                if global_row_end < 0:
                    global_row_end = -global_row_end
                elif global_row_end > 63:
                    overshoot_row = global_row_end - 63
                    global_row_end = 63 - overshoot_row
                
                if global_col_end < 0:
                    global_col_end = -global_col_end
                elif global_col_end > 63:
                    overshoot_col = global_col_end - 63
                    global_col_end = 63 - overshoot_col

            self.q1 = int(global_row_end // 8) + 1
            self.s1 = int(global_row_end % 8) + 1
            self.q2 = int(global_col_end // 8) + 1
            self.s2 = int(global_col_end % 8) + 1
            
            time_elapsed = 1.0

        # --- STEP 6: POST-MOVE UPDATES ---
        self.energy -= (distance_sectors + 10)
        self.stardate += time_elapsed
        
        repair_rate = 1.0 if warp >= 1.0 else warp
        repair_header_printed = False
        
        device_keys = list(self.damage.keys()) 
        for i in range(8):
            key = device_keys[i]
            if self.damage[key] < 0:
                self.damage[key] += repair_rate
                if self.damage[key] >= 0:
                    self.damage[key] = 0.0 
                    if not repair_header_printed:
                        self.queue_message_instant("   DAMAGE CONTROL REPORT:", color=Colors.CYAN)
                        repair_header_printed = True
                    device_name = get_device_name(i + 1)
                    self.queue_message_instant(f"     {device_name} REPAIR COMPLETED.", color=Colors.GREEN)

        if random.random() < 0.20:
            device_index = random.randint(1, 8) 
            device_key = list(self.damage.keys())[device_index - 1]
            device_name = get_device_name(device_index)
            
            if random.random() < 0.60:
                damage_amount = random.random() * 5 + 1
                self.damage[device_key] -= damage_amount
                self.queue_message_instant("   DAMAGE CONTROL REPORT:", color=Colors.RED)
                self.queue_message_instant(f"     {device_name} DAMAGED.", color=Colors.RED)
            else:
                repair_amount = random.random() * 3 + 1
                self.damage[device_key] += repair_amount
                if self.damage[device_key] > 0:
                    self.damage[device_key] = 0.0 
                    
                self.queue_message_instant("   DAMAGE CONTROL REPORT:", color=Colors.YELLOW)
                self.queue_message_instant(f"     {device_name} STATE OF REPAIR IMPROVED.", color=Colors.YELLOW)
        
        self.hostile_action_taken = True
        
        if quadrant_changed:
            self.enter_quadrant() 
        
        if self.stardate > self.stardate_end:
            self.queue_message_instant(f"IT IS STARDATE {self.stardate}.", color=Colors.YELLOW)
            self.queue_message_instant("YOUR MISSION HAS FAILED.", color=Colors.RED)
            self.is_running = False 
            self.game_over_reason = "TIME"
        
    def srs_command(self):
        """
        Draws the Short Range Sensor scan and status report.
        This translates lines 6430-7260.
        """
        self._draw_current_srs_map()
       
        
    def lrs_command(self):
        """TranslATES logic from line 4000."""
        
        
        self.queue_message_instant("--- Long Range Scan ---", color=Colors.GREEN)
        self.queue_message_instant("-------------------", color=Colors.GREEN)
        
        for r in range(self.q1 - 1, self.q1 + 2):
            row_str = "|"
            for c in range(self.q2 - 1, self.q2 + 2):
                
                is_current_quadrant = (r == self.q1 and c == self.q2)
                start_color = Colors.CYAN if is_current_quadrant else ""
                end_color = Colors.RESET if is_current_quadrant else ""

                if 1 <= r <= 8 and 1 <= c <= 8:
                    scan_data = self.galaxy[r][c]
                    self.galaxy_known[r][c] = True
                    row_str += f" {start_color}{scan_data:03d}{end_color} |"
                else:
                    row_str += f" {start_color}***{end_color} |" # Outside galaxy
            
            self.queue_message_instant(row_str)
        
        self.queue_message_instant("-------------------", color=Colors.GREEN)

    
    def pha_command(self):
        """
        Handles the PHA command for firing phasers.
        This now queues the menu and sets the input handler.
        """
        # --- 1. PRE-FIRE CHECKS ---
        if self.damage["PHASER_CONTROL"] < 0:
            self.queue_message_instant(f"   {Colors.RED}PHASERS ARE INOPERATIVE.{Colors.RESET}")
            return

        active_klingons = [k for k in self.quadrant_klingons if k['shields'] > 0]
        
        if not active_klingons:
            self.queue_message_instant(f"   {Colors.CYAN}MR. SPOCK: 'SENSORS SHOW NO ENEMY SHIPS IN THIS QUADRANT.'{Colors.RESET}")
            return
            
        # --- 2. QUEUE PROMPTS & SET HANDLER ---
        self.queue_message_instant(f"   PHASERS LOCKED ON {len(active_klingons)} KLINGON(S).")
        self.queue_message_instant(f"   ENERGY AVAILABLE = {self.energy:.0f} UNITS")
        
        self.input_handler = self.handle_pha_input

    def handle_pha_input(self):
        """Gets the ENERGY input for PHA and executes the command."""
        try:
            fire_energy = float(input("   NUMBER OF UNITS TO FIRE: "))
            
            if fire_energy <= 0:
                return # Abort
            if fire_energy > self.energy:
                self.queue_message_instant(f"   {Colors.RED}ENGINEERING: 'INSUFFICIENT ENERGY.'{Colors.RESET}")
                return
            
            # --- All input is gathered, now execute the command ---
            self.execute_pha_fire(fire_energy)

        except ValueError:
            self.queue_message_instant(f"   {Colors.RED}INVALID ENERGY AMOUNT.{Colors.RESET}")
            return

    def execute_pha_fire(self, fire_energy):
        """The actual logic for firing phasers, separated from input."""
        
        self.energy -= fire_energy
        active_klingons = [k for k in self.quadrant_klingons if k['shields'] > 0]
        
        # --- 3. CALCULATE & DISTRIBUTE ENERGY ---
        energy_per_klingon = fire_energy / len(active_klingons)
        
        # Re-draw the map so the animation has a background
        self._draw_current_srs_map()
        
        self.queue_message("   PHASERS FIRING...", delay=0.02)
        
        for k in active_klingons:
            distance = get_distance(self.s1, self.s2, k['s1'], k['s2'])
            if distance == 0: distance = 0.1
            
            # --- 4. ANIMATION (Draw beam) ---
            self._move_to_map_sector(self.s1, self.s2)
            print(f"{Colors.MAGENTA}*--{Colors.RESET}", end="")
            sys.stdout.flush()
            time.sleep(0.1)
            self._move_to_map_sector(k['s1'], k['s2'])
            print(f"{Colors.MAGENTA}--*{Colors.RESET}", end="")
            sys.stdout.flush()
            time.sleep(0.3)
            
            # --- 5. CALCULATE & REPORT HIT ---
            hit_strength = int((energy_per_klingon / distance) * (2 + random.random()))
            k['shields'] -= hit_strength
            
            if k['shields'] <= 0:
                self.queue_message_instant(f"   *** {Colors.RED}KLINGON DESTROYED{Colors.RESET} AT SECTOR {k['s1']},{k['s2']} ***", color=Colors.RED)
                k['shields'] = 0 # Set shields to 0
                self.klingons_total -= 1
                time.sleep(1)
            else:
                self.queue_message_instant(f"   {hit_strength} UNIT HIT ON KLINGON AT SECTOR {k['s1']},{k['s2']}. (SENSORS SHOW {k['shields']:.0f} UNITS REMAINING)", color=Colors.YELLOW)
                time.sleep(1)
        # --- 6. CLEANUP & POST-FIRE ---
        
        # Update galaxy map data
        k_count = len([k for k in self.quadrant_klingons if k['shields'] > 0])
        b_count = 1 if self.quadrant_starbase else 0
        s_count = len(self.quadrant_stars)
        self.galaxy[self.q1][self.q2] = k_count * 100 + b_count * 10 + s_count
        
        self.hostile_action_taken = True
        
            
    
    def tor_command(self):
        """
        Handles the TOR command. Queues the first prompt
        and sets the input handler.
        """
        # --- 1. PRE-FIRE CHECKS ---
        if self.torpedoes <= 0:
            self.queue_message_instant(f"   {Colors.RED}ALL PHOTON TORPEDOES EXPENDED.{Colors.RESET}")
            return

        if self.damage["PHOTON_TUBES"] < 0:
            self.queue_message_instant(f"   {Colors.RED}PHOTON TUBES ARE NOT OPERATIONAL.{Colors.RESET}")
            return
            
        # --- 2. QUEUE MENU & SET HANDLER ---
        self.queue_message_instant("'TOR' COMMAND = PHOTON TORPEDO CONTROL --", color=Colors.CYAN)
        self.queue_message_instant("      4  3  2")
        self.queue_message_instant("       . . .")
        self.queue_message_instant("        ...")
        self.queue_message_instant("    5 ---*--- 1")
        self.queue_message_instant("        ...")
        self.queue_message_instant("      . . .")
        self.queue_message_instant("      6  7  8")
        self.input_handler = self.handle_tor_course

    def handle_tor_course(self):
        """Gets the COURSE input for TOR and executes the command."""
        try:
            course = float(input("PHOTON TORPEDO COURSE (1-8): "))
            if course == 9: course = 1
            if not 1 <= course < 9:
                self.queue_message_instant("   ENSIGN CHEKOV: 'INCORRECT COURSE DATA, SIR!'")
                return
                
            # --- All input is gathered, now execute the command ---
            self.execute_tor_fire(course)

        except ValueError:
            self.queue_message_instant("   ENSIGN CHEKOV: 'INCORRECT COURSE DATA, SIR!'")

    def execute_tor_fire(self, course):
        """The actual logic for firing a torpedo, separated from input."""
        # --- 3. FIRE TORPEDO & ANIMATE ---
        self.energy -= 2
        self.torpedoes -= 1
        dRow, dCol = self._get_vector(course)
        
        track_row_f = float(self.s1)
        track_col_f = float(self.s2)
        prev_r, prev_c = self.s1, self.s2
        
        hit_target = False

        # Redraw the map for the animation
        self._draw_current_srs_map()

        # --- 4. TRACKING LOOP ---
        for _ in range(15): # Max range of 15 sectors
            track_row_f += dRow
            track_col_f += dCol
            r, c = int(track_row_f + 0.5), int(track_col_f + 0.5)

            # --- Animation Part ---
            self._move_to_map_sector(prev_r, prev_c)
            print(f"{Colors.YELLOW}.{Colors.RESET}", end="")
            self._move_to_map_sector(r, c)
            print(f"{Colors.RED}*{Colors.RESET}", end="")
            sys.stdout.flush() 
            time.sleep(0.2)
            prev_r, prev_c = r, c
            # --- End Animation Part ---

            # Check if torpedo left the quadrant
            if not (1 <= r <= 8 and 1 <= c <= 8):
                self.queue_message_instant("   TORPEDO MISSED.", color=Colors.YELLOW)
                break
                
            # Check for Klingon hit
            for k in self.quadrant_klingons:
                if k['shields'] > 0 and k['s1'] == r and k['s2'] == c:
                    self._move_to_map_sector(r, c)
                    print(f"{Colors.RED}{Colors.BOLD}*!*{Colors.RESET}", end="") # EXPLOSION
                    sys.stdout.flush()
                    self.queue_message_instant(f"\n*** {Colors.RED}KLINGON DESTROYED{Colors.RESET} ***")
                    k['shields'] = 0
                    self.klingons_total -= 1
                    k_count = len([k for k in self.quadrant_klingons if k['shields'] > 0])
                    b_count = 1 if self.quadrant_starbase else 0
                    s_count = len(self.quadrant_stars)
                    self.galaxy[self.q1][self.q2] = k_count * 100 + b_count * 10 + s_count
                    hit_target = True
                    break
            if hit_target: break

            # Check for Starbase hit
            if self.quadrant_starbase and self.quadrant_starbase['s1'] == r and self.quadrant_starbase['s2'] == c:
                self._move_to_map_sector(r, c)
                print(f"{Colors.RED}{Colors.BOLD}*!*{Colors.RESET}", end="") # EXPLOSION
                sys.stdout.flush()
                self.queue_message_instant(f"\n*** {Colors.RED}{Colors.BOLD}STARBASE DESTROYED{Colors.RESET} ***")
                self.queue_message_instant("   STARFLEET COMMAND REVIEWING YOUR RECORD...")
                self.quadrant_starbase = None
                self.starbases_total -= 1
                hit_target = True
                break
            
            # Check for Star hit
            for s in self.quadrant_stars:
                if s['s1'] == r and s['s2'] == c:
                    self.queue_message_instant(f"   {Colors.YELLOW}STAR AT {r},{c} ABSORBED TORPEDO ENERGY.{Colors.RESET}")
                    hit_target = True
                    break
            if hit_target: break
        
        # --- 5. POST-FIRE ---
        time.sleep(1) # Pause on the final frame
        self.hostile_action_taken = True
        
    def she_command(self):
        """
        Handles the SHE command. Queues the first prompt
        and sets the input handler.
        """
        # --- 1. PRE-COMMAND CHECKS ---
        if self.damage["SHIELD_CONTROL"] < 0:
            self.queue_message_instant(f"   {Colors.RED}SHIELD CONTROL IS INOPERABLE.{Colors.RESET}")
            return

        # --- 2. QUEUE PROMPTS & SET HANDLER ---
        total_energy = self.energy + self.shields
        self.queue_message_instant(f"   ENERGY AVAILABLE = {total_energy:.0f} UNITS")
        self.input_handler = self.handle_she_input

    def handle_she_input(self):
        """Gets the ENERGY input for SHE and executes the command."""
        try:
            total_energy = self.energy + self.shields
            new_shield_level = float(input(f" NUMBER OF UNITS TO SHIELDS (currently {self.shields:.0f}): "))
            
        except ValueError:
            self.queue_message_instant(f"   {Colors.RED}INVALID ENERGY AMOUNT.{Colors.RESET}")
            return

        # --- 3. VALIDATE INPUT ---
        if new_shield_level < 0 or new_shield_level == self.shields:
            self.queue_message_instant(f"   {Colors.YELLOW}<SHIELDS UNCHANGED>{Colors.RESET}")
            return

        if new_shield_level > total_energy:
            self.queue_message_instant(f"   {Colors.RED}SHIELD CONTROL: 'THIS IS NOT THE FEDERATION TREASURY.'{Colors.RESET}")
            self.queue_message_instant(f"   {Colors.YELLOW}<SHIELDS UNCHANGED>{Colors.RESET}")
            return

        # --- 4. EXECUTE TRANSFER ---
        self.energy = total_energy - new_shield_level
        self.shields = new_shield_level
        
        self.queue_message_instant("   DEFLECTOR CONTROL ROOM:")
        self.queue_message_instant(f"   'SHIELDS NOW AT {self.shields:.0f} UNITS PER YOUR COMMAND.'", color=Colors.GREEN)
        
    def _queue_damage_report(self):
        """Queues the Damage Control Report to be displayed in the message box."""
        self.queue_message_instant("--- Damage Control Report ---", color=Colors.CYAN)
        for device, status in self.damage.items():
            status_formatted = f"{status:.2f}"
            if status < 0:
                self.queue_message_instant(f"  {device.ljust(22)}: {status_formatted}", color=Colors.RED)
            else:
                self.queue_message_instant(f"  {device.ljust(22)}: {status_formatted}")
        
    def dam_command(self):
        """
        Queues the Damage Control Report and, if docked,
        asks for repair authorization.
        """
        # 1. Queue the damage report for this turn
        self._queue_damage_report()

        # 2. Check if we are docked
        if self.is_docked:
            total_damage = sum(abs(d) for d in self.damage.values() if d < 0)
            if total_damage > 0:
                # 3. If docked and damaged, set input handler for next turn
                # Calculate repair time
                repair_time = (total_damage / 10.0) + 0.1 # Simplified time calculation
                self.command_data = {'repair_time': repair_time} # Store for the handler
                
                self.queue_message_instant("") # Blank line
                self.queue_message_instant("TECHNICIANS STANDING BY TO EFFECT REPAIRS.", color=Colors.YELLOW)
                self.queue_message_instant(f"ESTIMATED TIME TO REPAIR: {repair_time:.2f} STARDATES.", color=Colors.YELLOW)
                
                self.input_handler = self.handle_repair_input
            else:
                self.queue_message_instant("ALL SYSTEMS FUNCTIONAL.", color=Colors.GREEN)

    def handle_repair_input(self):
        """
        Handles the repair authorization input and executes the repair action 
        if authorized. (Translates part of BASIC lines 5590-5620).
        """
        repair_time = self.command_data.get('repair_time', 0)
        
        # --- Prompt for Authorization ---
        response = input("DO YOU AUTHORIZE REPAIRS? (Y/N): ").strip().upper()
        
        if response == "Y":
            # --- Execute Repair ---
            self.stardate += repair_time
            self.time_remaining -= repair_time
            
            # Reset all damage to zero
            for key in self.damage:
                self.damage[key] = 0.0
            
            # Reset the hostile action flag to prevent immediate Klingon attack
            # since time has jumped forward.
            self.hostile_action_taken = False
            
            self.queue_message_instant(f"REPAIRS COMPLETED. TIME ELAPSED: {repair_time:.2f} STARDATES.", color=Colors.GREEN)
            
            # Check for immediate time-based game over
            if self.stardate > self.stardate_end:
                self.queue_message_instant(f"IT IS STARDATE {self.stardate:.1f}.", color=Colors.YELLOW)
                self.queue_message_instant("YOUR MISSION HAS FAILED.", color=Colors.RED)
                self.is_running = False 
                self.game_over_reason = "TIME"

        elif response == "N":
            self.queue_message_instant("REPAIRS ABORTED. DAMAGE REMAINS.", color=Colors.YELLOW)
        else:
            self.queue_message_instant("INVALID RESPONSE. REPAIRS ABORTED.", color=Colors.RED)
        
        self.command_data = {} # Clear temp data
    
    
    
    def _com_galactic_record(self):
        """
        COM Option 0: Queues the new full-panel Galactic Record
        to be printed in the message box.
        """
        # --- FIX: We are now a "report" command. ---
        # We ONLY queue messages.
        
        self.queue_message_instant(f"   {Colors.CYAN}COMPUTER RECORD OF GALAXY{Colors.RESET}")
        self.queue_message_instant(f"   (Quadrant {self.q1},{self.q2} is highlighted)")
        self.queue_message_instant("") # Blank line
        
        # --- Draw the new compact map (from example.txt) ---
        self.queue_message_instant("     1   2   3   4   5   6   7   8")
        
        # Border is 37 chars wide, fits in our 40-char box
        border = "   +---+---+---+---+---+---+---+---+"
        self.queue_message_instant(border)
        
        for r in range(1, 9):
            # Start row with "r|" (e.g., " 1|")
            row_str = f" {r} |" 
            for c in range(1, 9):
                if self.galaxy_known[r][c]:
                    scan_data = self.galaxy[r][c] # K, B, S (e.g., 201)
                    
                    if r == self.q1 and c == self.q2:
                        # Highlight the current quadrant
                        row_str += f"{Colors.CYAN}{scan_data:03d}{Colors.RESET}|"
                    else:
                        # Show all three digits
                        row_str += f"{scan_data:03d}|"
                else:
                    # Quadrant not yet scanned, as per example.txt
                    row_str += f"...|" 
            
            self.queue_message_instant(row_str)
            
        self.queue_message_instant(border)
        self.queue_message_instant("   (Map shows Klingon, Base, Star count)")

        # --- FIX: No input() pause needed. ---

    def _com_status_report(self):
        """COM Option 1: Queues Status Report"""
        self.queue_message_instant("   STATUS REPORT:", color=Colors.CYAN)
        
        klingon_s = "S" if self.klingons_total != 1 else ""
        self.queue_message_instant(f"   {self.klingons_total} KLINGON{klingon_s} LEFT.")
        
        time_left = (self.stardate_end - self.stardate)
        self.queue_message_instant(f"   MISSION MUST BE COMPLETED IN {time_left:.1f} STARDATES.")
        
        starbase_s = "S" if self.starbases_total != 1 else ""
        if self.starbases_total > 0:
            self.queue_message_instant(f"   THE FEDERATION IS MAINTAINING {self.starbases_total} STARBASE{starbase_s} IN THE GALAXY.")
        else:
            self.queue_message_instant(f"   {Colors.RED}YOUR STUPIDITY HAS LEFT YOU ON YOUR OWN -- YOU HAVE NO STARBASES LEFT!{Colors.RESET}")
        
        # Also queue the damage report
        self.queue_message_instant("") # Blank line
        self._queue_damage_report() # This will queue the damage report

    def _com_torpedo_data(self):
        """COM Option 2: Queues Photon Torpedo Data"""
        active_klingons = [k for k in self.quadrant_klingons if k['shields'] > 0]
        if not active_klingons:
            self.queue_message_instant(f"   {Colors.CYAN}MR. SPOCK: 'SENSORS SHOW NO ENEMY SHIPS IN THIS QUADRANT.'{Colors.RESET}")
            return
            
        klingon_s = "S" if len(active_klingons) != 1 else ""
        self.queue_message_instant(f"   FROM ENTERPRISE TO KLINGON BATTLE CRUSER{klingon_s}:", color=Colors.CYAN)
        
        for k in active_klingons:
            course, distance = get_course_and_distance(self.s1, self.s2, k['s1'], k['s2'])
            self.queue_message_instant(f"     SECTOR {k['s1']},{k['s2']}: DIRECTION = {course:.2f}, DISTANCE = {distance:.2f}")

    def _com_starbase_data(self):
        """COM Option 3: Queues Starbase Nav Data"""
        if not self.quadrant_starbase:
            self.queue_message_instant(f"   {Colors.CYAN}MR. SPOCK: 'SENSORS SHOW NO STARBASES IN THIS QUADRANT.'{Colors.RESET}")
            return
            
        self.queue_message_instant("   FROM ENTERPRISE TO STARBASE:", color=Colors.CYAN)
        b = self.quadrant_starbase
        course, distance = get_course_and_distance(self.s1, self.s2, b['s1'], b['s2'])
        self.queue_message_instant(f"     SECTOR {b['s1']},{b['s2']}: DIRECTION = {course:.2f}, DISTANCE = {distance:.2f}")

    def com_command(self):
        """
        Handles the COM command for the Library-Computer.
        This now queues the menu and sets the input handler.
        """
        if self.damage["LIBRARY_COMPUTER"] < 0:
            self.queue_message_instant(f"   {Colors.RED}LIBRARY-COMPUTER IS INOPERABLE.{Colors.RESET}")
            return

        # --- FIX: Queue the menu ---
        self.queue_message_instant(f"   {Colors.CYAN}FUNCTIONS AVAILABLE FROM LIBRARY-COMPUTER:{Colors.RESET}")
        self.queue_message_instant("   -----------------------------------------")
        self.queue_message_instant("   0 = CUMULATIVE GALACTIC RECORD")
        self.queue_message_instant("   1 = STATUS REPORT")
        self.queue_message_instant("   2 = PHOTON TORPEDO DATA")
        self.queue_message_instant("   3 = STARBASE NAV DATA")
        self.queue_message_instant("   4 = DIRECTION/DISTANCE CALCULATOR")
        self.queue_message_instant("   5 = GALAXY 'REGION NAME' MAP")
        self.queue_message_instant("")
        
        # --- FIX: Set the input handler ---
        self.input_handler = self.handle_com_input
            
    def _com_region_map(self):
        """COM Option 5: Queues Galaxy 'Region Name' Map"""
        self.queue_message_instant("         --- GALACTIC REGION MAP ---", color=Colors.CYAN)
        border = "    +-----------------+-----------------+"
        self.queue_message_instant(border)
        self.queue_message_instant("    |   (Columns 1-4) |   (Columns 5-8) |")
        self.queue_message_instant(border)
        
        for r in range(1, 9):
            name1 = get_quadrant_name(r, 1).split(" ")[0]
            name2 = get_quadrant_name(r, 5).split(" ")[0]
            
            row_str = f" {r}  | {name1.ljust(15)} | {name2.ljust(15)} |"
            self.queue_message_instant(row_str)
        self.queue_message_instant(border)
    
    
    def handle_com_input(self):
        """Handles the input *after* the COM menu is displayed."""
        try:
            choice = int(input(f"COMPUTER ACTIVE AND AWAITING COMMAND: "))
            
            if choice == 0:
                self._com_galactic_record()
            elif choice == 1:
                self._com_status_report()
            elif choice == 2:
                self._com_torpedo_data()
            elif choice == 3:
                self._com_starbase_data()
            elif choice == 4:
                self._com_calculator_run() # This one is special
            elif choice == 5:
                self._com_region_map()
            else:
                self.queue_message_instant(f"   {Colors.RED}INVALID COMMAND.{Colors.RESET}")
                
        except ValueError:
            self.queue_message_instant(f"   {Colors.RED}INVALID COMMAND.{Colors.RESET}")

    def _com_calculator_run(self):
        """COM Option 4: Queues prompts for the calculator."""
        self.queue_message_instant(f"   --- DIRECTION/DISTANCE CALCULATOR ---")
        self.queue_message_instant(f"   You are at Quadrant {self.q1},{self.q2} Sector {self.s1},{self.s2}")
        
        # Set the next input handler
        self.input_handler = self.handle_calc_input_start
    
    def handle_calc_input_1(self):
        """Gets the START coordinates (Q1, S1)."""
        try:
            # We are asking for two numbers (Q1 and S1) separated by a comma
            coords_str = input("START Q/S (e.g., 5,1): ").strip()
            q1, s1 = map(int, coords_str.split(','))
            
            # Input validation (must be between 1 and 8)
            if not (1 <= q1 <= 8 and 1 <= s1 <= 8):
                 self.queue_message_instant(f"   {Colors.RED}INVALID START COORDINATES (Q and S must be 1-8).{Colors.RESET}")
                 return
            
            # Store Q1 and S1 and proceed to next handler
            self.command_data['q1'] = q1
            self.command_data['s1'] = s1
            self.input_handler = self.handle_calc_input_2
            
        except ValueError:
            self.queue_message_instant(f"   {Colors.RED}INVALID INPUT FORMAT. USE Q,S (e.g., 5,1).{Colors.RESET}")
    
    def handle_calc_input_2(self):
        """Gets the END coordinates (Q2, S2) and performs the calculation."""
        try:
            # Get data stored from previous step
            q1 = self.command_data['q1']
            s1 = self.command_data['s1']
            
            coords_str = input("END Q/S (e.g., 8,8): ").strip()
            q2, s2 = map(int, coords_str.split(','))
            
            # Input validation (must be between 1 and 8)
            if not (1 <= q2 <= 8 and 1 <= s2 <= 8):
                 self.queue_message_instant(f"   {Colors.RED}INVALID END COORDINATES (Q and S must be 1-8).{Colors.RESET}")
                 return

            # --- CORE CALCULATION LOGIC ---
            # 1. Convert Q/S coordinates to 64x64 global coordinates
            # BASIC uses 0-63, so we convert Q(1-8) S(1-8) -> Global(0-63)
            r1_global = (q1 - 1) * 8 + (s1 - 1)
            c1_global = (self.q2 - 1) * 8 + (self.s2 - 1) # Note: We assume the starting Q2 is the Enterprise's current Q2
            
            r2_global = (q2 - 1) * 8 + (s2 - 1)
            c2_global = (self.q2 - 1) * 8 + (self.s2 - 1) # Note: We assume the target Q2 is the Enterprise's current Q2
            
            # Since the original BASIC only ever calculates based on the Enterprise's Q2/S2
            # for the starting point, the logic is simplified here to match. 
            # Let's adjust to allow Q1, S1, Q2, S2 input for maximum flexibility.
            
            # R1 and C1 are the first coordinate's global row/col
            # R2 and C2 are the second coordinate's global row/col
            r1_global = (q1 - 1) * 8 + (s1 - 1)
            r2_global = (q2 - 1) * 8 + (s2 - 1)
            # The calculation is based on the difference, so column coordinates
            # don't actually matter unless they differ. Since they both define the start/end
            # of a *single* course, we will calculate based on global row-to-row, 
            # and col-to-col.
            
            # The user meant to input Q1, Q2, S1, S2, but the prompt only asked for Q,S twice.
            # We'll assume the user meant to input (Q_Row, S_Row) and (Q_Col, S_Col).
            
            # For a proper global distance:
            # P1: (Q1, self.q2) (S1, self.s2) -> P1_G(R, C)
            # P2: (Q2, S2) (S1, S2) -> P2_G(R, C)
            
            # To simplify and match common implementations: treat all 4 inputs as (R1, C1) and (R2, C2)
            # where R = Q-row, C = S-col. This calculates distance in Quadrant-Sector-space.
            
            # We must convert to 64x64 coordinates for accurate inter-quadrant distance.
            # R1_G = (Q1-1)*8 + S1. R2_G = (Q2-1)*8 + S2
            # C1_G = (self.q2-1)*8 + self.s2 (This assumes Q2,S2 is Enterprise's current location, which is confusing).
            
            # LETS USE THE SIMPLER INTERPRETATION: The user is providing the starting point (P1) and ending point (P2)
            # in Q(1-8), S(1-8) pairs.
            
            p1_r = (q1 - 1) * 8 + s1
            p1_c = (self.q2 - 1) * 8 + self.s2 # Assume Enterprise's current Q2/S2 for column for P1
            
            p2_r = (q2 - 1) * 8 + s2
            p2_c = (self.q2 - 1) * 8 + self.s2 # Assume Enterprise's current Q2/S2 for column for P2
            
            # A correct implementation requires the user to input (Q_row, S_row) and (Q_col, S_col) or all 4
            # For simplicity, we'll assume the user entered (Q_R, S_R) and (Q_R_Target, S_R_Target)
            # and that the column component of both is the Enterprise's current Q2, S2.
            
            # Recalculate based on a clear interpretation of the BASIC logic:
            # We need 4 inputs: R1, C1, R2, C2 (all from 1-64 space)
            
            # Let's ask for Q1, Q2, S1, S2 in one line.
            
            
            # Re-read the inputs as two full Q/S coordinates:
            # P1: (Q1, S1) - from command_data
            # P2: (Q2, S2) - from current input
            
            q_start = self.command_data['q1']
            s_start = self.command_data['s1'] # We've overloaded S1 for the Q-row of P1
            q_end = q2
            s_end = s2 # We've overloaded S2 for the Q-row of P2
            
            # To get an actual distance, we need a 4-coordinate system:
            # (Q_row, Q_col, S_row, S_col)
            
            # Let's assume the user is inputting Q-Row and Q-Col for both P1 and P2,
            # and the sector coordinates are assumed to be 5,5 (center of sector)
            # This is simpler and often works for macro-level nav.
            
            # Let P1 = (Q1, Q2) -> Q_row, Q_col
            # Let P2 = (S1, S2) -> Q_row, Q_col
            
            # RE-implementing the BASIC-style calculator prompt:
            # The original game's calculator asked for Q1, S1, Q2, S2 (all 4), where
            # Q1, S1 = Quadrant/Sector row (y-axis)
            # Q2, S2 = Quadrant/Sector col (x-axis)
            
            # We need to adapt the input to allow 4 numbers.
            # Since input_handler only expects one input per turn, let's simplify 
            # the calculation to just the **difference in quadrants and sectors**.
            
            # Assuming the user provided Q_row and Q_col for P2:
            
            # To achieve the proper 64x64 calculation, we need to ask for all 4 parts.
            
            # --- RESTARTING THE CALCULATOR INPUT FLOW FOR 4 COORD INPUT ---
            
            self.queue_message_instant(f"   {Colors.YELLOW}Enter START point coordinates: Q-Row, Q-Col, S-Row, S-Col.{Colors.RESET}")
            self.input_handler = self.handle_calc_input_start
            
            
        except ValueError:
            self.queue_message_instant(f"   {Colors.RED}INVALID INPUT FORMAT. USE Q,S (e.g., 8,8).{Colors.RESET}")
            self.command_data = {} # Clear temp data for restart
            self.input_handler = self._com_calculator_run # Restart the command


    def handle_calc_input_start(self):
        """Gets the four start coordinates (Q1, Q2, S1, S2)."""
        try:
            coords_str = input("START POINT (QR, QC, SR, SC): ").strip()
            # Q1=QR, Q2=QC, S1=SR, S2=SC
            qr1, qc1, sr1, sc1 = map(int, coords_str.split(','))
            
            # Validate all inputs are 1-8
            if not all(1 <= c <= 8 for c in [qr1, qc1, sr1, sc1]):
                 self.queue_message_instant(f"   {Colors.RED}INVALID START COORDINATES (All components must be 1-8).{Colors.RESET}")
                 return
            
            # Store all four coordinates
            self.command_data['qr1'] = qr1
            self.command_data['qc1'] = qc1
            self.command_data['sr1'] = sr1
            self.command_data['sc1'] = sc1
            
            # Set next handler
            self.input_handler = self.handle_calc_input_end
            
        except ValueError:
            self.queue_message_instant(f"   {Colors.RED}INVALID INPUT FORMAT. USE QR,QC,SR,SC (e.g., 5,3,4,8).{Colors.RESET}")
            self.command_data = {}

    def handle_calc_input_end(self):
        """Gets the four end coordinates and performs the calculation."""
        # --- Retrieve Start Coordinates ---
        qr1 = self.command_data['qr1']
        qc1 = self.command_data['qc1']
        sr1 = self.command_data['sr1']
        sc1 = self.command_data['sc1']

        try:
            coords_str = input("END POINT (QR, QC, SR, SC): ").strip()
            qr2, qc2, sr2, sc2 = map(int, coords_str.split(','))
            
            # Validate all inputs are 1-8
            if not all(1 <= c <= 8 for c in [qr2, qc2, sr2, sc2]):
                 self.queue_message_instant(f"   {Colors.RED}INVALID END COORDINATES (All components must be 1-8).{Colors.RESET}")
                 return

            # --- CONVERT TO GLOBAL 64x64 COORDINATES ---
            # Global Row (R) = (Q_Row - 1) * 8 + S_Row
            r1_global = (qr1 - 1) * 8 + sr1
            r2_global = (qr2 - 1) * 8 + sr2
            
            # Global Column (C) = (Q_Col - 1) * 8 + S_Col
            c1_global = (qc1 - 1) * 8 + sc1
            c2_global = (qc2 - 1) * 8 + sc2

            # --- PERFORM CALCULATION ---
            # We are using the function you moved to utils.py
            from utils import get_course_and_distance
            course, distance = get_course_and_distance(r1_global, c1_global, r2_global, c2_global)
            
            # --- DISPLAY RESULTS ---
            self.queue_message_instant("") # Blank line
            self.queue_message_instant(f"   DIRECTION: {course:.2f}", color=Colors.CYAN)
            self.queue_message_instant(f"   DISTANCE: {distance:.2f} QUADRANT/SECTOR UNITS", color=Colors.CYAN)

        except ValueError:
            self.queue_message_instant(f"   {Colors.RED}INVALID INPUT FORMAT. USE QR,QC,SR,SC (e.g., 8,8,1,1).{Colors.RESET}")
            
        self.command_data = {} # Clear temp data   
    
    def xxx_command(self):
        """Translates logic from line 6270."""
        self.queue_message_instant("XXX: You have resigned your command.")
        self.is_running = False
        self.game_over_reason = "QUIT"
        pass
    
             
    
    def _end_game(self):
        """
        Handles all end-of-game reports and the replay prompt.
        This translates lines 6220-6400.
        Returns True if the user wants to play again, False otherwise.
        """
        # --- Clear the entire prompt area for messages ---
        print(f"\033[{self.cmd_box_top};{self.msg_box_col}H\033[J", end="") 

        if self.game_over_reason == "WIN":
            # --- Show WIN art in the message box ---
            self._show_art("ufp_logo.txt")
            
            # --- Print messages in the *prompt* area ---
            self.typewriter_print("CONGRATULATIONS, CAPTAIN!", color=Colors.GREEN)
            self.typewriter_print("THE LAST KLINGON BATTLE CRUISER HAS BEEN DESTROYED.", color=Colors.GREEN)
            
            # Calculate Efficiency Rating (line 6400)
            time_taken = self.stardate - self.stardate_start
            if time_taken == 0: time_taken = 0.1 # Avoid division by zero
            
            rating = 1000 * (self.klingons_start / time_taken)**2
            self.typewriter_print(f"\nYOUR EFFICIENCY RATING IS: {rating:.2f}", color=Colors.CYAN)
        
        else:
            # --- Show DEFEAT art in the message box ---
            self._show_art("klingon.txt")
            
            # --- Print messages in the *prompt* area ---
            if self.game_over_reason == "TIME":
                self.typewriter_print(f"IT IS STARDATE {self.stardate:.1f}.", color=Colors.YELLOW)
                self.typewriter_print("YOUR MISSION HAS FAILED.", color=Colors.RED)
            elif self.game_over_reason == "DESTROYED":
                self.typewriter_print("THE ENTERPRISE HAS BEEN DESTROYED.", color=Colors.RED)
            elif self.game_over_reason == "QUIT":
                self.typewriter_print("", color=Colors.YELLOW)
                self.typewriter_print("You resigned your command.", color=Colors.YELLOW)
            
            self.typewriter_print(f"\nTHERE WERE {self.klingons_total} KLINGON BATTLE CRUISERS LEFT AT", color=Colors.YELLOW)
            self.typewriter_print("THE END OF YOUR MISSION.", color=Colors.YELLOW)

        # Replay logic (lines 6310-6330)
        print("\n")
        #spacer = " " * self.msg_box_col
        self.typewriter_print("THE FEDERATION IS IN NEED OF A NEW STARSHIP COMMANDER.")
        response = input("IF THERE IS A VOLUNTEER, LET HIM STEP FORWARD AND ENTER 'AYE': ").strip().upper()
        
        if response == "AYE":
            return True # Play again
        
        self.typewriter_print("\nBACK TO SYSTEM.", color=Colors.CYAN)
        return False # Quit
