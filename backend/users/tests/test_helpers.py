from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.files.storage import default_storage
import os

Image.MAX_IMAGE_PIXELS = None

def create_test_image(size_in_mb):

    width = height = 5000

    img_io = BytesIO()
    image = Image.new("RGB", (width, height), color="red")
    image.save(img_io, format="JPEG", quality=30)

    target_size = size_in_mb * 1024 * 1024
    while img_io.tell() < target_size:
        width += 500
        height += 500

        img_io = BytesIO()
        image = Image.new("RGB", (width, height), color="red")
        image.save(img_io, format="JPEG", quality=30)

    img_io.seek(0)

    return SimpleUploadedFile(
        "test_image.jpeg", content=img_io.read(), content_type="image/jpeg"
    )


def delete_test_images(test_images):

    for image_name in test_images:
        profile_pictures_dir = os.path.join(settings.MEDIA_ROOT, 'profile_pictures')

        for dirpath, dirnames, filenames in os.walk(profile_pictures_dir):
            for filename in filenames:
                if image_name == filename:
                    image_path = os.path.join(dirpath, filename)
                    if default_storage.exists(image_path):
                        default_storage.delete(image_path)
