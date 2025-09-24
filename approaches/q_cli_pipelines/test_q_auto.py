#!/usr/bin/env python3
import subprocess
import time
from pathlib import Path

def test_q_cli_with_auto_approval():
    """Test Q CLI with automatic tool approval"""
    
    prompt = "Please create a simple text file called 'test_output.txt' in the current directory with the content: 'Hello from Q CLI! This is a test of automated invocation.' Then report completion."
    
    print("🤖 Invoking Q CLI with auto-approval...")
    
    try:
        # Start Q CLI process
        process = subprocess.Popen(
            ["q", "chat"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # Send the prompt
        process.stdin.write(prompt + "\n")
        process.stdin.flush()
        
        # Wait a bit for processing
        time.sleep(3)
        
        # Send 't' to trust the tool for the session
        process.stdin.write("t\n")
        process.stdin.flush()
        
        # Wait for completion
        time.sleep(5)
        
        # Send quit command
        process.stdin.write("/quit\n")
        process.stdin.flush()
        
        # Get output
        stdout, stderr = process.communicate(timeout=10)
        
        print(f"Return code: {process.returncode}")
        print("Output received (truncated):")
        print(stdout[-500:] if len(stdout) > 500 else stdout)
        
        # Check if file was created
        if Path("test_output.txt").exists():
            content = Path("test_output.txt").read_text()
            print(f"✅ File created with content: {content}")
            Path("test_output.txt").unlink()  # Clean up
            return True
        else:
            print("❌ Expected file not created")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Q CLI timeout")
        process.kill()
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_q_cli_with_auto_approval()
    print(f"\nTest result: {'SUCCESS' if success else 'FAILED'}")
