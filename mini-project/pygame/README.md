Shoot the Enemy Game

This is a 2D shooting game built in Python using Pygame. The goal is to survive against incoming bird enemies flying from various directions and ground enemies walking from the right. It features background music, sound effects, drifting clouds, a simple start screen, and gameplay controls designed to work either with a mouse or using just a laptop keyboard trackpad.

---

Game Controls

The game supports two control modes. It automatically detects if you are using the mouse or the keyboard to aim.

Action | Option A (Mouse and Keyboard) | Option B (Keyboard Only / Laptop)
Move Left / Right | A / D | A / D
Jump | W | W
Aim Gun | Move mouse cursor | Arrow Keys (UP, DOWN, LEFT, RIGHT and diagonals)
Shoot | Left Mouse Click | Spacebar
Pause / Play | P | P
Volume Control | Page Up / Page Down | ] / [

Note: Moving the mouse or clicking switches the aim mode to follow the cursor. Pressing any Arrow key switches the aim mode back to the keyboard.

---

How It Works (Libraries Used)

This project is written in standard Python and uses a few libraries:

1. pygame: Handles the game window, graphics rendering, clock/frame rates (locked at 80 FPS), playing background music, triggering sound effects, and listening to user inputs.
2. math: Calculates the angles for aiming the player's gun (math.atan2) and computing the speed and trajectory vectors of the bullets (math.sin and math.cos).
3. random: Determines random enemy spawn positions and introduces slight variations to the birds' flight paths.

---

How to Setup and Run in VS Codegit add mini-project/pygame/

Here are the step-by-step commands to run the project. Open your VS Code terminal (Ctrl + Shift + `) and run them.

1. Create a virtual environment:
python -m venv venv

2. Activate the virtual environment:
On Windows:
.\venv\Scripts\Activate.ps1

On macOS or Linux:
source venv/bin/activate

3. Install Pygame:
pip install pygame

4. Run the game:
python game.py

---

Security and Audio Assets

Credentials and API Keys:
This game runs entirely locally and does not require any credentials, secret keys, or database connections.

Audio Assets:
The following files must reside in the same directory as game.py for the audio engine to initialize correctly:

1. [FREE] DRAKE x TRAVIS SCOTT TYPE BEAT - INSIDE.wav (Background music loop)
2. mixkit-game-gun-shot-1662.wav (Gun shot sound)
3. game-over-arcade-6435.wav (Game over sound)
