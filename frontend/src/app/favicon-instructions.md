# Favicon Creation Instructions

To complete the favicon setup, you'll need to:

1. **Create favicon.ico**
   - Convert the icon.svg to a multi-resolution .ico file (16x16, 32x32, 48x48)
   - Place it at: `src/app/favicon.ico`

2. **Create PNG icons**
   - Generate from icon.svg:
     - `icon-192.png` (192x192) for Android Chrome
     - `icon-512.png` (512x512) for PWA
   - Place them in: `src/app/`

3. **Create Apple Touch Icon**
   - Generate `apple-icon.png` (180x180) from icon.svg
   - Place it at: `src/app/apple-icon.png`

4. **Create OpenGraph Image**
   - Convert `og-image.svg` to `og-image.png` (1200x630)
   - Place it at: `src/app/og-image.png`

## Online Tools for Conversion:

- SVG to ICO: https://convertio.co/svg-ico/
- SVG to PNG: https://svgtopng.com/
- Favicon Generator: https://favicon.io/

## Command Line (if you have ImageMagick):

```bash
# Convert SVG to PNG
convert -background none icon.svg -resize 192x192 icon-192.png
convert -background none icon.svg -resize 512x512 icon-512.png
convert -background none icon.svg -resize 180x180 apple-icon.png
convert -background none og-image.svg -resize 1200x630 og-image.png

# Create multi-resolution ICO
convert -background none icon.svg -resize 16x16 icon-16.png
convert -background none icon.svg -resize 32x32 icon-32.png
convert -background none icon.svg -resize 48x48 icon-48.png
convert icon-16.png icon-32.png icon-48.png favicon.ico
```

After creating these files, delete this instructions file.
