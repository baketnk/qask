from rich.console import Console

class ConsoleWrapper:
    def __init__(self):
        self._rich_console = Console()
        self._plain_mode = False
    
    def set_plain_mode(self, plain: bool):
        self._plain_mode = plain
    
    def print(self, *args, **kwargs):
        if self._plain_mode:
            # Strip any Rich markup and just print plain text
            if len(args) == 1 and hasattr(args[0], '__rich__'):
                # Handle Markdown objects
                print(args[0].markup)
            else:
                print(*args)
        else:
            self._rich_console.print(*args, **kwargs)

console = ConsoleWrapper()
