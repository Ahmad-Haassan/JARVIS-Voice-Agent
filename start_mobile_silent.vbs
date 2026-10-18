Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strPath = fso.GetParentFolderName(WScript.ScriptFullName)

WshShell.CurrentDirectory = strPath
WshShell.Run "cmd.exe /c start """" """ & strPath & "\venv\Scripts\pythonw.exe"" """ & strPath & "\server.py""", 0, False
