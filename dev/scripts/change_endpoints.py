import re
from pathlib import Path

DRY_RUN = False

p = Path('.')

pattern = re.compile(
    r'''(await\s+)?(\w+)\.post\(endpoints\.api\.rooms\.room_create(?:\.rstrip\('/'\))?,\s*json=\{"room_name":\s*(.*?),\s*"room_type":\s*(.*?)\}\)'''
)

total = 0

for test in p.rglob('*.py'):
    if test.name == "conftest.py": continue
    try:
        content = test.read_text(encoding='utf-8')
    except (UnicodeDecodeError, PermissionError) as e:
        print(f"Could not read {test}: {e}")
        continue

    def replace(match):
        isasync = match.group(1)
        client_name = match.group(2)
        room_name = match.group(3)
        room_type = match.group(4)

        return f'create_room_sync({client_name}, endpoints, {room_name}, {room_type})' if isasync is None else f'await create_room_async({client_name}, endpoints, {room_name}, {room_type})'

    new_content, count = pattern.subn(replace, content)

    if count == 0:
        continue
    
    total += count

    print(f'{test}: {count} replacement(s)')

    if DRY_RUN:
        print('--- AFTER ---')
        print(new_content)
    else:
        test.write_text(new_content, encoding='utf-8')

print(total, "replacement(s).")