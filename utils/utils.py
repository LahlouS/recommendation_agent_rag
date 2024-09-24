
def write_to_file(filename, content):
    try:
        with open(filename, 'w') as file:
            file.write(content)
        print(f"Content written to {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")