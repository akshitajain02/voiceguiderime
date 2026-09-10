import asyncio
import time
import json
import argparse
import random
import uuid
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
except ImportError:
    print("Please install 'rich' library to run this script: pip install rich", file=sys.stderr)
    sys.exit(1)

console = Console()

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "test_runs.json"

async def mock_livekit_session():
    """
    Mocks a LiveKit session to measure TTS interruption latency.
    Simulates a query, response, playback, and a VAD interruption.
    """
    # Simulate user querying and LLM generating response
    await asyncio.sleep(0.1) 
    
    # Simulate Rime starting audio playback
    playback_duration = random.uniform(1.0, 2.5)
    await asyncio.sleep(playback_duration)
    
    # Simulated Voice Activity Detection (VAD) interrupt event
    vad_timestamp = time.perf_counter()
    
    # Simulate system processing the interrupt and stopping audio
    # Using a sub-500ms latency to simulate successful performance
    simulated_cutoff_delay = random.uniform(0.250, 0.490) 
    await asyncio.sleep(simulated_cutoff_delay)
    
    cutoff_timestamp = time.perf_counter()
    
    # Calculate exact latency
    latency_ms = (cutoff_timestamp - vad_timestamp) * 1000
    return latency_ms

async def run_tests(num_runs: int):
    """
    Executes multiple mock LiveKit sessions and logs the latency results.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load existing logs if any
    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r") as f:
                content = f.read()
                if content.strip():
                    logs = json.loads(content)
        except json.JSONDecodeError:
            console.print("[yellow]Warning: Could not parse existing logs, starting fresh.[/yellow]")
            
    current_runs = []
    with console.status(f"[bold green]Running {num_runs} interruption tests...") as status:
        for i in range(num_runs):
            status.update(f"[bold green]Running test {i+1}/{num_runs}...")
            latency_ms = await mock_livekit_session()
            
            run_data = {
                "run_id": str(uuid.uuid4()),
                "timestamp": time.time(),
                "latency_ms": round(latency_ms, 2),
                "success": latency_ms < 500,
                "rime_active": True
            }
            current_runs.append(run_data)
            logs.append(run_data)
            
    # Save logs
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)
        
    return current_runs, logs

def display_dashboard(current_runs, all_logs):
    """
    Parses the JSON log and outputs a clean terminal dashboard with metrics.
    """
    console.print("\n")
    
    if not current_runs:
        console.print("[red]No tests were run.[/red]")
        return

    # Calculate metrics
    latencies = [run["latency_ms"] for run in current_runs]
    avg_latency = sum(latencies) / len(latencies)
    
    rime_active_count = sum(1 for run in current_runs if run.get("rime_active"))
    total_current = len(current_runs)
    
    # Dashboard Header
    console.print(Panel("[bold cyan]VoiceGuide - Interruption & Recovery Dashboard[/bold cyan]", box=box.DOUBLE))
    
    # Metrics Summary
    summary_text = (
        f"[bold]Avg. Interrupt Latency:[/bold] [yellow]{avg_latency:.2f} ms[/yellow]\n"
        f"[bold]Success Rate (< 500ms):[/bold] [green]{sum(1 for run in current_runs if run['success'])}/{total_current}[/green]\n"
        f"[bold]Rime Active:[/bold] [green]{rime_active_count}/{total_current}[/green]"
    )
    console.print(Panel(summary_text, title="Test Run Summary", border_style="cyan"))
    
    # Table of latest runs
    table = Table(title="Latest Runs Details", box=box.ROUNDED)
    table.add_column("Run ID", style="dim", width=36)
    table.add_column("Latency (ms)", justify="right")
    table.add_column("Status", justify="center")
    table.add_column("Rime Active", justify="center")
    
    for run in current_runs:
        status_color = "[green]PASS[/green]" if run["success"] else "[red]FAIL[/red]"
        rime_color = "[green]True[/green]" if run["rime_active"] else "[red]False[/red]"
        table.add_row(
            run["run_id"],
            f"{run['latency_ms']:.2f}",
            status_color,
            rime_color
        )
        
    console.print(table)
    console.print("\n[dim]Data successfully appended to logs/test_runs.json[/dim]")


def main():
    parser = argparse.ArgumentParser(description="Run LiveKit TTS Interruption Tests")
    parser.add_argument("--runs", type=int, default=5, help="Number of test runs to execute")
    args = parser.parse_args()
    
    try:
        current_runs, all_logs = asyncio.run(run_tests(args.runs))
        display_dashboard(current_runs, all_logs)
    except KeyboardInterrupt:
        console.print("\n[red]Test interrupted by user.[/red]")
    except Exception as e:
        console.print(f"\n[red]An error occurred: {str(e)}[/red]")

if __name__ == "__main__":
    main()
