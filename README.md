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
bash build.sh
popd
```

## Usage

- Obtain a legal copy of Nintendo Switch version of the game.
- Dump game romfs with [nxdumptool](https://github.com/DarkMatterCore/nxdumptool).
- Install the emulator of the game on your device, and get the litedb file from installation.
```bash
adb pull /storage/emulated/0/Android/data/com.Certain.Rhythm.Game.Emulator/files/Persistent/some_litedb_file.litedb
```
- Run the program.
```bash
# Change this to your own compiled path
export ARCUNPACK_LITEDB_PATH="ArcUnpack.LiteDB/bin/Release/net7.0/linux-x64/publish/ArcUnpack.LiteDB"
python3 arc_unpack.py 'path/to/romfs' 'path/to/litedb/file'
```
- Enjoy!