from interpreter import interpreter
from pynput import keyboard, mouse
import time
import threading
import pyperclip
from pynput.keyboard import Key, Controller


class BijoyMapper:
    def __init__(self):
        # Initialize keyboard controller
        self.keyboard_controller = Controller()
        self.is_active = False
        self.is_processing = False

        # Current word being typed
        self.current_word = ""

        # Debug mode
        self.debug = True

        # Store original clipboard content to restore later
        self.original_clipboard = ""

        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.keyboard_listener.start()

        # Start mouse listener
        self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
        self.mouse_listener.start()

        print("Bijoy Keyboard Mapper is running!")
        print("Press F12 to toggle on/off")
        print("Debug mode is enabled. Check console for details.")

    def is_ascii_only(self, text):
        return all(ord(char) < 128 for char in text)

    def process_mapping(self, original, mapped):
        if self.debug:
            print(f"Processing mapping: '{original}' -> '{mapped}'")

        if self.is_ascii_only(original) and not self.is_ascii_only(mapped):
            if self.debug:
                print("ASCII to non-ASCII mapping detected - replacing entirely")
            return mapped

        if original == mapped:
            if self.debug:
                print("No mapping change detected")
            return ""

        i = 0
        while i < len(original) and i < len(mapped):
            if original[i] == mapped[i]:
                i += 1
            else:
                break

        result = mapped[i:]
        if self.debug:
            print(f"Common prefix length: {i}, returning: '{result}'")
        return result

    def on_key_press(self, key):
        try:
            if self.is_processing:
                if self.debug:
                    print("Ignoring keystroke - currently processing")
                return

            if self.debug and hasattr(key, "char") and key.char:
                print(f"Key pressed: '{key.char}'")

            if key == keyboard.Key.f12:
                self.is_active = not self.is_active
                print(f"Bijoy Mapper {'activated' if self.is_active else 'deactivated'}")
                return

            if not self.is_active:
                return

            if hasattr(key, "char") and key.char:
                if ord(key.char) < 128:  # ASCII only
                    self.current_word += key.char
                    if self.debug:
                        print(f"Current word buffer: '{self.current_word}'")
                else:
                    if self.debug:
                        print(f"Ignoring non-ASCII character: '{key.char}'")

            elif key == keyboard.Key.space:
                if self.current_word:
                    if self.debug:
                        print(f"Space pressed. Processing word: '{self.current_word}'")
                    # Use threading to prevent blocking
                    threading.Thread(target=self.process_current_word_reliable, daemon=True).start()
                else:
                    if self.debug:
                        print("Space pressed but no word to process.")
                self.current_word = ""

            elif key == keyboard.Key.backspace:
                if self.current_word:
                    self.current_word = self.current_word[:-1]
                    if self.debug:
                        print(f"Backspace pressed. Current word buffer: '{self.current_word}'")

            elif key in [keyboard.Key.enter, keyboard.Key.tab]:
                if self.debug:
                    print(f"Enter/Tab pressed. Clearing word buffer: '{self.current_word}'")
                self.current_word = ""

        except Exception as e:
            print(f"Error in key handler: {e}")
            self.current_word = ""

    def on_mouse_click(self, x, y, button, pressed):
        if pressed:
            self.current_word = ""

    def backup_clipboard(self):
        """Backup current clipboard content"""
        try:
            self.original_clipboard = pyperclip.paste()
            if self.debug:
                print("Clipboard backed up")
        except Exception as e:
            if self.debug:
                print(f"Failed to backup clipboard: {e}")
            self.original_clipboard = ""

    def restore_clipboard(self):
        """Restore original clipboard content"""
        try:
            if self.original_clipboard is not None:
                pyperclip.copy(self.original_clipboard)
                if self.debug:
                    print("Clipboard restored")
        except Exception as e:
            if self.debug:
                print(f"Failed to restore clipboard: {e}")

    def type_with_pyperclip(self, text):
        """Type text using pyperclip and Ctrl+V"""
        try:
            if self.debug:
                print(f"Typing with pyperclip: '{text}'")

            # Backup current clipboard
            self.backup_clipboard()

            # Set text to clipboard
            pyperclip.copy(text)
            
            # Small delay to ensure clipboard is set
            time.sleep(0.05)

            # Verify clipboard content
            clipboard_content = pyperclip.paste()
            if clipboard_content != text:
                if self.debug:
                    print("Clipboard verification failed")
                return False

            # Paste using Ctrl+V
            with self.keyboard_controller.pressed(Key.ctrl):
                self.keyboard_controller.press('v')
                self.keyboard_controller.release('v')

            # Wait for paste operation to complete
            time.sleep(0.1)

            # Restore original clipboard after a short delay
            threading.Timer(1.0, self.restore_clipboard).start()

            if self.debug:
                print("Successfully typed using pyperclip")
            return True

        except Exception as e:
            if self.debug:
                print(f"Pyperclip method failed: {e}")
            # Try to restore clipboard even if there was an error
            self.restore_clipboard()
            return False

    def process_current_word_reliable(self):
        if not self.current_word:
            return

        self.is_processing = True
        try:
            original_word = self.current_word
            mapped_word = interpreter(original_word)

            if self.debug:
                print(f"Original input: '{original_word}'")
                print(f"Interpreter output: '{mapped_word}'")

            text_to_type = self.process_mapping(original_word, mapped_word)

            if not text_to_type:
                if self.debug:
                    print("No changes made. Skipping.")
                return

            word_length = len(original_word)

            if self.debug:
                print(f"Will delete {word_length} chars and type '{text_to_type}'")

            # Wait a bit for any pending keystrokes to complete
            time.sleep(0.1)

            # Delete the original word + space
            total_to_delete = word_length + 1
            if self.debug:
                print(f"Deleting {total_to_delete} characters (word + space)")

            for i in range(total_to_delete):
                self.keyboard_controller.press(Key.backspace)
                self.keyboard_controller.release(Key.backspace)
                time.sleep(0.01)

            # Wait before typing new text
            time.sleep(0.1)
            
            # Type the new text using pyperclip
            if not self.type_with_pyperclip(text_to_type):
                if self.debug:
                    print("Pyperclip method failed, skipping replacement")
                return

            # Add space after the new text
            time.sleep(0.1)
            self.keyboard_controller.press(Key.space)
            self.keyboard_controller.release(Key.space)

            if self.debug:
                print(f"Replaced '{original_word}' + space with '{text_to_type}' + space")

        except Exception as e:
            print(f"Error in reliable processing: {e}")
        finally:
            self.is_processing = False
            # Clear current word buffer
            self.current_word = ""

    def run(self):
        try:
            print("Bijoy Mapper is ready. Use F12 to toggle on/off.")
            print("Make sure pyperclip is installed: pip install pyperclip")
            self.keyboard_listener.join()
            self.mouse_listener.join()
        except KeyboardInterrupt:
            print("Program terminated")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # Cleanup
            if hasattr(self, 'keyboard_listener'):
                self.keyboard_listener.stop()
            if hasattr(self, 'mouse_listener'):
                self.mouse_listener.stop()