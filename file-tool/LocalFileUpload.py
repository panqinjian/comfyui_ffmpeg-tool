import os
import hashlib
from PIL import Image, ImageOps, ImageSequence
import numpy as np
import torch
import folder_paths

class LoadImageAndReturnPath:
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        return {
            "required": {
                "image": (sorted(files), {"image_upload": True}),  # 图像文件
            }
        }

    CATEGORY = "File-tool"  # 节点类别
    RETURN_TYPES = ("STRING",)  # 返回保存文件的路径
    RETURN_NAMES = ("File_path",)  # 返回名称
    FUNCTION = "load_image_and_return_path"  # 节点功能名称

    def load_image_and_return_path(self, image):
        """
        加载图像并返回文件路径。
        """
        # 获取图像文件的完整路径
        image_path = folder_paths.get_annotated_filepath(image)
        return (image_path,)

    @classmethod
    def IS_CHANGED(cls, image):
        """
        检查文件是否发生变化。
        """
        image_path = folder_paths.get_annotated_filepath(image)
        m = hashlib.sha256()
        with open(image_path, "rb") as f:
            m.update(f.read())
        return m.digest().hex()

    @classmethod
    def VALIDATE_INPUTS(cls, image):
        """
        验证输入文件是否有效。
        """
        if not folder_paths.exists_annotated_filepath(image):
            return f"Invalid image file: {image}"
        return True

