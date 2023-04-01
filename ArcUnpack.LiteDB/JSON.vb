' VBJSON is a VB6 adaptation of the VBA JSON project at http://code.google.com/p/vba-json/
' Some bugs fixed, speed improvements added for VB6 by Michael Glaser (vbjson@ediy.co.nz)
' BSD Licensed

' Ported to dotnet & modified by YidaozhanYa

Option Explicit On

Public Class JsonParser
    Const INVALID_JSON As Integer = 1
    Const INVALID_OBJECT As Integer = 2
    Const INVALID_ARRAY As Integer = 3
    Const INVALID_BOOLEAN As Integer = 4
    Const INVALID_NULL As Integer = 5
    Const INVALID_KEY As Integer = 6
    Const INVALID_RPC_CALL As Integer = 7

    Private psErrors As String = ""


    Public Function GetParserErrors() As String
        Return psErrors
    End Function

    Public Sub ClearParserErrors()
        psErrors = ""
    End Sub

    '
    '   parse string and create JSON object
    '

    Public Function Parse(ByRef str As String) As Object
        Dim index As Integer
        index = 1
        psErrors = ""
        On Error Resume Next
        Call SkipChar(str, index)
        Select Case Mid(str, index, 1)
            Case "{"
                Parse = ParseObject(str, index)
            Case "["
                Parse = ParseArray(str, index) 'Collection
            Case Else
                psErrors = "Invalid JSON"
                Parse = New Dictionary(Of String, Object)
        End Select
        Return Parse
    End Function
    '
    '   parse collection of key/value
    '
    Private Function ParseObject(ByRef str As String, ByRef index As Integer) As Dictionary(Of String, Object)

        ParseObject = New Dictionary(Of String, Object)
        Dim sKey As String

        ' "{"
        Call skipChar(str, index)
        If Mid(str, index, 1) <> "{" Then
            psErrors = psErrors & "Invalid Object at position " & index & " : " & Mid(str, index) & vbCrLf
            Exit Function
        End If

        index += 1

        Do
            Call skipChar(str, index)
            If "}" = Mid(str, index, 1) Then
                index += 1
                Exit Do
            ElseIf "," = Mid(str, index, 1) Then
                index += 1
                Call skipChar(str, index)
            ElseIf index > Len(str) Then
                psErrors = psErrors & "Missing '}': " & Right(str, 20) & vbCrLf
                Exit Do
            End If


            ' add key/value pair
            sKey = parseKey(str, index)
            On Error Resume Next

            ParseObject.Add(sKey, parseValue(str, index))
            If Err.Number <> 0 Then
                psErrors = psErrors & Err.Description & ": " & sKey & vbCrLf
                Exit Do
            End If
        Loop
    End Function
    '
    '   parse list
    '
    Private Function ParseArray(ByRef str As String, ByRef index As Integer) As Collection

        Dim RetVal As New Collection

        ' "["
        Call skipChar(str, index)
        If Mid(str, index, 1) <> "[" Then
            psErrors = psErrors & "Invalid Array at position " & index & " : " + Mid(str, index, 20) & vbCrLf
            Exit Function
        End If

        index += 1

        Do

            Call skipChar(str, index)
            If "]" = Mid(str, index, 1) Then
                index += 1
                Exit Do
            ElseIf "," = Mid(str, index, 1) Then
                index += 1
                Call skipChar(str, index)
            ElseIf index > Len(str) Then
                psErrors = psErrors & "Missing ']': " & Right(str, 20) & vbCrLf
                Exit Do
            End If

            ' add value
            On Error Resume Next
            RetVal.Add(parseValue(str, index))
            If Err.Number <> 0 Then
                psErrors = psErrors & Err.Description & ": " & Mid(str, index, 20) & vbCrLf
                Exit Do
            End If
        Loop
        Return RetVal

    End Function

    '
    '   parse string / number / object / array / true / false / null
    '
    Private Function ParseValue(ByRef str As String, ByRef index As Integer)
        Dim RetVal
        Call SkipChar(str, index)

        Select Case Mid(str, index, 1)
            Case "{"
                RetVal = ParseObject(str, index)
            Case "["
                RetVal = ParseArray(str, index)
            Case """", "'"
                RetVal = ParseString(str, index)
            Case "t", "f"
                RetVal = ParseBoolean(str, index)
            Case "d"
                RetVal = ParseDateTime(str, index)
            Case "n"
                RetVal = ParseNull(str, index)
            Case Else
                RetVal = ParseNumber(str, index)
        End Select
        Return RetVal
    End Function

    '
    '   parse string
    '
    Private Function ParseString(ByRef str As String, ByRef index As Integer) As String

        Dim quote As String
        Dim Character As String = ""
        Dim Code As String

        Dim SB As String = ""

        Call skipChar(str, index)
        quote = Mid(str, index, 1)
        index += 1

        Do While index > 0 And index <= Len(str)
            Character = Mid(str, index, 1)
            Select Case Character
                Case "\"
                    index += 1
                    Character = Mid(str, index, 1)
                    Select Case Character
                        Case """", "\", "/", "'"
                            SB &= Character
                            index += 1
                        Case "b"
                            SB &= vbBack
                            index += 1
                        Case "f"
                            SB &= vbFormFeed
                            index += 1
                        Case "n"
                            SB &= vbLf
                            index += 1
                        Case "r"
                            SB &= vbCr
                            index += 1
                        Case "t"
                            SB &= vbTab
                            index += 1
                        Case "u"
                            index += 1
                            Code = Mid(str, index, 4)
                            SB &= ChrW(Val("&h" + Code))
                            index += 4
                    End Select
                Case quote
                    index += 1
                    Return SB
                Case Else
                    SB &= Character
                    index += 1
            End Select
        Loop

        Return SB

    End Function

    '
    '   parse number
    '
    Private Function ParseNumber(ByRef str As String, ByRef index As Integer) As Object  'Integer / Single

        Dim Value As String = ""
        Dim Character As String = ""

        Call skipChar(str, index)
        Do While index > 0 And index <= Len(str)
            Character = Mid(str, index, 1)
            If InStr("+-0123456789.eE", Character) Then
                Value &= Character
                index += 1
            Else
                If CDbl(Value) = CInt(Value) Then
                    Return CInt(Value)
                Else
                    Return CDbl(Value)
                End If
            End If
        Loop
    End Function

    '
    '   parse timestamp
    '
    Private Function ParseDateTime(ByRef str As String, ByRef index As Integer) As DateTime

        Dim Value As String = ""
        Dim Character As String = ""

        Call skipChar(str, index)
        Do While index > 0 And index <= Len(str)
            Character = Mid(str, index, 1)
            If InStr("d0123456789", Character) Then
                Value &= Character
                index += 1
            Else
                Dim UnixTimestamp As Integer = CInt(Value.Replace("d", ""))
                Return New DateTime(1970, 1, 1, 0, 0, 0, 0).AddMilliseconds(UnixTimestamp)
            End If
        Loop
    End Function

    '
    '   parse true / false
    '
    Private Function ParseBoolean(ByRef str As String, ByRef index As Integer) As Boolean
        Dim RetVal As Boolean
        Call skipChar(str, index)
        If Mid(str, index, 4) = "true" Then
            RetVal = True
            index += 4
        ElseIf Mid(str, index, 5) = "false" Then
            RetVal = False
            index += 5
        Else
            psErrors = psErrors & "Invalid Boolean at position " & index & " : " & Mid(str, index) & vbCrLf
        End If
        Return RetVal

    End Function

    '
    '   parse null
    '
    Private Function ParseNull(ByRef str As String, ByRef index As Integer)
        Dim RetVal As String = ""
        Call skipChar(str, index)
        If Mid(str, index, 4) = "null" Then
            RetVal = Nothing
            index += 4
        Else
            psErrors = psErrors & "Invalid null value at position " & index & " : " & Mid(str, index) & vbCrLf
        End If
        Return RetVal

    End Function

    Private Function ParseKey(ByRef str As String, ByRef index As Integer) As String

        Dim dquote As Boolean
        Dim squote As Boolean
        Dim Character As String
        Dim RetVal As String = ""

        Call skipChar(str, index)
        Do While index > 0 And index <= Len(str)
            Character = Mid(str, index, 1)
            Select Case Character
                Case """"
                    dquote = Not dquote
                    index += 1
                    If Not dquote Then
                        Call skipChar(str, index)
                        If Mid(str, index, 1) <> ":" Then
                            psErrors = psErrors & "Invalid Key at position " & index & " : " & RetVal & vbCrLf
                            Exit Do
                        End If
                    End If
                Case "'"
                    squote = Not squote
                    index += 1
                    If Not squote Then
                        Call skipChar(str, index)
                        If Mid(str, index, 1) <> ":" Then
                            psErrors = psErrors & "Invalid Key at position " & index & " : " & RetVal & vbCrLf
                            Exit Do
                        End If
                    End If
                Case ":"
                    index += 1
                    If Not dquote And Not squote Then
                        Exit Do
                    Else
                        RetVal &= Character
                    End If
                Case Else
                    If InStr(vbCrLf & vbCr & vbLf & vbTab & " ", Character) Then
                    Else
                        RetVal &= Character
                    End If
                    index += 1
            End Select
        Loop
        Return RetVal

    End Function

    '
    '   skip special character
    '
    Private Sub SkipChar(ByRef str As String, ByRef index As Integer)
        Dim bComment As Boolean
        Dim bStartComment As Boolean
        Dim bLongComment As Boolean
        Do While index > 0 And index <= Len(str)
            Select Case Mid(str, index, 1)
                Case vbCr, vbLf
                    If Not bLongComment Then
                        bStartComment = False
                        bComment = False
                    End If

                Case vbTab, " ", "(", ")"

                Case "/"
                    If Not bLongComment Then
                        If bStartComment Then
                            bStartComment = False
                            bComment = True
                        Else
                            bStartComment = True
                            bComment = False
                            bLongComment = False
                        End If
                    Else
                        If bStartComment Then
                            bLongComment = False
                            bStartComment = False
                            bComment = False
                        End If
                    End If

                Case "*"
                    If bStartComment Then
                        bStartComment = False
                        bComment = True
                        bLongComment = True
                    Else
                        bStartComment = True
                    End If

                Case Else
                    If Not bComment Then
                        Exit Do
                    End If
            End Select

            index += 1
        Loop

    End Sub

End Class
