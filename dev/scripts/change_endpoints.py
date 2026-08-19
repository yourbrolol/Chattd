import re
from pathlib import Path

DRY_RUN = True

p = Path('.')

pattern = re.compile(
    r'''await\s+(\w+)\.post\(endpoints\.api\.rooms\.room_create(?:\.rstrip\('/'\))?,\s*json=\{"room_name":\s*(.*?),\s*"room_type":\s*(.*?)\}\)'''
)

total = 0

for test in p.rglob('*.py'):
    try:
        content = test.read_text(encoding='utf-8')
    except (UnicodeDecodeError, PermissionError) as e:
        print(f"Could not read {test}: {e}")
        continue

    def replace(match):
        client_name = match.group(1)
        room_name = match.group(2)
        room_type = match.group(3)

        return f'create_room({client_name}, endpoints, {room_name}, {room_type})'

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