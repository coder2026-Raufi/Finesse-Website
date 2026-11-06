import io
from pathlib import Path

from django import forms
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

from portfolio.models import Project

MAX_UPLOAD = 8 * 1024 * 1024  # 8 MB


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            "title_en", "description_en", "title_fa", "description_fa",
            "title_ps", "description_ps", "title_ar", "description_ar",
            "category", "year", "duration_months", "client", "image", "is_published",
        ]
        widgets = {
            "description_en": forms.Textarea(attrs={"rows": 4}),
            "title_fa": forms.TextInput(attrs={"dir": "rtl"}),
            "title_ps": forms.TextInput(attrs={"dir": "rtl"}),
            "title_ar": forms.TextInput(attrs={"dir": "rtl"}),
            "description_fa": forms.Textarea(attrs={"rows": 4, "dir": "rtl"}),
            "description_ps": forms.Textarea(attrs={"rows": 4, "dir": "rtl"}),
            "description_ar": forms.Textarea(attrs={"rows": 4, "dir": "rtl"}),
            "image": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def clean_image(self):
        img = self.cleaned_data.get("image")
        # only process a NEW upload (an existing image arrives as a FieldFile)
        if not img or not hasattr(img, "content_type"):
            return img
        if img.size > MAX_UPLOAD:
            raise forms.ValidationError("The image is larger than 8 MB. Please choose a smaller one.")
        # Re-encode: shrinks big photos (faster website), fixes rotation, and
        # removes hidden metadata such as GPS location from phone photos.
        pic = ImageOps.exif_transpose(Image.open(img))
        if pic.mode in ("RGBA", "LA", "P"):
            pic = pic.convert("RGBA")
            bg = Image.new("RGB", pic.size, "white")
            bg.paste(pic, mask=pic.split()[-1])
            pic = bg
        else:
            pic = pic.convert("RGB")
        pic.thumbnail((1600, 1600))
        buf = io.BytesIO()
        pic.save(buf, "JPEG", quality=85, optimize=True)
        return ContentFile(buf.getvalue(), name=Path(img.name).stem[:60] + ".jpg")
