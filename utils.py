import os
import re
import math

# --- Helper Functions ---

def clear_screen(): #clear sceen almost self documenting
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_quadrant_name(q1, q2): #holds the names of quadrents and gives a process to retrieve
    """
    Translates GOSUB 9030.
    Gets the galaxy region name for a given quadrant.
    """
    regions = [
        "ANTARES", "RIGEL", "PROCYON", "VEGA",
        "CANOPUS", "ALTAIR", "SAGITTARIUS", "POLLUX",
        "SIRIUS", "DENEB", "CAPELLA", "BETELGEUSE",
        "ALDEBARAN", "REGULUS", "ARCTURUS", "SPICA"
    ]
    romans = ["I", "II", "III", "IV"]
    
    if q2 <= 4:
        name = regions[q1 - 1]
    else:
        name = regions[q1 - 1 + 8]
        
    return f"{name} {romans[(q2 - 1) % 4]}"

def load_ascii_art(filename):#loads art fromo file
    """
    Loads ASCII art from a specified text file.

    Args:
        filename (str): The name of the .txt file to load.

    Returns:
        list: A list of strings, where each string is a line of the art.
              Returns a default error message list if the file isn't found.
    """
    try:
        with open(filename, 'r') as f:
            # Read all lines and strip the newline character from the end
            return [line.rstrip('\n') for line in f.readlines()]
    except FileNotFoundError:
        return [
            f"ERROR: Art file not found.",
            f"'{filename}'"
        ]
    except Exception as e:
        return [
            f"ERROR: Could not read art file.",
            f"{e}"
        ]
# --- Constants ---

class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    BLINK = '\033[5m'
    BLACK = '\033[90m'     # Bright Black
    RED = '\033[91m'     # Bright Red
    GREEN = '\033[92m'   # Bright Green
    YELLOW = '\033[93m'  # Bright Yellow
    BLUE = '\033[94m'    # Bright Blue
    MAGENTA = '\033[95m' # Bright Magenta
    CYAN = '\033[96m'    # Bright Cyan
    WHITE = '\033[97m'   # Bright White
    BGBLACK = '\033[40m'     # Bright Black Background
    BGRED = '\033[41m'     # Bright Red Background
    BGGREEN = '\033[42m'   # Bright Green Background
    BGYELLOW = '\033[43m'  # Bright Yellow Background
    BGBLUE = '\033[44m'    # Bright Blue Background
    BGMAGENTA = '\033[45m' # Bright Magenta Background
    BGCYAN = '\033[46m'    # Bright Cyan Background
    BGWHITE = '\033[47m'   # Bright White Background

# --- ANSI pattern to strip codes ---
_ansi_escape_pattern = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def get_visible_length(text):
    """Returns the visible length of a string, stripping ANSI codes."""
    return len(_ansi_escape_pattern.sub('', text))

def translate_art_tags(line):
    """
    Translates human-readable tags like [RED] in a string
    to their proper ANSI color codes.
    """
    return (line
            .replace("[RESET]", Colors.RESET)
            .replace("[BOLD]", Colors.BOLD)
            .replace("[BLINK]", Colors.BLINK)
            .replace("[RED]", Colors.RED)
            .replace("[GREEN]", Colors.GREEN)
            .replace("[YELLOW]", Colors.YELLOW)
            .replace("[BLUE]", Colors.BLUE)
            .replace("[MAGENTA]", Colors.MAGENTA)
            .replace("[CYAN]", Colors.CYAN)
            .replace("[WHITE]", Colors.WHITE)
            .replace("[BLACK]", Colors.BLACK)
            .replace("[BGRED]", Colors.BGRED)
            .replace("[BGGREEN]", Colors.BGGREEN)
            .replace("[BGYELLOW]", Colors.BGYELLOW)
            .replace("[BGBLUE]", Colors.BGBLUE)
            .replace("[BGMAGENTA]", Colors.BGMAGENTA)
            .replace("[BGCYAN]", Colors.BGCYAN)
            .replace("[BGWHITE]", Colors.BGWHITE)
            .replace("[BGBLACK]", Colors.BGBLACK)
            )

def get_distance(r1, c1, r2, c2):
    """Calculates the Euclidean distance between two sector coordinates."""
    return math.sqrt((r1 - r2)**2 + (c1 - c2)**2)

def get_course_and_distance(r1, c1, r2, c2):
    """
    Calculates the course (1-8.99) and distance between two points (r1,c1) and (r2,c2).
    Re-implements the math from lines 8220-8460.
    Returns (course, distance)
    """
    delta_r = r2 - r1
    delta_c = c2 - c1

    if delta_r == 0 and delta_c == 0:
        return 0, 0 # No movement

    # Get angle. Y-axis is inverted for screen, so use -delta_r
    angle_rad = math.atan2(-delta_r, delta_c)
    angle_deg = math.degrees(angle_rad)

    # Normalize angle to 0-360
    if angle_deg < 0:
        angle_deg += 360

    # Convert angle (0-360) to course (1-9)
    course = (angle_deg / 45.0) + 1

    # Handle wraparound (course 9 is same as 1)
    if course >= 9.0:
        course = 1.0

    distance = math.sqrt(delta_r**2 + delta_c**2)

    return course, distance

def get_device_name(device_index):
    """
    Gets the string name for a device from its 1-8 index.
    Based on GOSUB 8790.
    """
    device_names = [
        "WARP ENGINES", "SHORT RANGE SENSORS", "LONG RANGE SENSORS",
        "PHASER CONTROL", "PHOTON TUBES", "DAMAGE CONTROL",
        "SHIELD CONTROL", "LIBRARY-COMPUTER"
    ]
    return device_names[device_index - 1]

# In utils.py

class Difficulty:
    """Defines scaling factors for game difficulty."""
    def __init__(self, name, shield_multiplier, base_klingon_shields, energy_divisor, initial_klingons, initial_starbases): # <-- ADD initial_starbases
        self.name = name
        # Multiplier for Enterprise shield/energy effectiveness
        self.shield_multiplier = shield_multiplier 
        # Base shields for each new Klingon
        self.base_klingon_shields = base_klingon_shields
        # Divisor for Klingon hit strength (higher number = lower damage)
        self.energy_divisor = energy_divisor
        # Total number of Klingons at start of game
        self.initial_klingons = initial_klingons
        # Total number of Starbases at start of game <-- NEW
        self.initial_starbases = initial_starbases

# Define the three difficulty settings with new names and starbase counts
EASY = Difficulty(
    name="CPT PIKE", # <-- NAME CHANGE
    shield_multiplier=1.2,
    base_klingon_shields=150,
    energy_divisor=15, 
    initial_klingons=15,
    initial_starbases=8 # <-- EASIER
)
STANDARD = Difficulty(
    name="CPT KIRK", # <-- NAME CHANGE
    shield_multiplier=1.0, 
    base_klingon_shields=200, 
    energy_divisor=10, 
    initial_klingons=25,
    initial_starbases=5 # <-- STANDARD
)
HARD = Difficulty(
    name="CAP PICARD", # <-- NAME CHANGE
    shield_multiplier=0.8,
    base_klingon_shields=300,
    energy_divisor=5,
    initial_klingons=40,
    initial_starbases=3 # <-- HARDER
)

# List of difficulties for the menu
DIFFICULTIES = [EASY, STANDARD, HARD]