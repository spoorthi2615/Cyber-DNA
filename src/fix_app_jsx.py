import os

def main():
    file_path = 'web_app/src/App.jsx'
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace the specific raw '>' in JSX text blocks with '&gt;'
    replacements = [
        ('$BSI > 0.85$', '$BSI &gt; 0.85$'),
        ('BSI > 0.85 is too permissive', 'BSI &gt; 0.85 is too permissive'),
        ('where BSI > 0.99 for', 'where BSI &gt; 0.99 for'),
        ('BSI > 0.99 for different', 'BSI &gt; 0.99 for different'),
        ('($>0.95$)', '(&gt; 0.95)'),
        ('($>0.95)', '(&gt; 0.95)'),
        ('BSI > 0.99', 'BSI &gt; 0.99'),
        ('BSI > 0.85', 'BSI &gt; 0.85'),
        ('BSI > 1.0', 'BSI &gt; 1.0')
    ]
    
    modified = content
    for target, replacement in replacements:
        modified = modified.replace(target, replacement)
        
    if modified != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified)
        print("Successfully replaced raw '>' with '&gt;' in App.jsx")
    else:
        print("No replacements made. App.jsx might already be clean or target strings didn't match.")

if __name__ == '__main__':
    main()
