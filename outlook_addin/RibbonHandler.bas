Attribute VB_Name = "RibbonHandler"
' Обработчики для Ribbon кнопок
' Минимальный VBA код - только вызовы Python скрипта

Option Explicit

' Путь к Python скрипту (должен быть настроен)
Private Const PYTHON_SCRIPT_PATH As String = "C:\path\to\gold-outreach\outlook_launcher.py"

' Обработчик загрузки Ribbon
Public Sub RibbonOnLoad(ribbon As IRibbonUI)
    ' Можно добавить инициализацию, если необходимо
End Sub

' Создание кампании
Public Sub OnCreateCampaign(control As IRibbonControl)
    Call RunPythonScript("create_campaign")
End Sub

' Управление кампаниями
Public Sub OnManageCampaigns(control As IRibbonControl)
    Call RunPythonScript("manage_campaigns")
End Sub

' Загрузка шаблонов
Public Sub OnLoadTemplates(control As IRibbonControl)
    Call RunPythonScript("load_templates")
End Sub

' Показать логи
Public Sub OnShowLogs(control As IRibbonControl)
    Call RunPythonScript("show_logs")
End Sub

' Проверить ответы
Public Sub OnCheckReplies(control As IRibbonControl)
    Call RunPythonScript("check_replies")
End Sub

' Запуск Python скрипта
Private Sub RunPythonScript(action As String)
    On Error GoTo ErrorHandler
    
    Dim pythonPath As String
    Dim scriptPath As String
    Dim command As String
    
    ' Определяем путь к Python (можно настроить)
    pythonPath = "python"  ' Или полный путь, например "C:\Python312\python.exe"
    scriptPath = PYTHON_SCRIPT_PATH
    
    ' Формируем команду
    command = pythonPath & " """ & scriptPath & """ " & action
    
    ' Запускаем скрипт
    Shell command, vbNormalFocus
    
    Exit Sub
    
ErrorHandler:
    MsgBox "Ошибка при запуске Python скрипта: " & Err.Description, vbCritical
End Sub
