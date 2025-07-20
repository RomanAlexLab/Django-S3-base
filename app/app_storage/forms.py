# app_storage/forms.py
#
# Этот файл содержит формы загрузки публичных и приватных файлов.
# Формы включают валидацию файлов используя конфигурации из S3Data.

import logging
from django import forms
from django.core.exceptions import ValidationError
from PIL import Image
from .models import (
    PublicImage, PublicVideo, PublicFile,
    PrivateImage, PrivateVideo, PrivateFile, MediaFile
)
from app_config.s3_conf import S3Data


logger = logging.getLogger(__name__)


# =======================
# Формы публичных моделей
# =======================


class PublicImageForm(forms.ModelForm):
    """
    Форма загрузки публичных изображений.
    Валидирует: реаальность изображения и максимальный размер.
    """
    class Meta:
        model = PublicImage
        fields = "__all__"

    # Валидация файла
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            logger.error("PublicImageForm: изображение отсутствует")
            raise ValidationError("Необходимо загрузить изображение.")

        # Проверка размера
        S3Data.validate_file_size(image)

        # Проверка валидности через PIL
        try:
            img = Image.open(image)
            img.verify()
        except Exception:
            logger.error("PublicImageForm: файл не является допустимым изображением")
            raise ValidationError("Файл не является допустимым изображением.")

        return image


class PublicVideoForm(forms.ModelForm):
    """
    Форма загрузки публичных видео.
    Валидирует: расширение и максимальный размер.
    """
    class Meta:
        model = PublicVideo
        fields = "__all__"

    # Валидация файла
    def clean_video(self):
        video = self.cleaned_data.get('video')
        if not video:
            logger.error("PublicVideoForm: видеофайл отсутствует")
            raise ValidationError("Пожалуйста, загрузите видеофайл.")

        # Проверка размера
        S3Data.validate_file_size(video)

        # Проверка расширения
        allowed = S3Data.ALLOWED_VIDEO_EXTENSIONS
        ext = '.' + video.name.split('.')[-1].lower()
        if ext not in allowed:
            msg = (
                f"Формат '{ext}' не поддерживается. "
                f"Разрешены: {', '.join(allowed)}."
            )
            logger.error(f"PublicVideoForm: {msg}")
            raise ValidationError(msg)

        return video


class PublicFileForm(forms.ModelForm):
    """
    Форма загрузки публичных файлов.
    Валидирует: расширение и максимальный размер.
    """
    class Meta:
        model = PublicFile
        fields = "__all__"

    # Валидация файла
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            logger.error("PublicFileForm: файл отсутствует")
            raise ValidationError("Пожалуйста, загрузите файл.")

        # Проверка размера
        S3Data.validate_file_size(file)

        # Проверка расширения
        allowed = S3Data.ALLOWED_FILE_EXTENSIONS
        ext = '.' + file.name.split('.')[-1].lower()
        if ext not in allowed:
            msg = (
                f"Формат '{ext}' не поддерживается. "
                f"Разрешены: {', '.join(allowed)}."
            )
            logger.error(f"PublicFileForm: {msg}")
            raise ValidationError(msg)

        return file


# =======================
# Формы приватных моделей
# =======================


class PrivateImageForm(forms.ModelForm):
    """
    Форма загрузки приватных изображений.
    Валидирует: реальность изображения и максимальный размер.
    """
    class Meta:
        model = PrivateImage
        fields = "__all__"

    # Валидация файла
    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image:
            logger.error("PrivateImageForm: изображение отсутствует")
            raise ValidationError("Необходимо загрузить изображение.")

        # Проверка размера
        S3Data.validate_file_size(image)

        # Проверка валидности через PIL
        try:
            img = Image.open(image)
            img.verify()
        except Exception:
            logger.error("PrivateImageForm: файл не является допустимым изображением")
            raise ValidationError("Файл не является допустимым изображением.")

        return image


class PrivateVideoForm(forms.ModelForm):
    """
    Форма загрузки приватных видео.
    Валидирует: расширение и максимальный размер.
    """
    class Meta:
        model = PrivateVideo
        fields = "__all__"

    # Валидация файла
    def clean_video(self):
        video = self.cleaned_data.get('video')
        if not video:
            logger.error("PrivateVideoForm: фидефайл отсутствует")
            raise ValidationError("Пожалуйста, загрузите видеофайл.")

        # Проверка размера
        S3Data.validate_file_size(video)

        # Проверка расширения
        allowed = S3Data.ALLOWED_VIDEO_EXTENSIONS
        ext = '.' + video.name.split('.')[-1].lower()
        if ext not in allowed:
            msg = (
                f"Формат '{ext}' не поддерживается. "
                f"Разрешены: {', '.join(allowed)}."
            )
            logger.error(f"PrivateVideoForm: {msg}")
            raise ValidationError(msg)

        return video


class PrivateFileForm(forms.ModelForm):
    """
    Форма загрузки приватных файлов.
    Валидирует: расширение и максимальный размер.
    """
    class Meta:
        model = PrivateFile
        fields = "__all__"

    # Валидация файла
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            logger.error("PrivateFileForm: файл отсутствует")
            raise ValidationError("Пожалуйста, загрузите файл.")

        # Проверка размера
        S3Data.validate_file_size(file)

        # Проверка расширения
        allowed = S3Data.ALLOWED_FILE_EXTENSIONS
        ext = '.' + file.name.split('.')[-1].lower()
        if ext not in allowed:
            msg = (
                f"Формат '{ext}' не поддерживается. "
                f"Разрешены: {', '.join(allowed)}."
            )
            logger.error(f"PrivateFileForm: {msg}")
            raise ValidationError(msg)

        return file


class MediaFileForm(forms.ModelForm):
    """
    Форма загрузки пользовательских файлов.
    Валидирует: расширение и максимальный размер.
    """
    class Meta:
        model = MediaFile
        fields = "__all__"

    # Валидация файла
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            logger.error("MediaFileForm: файл отсутствует")
            raise ValidationError("Пожалуйста, загрузите файл.")

        # Проверка размера
        S3Data.validate_file_size(file)

        # Проверка расширения
        allowed = S3Data.ALLOWED_FILE_EXTENSIONS
        ext = '.' + file.name.split('.')[-1].lower()
        if ext not in allowed:
            msg = (
                f"Формат '{ext}' не поддерживается. "
                f"Разрешены: {', '.join(allowed)}."
            )
            logger.error(f"MediaFileForm: {msg}")
            raise ValidationError(msg)

        return file