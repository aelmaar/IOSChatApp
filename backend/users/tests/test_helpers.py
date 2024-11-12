from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

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