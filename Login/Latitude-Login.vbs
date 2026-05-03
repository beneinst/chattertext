Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\ChatterText\chattertext"
WshShell.Run """C:\ChatterText\chattertext\Login\Latitude-Login.bat""", 0, False