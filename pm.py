import argparse
from generator import generate_password
from vault import get_pin, vault_exists, init_vault, load_vault, save_vault, reset_pin


def cmd_init():
    pin = get_pin("Set PIN: ")
    confirm = get_pin("Confirm PIN: ")
    if pin != confirm:
        print("PINs do not match.")
        return
    if len(pin) < 4:
        print("PIN must be at least 4 characters long")
        return
    init_vault(pin)

def cmd_add(service: str):
    pin = get_pin()
    vault = load_vault(pin)

    username = input("Username: ")
    password = get_pin("Password (leave blank to generate): ")

    if not password:
        password = generate_password()
        print(f"Generated: {password}")

    entry = {'username': username, 'password': password}

    if service in vault:
        # check if username already exists under the service
        existing_users = [e['username'] for e in vault[service]]
        if username in existing_users:
            confirm = input(f"'{service}' already exits. Overwrite? [y/N]: ")
            if confirm.lower() != 'y':
                return
            # replace the existing entry for this username
            vault[service] = [e for e in vault[service] if e[username] != username]

        vault[service].append(entry)
    else:
        vault[service] = [entry]
  
    save_vault(pin, vault)
    print(f"Saved '{service}'.")


def cmd_get(service):
    pin = get_pin()
    vault = load_vault(pin)


    if service not in vault:
        print("Service not found.")
        return

    entries = vault[service]
    print(f"\n{service} ({len(entries)} credential(s)):")
    for i, entry in enumerate (entries, 1):
        print(f"\n [{i}] Username: {entry['username']}")
        print(f"     Password: {entry['password']}")


def cmd_list():
    pin = get_pin()
    vault = load_vault(pin)

    if not vault:
        print("Vault is empty.")
        return

    for service in vault.keys():
        print(f" · {service}")


def cmd_generate(service, length):
    password = generate_password(length)
    print(f"Generated: {password}")

    if service:
        pin = get_pin()
        vault = load_vault(pin)
        username = input("Username to save with: ")
        entry = {'username': username, 'password':password}

        if service in vault:
            existing_users = [e['username'] for e in vault[service]]
            if username in existing_users:
                confirm = input(f"'{username}' already exists under '{service}'. Overwrite? [y/N] ")
                if confirm.lower() != 'y':
                    return
                vault[service] = [e for e in vault[service] if e['username'] != username]
            vault[service].append(entry)
        else:
            vault[service] = [entry]

        save_vault(pin, vault)
        print(f"Saved under '{service}'.")


def cmd_delete(service: str):
    pin = get_pin()
    vault = load_vault(pin)

    if service not in vault:
        print(f"No entry for '{service}'.")
        return

    entries = vault[service]

    if len(entries) == 1:
        # only one credential - delete the whole service
        confirm = input(f"Delete '{service}'? [y/N]: ")
        if confirm.lower() == 'y':
            del vault[service]
            save_vault(pin, vault)
            print(f"Deleted '{service}'.")
    else:
        # multiple credentials - ask which one to delete
        print(f"\n{service} has {len(entries)} credential(s):")
        for i, entry in enumerate(entries, 1):
            print(f"  [{i}] {entry['username']}")

        choice = input(f"\nEnter number to delete (or 'all' to delete service): ")

        if choice.lower() == 'all':
            confirm = input(f"Delete all credentials for '{service}'? [y/N]: ")
            if confirm.lower() == 'y':
                del vault[service]
                save_vault(pin, vault)
                print(f"Deleted '{service}'.")
        elif choice.isdigit() and 1 <= int(choice) <= len(entries):
            target = entries[int(choice) - 1]
            confirm = input(f"Delete '{target['username']}' under '{service}'? [y/N]: ")
            if confirm.lower() == 'y':
                vault[service].pop(int(choice) - 1)
                save_vault(pin, vault)
                print(f"Deleted '{target['username']}' from '{service}'.")
        else:
            print("Invalid choice.")


def cmd_resetpin():
    recovery_key = get_pin("Recovery key: ")
    confirm_key = get_pin("Confirm key: ")
    if recovery_key != confirm_key:
        print("keys do not match.")
        return
    new_pin = get_pin("New PIN: ")
    confirm_pin = get_pin("Confirm: ")
    if new_pin != confirm_pin:
        print("PINs do not match.")
        return
    reset_pin(recovery_key, new_pin)
    



def main():
    banner = r"""
  ██████╗   ███╗   ███╗
  ██╔══██╗  ████╗ ████║
  ██████╔╝  ██╔████╔██║
  ██╔═══╝   ██║╚██╔╝██║
  ██║       ██║ ╚═╝ ██║
  ╚═╝       ╚═╝     ╚═╝
  
  Password Manager - v1.0.0
"""


    
    parser = argparse.ArgumentParser(
        prog='pm', description='A simple CLI password manager', epilog='Run `pm <command> --help` for detailed usage of each command.'
    )
    sub = parser.add_subparsers(dest='command', metavar='command')

    #Subcommands
    sub.add_parser('init', help='Create a new vault')

    p_add = sub.add_parser('add', help='Add a new entry')
    p_add.add_argument('service', help='Service name (e.g. github)')

    p_get = sub.add_parser('get', help='Retrieve an entry')
    p_get.add_argument('service')

    sub.add_parser('ls', help='List all saved services')

    p_gen = sub.add_parser('gen', help='Generate and optionally save a password')
    p_gen.add_argument('service', nargs='?', help='Service to save it under(optional)')
    p_gen.add_argument('--length', type=int, default=16, help='Length of generated password (default: 16)')

    p_del = sub.add_parser('del', help='Delete an entry')
    p_del.add_argument('service')

    sub.add_parser('rpin', help='Reset PIN using recovery key')

    args = parser.parse_args()

    if not args.command:
        print(banner)
        parser.print_help()
        return


    #Dispatch
    if args.command == 'init': cmd_init()
    elif args.command == 'add': cmd_add(args.service)
    elif args.command == 'get': cmd_get(args.service)
    elif args.command == 'ls': cmd_list()
    elif args.command == 'gen': cmd_generate(args.service, args.length)
    elif args.command == 'del': cmd_delete(args.service)
    elif args.command == 'rpin': cmd_resetpin()

if __name__ == '__main__':
    main()
