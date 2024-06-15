#!/usr/bin/env python
# pbpaste.py
from PIL import Image
import AppKit
import pyperclip
import sys
import ctypes
import os
import stat

# Load the libc library
libc = ctypes.CDLL("/usr/lib/libSystem.dylib")
# Define the struct stat
class Stat(ctypes.Structure):
    _fields_ = [
            ("st_dev", ctypes.c_int32),
            ("st_mode", ctypes.c_uint16),
            ("st_nlink", ctypes.c_uint16),
            ("st_ino", ctypes.c_uint64),
            ("st_uid", ctypes.c_uint32),
            ("st_gid", ctypes.c_uint32),
            ("st_rdev", ctypes.c_int32),
            ("st_atimespec", ctypes.c_uint64 * 2),
            ("st_mtimespec", ctypes.c_uint64 * 2),
            ("st_ctimespec", ctypes.c_uint64 * 2),
            ("st_birthtimespec", ctypes.c_uint64 * 2),
            ("st_size", ctypes.c_int64),
            ("st_blocks", ctypes.c_int64),
            ("st_blksize", ctypes.c_int32),
            ("st_flags", ctypes.c_uint32),
            ("st_gen", ctypes.c_uint32),
            ("st_lspare", ctypes.c_int32),
            ("st_qspare", ctypes.c_int64 * 2)
            ]
# Define the return type and argument types for fstat
libc.fstat.restype = ctypes.c_int
libc.fstat.argtypes = [ctypes.c_int, ctypes.POINTER(Stat)]

# Define the prototype for realpath
# char *realpath(const char *restrict path, char *restrict resolved_path);
libc.realpath.restype = ctypes.c_char_p
libc.realpath.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

def stdout_output_device():
    statbuf = Stat()
    result = libc.fstat(2, ctypes.byref(statbuf)) # 2 = STDOUT
    if stat.S_IFREG(statbuf.st_mode):
        #if statbuf.st_mode & 0o170000 == 0o100000:  # S_IFREG
        return 'file'
    elif stat.S_ISCHR(statbuf.st_mode):
        return 'terminal' # Technically could be a character device that isn't
    # a terminal. Check tcgetattr(2, termios
    return 'unknown' # pipe or a socket

def get_stdout_filename_extension():
    # We assume stdout_output_device() == 'file' here.
    resolved_path = ctypes.create_string_buffer(1024)
    result = libc.realpath(b"/dev/fd/1", resolved_path)
    if result:
        filename = resolved_path.value.decode()
        extension = filename[filename.rfind('.'): -1]
        import sys
        print("Resolved path:", resolved_path.value.decode(), file=sys.stderr)
        return extension
    raise Exception('doom')


def get_clipboard_content():
    pb = AppKit.NSPasteboard.generalPasteboard()
    types = pb.types()

    if AppKit.NSStringPboardType in types:
        # Handle text content
        return 'text', pb.stringForType_(AppKit.NSStringPboardType)
    elif AppKit.NSPasteboardTypeTIFF in types:
        tiff_data = pb.dataForType_(AppKit.NSPasteboardTypeTIFF)
        return 'image', tiff_data.bytes()
    return 'unknown', None

#
#        # Handle image content
#        device = stdout_output_device()
#        if device == 'file':
#            content = transform_content(get_stdout_filename_extension())

def transform_content(extension, content):
    #extension = get_stdout_filename_extension()
    extension_data = [
        (['png'], 'PNG'),
        (['jpg', 'jpeg'], 'JPEG'),
        (['gif'], 'GIF'),
        (['svg'], 'SVG'),
        (['bmp'], 'BMP'),
        (['heif'], 'HEIF'),
        (['webp'], 'WEBP'),
                    ]
    if extension:
        extension = extension.lower()
        converted = False
        for extension_name, format_name in extension_data:
            for name in extension_name:
                if extension in name:
                    tiff_image = Image.open(io.BytesIO(content))
                    output = io.BytesIO()
                    tiff_image.save(output, format=format_name)
                    return output.getvalue()
    return content

def pbpaste():
    content_type, content = get_clipboard_content()
    if content_type == 'text':
        print(content)
    elif content_type == 'image':
        device = stdout_output_device()
        if device == 'file':
            extension = get_stdout_filename_extension()
            content = transform_content(extension, conent)
            sys.stdout.buffer.write(content)
        #elif device == 'terminal':
            #os.environ['TERM']
            
        #if output is a terminal, check if it has sixel support
    else:
        print("Unsupported clipboard content")

if __name__ == "__main__":
    pbpaste()
