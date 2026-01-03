"""
Generate PWA icons from SVG or create simple PNG icons
Run: python generate_icons.py
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  Pillow not installed. Install with: pip install Pillow")

def create_icon(size, output_path):
    """Create a simple icon with gradient background"""
    # Create image with gradient-like background
    img = Image.new('RGB', (size, size), '#7c3aed')
    draw = ImageDraw.Draw(img)
    
    # Draw gradient effect (simple approximation)
    for i in range(size):
        # Gradient from #7c3aed to #a855f7
        ratio = i / size
        r = int(124 + (168 - 124) * ratio)
        g = int(58 + (85 - 58) * ratio)
        b = int(237 + (247 - 237) * ratio)
        color = (r, g, b)
        draw.line([(0, i), (size, i)], fill=color)
    
    # Add text "ES" in white
    try:
        # Try to use a nice font
        font_size = int(size * 0.4)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    text = "ES"
    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = ((size - text_width) // 2, (size - text_height) // 2 - size // 20)
    
    # Draw text with shadow for better visibility
    shadow_offset = max(2, size // 100)
    draw.text((position[0] + shadow_offset, position[1] + shadow_offset), text, fill='#000000', font=font)
    draw.text(position, text, fill='#ffffff', font=font)
    
    img.save(output_path, 'PNG', optimize=True)
    print(f"✅ Created: {output_path} ({size}x{size})")

if __name__ == "__main__":
    import os
    import subprocess
    
    if not PIL_AVAILABLE:
        print("\n📦 Installing Pillow...")
        try:
            subprocess.check_call(["pip", "install", "Pillow"])
            from PIL import Image, ImageDraw, ImageFont
        except Exception as e:
            print(f"❌ Failed to install Pillow: {e}")
            print("Please install manually: pip install Pillow")
            exit(1)
    
    # Ensure we're in the frontend/public directory
    public_dir = os.path.join(os.path.dirname(__file__), 'frontend', 'public')
    if not os.path.exists(public_dir):
        public_dir = 'frontend/public'
    if not os.path.exists(public_dir):
        public_dir = 'public'
    if not os.path.exists(public_dir):
        public_dir = '.'
    
    print(f"\n🎨 Generating PWA icons in: {public_dir}\n")
    
    # Generate required sizes
    sizes = [
        (72, 'icon-72.png'),
        (96, 'icon-96.png'),
        (128, 'icon-128.png'),
        (144, 'icon-144.png'),
        (152, 'icon-152.png'),
        (192, 'icon-192.png'),
        (384, 'icon-384.png'),
        (512, 'icon-512.png'),
    ]
    
    for size, filename in sizes:
        output_path = os.path.join(public_dir, filename)
        create_icon(size, output_path)
    
    print("\n✅ All icons generated successfully!")
    print("\n📱 Icons ready for:")
    print("   - Android home screen")
    print("   - iOS home screen")
    print("   - Windows tiles")
    print("   - PWA installation")
