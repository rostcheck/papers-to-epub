#!/usr/bin/env python3
import subprocess
import tempfile
from pathlib import Path

def test_q_cli_invocation():
    """Test invoking Q CLI with instructions"""
    
    # Create simple test instructions
    instructions = """
# Test Instructions for Q CLI

Please create a simple text file called 'test_output.txt' in the current directory with the content:
"Hello from Q CLI! This is a test of automated invocation."

Then report that you have completed the task.
"""
    
    # Save instructions to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(instructions)
        instructions_file = f.name
    
    print(f"📝 Created instructions: {instructions_file}")
    
    try:
        # Invoke Q CLI with stdin input instead of file reference
        prompt = f"Please create a simple text file called 'test_output.txt' in the current directory with the content: 'Hello from Q CLI! This is a test of automated invocation.' Then report that you have completed the task."
        
        cmd = ["q", "chat"]
        
        print("🤖 Invoking Q CLI with direct prompt...")
        result = subprocess.run(
            cmd, 
            input=prompt,
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Output: {result.stdout}")
        if result.stderr:
            print(f"Error: {result.stderr}")
        
        # Check if file was created
        if Path("test_output.txt").exists():
            content = Path("test_output.txt").read_text()
            print(f"✅ File created with content: {content}")
            Path("test_output.txt").unlink()  # Clean up
        else:
            print("❌ Expected file not created")
            
    except subprocess.TimeoutExpired:
        print("❌ Q CLI timeout")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Clean up
        Path(instructions_file).unlink()

if __name__ == "__main__":
    test_q_cli_invocation()
