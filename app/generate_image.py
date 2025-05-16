from PIL import Image, ImageDraw, ImageFont

def create_image(amount, date_range, output_path="output_image.png"):
    width, height = 800, 400
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    is_profit = amount > 0
    pnl_text = "Profit" if is_profit else "Loss"
    padding_edge = 50

    # Load fonts (adjust paths or use default if custom fonts are unavailable)
    try:
        bold_font = ImageFont.truetype("fonts/arialbd.ttf", 72)  # Bold font
        large_bold_font = ImageFont.truetype("fonts/arialbd.ttf", 96)  # Larger bold font
        regular_font = ImageFont.truetype("fonts/arial.ttf", 48)  # Regular font
    except IOError:
        bold_font = large_bold_font = regular_font = ImageFont.load_default()

    # Draw "profit" or "loss" text
    text_x = padding_edge
    text_y = padding_edge
    draw.text((text_x, text_y), pnl_text, fill="black", font=bold_font)

    # Draw the amount
    text_color = "green" if is_profit else "red"
    text_y += 84  # Adjust vertical spacing
    draw.text((text_x, text_y), f"{'+' if is_profit else '-'}${abs(amount):,}", fill=text_color, font=large_bold_font)

    # Draw the date range
    text_y = height - padding_edge - 48  # Adjust vertical spacing
    draw.text((text_x, text_y), date_range, fill="black", font=regular_font)

    # Save the image
    image.save(output_path)

if __name__ == "__main__":
    create_image(10000000, "2025-05-15 to 2025-05-16", "test-profit.png")
    create_image(-10000000, "2025-05-15 to 2025-05-16", "test-loss.png")