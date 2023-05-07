#!/usr/bin/env python3
from copy import deepcopy
from pathlib import Path
import sys, shutil, json, subprocess, re, os
from time import time
from hashlib import sha1


class Message:
    ALL_OFF = '\033[0m'
    BOLD = '\033[1m'
    BLUE = f'{BOLD}\033[34m'
    GREEN = f'{BOLD}\033[32m'
    RED = f'{BOLD}\033[31m'
    YELLOW = f'{BOLD}\033[33m'

    def plain(self, message):
        print(f'{self.BOLD}   {message}{self.ALL_OFF}')

    def msg(self, message):
        print(f'{self.GREEN}==>{self.ALL_OFF}{self.BOLD} {message}{self.ALL_OFF}')

    def msg2(self, message):
        print(f'{self.BLUE}  ->{self.ALL_OFF}{self.BOLD} {message}{self.ALL_OFF}')

    def ask(self, message):
        print(f'{self.BLUE}::{self.ALL_OFF}{self.BOLD} {message}{self.ALL_OFF}')

    def warning(self, message):
        print(f'{self.YELLOW}==> WARNING:{self.ALL_OFF}{self.BOLD} {message}{self.ALL_OFF}', file=sys.stderr)

    def error(self, message):
        print(f'{self.RED}==> ERROR:{self.ALL_OFF}{self.BOLD} {message}{self.ALL_OFF}', file=sys.stderr)


msg = Message()

litedb_path = Path(os.environ.get(
    'ARCUNPACK_LITEDB_PATH',
    f'./ArcUnpack.LiteDB/bin/Release/net7.0/'
    f'{("win" if sys.platform == "win32" else "linux")}'
    f'-{("x64" if sys.maxsize > 2**32 else "")}/publish/ArcUnpack.LiteDB'
))


class LiteDB:
    def __init__(self, path: Path):
        if not path.exists():
            raise FileNotFoundError(f'LiteDB not found at {path}')
        self.path = path

    def pack_count(self) -> int:
        proc = subprocess.Popen(
            [
                litedb_path,
                self.path,
                'PackCount'
            ],
            stdout=subprocess.PIPE,
        )
        proc.wait()
        return int(proc.stdout.read().strip().decode('utf-8'))

    def level_count(self) -> int:
        proc = subprocess.Popen(
            [
                litedb_path,
                self.path,
                'LevelCount'
            ],
            stdout=subprocess.PIPE,
        )
        proc.wait()
        return int(proc.stdout.read().strip().decode('utf-8'))

    def subcommand(self, subcommand: str, content: str):
        # For AddPack, AddLevel, AddFile
        proc = subprocess.Popen(
            [
                litedb_path,
                self.path,
                subcommand,
                content
            ],
            stdout=subprocess.PIPE,
        )
        proc.wait()


input_romfs_path = Path(sys.argv[1])  # romfs
extracted_romfs_path = Path('./extracted_romfs')
arc_create_db_input_path = Path(sys.argv[2])  # arccreate.litedb
final_path = Path('./final')

msg.ask('Preparing ...')

# Check for required files
if not litedb_path.exists():
    msg.error('ArcUnpack.LiteDB not found!')
    sys.exit(1)

if not input_romfs_path.exists():
    if extracted_romfs_path.exists():
        msg.warning('Extracted romfs found, skipping extraction...')
    else:
        msg.error('Input romfs not found!')
        sys.exit(1)

# Make folders
extracted_romfs_path.mkdir(parents=True, exist_ok=True)
final_path.mkdir(parents=True, exist_ok=True)

# Copy database file
arc_create_db_path = final_path / 'arccreate.litedb'
if not arc_create_db_path.exists():
    shutil.copy(arc_create_db_input_path, arc_create_db_path)

# LiteDB instance
litedb = LiteDB(arc_create_db_path)

# File list to extract
pack_list: list[Path] = []
for pack in input_romfs_path.glob('*.pack'):
    pack_list.append(pack)
pack_list.sort()

msg.ask('Extracting romfs...')

# Extract romfs
for pack_path in pack_list:
    with open(pack_path, 'rb') as pack:
        msg.msg(f'Extracting pack {pack_path.name}...')
        index_file = pack_path.with_suffix('.json')
        with open(index_file) as index_f:
            index: dict = json.load(index_f)
            for group in index['Groups']:
                msg.msg2(f'Extracting group {group["Name"]}...')
                group_path = extracted_romfs_path / group['Name']
                group_path.mkdir(parents=True, exist_ok=True)

                for ordered_entry in group['OrderedEntries']:
                    file_path = group_path / ordered_entry['OriginalFilename']
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    pack.seek(ordered_entry['Offset'])
                    with open(file_path, 'wb') as out_f:
                        out_f.write(pack.read(ordered_entry['Length']))
                        out_f.close()
        index_f.close()
    pack.close()

converted_songs: list[dict] = []
converted_packs: list[dict] = []
converted_files: list[dict] = []
level_identifiers: dict[str, list[str]] = {}

msg.ask('Converting songs...')

