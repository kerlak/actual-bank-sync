#!/usr/bin/env python3
"""
Genera iconos PNG para la PWA desde un color de fondo y texto.
No requiere dependencias externas complejas.
"""

import base64
import os

# Icono PNG simple de 192x192 (un cuadrado con gradiente)
# Generado programaticamente como PNG valido

def create_simple_png(size, filename):
    """Crea un PNG simple con un diseno de presupuesto."""

    # PNG header
    import struct
    import zlib

    def png_chunk(chunk_type, data):
        chunk_len = struct.pack('>I', len(data))
        chunk_crc = struct.pack('>I', zlib.crc32(chunk_type + data) & 0xffffffff)
        return chunk_len + chunk_type + data + chunk_crc

    # PNG signature
    signature = b'\x89PNG\r\n\x1a\n'

    # IHDR chunk
    ihdr_data = struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)
    ihdr = png_chunk(b'IHDR', ihdr_data)

    # Generate image data (simple gradient with bars)
    raw_data = []

    for y in range(size):
        raw_data.append(0)  # Filter byte
        for x in range(size):
            # Background color (dark blue)
            r, g, b = 26, 26, 46  # #1a1a2e

            # Draw progress bars
            bar_height = size // 10
            bar_margin = size // 20
            bar_start = size // 6

            # Bar 1 (green) - 70% progress
            bar1_y = bar_start
            if bar1_y <= y < bar1_y + bar_height:
                bar_left = bar_margin
                bar_right = size - bar_margin
                bar_progress = int((bar_right - bar_left) * 0.7) + bar_left
                if bar_left <= x < bar_right:
                    if x < bar_progress:
                        r, g, b = 74, 222, 128  # Green
                    else:
                        r, g, b = 55, 65, 81  # Gray

            # Bar 2 (yellow) - 90% progress
            bar2_y = bar_start + bar_height + bar_margin
            if bar2_y <= y < bar2_y + bar_height:
                bar_left = bar_margin
                bar_right = size - bar_margin
                bar_progress = int((bar_right - bar_left) * 0.9) + bar_left
                if bar_left <= x < bar_right:
                    if x < bar_progress:
                        r, g, b = 251, 191, 36  # Yellow
                    else:
                        r, g, b = 55, 65, 81  # Gray

            # Bar 3 (red) - 110% progress (overspent)
            bar3_y = bar_start + 2 * (bar_height + bar_margin)
            if bar3_y <= y < bar3_y + bar_height:
                bar_left = bar_margin
                bar_right = size - bar_margin
                if bar_left <= x < bar_right:
                    r, g, b = 239, 68, 68  # Red

            # Dollar sign area
            dollar_y = size - size // 3
            dollar_size = size // 4
            center_x = size // 2

            if dollar_y <= y < dollar_y + dollar_size:
                # Simple $ representation
                rel_y = y - dollar_y
                rel_x = x - (center_x - dollar_size // 2)
                if 0 <= rel_x < dollar_size:
                    # Draw a simplified $
                    if rel_y < dollar_size // 5:  # Top bar
                        if dollar_size // 4 <= rel_x < 3 * dollar_size // 4:
                            r, g, b = 233, 69, 96  # Accent
                    elif rel_y >= 4 * dollar_size // 5:  # Bottom bar
                        if dollar_size // 4 <= rel_x < 3 * dollar_size // 4:
                            r, g, b = 233, 69, 96
                    elif dollar_size // 3 <= rel_x < 2 * dollar_size // 3:  # Vertical
                        r, g, b = 233, 69, 96

            raw_data.extend([r, g, b])

    raw_bytes = bytes(raw_data)
    compressed = zlib.compress(raw_bytes)
    idat = png_chunk(b'IDAT', compressed)

    # IEND chunk
    iend = png_chunk(b'IEND', b'')

    # Write PNG
    with open(filename, 'wb') as f:
        f.write(signature + ihdr + idat + iend)

    print(f"Created {filename} ({size}x{size})")

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))

    create_simple_png(192, os.path.join(script_dir, 'icon-192.png'))
    create_simple_png(512, os.path.join(script_dir, 'icon-512.png'))

    print("\nIconos generados. Puedes reemplazarlos con iconos personalizados.")
