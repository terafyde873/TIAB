import curses
import sys
import os
import subprocess

def normalize_path(path):
    variations = [path]
    if '/' in path:
        variations.append(path.replace('/', '\\'))
    
    for i in range(path.count('/')):
        new_path = list(path)
        count = 0
        for j, char in enumerate(new_path):
            if char == '/':
                count += 1
                if count > i:
                    new_path[j] = '\\'
        variations.append(''.join(new_path))

    for var in variations:
        if os.path.exists(var):
            return var
    return path  # Return original if no variation exists

def save_file(filename, content):
    with open(filename, 'w') as file:
        file.write('\n'.join(content))

def load_file(filename):
    try:
        with open(filename, 'r') as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return [""]

def confirm_action(stdscr, action):
    height, width = stdscr.getmaxyx()
    stdscr.addstr(height-1, 0, f"Are you sure you want to {action}? (y/n)")
    stdscr.refresh()
    while True:
        key = stdscr.getch()
        if key in [ord('y'), ord('Y')]:
            return True
        elif key in [ord('n'), ord('N')]:
            return False

def generate_text(prompt):
    try:
        process = subprocess.Popen(['python', 'tet.py'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(input=prompt)
        
        if stderr:
            return f"Error: {stderr}"
        
        return stdout.strip()  # Strip to remove any leading/trailing whitespace
    except Exception as e:
        return f"Error: {str(e)}"

def confirm_and_add_text(stdscr, text, cursor_y, cursor_x, generated_text):
    height, width = stdscr.getmaxyx()
    stdscr.clear()
    
    # Show surrounding text
    start_y = max(0, cursor_y - 2)
    end_y = min(len(text), cursor_y + 4)
    
    stdscr.addstr(0, 0, "Generated text preview:", curses.A_BOLD)
    line_num = 2

    # Display lines before the cursor
    for i in range(start_y, cursor_y):
        stdscr.addstr(line_num, 0, text[i])
        line_num += 1

    # Display the line with the generated text inserted
    if cursor_y < len(text):
        line_to_insert = text[cursor_y][:cursor_x] + generated_text + text[cursor_y][cursor_x:]
    else:
        line_to_insert = text[cursor_y] + generated_text

    stdscr.addstr(line_num, 0, line_to_insert, curses.color_pair(1))
    line_num += 1

    # Display lines after the cursor
    for i in range(cursor_y + 1, end_y):
        stdscr.addstr(line_num, 0, text[i])
        line_num += 1

    # Ensure the preview fits within the terminal window
    if line_num >= height - 1:
        line_num = height - 2

    stdscr.addstr(height-1, 0, "Add this text? (y/n)", curses.A_BOLD)
    stdscr.refresh()

    while True:
        key = stdscr.getch()
        if key in [ord('y'), ord('Y')]:
            return True
        elif key in [ord('n'), ord('N')]:
            return False

def editor(stdscr, filename="untitled.txt"):
    curses.use_default_colors()
    curses.curs_set(1)  # Show cursor
    stdscr.keypad(True)
    
    text = load_file(filename) if filename != "untitled.txt" else [""]
    
    cursor_y, cursor_x = 0, 0
    top_line = 0

    def refresh_screen():
        nonlocal top_line
        height, width = stdscr.getmaxyx()
        
        if cursor_y < top_line:
            top_line = cursor_y
        elif cursor_y >= top_line + height - 2:
            top_line = cursor_y - height + 3

        stdscr.clear()
        for i, line in enumerate(text[top_line:top_line+height-2]):
            try:
                stdscr.addnstr(i, 0, line, width-1)
            except curses.error:
                pass

        status = f" {filename} | Line {cursor_y+1}/{len(text)} | Col {cursor_x+1} | Ctrl+S: Save | Ctrl+Q: Quit | Ctrl+G: Generate"
        stdscr.attron(curses.A_REVERSE)
        stdscr.addnstr(height-1, 0, status.ljust(width), width-1)
        stdscr.attroff(curses.A_REVERSE)

        try:
            stdscr.move(cursor_y - top_line, min(cursor_x, width-1))
        except curses.error:
            pass

        stdscr.refresh()

    def get_user_input(prompt):
        height, width = stdscr.getmaxyx()
        curses.echo()
        stdscr.addstr(height-1, 0, prompt)
        user_input = stdscr.getstr().decode('utf-8')
        curses.noecho()
        return user_input

    while True:
        refresh_screen()
        
        try:
            key = stdscr.getch()
        except KeyboardInterrupt:
            if confirm_action(stdscr, "quit"):
                break
            else:
                continue

        height, width = stdscr.getmaxyx()

        if key == ord('\n'):
            text.insert(cursor_y + 1, text[cursor_y][cursor_x:])
            text[cursor_y] = text[cursor_y][:cursor_x]
            cursor_y += 1
            cursor_x = 0
        elif key in (curses.KEY_BACKSPACE, ord('\b'), 127):
            if cursor_x > 0:
                text[cursor_y] = text[cursor_y][:cursor_x-1] + text[cursor_y][cursor_x:]
                cursor_x -= 1
            elif cursor_y > 0:
                cursor_x = len(text[cursor_y-1])
                text[cursor_y-1] += text[cursor_y]
                text.pop(cursor_y)
                cursor_y -= 1
        elif key == curses.KEY_LEFT and cursor_x > 0:
            cursor_x -= 1
        elif key == curses.KEY_RIGHT and cursor_x < len(text[cursor_y]):
            cursor_x += 1
        elif key == curses.KEY_UP and cursor_y > 0:
            cursor_y -= 1
            cursor_x = min(cursor_x, len(text[cursor_y]))
        elif key == curses.KEY_DOWN and cursor_y < len(text) - 1:
            cursor_y += 1
            cursor_x = min(cursor_x, len(text[cursor_y]))
        elif key == 19:  # Ctrl+S
            if confirm_action(stdscr, "save"):
                if filename == "untitled.txt":
                    new_filename = get_user_input("Enter file name to save: ")
                    if new_filename:
                        filename = new_filename
                save_file(filename, text)
        elif key == 17 or key == 3:  # Ctrl+Q or Ctrl+C
            if confirm_action(stdscr, "quit"):
                break
        elif key == 7:  # Ctrl+G
            query = get_user_input("Enter prompt for text generation: ")
            if query:
                stdscr.addstr(height-1, 0, "Generating text... Please wait.")
                stdscr.refresh()
                generated_text = generate_text(query)
                if confirm_and_add_text(stdscr, text, cursor_y, cursor_x, generated_text):
                    # Add the generated text to the document
                    lines = generated_text.split('\n')
                    text[cursor_y] = text[cursor_y][:cursor_x] + lines[0] + text[cursor_y][cursor_x:]
                    text[cursor_y+1:cursor_y+1] = lines[1:]
                    cursor_y += len(lines) - 1
                    cursor_x = len(lines[-1])
        elif 32 <= key <= 126:  # Printable characters
            text[cursor_y] = text[cursor_y][:cursor_x] + chr(key) + text[cursor_y][cursor_x:]
            cursor_x += 1
        elif key == curses.KEY_RESIZE:
            stdscr.clear()

def menu(stdscr):
    curses.curs_set(0)  # Hide cursor
    stdscr.keypad(True)

    options = ["Create New File", "Open File", "Quit"]
    current_option = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        title = "Text Editor Menu"
        stdscr.addstr(height//2 - 4, (width - len(title))//2, title, curses.A_BOLD)

        for idx, option in enumerate(options):
            x = width//2 - len(option)//2
            y = height//2 - len(options)//2 + idx
            if idx == current_option:
                stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(y, x, option)
                stdscr.attroff(curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, option)

        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP and current_option > 0:
            current_option -= 1
        elif key == curses.KEY_DOWN and current_option < len(options) - 1:
            current_option += 1
        elif key == ord('\n'):  # Enter key
            if current_option == 0:  # Create New File
                editor(stdscr)  # Start with untitled.txt
            elif current_option == 1:  # Open File
                filename = get_user_input(stdscr, "Enter file name to open: ")
                if filename:
                    normalized_filename = normalize_path(filename)
                    if os.path.exists(normalized_filename):
                        editor(stdscr, normalized_filename)
                    else:
                        stdscr.addstr(height-1, 0, "File not found. Press any key to continue.")
                        stdscr.getch()
            else:  # Quit
                if confirm_action(stdscr, "quit"):
                    break

        stdscr.clear()

if __name__ == "__main__":
    curses.wrapper(menu)