# Convert songs
level_count = litedb.level_count()
song_list_path = extracted_romfs_path / 'not_audio_or_images' / 'songs' / 'songlist'
song_list: dict = json.load(open(song_list_path, 'r'))


def copy_audio(_original_id: str, _song_root_path: Path):
    audio_root_path = extracted_romfs_path / 'Fallback' / 'songs'
    shutil.copyfile(  # Copy audio
        audio_root_path / _original_id / 'base.ogg',
        _song_root_path / 'base.ogg'
    )


def copy_jacket(_original_id: str, _song_root_path: Path):
    jacket_root_path = extracted_romfs_path / 'jackets_large' / 'songs'
    shutil.copyfile(  # Copy jacket
        jacket_root_path / _original_id / 'base.jpg',
        _song_root_path / 'base.jpg'
    )


def convert_chart(
        _diff: dict,
        _song: dict,
        _original_id: str,
        _song_root_path: Path,
        convert_controller_alt_chart_mode: bool = False
):
    _background_paths = []
    background_root_path = extracted_romfs_path / 'not_audio' / 'img' / 'bg'
    charts_root_path = extracted_romfs_path / 'charts' / 'songs'
    difficulty_names = ['Past', 'Present', 'Future', 'Beyond']
    difficulty_colors = ['#3A6B78FF', '#566947FF', '#482B54FF', '#7C1C30FF']

    if not convert_controller_alt_chart_mode:
        chart_path = charts_root_path / _original_id / f"{_diff['ratingClass']}.aff"
        if 'has_controller_alt_chart' in _diff and _diff['has_controller_alt_chart']:
            _has_controller_charts = True
        else:
            _has_controller_charts = False
    else:
        chart_path = charts_root_path / _original_id / f"{_diff['ratingClass']}c.aff"
        _has_controller_charts = False

    _chart: dict = {
        'ChartPath': chart_path.name,
        'AudioPath': 'base.ogg',
        'JacketPath': 'base.jpg',
        'BaseBpm': float(_song['bpm_base']),
        'Title': (
            _song['title_localized']['en'] if not convert_controller_alt_chart_mode
            else _song['title_localized']['en'] + ' (Alt)'
        ),
        'Composer': _song['artist'],
        'Charter': _diff['chartDesigner'],
        'Illustrator': _diff['jacketDesigner'],
        'Difficulty': f"{difficulty_names[_diff['ratingClass']]} {_diff['rating']}",
        'ChartConstant': float(_diff['rating']),
        'DifficultyColor': difficulty_colors[_diff['ratingClass']],
    }

    shutil.copyfile(  # Copy chart
        chart_path,
        _song_root_path / chart_path.name
    )

    if _song['side'] in [0, 1]:
        _chart['Skin'] = {
            'Side': 'light' if _song['side'] == 0 else 'conflict',
        }
    if _song['bpm'] == str(_song['bpm_base']):
        _chart['SyncBaseBpm'] = True
    else:
        _chart['SyncBaseBpm'] = False
        _chart['BpmText'] = _song['bpm'].replace(' ', '').replace('-', ' - ')
    if _song['bg'] != '':
        # Song-specific background
        background_path = background_root_path / f"{song['bg']}.jpg"
    else:
        # Use default background
        base_background_type = 'byd' if _diff['ratingClass'] == 3 else 'base'
        base_background_name = 'light' if song['side'] == 0 else 'conflict'
        background_path = background_root_path / f"{base_background_type}_{base_background_name}.jpg"
    if not (song_root_path / background_path.name).exists():
        shutil.copyfile(  # Copy background
            background_path,
            song_root_path / background_path.name
        )
        _background_paths.append(background_path)
    _chart['BackgroundPath'] = background_path.name
    return _chart, _background_paths, _has_controller_charts


