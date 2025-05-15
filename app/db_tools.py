from app.models import Share, Image, User
from app import db

SEPARATOR = '-'

def get_image_filename_from_ids(author_id, share_id):
    file_extension = "png"
    return f"{author_id}{SEPARATOR}{share_id}.{file_extension}"

def get_ids_from_filename(filename):
    minus_extension = filename.split('.')[0]
    ids = minus_extension.split(SEPARATOR)
    if len(ids) != 2:
        return None
    author_id, share_id = ids
    return (int(author_id), int(share_id))

def can_user_access_image(user_id, image_id):
    # Check if the user is the author of the image
    image = Image.query.filter_by(image_id=image_id).first()
    if image and image.author_id == user_id:
        return True

    # Otherwise, check if the image is shared with the user
    share = Share.query.filter_by(
        user_id_shared_to=user_id,
        share_type="image",
        trade_or_image_id=image_id
    ).first()
    return share is not None

def generate_feed_items(user_id):
    shares = Share.query.filter_by(user_id_shared_to=user_id).all()
    feed_items = []
    for share in shares:
        item = {
            "type": share.share_type,
        }

        author = None
        image_filename = None

        if share.share_type == "image":
            image = Image.query.filter_by(image_id=share.trade_or_image_id).first()
            if image:
                author = User.query.filter_by(user_id=image.author_id).first()
                image_filename = get_image_filename_from_ids(image.author_id, image.image_id)
                item["image"] = image_filename

        elif share.share_type == "post":
            # For posts, you may want to fetch the Trade and its author
            # This is optional and depends on your requirements
            pass

        if author:
            item["author"] = author.username
        else:
            item["author"] = None

        feed_items.append(item)
    return feed_items