import random

def generate_rc_file(output_path, product_name="Google Chrome", company="Google LLC"):
    """
    Generates a Windows Resource (.rc) file to spoof file metadata.
    This makes the EXE look like a legitimate corporate application.
    """
    version_id = f"{random.randint(10, 99)}.{random.randint(0, 9)}.{random.randint(1000, 9999)}.{random.randint(0, 99)}"
    
    rc_content = f"""
1 VERSIONINFO
FILEVERSION {version_id.replace('.', ',')}
PRODUCTVERSION {version_id.replace('.', ',')}
FILEFLAGSMASK 0x3fL
#ifdef _DEBUG
 FILEFLAGS 0x1L
#else
 FILEFLAGS 0x0L
#endif
 FILEOS 0x40004L
 FILETYPE 0x1L
 FILESUBTYPE 0x0L
BEGIN
    BLOCK "StringFileInfo"
    BEGIN
        BLOCK "040904b0"
        BEGIN
            VALUE "CompanyName", "{company}"
            VALUE "FileDescription", "{product_name} Installer"
            VALUE "FileVersion", "{version_id}"
            VALUE "InternalName", "{product_name.lower().replace(' ', '_')}.exe"
            VALUE "LegalCopyright", "Copyright (C) {random.randint(2020, 2024)} {company}. All rights reserved."
            VALUE "OriginalFilename", "{product_name.lower().replace(' ', '_')}.exe"
            VALUE "ProductName", "{product_name}"
            VALUE "ProductVersion", "{version_id}"
        END
    END
    BLOCK "VarFileInfo"
    BEGIN
        VALUE "Translation", 0x409, 1200
    END
END
"""
    with open(output_path, "w") as f:
        f.write(rc_content)
    return output_path