i: int = level_count + 1
for song in song_list['songs']:
    msg.msg2(f'Converting song {song["id"]}...')
    original_id: str = f"dl_{song['id']}" if 'remote_dl' in song and song['remote_dl'] else song['id']
    new_id: str = f"{song['set']}.{song['id']}"
    song_root_path = final_path / 'Level' / new_id
    song_root_path.mkdir(parents=True, exist_ok=True)

    copy_audio(original_id, song_root_path)
    copy_jacket(original_id, song_root_path)

    converted_song: dict = {  # Base information
        '_id': i,
        'Type': 'Level',
        'Identifier': new_id,
        'IsDefaultAsset': True,
        'AddedDate': f"d{song['date']}",
        'Version': 0
    }
    has_controller_charts: bool = False  # need reconvert
    charts: list[dict] = []
    background_paths: list[Path] = []
    for diff in song['difficulties']:
        (
            chart,
            background_paths_to_extend,
            has_controller_charts_to_extend
        ) = convert_chart(
            diff,
            song,
            original_id,
            song_root_path,
            False
        )
        background_paths.extend(background_paths_to_extend)
        if has_controller_charts_to_extend:
            has_controller_charts = True
        charts.append(chart)
    converted_song['Settings'] = {
        'Charts': charts,
        'LastOpenedChartPath': charts[-1]['ChartPath'],
    }
    converted_song['FileReferences'] = [
        'base.ogg',
        'base.jpg',
        *map(lambda x: x.name, background_paths),
        *map(lambda x: x['ChartPath'], charts),
    ]
    converted_songs.append(converted_song)
    if song['set'] not in level_identifiers:
        level_identifiers[song['set']] = []
    level_identifiers[song['set']].append(new_id)
    i += 1

    if has_controller_charts:
        converted_song_alt: dict = deepcopy(converted_song)
        alt_new_id: str = f"{song['set']}.{song['id']}.alt"
        song_root_path = final_path / 'Level' / alt_new_id
        song_root_path.mkdir(parents=True, exist_ok=True)
        copy_audio(original_id, song_root_path)
        copy_jacket(original_id, song_root_path)
        converted_song_alt['_id'] = i
        converted_song_alt['Identifier'] = alt_new_id

        alt_charts: list[dict] = []
        for diff in song['difficulties']:
            if 'has_controller_alt_chart' in diff and diff['has_controller_alt_chart']:
                chart, _, _ = convert_chart(
                    diff,
                    song,
                    original_id,
                    song_root_path,
                    True
                )
                alt_charts.append(chart)
        converted_song_alt['Settings'] = {
            'Charts': alt_charts,
            'LastOpenedChartPath': alt_charts[-1]['ChartPath'],
        }
        converted_song['FileReferences'] = [
            'base.ogg',
            'base.jpg',
            *map(lambda x: x.name, background_paths),
            *map(lambda x: x['ChartPath'], alt_charts),
        ]
        level_identifiers[song['set']].append(alt_new_id)
        converted_songs.append(converted_song_alt)
        i += 1

msg.ask('Converting packs...')

# Convert packs
pack_count = litedb.pack_count()
pack_list_path = extracted_romfs_path / 'not_audio_or_images' / 'songs' / 'packlist'
pack_list: dict = json.load(open(pack_list_path, 'r'))
pack_cover_root_path = extracted_romfs_path / 'packs' / 'songs' / 'pack'
singles_cover_path = extracted_romfs_path / 'not_large_png' / 'layouts' / 'songselect' / 'folder_singles.png'
i: int = pack_count + 1

for pack in pack_list['packs']:
    msg.msg2(f'Converting pack {pack["id"]}...')
    new_id: str = pack['pack_parent'] if 'pack_parent' in pack else pack['id']
    pack_root_path = final_path / 'Pack' / new_id
    pack_root_path.mkdir(parents=True, exist_ok=True)
    pack_cover_path = pack_cover_root_path / f"select_{new_id}.png"
    if new_id == 'single':  # Copy cover (Memory Archive)
        pack_cover_path = singles_cover_path
    else:
        shutil.copyfile(  # Copy cover (Pack)
            pack_cover_path,
            pack_root_path / pack_cover_path.name
        )
    converted_pack: dict = {
        '_id': i,
        'Type': 'Pack',
        'PackName': pack['name_localized']['en'],
        'ImagePath': pack_cover_path.name,
        'LevelIdentifiers': level_identifiers[pack['id']],
        'Identifier': new_id,
        'Version': 0,
        'FileReferences': [pack_cover_path.name],
        'AddedDate': f"d{int(time())}",
        "IsDefaultAsset": True,
    }
    converted_packs.append(converted_pack)
    i += 1

msg.ask('Moving files...')

# exit(0)

# Move files
storage_root_path = final_path / 'storage'
storage_root_path.mkdir(parents=True, exist_ok=True)

for type_name in ['Level', 'Pack']:
    for file in (final_path / type_name).glob('**/*'):
        if file.is_file():
            file_real_path: str = file.relative_to(final_path).as_posix()
            file_hash: str = sha1(open(file, 'rb').read()).hexdigest()
            file_hash_path = storage_root_path / f"{file_hash}{file.suffix}"
            file_hash_path_optimized = storage_root_path / file_hash[0] / file_hash[1] / f"{file_hash}{file.suffix}"
            file_hash_path_optimized.parent.mkdir(parents=True, exist_ok=True)
            if not file_hash_path_optimized.exists():
                file.rename(file_hash_path_optimized)
            converted_files.append({
                '_id': file_real_path,
                'RealPath': file_hash_path.name,
                'CorrectHashPath': file_hash_path.name,
            })
    shutil.rmtree(final_path / type_name)

msg.ask("Updating database...")

# Update database
msg.msg('Inserting songs...')
for song in converted_songs:
    litedb.subcommand(
        'AddLevel',
        re.sub(r'"(d\d+)"', r'\1', json.dumps(song))
    )
msg.msg('Inserting packs...')
for pack in converted_packs:
    litedb.subcommand(
        'AddPack',
        re.sub(r'"(d\d+)"', r'\1', json.dumps(pack))
    )
msg.msg('Inserting files...')
for file in converted_files:
    litedb.subcommand(
        'AddFile',
        json.dumps(file)
    )

msg.ask('Done!')
