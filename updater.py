import os
import shutil

import FreeSimpleGUI as sg

"""
Steps to update Factorio server:
1. Copy everything from existing server into a new folder except /data and /bin
2. Copy /data and /bin folder from local factorio game directory
3. Edit /config.path.cfg to have proper path to new /config folder
4. Edit /config/config.ini, read data should be new /data path, write should be server master dir path
5. Edit start.bat file to have new /server-settings.json path
"""

WIN_WIDTH = 50

def clone_directory(source_dir: str, dest_dir: str, exclusions=(), whitelist=False) -> bool: # False whitelist = blacklist
    if not os.path.exists(source_dir):
        return False  # Failure: Source directory does not exist

    os.makedirs(dest_dir, exist_ok=True)

    if whitelist:
        for item in exclusions:
            if not os.path.exists(os.path.join(source_dir, item)):
                return False # Failure: Whitelisted paths do not exist

    for item in os.listdir(source_dir):
        if not whitelist and item in exclusions: # Blacklist ignores exclusions
            continue

        source_path = os.path.join(source_dir, item)
        # print(f'Cloning {source_path}')

        if whitelist and item not in exclusions: # Whitelist only copies exclusions
            continue

        dest_path = os.path.join(dest_dir, item)

        if os.path.isfile(source_path):
            shutil.copy2(source_path, dest_path)

        elif os.path.isdir(source_path):
            shutil.copytree(source_path, dest_path, dirs_exist_ok=True)

    return True  # Success



def replace_after_prefix_file(file_path: str, new_value: str, prefix: str) -> bool:
    new_line = prefix + new_value + '\n'
    all_lines = []

    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.startswith(prefix):
                    all_lines.append(new_line)
                else:
                    all_lines.append(line)

        with open(file_path, 'w') as f:
            f.writelines(all_lines)

        return True # Success

    except FileNotFoundError:
        return False # Failure


def replace_substring_file(file_path: str, substring: str, replacement: str) -> bool:
    all_lines = []

    try:
        with open(file_path, 'r') as f:
            for line in f:
                if substring in line:
                    new_line = line.replace(substring, replacement)
                    all_lines.append(new_line)
                else:
                    all_lines.append(line)

        with open(file_path, 'w') as f:
            f.writelines(all_lines)

        return True # Success

    except FileNotFoundError:
        return False # Failure


if __name__ == '__main__':
    sg.theme('DarkAmber')

    input_rows = [  [sg.Text('Factorio Directory: '), sg.Input(key='-DIR_GAME-', enable_events=True), sg.FolderBrowse(target='-DIR_GAME-')],
                    [sg.Text('Server Directory: '), sg.Input(key='-DIR_SERVER-', enable_events=True), sg.FolderBrowse(target='-DIR_SERVER-')],
                    [sg.Text('Output Directory: '), sg.Input(key='-DIR_OUT-', enable_events=True), sg.FolderBrowse(target='-DIR_OUT-')]]

    # Define the window's contents
    layout = [  [sg.Text('Factorio Headless Server Updater', size=(WIN_WIDTH, 1))],
                [sg.Column(input_rows, key='-FILE_INPUTS-')],
                [sg.Text('', key='-UPDATE_PROGRESS-', visible=False)],
                [sg.Text('', key='-UPDATE_CONCLUSION-', visible=False)],
                [sg.Button('Start', key='-START_BUTTON-', visible=False), sg.Button('Quit', key='-QUIT_BUTTON-')],]

    # Create the window
    window = sg.Window('Factorio Server Updater', layout)

    # Display and interact with the Window using an Event Loop
    while True:
        event, values = window.read()
        if event == sg.WINDOW_CLOSED or event == '-QUIT_BUTTON-':
            break

        if event == '-DIR_GAME-' or event == '-DIR_SERVER-' or event == '-DIR_OUT-':
            game_directory = values['-DIR_GAME-']
            server_directory = values['-DIR_SERVER-']
            output_directory = values['-DIR_OUT-']

            if game_directory and server_directory and output_directory:
                window['-START_BUTTON-'].update(visible=True)

        if event == '-START_BUTTON-':
            # Normalize paths
            game_directory = os.path.normpath(game_directory)
            server_directory = os.path.normpath(server_directory)
            output_directory = os.path.normpath(output_directory)

            # Hide all fields and buttons
            window['-FILE_INPUTS-'].update(visible=False)
            window['-START_BUTTON-'].update(visible=False)
            window['-QUIT_BUTTON-'].update(visible=False)
            status_text = window['-UPDATE_PROGRESS-']

            # Show update progress
            status_text.update(visible=True)

            config_path = os.path.join(output_directory, r'config')
            read_data = os.path.join(output_directory, r'data')
            write_data = output_directory
            start_path = os.path.join(output_directory, r'bin\x64\start.bat')

            update_status = 'Done'
            update_conclusion = f'Updated Factorio server located in directory: {output_directory}'

            try:
                # Copy only bin and data from game files
                status_text.update('Cloning game files from local Factorio install...')
                window.refresh()
                if not clone_directory(game_directory, output_directory, exclusions=('bin', 'data'), whitelist=True):
                    raise FileNotFoundError('Factorio game path does not exist or is missing Factorio game files')

                # Clone all files except bin and data
                status_text.update('Cloning old server data...')
                window.refresh()
                if not clone_directory(server_directory, output_directory, exclusions=('bin', 'data'), whitelist=False):
                    raise FileNotFoundError('Original server path does not exist')

                # Update .cfg config
                status_text.update('Updating configuration paths...')
                window.refresh()
                if not replace_after_prefix_file(os.path.join(output_directory, r'config-path.cfg'), config_path, prefix='config-path='):
                    raise FileNotFoundError('Config-path.cfg file not detected in original server path')

                # Update read and write values in config.ini
                if not (replace_after_prefix_file(os.path.join(output_directory, r'config\config.ini'), read_data, prefix='read-data=')
                    and replace_after_prefix_file(os.path.join(output_directory, r'config\config.ini'), write_data, prefix='write-data=')):
                    raise FileNotFoundError('Config-config.ini file not detected in original server path')

                # Copy start.bat from old server
                status_text.update('Updating Windows batch file...')
                window.refresh()
                try:
                    shutil.copy2(os.path.join(server_directory, r'bin\x64\start.bat'), start_path)
                except FileNotFoundError:
                    raise FileNotFoundError('Start.bat file does not exist in original server path')

                # Replace server-settings path in bat
                old_settings_path = os.path.join(server_directory, 'server-settings.json')
                new_settings_path = os.path.join(output_directory, 'server-settings.json')

                replace_substring_file(start_path, old_settings_path, new_settings_path)

            except FileNotFoundError as error:
                update_status = 'Failed'
                update_conclusion = error

            # Conclude update
            status_text.update(update_status)
            window['-UPDATE_CONCLUSION-'].update(visible=True)
            window['-UPDATE_CONCLUSION-'].update(update_conclusion)
            window['-QUIT_BUTTON-'].update(visible=True)
            window.refresh()


    # Finish up by removing from the screen
    window.close()
