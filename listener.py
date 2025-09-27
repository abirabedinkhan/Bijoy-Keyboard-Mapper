from interpreter import interpreter
from pynput import keyboard, mouse
import time
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
        """Check if text contains only ASCII characters"""
        return all(ord(char) < 128 for char in text)

    def process_mapping(self, original, mapped):
        """Process the mapping and determine what should be typed"""
        if self.debug:
            print(f"Processing mapping: '{original}' -> '{mapped}'")
        
        # If original is ASCII and mapped is non-ASCII (like Bengali), replace entirely
        if self.is_ascii_only(original) and not self.is_ascii_only(mapped):
            if self.debug:
                print("ASCII to non-ASCII mapping detected - replacing entirely")
            return mapped
        
        # If they're the same, no change needed
        if original == mapped:
            if self.debug:
                print("No mapping change detected")
            return ""
        
        # For other cases, find common prefix and return the difference
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
        """Handle keystrokes"""
        try:
            # CRITICAL: Ignore all input while processing to prevent loops
            if self.is_processing:
                if self.debug:
                    print("Ignoring keystroke - currently processing")
                return

            if self.debug and hasattr(key, "char") and key.char:
                print(f"Key pressed: '{key.char}'")

            # Control keys
            if key == keyboard.Key.f12:
                self.is_active = not self.is_active
                print(f"Bijoy Mapper {'activated' if self.is_active else 'deactivated'}")
                return

            if not self.is_active:
                return

            if hasattr(key, "char") and key.char:
                # CRITICAL: Only accept ASCII characters for input buffer
                # This prevents Bengali characters from being processed again
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
                    self.process_current_word_reliable()
                else:
                    if self.debug:
                        print("Space pressed but no word to process.")
                self.current_word = ""

            elif key == keyboard.Key.backspace:
                if self.current_word:
                    self.current_word = self.current_word[:-1]
                    if self.debug:
                        print(
                            f"Backspace pressed. Current word buffer: '{self.current_word}'"
                        )

            elif key in [keyboard.Key.enter, keyboard.Key.tab]:
                if self.debug:
                    print(
                        f"Enter/Tab pressed. Clearing word buffer: '{self.current_word}'"
                    )
                self.current_word = ""

        except Exception as e:
            print(f"Error in key handler: {e}")
            self.current_word = ""  # Reset on error

    def on_mouse_click(self, x, y, button, pressed):
        """Clear current word on mouse click"""
        if pressed:
            self.current_word = ""

    def type_text_direct(self, text):
        """Type text character-by-character without any clipboard operations"""
        try:
            if self.debug:
                print(f"Typing text character by character: '{text}'")
            
            # Simple character-by-character typing
            for i, char in enumerate(text):
                try:
                    self.keyboard_controller.press(char)
                    self.keyboard_controller.release(char)
                    time.sleep(0.02)  # Small delay between characters
                    
                    if self.debug and i < 3:  # Log first few characters only
                        print(f"Typed character {i+1}/{len(text)}: '{char}'")
                        
                except Exception as char_error:
                    if self.debug:
                        print(f"Could not type character '{char}': {char_error}")
                    # Continue with next character instead of failing completely
                    continue

        except Exception as e:
            if self.debug:
                print(f"Error in character-by-character typing: {e}")

    def process_current_word_reliable(self):
        """Process and replace the current word with reliable deletion"""
        if not self.current_word:
            return

        # Set processing flag IMMEDIATELY to block new input
        self.is_processing = True
        
        try:
            original_word = self.current_word
            mapped_word = interpreter(original_word)

            if self.debug:
                print(f"Original input: '{original_word}'")
                print(f"Interpreter output: '{mapped_word}'")

            # Process the mapping to determine what should be typed
            text_to_type = self.process_mapping(original_word, mapped_word)

            if not text_to_type:
                if self.debug:
                    print("No changes made. Skipping.")
                self.current_word = ""
                self.is_processing = False
                return

            # Clear buffer before operations
            word_length = len(original_word)
            self.current_word = ""

            if self.debug:
                print(f"Will delete {word_length} chars and type '{text_to_type}'")

            # Wait for space to be processed first
            time.sleep(0.1)

            # Delete with more aggressive approach - delete one extra character (the space)
            # then type everything back with the replacement
            total_to_delete = word_length + 1  # +1 for the space that was just added
            
            if self.debug:
                print(f"Deleting {total_to_delete} characters (word + space)")
            
            for i in range(total_to_delete):
                self.keyboard_controller.press(Key.backspace)
                self.keyboard_controller.release(Key.backspace)
                time.sleep(0.01)

            # Now type the replacement text
            time.sleep(0.05)
            self.type_text_direct(text_to_type)

            # Add space back
            time.sleep(0.05)
            self.keyboard_controller.press(Key.space)
            self.keyboard_controller.release(Key.space)

            if self.debug:
                print(f"Replaced '{original_word}' + space with '{text_to_type}' + space")

            # Add extra delay before allowing new input to ensure all typing is complete
            time.sleep(0.1)

        except Exception as e:
            print(f"Error in reliable processing: {e}")
        finally:
            # Always reset processing flag
            self.is_processing = False

    def run(self):
        try:
            self.keyboard_listener.join()
            self.mouse_listener.join()
        except KeyboardInterrupt:
            print("Program terminated")
        except Exception as e:
            print(f"Error: {e}")