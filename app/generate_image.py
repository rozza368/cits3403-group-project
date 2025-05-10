from PIL import Image, ImageDraw, ImageFont

def create_image(amount, date_range, output_path="output_image.png"):
    # Create a blank 4:3 image (e.g., 800x600)
    width, height = 800, 600
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    is_profit = amount > 0
    pnl_text = "Profit" if is_profit else "Loss"

    # Draw a placeholder square for the profile picture
    profile_size = 200
    profile_pic_padding = 30
    draw.rectangle(
        [profile_pic_padding, profile_pic_padding,
         profile_pic_padding + profile_size, profile_pic_padding + profile_size],
        fill="gray")

    # Load fonts (adjust paths or use default if custom fonts are unavailable)
    try:
        bold_font = ImageFont.truetype("fonts/arialbd.ttf", 72)  # Bold font
        large_bold_font = ImageFont.truetype("fonts/arialbd.ttf", 96)  # Larger bold font
        regular_font = ImageFont.truetype("fonts/arial.ttf", 48)  # Regular font
    except IOError:
        bold_font = large_bold_font = regular_font = ImageFont.load_default()

    # Draw "profit" or "loss" text
    text_x = profile_pic_padding * 2 + profile_size
    text_y = profile_pic_padding
    draw.text((text_x, text_y), pnl_text, fill="black", font=bold_font)

    # Draw the amount
    text_color = "green" if is_profit else "red"
    text_y += 72  # Adjust vertical spacing
    draw.text((text_x, text_y), f"{'+' if is_profit else '-'}${amount}", fill=text_color, font=large_bold_font)

    # Draw the date range
    text_y += 96 + profile_pic_padding  # Adjust vertical spacing
    draw.text((text_x, text_y), date_range, fill="black", font=regular_font)

    # Save the image
    image.save(output_path)

if __name__ == "__main__":
    create_image(1000000, "May 2 - May 7")