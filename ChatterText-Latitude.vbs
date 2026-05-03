Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\ChatterText\chattertext"
WshShell.Run "cmd.exe /c mamba run -n chatterbox pythonw ChatterText-App-23.py", 0, False