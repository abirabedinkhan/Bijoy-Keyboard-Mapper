from listener import BijoyMapper

if __name__ == "__main__":
    try:
        import pyperclip
    except ImportError:
        print("Installing pyperclip...")
        import subprocess
        subprocess.check_call(["pip", "install", "pyperclip"])
        import pyperclip

    mapper = BijoyMapper()
    mapper.run()