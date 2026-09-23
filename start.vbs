' chatgpt-auto-continue 静默启动（pythonw，无控制台窗口）
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
shell.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)
shell.Run "pythonw.exe main.py loop", 0, False
