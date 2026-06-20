"""Helper to send Python code to the Blender addon via socket (port 9876)."""
import socket, json, sys

def run_in_blender(code, host='localhost', port=9876, timeout=60):
    cmd = json.dumps({"type": "execute_code", "params": {"code": code}})
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((host, port))
    s.sendall(cmd.encode('utf-8'))
    chunks = []
    while True:
        try:
            chunk = s.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
            try:
                json.loads(b''.join(chunks).decode('utf-8'))
                break  # valid JSON received
            except json.JSONDecodeError:
                pass
        except socket.timeout:
            break
    s.close()
    raw = b''.join(chunks).decode('utf-8')
    resp = json.loads(raw)
    if resp.get('status') == 'error':
        print("BLENDER ERROR:", resp.get('message'))
    else:
        result = resp.get('result', {})
        out = result.get('result', '')
        if out:
            print(out)
    return resp

if __name__ == '__main__':
    code = sys.stdin.read() if not sys.argv[1:] else open(sys.argv[1]).read()
    run_in_blender(code)
