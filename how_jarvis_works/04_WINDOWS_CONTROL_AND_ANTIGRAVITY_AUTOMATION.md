# Chapter 4: Windows Control & Antigravity IDE Automation

## 1. Deep Win32 OS Integration

Controlling a desktop operating system like Windows 11 from a background Python service presents major architectural challenges that simple scripts fail to overcome:
1. **Windows Background Foreground Lock** prevents non-active processes from bringing windows to the front.
2. **Session / Desktop Isolation** prevents background threads from seeing visible desktop windows.
3. **Application Multiplexing** (e.g. Electron apps like VS Code and Antigravity) will hijack your active workspace unless explicitly isolated.

Here is how JARVIS solves every one of these challenges at the Win32 API level.

---

## 2. Bypassing Windows 11 Foreground Lock

### The Problem
Starting with Windows 10 and reinforced in Windows 11, Microsoft enforces `LockSetForegroundWindow`. If a background application (such as JARVIS receiving a command from your phone) calls `SetForegroundWindow(hwnd)`, Windows **blocks** the call and merely flashes the taskbar icon orange. The window is **not** brought to the front, and subsequent keystrokes (`Ctrl+L`, `Ctrl+V`) are dropped into whatever unrelated app is currently active.

### The Win32 Solution in JARVIS
In [`core/skills/system_control.py`](file:///c:/Users/Ahmad/OneDrive/Desktop/jarvis/core/skills/system_control.py), JARVIS executes a battle-tested 4-step sequence:

```python
# 1. Obtain thread IDs of current process and frontmost window
fg_hwnd = user32.GetForegroundWindow()
fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, None)
cur_tid = kernel32.GetCurrentThreadId()

# 2. Attach thread input queues together (bypasses Windows security barrier)
if fg_tid != cur_tid:
    user32.AttachThreadInput(cur_tid, fg_tid, True)

# 3. Simulate an ALT key tap (forces Windows to yield foreground permission)
user32.keybd_event(0x12, 0, 0, 0)
user32.keybd_event(0x12, 0, 2, 0)

# 4. Bring the target window to the absolute front
user32.ShowWindow(target_hwnd, 9)  # SW_RESTORE
user32.BringWindowToTop(target_hwnd)
user32.SetForegroundWindow(target_hwnd)

# 5. Detach thread input
if fg_tid != cur_tid:
    user32.AttachThreadInput(cur_tid, fg_tid, False)
```

---

## 3. Desktop Session Isolation Resolution

When running silently in the background (such as via Windows Startup or as a daemon task), Python threads may execute in a separate desktop session where `EnumWindows` returns an empty list.

JARVIS resolves this by explicitly opening and binding the interactive desktop:
```python
user32 = ctypes.windll.user32
h_desk = user32.OpenDesktopW("default", 0, False, 0x1FF)
if h_desk:
    user32.SetThreadDesktop(h_desk)
```
This guarantees that JARVIS can always enumerate, see, and interact with all real windows on the user's interactive desktop.

---

## 4. Antigravity IDE Automation & Workspace Isolation

When you instruct JARVIS:
> *"Open testing folder in Antigravity and write rules of cricket"*

JARVIS must perform complex multi-step automation without disrupting whatever project you are currently working on in your other Antigravity window.

### Step 1: Strict New Window Isolation (`-n`)
Electron applications (like Antigravity IDE and VS Code) reuse the active window by default. If a new folder is opened without special flags, Electron replaces the folder in your current window, closing your open files and destroying your state.

JARVIS prevents this by strictly enforcing the `-n` (`--new-window`) flag:
```python
cli = get_antigravity_cli_path() # antigravity-ide.cmd
subprocess.Popen([cli, "-n", target_path], shell=True)
```
This forces Antigravity to spawn a completely separate window for the requested folder.

### Step 2: Target Window Title Locking
Antigravity takes 2–4 seconds to render its Electron canvas. If a script blindly looks for *"Antigravity"*, it will immediately match your **already open** working window and inject keystrokes into the wrong project.

JARVIS prevents this by extracting the exact folder name (`window_keyword = "testing"`) and polling specifically for a window title matching that keyword:
```python
for attempt in range(24): # Poll up to 12 seconds
    time.sleep(0.5)
    # Match ONLY the target folder window, NEVER your other projects
    if window_keyword and window_keyword.lower() in title.lower():
        target_hwnd = hwnd
        break
```

### Step 3: Automated AI Prompt Injection
Once the new window is detected and brought to the front:
1. **Window Center Click**: JARVIS calculates the window's bounding box `(cx, cy)` and clicks inside the canvas to guarantee focus and dismiss any workspace trust overlays.
2. **Focus AI Agent (`Ctrl + Shift + L`)**: In Antigravity IDE, `Ctrl + L` is bound to `antigravity.toggleChatFocus` which has `shouldCloseWhenFocused: true`. If the chat panel is already open and focused from a previous session, pressing `Ctrl + L` will toggle it off (closing/disabling the chat). Instead, JARVIS sends `Ctrl + Shift + L` (`antigravity.startNewConversation`, weight: 300), which sets `shouldCloseWhenFocused: false`. This guarantees that if the chat is closed it opens, if it is already open it stays open, starts a fresh conversation, and explicitly focuses the prompt input box. (For VS Code, JARVIS continues to send `Ctrl + L`).
3. **Clipboard Injection (`Ctrl + V`)**: The user's prompt is verified in the system clipboard via `pyperclip` and pasted cleanly with `Ctrl + V`.
4. **Execution (`Enter`)**: JARVIS sends the `Enter` keystroke. The AI Agent in the new window immediately begins coding, generating files, and solving the prompt autonomously!
