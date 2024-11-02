import typer
import asyncio
import sys

from pathlib import Path
from rich.prompt import Prompt
from rich.markdown import Markdown
from .llm import llm_stream
from . import app 

from rich.console import Console
console = Console()

def read_prompt_file(file_path: Path) -> str:
    """Read and return the contents of the prompt file."""
    try:
        with file_path.open('r') as f:
            return f.read().strip()
    except Exception as e:
        console.print(f"Error reading prompt file: {str(e)}")
        raise typer.Exit(1)

async def stream_response(question: str, model: str = "llama3.2:3b", plain: bool = False):
    messages = [{"role": "user", "content": question}]
    response_text = ""
    
    try:
        async for chunk in llm_stream(
            messages=messages,
            api_base="http://localhost:11434/v1",
            api_key="",
            model=model,
            temperature=0.7,
            api_type="openai",
            add_noise=False
        ):
            if "choices" in chunk and chunk["choices"]:
                delta = chunk["choices"][0].get("delta", {}).get("content", "")
                response_text += delta
        
        if plain:
            console.print(response_text)
        else:
            console.print(Markdown(response_text))
    except Exception as e:
        console.print(f"Error: {str(e)}")
        raise typer.Exit(1)

@app.command()
def ask(
    question: str = typer.Argument(None, help="The question to ask"),
    model: str = typer.Option("llama3.2:3b", help="The model to use"),
    plain: bool = typer.Option(False, help="Disable rich formatting"),
    prompt_file: Path = typer.Option(None, help="Read prompt from file", exists=True, dir_okay=False)
):
    """
    Ask a question to an Ollama model and get a streaming response.
    The question can be provided as an argument, through stdin, or from a file.
    """
    # TODO: set plain mode
    # console.set_plain_mode(plain)
    if plain:
        plain = False
        # console.print("plain mode not implemented")
    
    # Handle different input sources in order of priority:
    # 1. prompt-file
    # 2. argument
    # 3. stdin
    if prompt_file:
        question = read_prompt_file(prompt_file)
    elif question is None:
        if sys.stdin.isatty():
            try:
                if plain:
                    question = input("Enter your question: ")
                else:
                    question = Prompt.ask("[blue]Enter your question[/blue]")
            except KeyboardInterrupt:
                console.print("\nInterrupted by user")
                raise typer.Exit()
        else:
            try:
                question = sys.stdin.read().strip()
            except KeyboardInterrupt:
                console.print("\nInterrupted by user")
                raise typer.Exit()
    
    if not question:
        console.print("Error: No question provided")
        raise typer.Exit(1)

    # Display the question
    if plain:
        print(f"Question: {question}\n")
        print("Answer:\n")
    else:
        console.print(f"[blue]Question: {question}[/blue]\n")
        console.print("[green]Answer:[/green]\n")

    try:
        asyncio.run(stream_response(question, model, plain))
    except KeyboardInterrupt:
        console.print("\nInterrupted by user")
        raise typer.Exit()

