import os

# Annotations for special files
ANNOTATIONS = {
    "New Text Document": "(Likely Junk)",
    "login.html": "(Note: Had reading error due to encoding)",
    "register.html": "(Note: Had reading error due to encoding)",
    "codeToNotepad.py": "(Scanning Script)",
    "code_files.txt": "(Output of Scanning Script)",
    "app.py": "(Main Flask Application - Note: Had reading error due to encoding)"
}

# Exclude exactly these files or folders by name
EXCLUDED_NAMES = {'.idea'}
# Exclude files with these extensions (binary + pyc)
EXCLUDED_EXTENSIONS = {
    '.pyc', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
    '.ico', '.pdf', '.exe', '.dll', '.so', '.zip', '.tar', '.gz', '.7z', '.rar'
}


def annotate(filename):
    """Add annotation based on known patterns."""
    for key, note in ANNOTATIONS.items():
        if key in filename:
            return f"{filename} {note}"
    return filename


def generate_tree(path, prefix=""):
    """Generate directory tree lines with arrow symbols."""
    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        return []  # Skip folders we can't open

    # Exclude hidden files/folders starting with '.', also exclude '.idea' folder and excluded file extensions
    entries = [
        e for e in entries
        if not e.startswith('.') and e not in EXCLUDED_NAMES and not e.endswith(tuple(EXCLUDED_EXTENSIONS))
    ]

    tree_lines = []

    for index, entry in enumerate(entries):
        full_path = os.path.join(path, entry)
        is_last = index == len(entries) - 1
        connector = "└── " if is_last else "├── "

        display_name = annotate(entry)
        tree_lines.append(f"{prefix}{connector}{display_name}")

        if os.path.isdir(full_path):
            new_prefix = prefix + ("    " if is_last else "│   ")
            tree_lines.extend(generate_tree(full_path, new_prefix))

    return tree_lines


def write_code_to_notepad(directory, output_file="code_files.txt"):
    with open(output_file, "w", encoding="utf-8") as f:
        # Write directory tree
        f.write(f"Project Root ({directory})\n")
        f.write("│\n")
        tree = generate_tree(directory)
        f.write("\n".join(tree))
        f.write("\n\n" + "=" * 60 + "\n")
        f.write("File Contents\n")
        f.write("=" * 60 + "\n\n")

        # Walk directory excluding unwanted folders and binary files
        for root, dirs, files in os.walk(directory):
            # Remove excluded folders (like '.idea') so walk skips them completely
            dirs[:] = [d for d in dirs if d not in EXCLUDED_NAMES and not d.startswith('.')]

            for file in files:
                # Skip excluded files (.pyc, images, binaries, hidden)
                if (file in EXCLUDED_NAMES or
                        file.startswith('.') or
                        file.endswith(tuple(EXCLUDED_EXTENSIONS))):
                    continue

                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    f.write(f"\n--- File: {file_path} ---\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as code_file:
                            content = code_file.read()
                            f.write(content + "\n")
                    except Exception as e:
                        f.write(f"Could not read {file_path}: {e}\n")

    print(f"✅ Directory tree and files written to '{output_file}'.")


# Set your project directory here
project_path = r"C:\Users\Ananda M\PycharmProjects\FCars version\working payment gateway FCars\FCars"
write_code_to_notepad(project_path)
