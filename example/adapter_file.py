import sys
import os
import glob

def transmit(base64_data, mode):
    folder = "./c2s" if mode == "client" else "./s2c"
    os.makedirs(folder, exist_ok=True)
    
    existing_files = glob.glob(f"{folder}/*.txt")
    next_index = len(existing_files) + 1
    
    filename = os.path.join(folder, f"{next_index:06d}.txt")
    
    temp_filename = filename + ".tmp"
    with open(temp_filename, "w") as f:
        f.write(base64_data + "\n")
    
    try:
        os.replace(temp_filename, filename)
    except OSError:
        try:
            os.remove(temp_filename)
        except OSError:
            pass

def receive(mode):
    folder = "./s2c" if mode == "client" else "./c2s"
    os.makedirs(folder, exist_ok=True)
    
    files = sorted(glob.glob(f"{folder}/*.txt"))
    
    for filepath in files:
        if filepath.endswith(".tmp"):
            continue
        try:
            with open(filepath, "r") as f:
                content = f.read().strip()
                if content:
                    print(content)
            os.remove(filepath)
        except Exception:
            pass
            
    print("__END_BATCH__")
    sys.stdout.flush()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
        
    mode = sys.argv[1]
    
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split(" ", 1)
            cmd = parts[0]
            
            if cmd == "TX" and len(parts) == 2:
                transmit(parts[1], mode)
            elif cmd == "RX":
                receive(mode)
    except KeyboardInterrupt:
        sys.exit(0)
