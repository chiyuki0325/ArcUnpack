'UltraLiteDB wrapper
'2023 YidaozhanYa

Imports System
Imports UltraLiteDB

Module LiteDB
    Function DictionaryToBsonDocument(Dict As Dictionary(Of String, Object)) As BsonDocument
        Dim Document As New BsonDocument()
        For Each Key As String In Dict.Keys
            Dim Value As Object = Dict(Key)
            Dim BValue As BsonValue = BsonValue.FromObject(Value)
            Document.Add(Key, BValue)
        Next
        Return Document
    End Function

    Sub Main(args As String())
        Dim Database As New UltraLiteDatabase(args(0))
        Dim PackStorageCol As UltraLiteCollection(Of BsonDocument) = Database.GetCollection("PackStorage")
        Dim LevelStorageCol As UltraLiteCollection(Of BsonDocument) = Database.GetCollection("LevelStorage")
        Dim FileReferenceCol As UltraLiteCollection(Of BsonDocument) = Database.GetCollection("FileReference")
        Dim Json As New JsonParser()
        Select Case args(1).ToLower()
            Case "viewcontent"  ' For testing
                Console.WriteLine("PackStorage")
                For Each Doc As BsonDocument In PackStorageCol.FindAll()
                    Console.WriteLine(Doc.ToString())
                Next
                Console.WriteLine("LevelStorage")
                For Each Doc As BsonDocument In LevelStorageCol.FindAll()
                    Console.WriteLine(Doc.ToString())
                Next
                Console.WriteLine("FileReference")
                For Each Doc As BsonDocument In FileReferenceCol.FindAll()
                    Console.WriteLine(Doc.ToString())
                Next
            Case "testjson"  'For testing
                Dim JsonContent = Json.Parse(args(2))
                Console.WriteLine(DictionaryToBsonDocument(JsonContent).ToString())
            Case "packcount"
                Console.WriteLine(PackStorageCol.Count())
            Case "levelcount"
                Console.WriteLine(LevelStorageCol.Count())
            Case "addlevel"
                Dim JsonContent = Json.Parse(args(2))
                LevelStorageCol.Insert(DictionaryToBsonDocument(JsonContent))
            Case "addpack"
                Dim JsonContent = Json.Parse(args(2))
                PackStorageCol.Insert(DictionaryToBsonDocument(JsonContent))
            Case "addfile"
                Dim JsonContent = Json.Parse(args(2))
                FileReferenceCol.Insert(DictionaryToBsonDocument(JsonContent))
            Case Else
                Console.WriteLine("Invalid command!")
                Environment.Exit(1)
        End Select
    End Sub
End Module
