Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\Siti GitHub\chattertext"
WshShell.Run "cmd.exe /c mamba run -n chatterbox pythonw ChatterText-App-23.py", 0, False