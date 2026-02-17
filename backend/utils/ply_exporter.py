"""
PLY (Polygon File Format) Exporter
Converts point cloud data to standard PLY format
"""

from typing import List, Dict
import struct


def export_to_ply(points: List[Dict[str, float]], filename: str = None) -> str:
    """
    Export point cloud data to PLY format
    
    Args:
        points: List of point dictionaries with keys: x, y, z, r, g, b
        filename: Optional filename to write to disk
        
    Returns:
        PLY file content as string
    """
    if not points:
        raise ValueError("No points provided for export")
    
    # Build PLY header
    header = f"""ply
format ascii 1.0
comment AetherScan Point Cloud Export
element vertex {len(points)}
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
"""
    
    # Build vertex data
    vertices = []
    for point in points:
        x = point.get('x', 0.0)
        y = point.get('y', 0.0)
        z = point.get('z', 0.0)
        r = int(point.get('r', 128))
        g = int(point.get('g', 128))
        b = int(point.get('b', 128))
        
        # Clamp RGB values to 0-255
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        vertices.append(f"{x} {y} {z} {r} {g} {b}")
    
    ply_content = header + "\n".join(vertices)
    
    # Optionally write to file
    if filename:
        with open(filename, 'w') as f:
            f.write(ply_content)
    
    return ply_content


def export_to_ply_binary(points: List[Dict[str, float]], filename: str) -> bytes:
    """
    Export point cloud data to binary PLY format (more efficient for large datasets)
    
    Args:
        points: List of point dictionaries with keys: x, y, z, r, g, b
        filename: Filename to write to disk
        
    Returns:
        Binary PLY file content
    """
    if not points:
        raise ValueError("No points provided for export")
    
    # Build PLY header
    header = f"""ply
format binary_little_endian 1.0
comment AetherScan Point Cloud Export
element vertex {len(points)}
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
"""
    
    # Convert header to bytes
    header_bytes = header.encode('ascii')
    
    # Build binary vertex data
    vertex_data = bytearray()
    for point in points:
        x = float(point.get('x', 0.0))
        y = float(point.get('y', 0.0))
        z = float(point.get('z', 0.0))
        r = int(point.get('r', 128))
        g = int(point.get('g', 128))
        b = int(point.get('b', 128))
        
        # Clamp RGB values
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        # Pack as: 3 floats (x,y,z) + 3 unsigned chars (r,g,b)
        vertex_data += struct.pack('<fffBBB', x, y, z, r, g, b)
    
    ply_content = header_bytes + bytes(vertex_data)
    
    # Write to file
    with open(filename, 'wb') as f:
        f.write(ply_content)
    
    return ply_content
