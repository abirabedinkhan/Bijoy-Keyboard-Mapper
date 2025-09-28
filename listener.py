from interpreter import interpreter
from pynput import keyboard, mouse
import time
import subprocess
import threading
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

        # Check available tools once at startup
        self.has_xdotool = self._check_xdotool()
        self.has_xclip = self._check_xclip()
        
        print(f"xdotool available: {self.has_xdotool}")
        print(f"xclip available: {self.has_xclip}")

        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.keyboard_listener.start()

        # Start mouse listener
        self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
        self.mouse_listener.start()

        print("Bijoy Keyboard Mapper is running!")
        print("Press F12 to toggle on/off")
        print("Debug mode is enabled. Check console for details.")

    def _check_xdotool(self):
        """Check if xdotool is available"""
        try:
            result = subprocess.run(['which', 'xdotool'], 
                                  capture_output=True, timeout=2)
            return result.returncode == 0
        except:
            return False

    def _check_xclip(self):
        """Check if xclip is available"""
        try:
            result = subprocess.run(['which', 'xclip'], 
                                  capture_output=True, timeout=2)
            return result.returncode == 0
        except:
            return False

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

    def clear_clipboard(self):
        """Clear clipboard to prevent interference"""
        try:
            if self.has_xclip:
                subprocess.run(['xclip', '-selection', 'clipboard', '-i'], 
                             input='', text=True, timeout=1)
        except:
            pass

    def type_text_direct(self, text):
        try:
            if self.debug:
                print(f"Typing text: '{text}'")

            import platform
            if platform.system() == "Linux":
                # Try xdotool first (more reliable for complex characters)
                if self.has_xdotool and self.type_with_xdotool(text):
                    return
                # Try clipboard method as fallback
                if self.has_xclip and self.type_with_clipboard(text):
                    return

            if self.debug:
                print("Falling back to character-by-character typing")
            self.type_char_by_char(text)

        except Exception as e:
            if self.debug:
                print(f"Error in text typing: {e}")

    def type_with_xdotool(self, text):
        """Improved xdotool typing with better error handling"""
        try:
            if not self.has_xdotool:
                return False

            # Add delay before typing to ensure focus
            time.sleep(0.1)
            
            # Use xdotool with proper encoding handling
            result = subprocess.run([
                'xdotool', 
                'type', 
                '--clearmodifiers',
                '--delay', '10',  # Small delay between characters
                '--', 
                text
            ], capture_output=True, timeout=5, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                if self.debug:
                    print("Successfully typed using xdotool")
                return True
            else:
                if self.debug:
                    print(f"xdotool failed: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            if self.debug:
                print("xdotool timeout - text too long or system busy")
            return False
        except Exception as e:
            if self.debug:
                print(f"xdotool method failed: {e}")
            return False

    def type_with_clipboard(self, text):
        """Improved clipboard method with better synchronization"""
        try:
            if not self.has_xclip:
                return False

            # Clear clipboard first
            self.clear_clipboard()
            time.sleep(0.05)

            # Set clipboard content with proper encoding
            proc = subprocess.Popen([
                'xclip', '-selection', 'clipboard', '-i'
            ], stdin=subprocess.PIPE, text=True, encoding='utf-8')
            
            stdout, stderr = proc.communicate(input=text, timeout=3)

            if proc.returncode != 0:
                if self.debug:
                    print(f"xclip failed to set clipboard: {stderr}")
                return False

            # Wait for clipboard to be set
            time.sleep(0.1)

            # Verify clipboard was set correctly
            verify_proc = subprocess.run([
                'xclip', '-selection', 'clipboard', '-o'
            ], capture_output=True, text=True, encoding='utf-8', timeout=2)
            
            if verify_proc.returncode == 0 and verify_proc.stdout == text:
                # Paste using Ctrl+V
                with self.keyboard_controller.pressed(Key.ctrl):
                    self.keyboard_controller.press('v')
                    self.keyboard_controller.release('v')
                
                time.sleep(0.1)
                
                if self.debug:
                    print("Successfully typed using clipboard")
                return True
            else:
                if self.debug:
                    print("Clipboard verification failed")
                return False

        except subprocess.TimeoutExpired:
            if self.debug:
                print("Clipboard operation timeout")
            return False
        except Exception as e:
            if self.debug:
                print(f"Clipboard method failed: {e}")
            return False

    def type_char_by_char(self, text):
        """Improved character-by-character typing"""
        try:
            if self.debug:
                print(f"Typing character by character: '{text}'")

            # Adaptive delay based on text complexity
            char_delay = 0.03 if any(ord(c) > 127 for c in text) else 0.02
            
            for i, char in enumerate(text):
                try:
                    self.keyboard_controller.press(char)
                    self.keyboard_controller.release(char)
                    
                    # Slightly longer delay for non-ASCII characters
                    delay = char_delay * 1.5 if ord(char) > 127 else char_delay
                    time.sleep(delay)

                    if self.debug and i < 3:
                        print(f"Typed character {i+1}/{len(text)}: '{char}'")
                        
                except ValueError as ve:
                    if self.debug:
                        print(f"Cannot type character '{char}' directly: {ve}")
                    # For unsupported characters, try alternative methods
                    continue
                except Exception as char_error:
                    if self.debug:
                        print(f"Error typing character '{char}': {char_error}")
                    continue

        except Exception as e:
            if self.debug:
                print(f"Error in character-by-character typing: {e}")

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

            # More reliable timing
            time.sleep(0.15)  # Longer initial delay

            # Delete the original word + space
            total_to_delete = word_length + 1
            if self.debug:
                print(f"Deleting {total_to_delete} characters (word + space)")

            for i in range(total_to_delete):
                self.keyboard_controller.press(Key.backspace)
                self.keyboard_controller.release(Key.backspace)
                time.sleep(0.015)  # Slightly longer delay between backspaces

            # Wait before typing new text
            time.sleep(0.1)
            
            # Type the new text
            self.type_text_direct(text_to_type)

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


if __name__ == "__main__":
    mapper = BijoyMapper()
    mapper.run()