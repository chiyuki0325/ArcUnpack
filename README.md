# ArcUnpack

Chart unpacker for certain rhythm game.

## Build

```bash
# Download and compile UltraLiteDB
git clone https://github.com/rejemy/UltraLiteDB.git
pushd UltraLiteDB
dotnet publish -c Release
popd
cp bin/Release/netstandard2.0/publish/UltraLiteDB.dll ./ArcUnpack.LiteDB/

# Compile LiteDB wrapper
pushd ArcUnpack.LiteDB
dotnet publish -c Release
popd
```

## Usage

... ...