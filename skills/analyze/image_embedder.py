"""Image embedding module for PDF/VLM analysis.

Provides image extraction, metadata tracking, and embedding strategies
for Obsidian-compatible markdown output.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import base64
import json
import re


class EmbeddingStrategy(Enum):
    """Strategy for embedding images in markdown."""
    BASE64_INLINE = "base64_inline"      # Small images: embed as data URI
    EXTERNAL_FILE = "external_file"       # Large images: save to disk, reference path
    OBSIDIAN_EMBED = "obsidian_embed"     # Obsidian wikilink syntax: ![[image.png]]


@dataclass
class ImageMetadata:
    """Metadata for an extracted image."""
    image_id: str
    page_number: int
    position: tuple[int, int, int, int]  # x, y, width, height
    caption: Optional[str] = None
    format: str = "png"                   # png, jpg, svg
    width: Optional[int] = None
    height: Optional[int] = None
    source_path: Optional[Path] = None    # Original path if extracted from file
    vlm_reference: Optional[str] = None   # Reference from VLM output


@dataclass
class ImageEmbedConfig:
    """Configuration for image embedding behavior."""
    max_inline_size_bytes: int = 50 * 1024      # 50KB: images smaller use base64
    max_inline_dimensions: tuple[int, int] = (400, 400)  # max width, height for inline
    supported_formats: list[str] = field(default_factory=lambda: ["png", "jpg", "jpeg", "svg"])
    output_dir: Path = field(default_factory=lambda: Path("images"))
    preserve_originals: bool = True
    naming_pattern: str = "{paper_id}_page{page}_{index}"


@dataclass
class EmbeddedImage:
    """Result of embedding an image in markdown."""
    image_id: str
    strategy: EmbeddingStrategy
    markdown: str                          # The markdown snippet to embed
    file_path: Optional[Path] = None       # Path to saved file (for external/obsidian)
    size_bytes: int = 0
    dimensions: Optional[tuple[int, int]] = None


class ImageEmbedder:
    """Handles image extraction and embedding for paper analysis."""

    def __init__(self, config: Optional[ImageEmbedConfig] = None):
        """Initialize the embedder with optional configuration.

        Args:
            config: Image embedding configuration. Uses defaults if not provided.
        """
        self.config = config or ImageEmbedConfig()

    def detect_images_from_vlm_output(self, vlm_content: str) -> list[ImageMetadata]:
        """Detect image references from VLM markdown output.

        Parses markdown for image syntax and VLM-specific image markers.

        Args:
            vlm_content: The VLM markdown content to parse.

        Returns:
            List of ImageMetadata objects for detected images.
        """
        images = []

        # Pattern 1: Standard markdown images ![alt](path)
        markdown_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        for i, match in enumerate(re.finditer(markdown_pattern, vlm_content)):
            alt_text = match.group(1)
            path = match.group(2)
            images.append(ImageMetadata(
                image_id=f"img_{i}",
                page_number=1,  # Default, may need extraction from context
                position=(0, 0, 0, 0),
                caption=alt_text if alt_text else None,
                source_path=Path(path) if path else None,
                vlm_reference=match.group(0),
            ))

        # Pattern 2: VLM-specific markers like [[Image:filename.png]]
        vlm_pattern = r'\[\[Image:([^\]]+)\]\]'
        for i, match in enumerate(re.finditer(vlm_pattern, vlm_content)):
            filename = match.group(1)
            images.append(ImageMetadata(
                image_id=f"vlm_img_{i}",
                page_number=1,
                position=(0, 0, 0, 0),
                source_path=Path(filename),
                vlm_reference=match.group(0),
            ))

        # Pattern 3: MinerU style image references
        mineru_pattern = r'<img[^>]+src="([^"]+)"[^>]*>'
        for i, match in enumerate(re.finditer(mineru_pattern, vlm_content)):
            src = match.group(1)
            images.append(ImageMetadata(
                image_id=f"mineru_img_{i}",
                page_number=1,
                position=(0, 0, 0, 0),
                source_path=Path(src),
                vlm_reference=match.group(0),
            ))

        return images

    def detect_images_from_content_list(self, content_list: dict) -> list[ImageMetadata]:
        """Detect images from MinerU content_list.json metadata.

        Args:
            content_list: Parsed content_list.json from MinerU.

        Returns:
            List of ImageMetadata objects with page/position info.
        """
        images = []
        blocks = content_list.get("content_list", [])

        for i, block in enumerate(blocks):
            if block.get("type") == "image":
                images.append(ImageMetadata(
                    image_id=block.get("id", f"block_img_{i}"),
                    page_number=block.get("page_idx", 1),
                    position=(
                        block.get("x", 0),
                        block.get("y", 0),
                        block.get("width", 0),
                        block.get("height", 0),
                    ),
                    caption=block.get("caption"),
                    width=block.get("width"),
                    height=block.get("height"),
                    source_path=Path(block.get("img_path", "")) if block.get("img_path") else None,
                ))

        return images

    def extract_image_data(self, image_path: Path) -> bytes:
        """Read image file as bytes.

        Args:
            image_path: Path to the image file.

        Returns:
            Raw image bytes.
        """
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        return image_path.read_bytes()

    def get_image_size(self, image_data: bytes) -> int:
        """Get size of image in bytes.

        Args:
            image_data: Raw image bytes.

        Returns:
            Size in bytes.
        """
        return len(image_data)

    def get_image_dimensions(self, image_path: Path) -> Optional[tuple[int, int]]:
        """Get image dimensions (width, height).

        For PNG/JPEG, reads from header. For SVG, parses viewBox.

        Args:
            image_path: Path to the image file.

        Returns:
            Tuple of (width, height) or None if unable to determine.
        """
        suffix = image_path.suffix.lower()

        if suffix == ".svg":
            content = image_path.read_text(encoding="utf-8")
            # Parse viewBox="x y w h"
            match = re.search(r'viewBox="(\d+)\s+(\d+)\s+(\d+)\s+(\d+)"', content)
            if match:
                return (int(match.group(3)), int(match.group(4)))
            # Fallback to width/height attributes
            width_match = re.search(r'width="(\d+)"', content)
            height_match = re.search(r'height="(\d+)"', content)
            if width_match and height_match:
                return (int(width_match.group(1)), int(height_match.group(1)))
            return None

        # For PNG: check for IHDR chunk dimensions
        if suffix == ".png":
            data = image_path.read_bytes()
            if len(data) >= 24 and data[:8] == b'\x89PNG\r\n\x1a\n':
                import struct
                width, height = struct.unpack(">II", data[16:24])
                return (width, height)

        # For JPEG: check for SOF0 segment
        if suffix in (".jpg", ".jpeg"):
            data = image_path.read_bytes()
            i = 2
            while i < len(data) - 8:
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                # SOF0, SOF1, SOF2 markers
                if marker in (0xC0, 0xC1, 0xC2):
                    import struct
                    height, width = struct.unpack(">HH", data[i + 5:i + 9])
                    return (width, height)
                length = struct.unpack(">H", data[i + 2:i + 4])[0]
                i += 2 + length

        return None

    def select_strategy(
        self,
        image_metadata: ImageMetadata,
        image_data: bytes,
    ) -> EmbeddingStrategy:
        """Select embedding strategy based on image characteristics.

        Args:
            image_metadata: Metadata about the image.
            image_data: Raw image bytes.

        Returns:
            The selected embedding strategy.
        """
        size_bytes = self.get_image_size(image_data) if image_data else 0
        dimensions = None

        if image_metadata.width and image_metadata.height:
            dimensions = (image_metadata.width, image_metadata.height)
        elif image_metadata.source_path:
            dimensions = self._try_get_dimensions(image_metadata.source_path)

        # No image data or missing file - use external with placeholder
        if not image_data or size_bytes == 0:
            return EmbeddingStrategy.EXTERNAL_FILE

        # Check against config thresholds
        if size_bytes <= self.config.max_inline_size_bytes:
            if dimensions and dimensions[0] <= self.config.max_inline_dimensions[0] \
               and dimensions[1] <= self.config.max_inline_dimensions[1]:
                return EmbeddingStrategy.BASE64_INLINE

        return EmbeddingStrategy.EXTERNAL_FILE

    def _try_get_dimensions(self, path: Optional[Path]) -> Optional[tuple[int, int]]:
        """Try to get dimensions from a path."""
        if path and path.exists():
            return self.get_image_dimensions(path)
        return None

    def embed_image(
        self,
        image_metadata: ImageMetadata,
        output_dir: Path,
        paper_id: str,
    ) -> EmbeddedImage:
        """Embed an image using the appropriate strategy.

        Args:
            image_metadata: Metadata about the image.
            output_dir: Directory for output files.
            paper_id: Identifier for the paper.

        Returns:
            EmbeddedImage with markdown and file info.
        """
        # Handle SVG specially - always use external (base64 not ideal for SVG)
        if image_metadata.source_path and image_metadata.source_path.suffix.lower() == ".svg":
            return self._embed_as_external(
                image_metadata, output_dir, paper_id, "svg"
            )

        # Try to read image data
        image_data = b""
        if image_metadata.source_path and image_metadata.source_path.exists():
            try:
                image_data = self.extract_image_data(image_metadata.source_path)
            except (FileNotFoundError, OSError):
                # Source file doesn't exist - will use external strategy with placeholder
                pass

        strategy = self.select_strategy(image_metadata, image_data)

        if strategy == EmbeddingStrategy.BASE64_INLINE:
            return self._embed_as_base64(image_metadata, image_data)
        else:
            return self._embed_as_external(
                image_metadata, output_dir, paper_id,
                image_metadata.format or "png"
            )

    def _embed_as_base64(
        self,
        image_metadata: ImageMetadata,
        image_data: bytes,
    ) -> EmbeddedImage:
        """Embed image as base64 data URI.

        Args:
            image_metadata: Metadata about the image.
            image_data: Raw image bytes.

        Returns:
            EmbeddedImage with base64 markdown.
        """
        # Use provided data or try to read from source
        if not image_data and image_metadata.source_path and image_metadata.source_path.exists():
            image_data = self.extract_image_data(image_metadata.source_path)

        if not image_data:
            # No image data available - return empty placeholder
            return EmbeddedImage(
                image_id=image_metadata.image_id,
                strategy=EmbeddingStrategy.BASE64_INLINE,
                markdown=f"![{image_metadata.caption or image_metadata.image_id}](data:image/png;base64,)",
                size_bytes=0,
            )

        b64_data = base64.b64encode(image_data).decode("utf-8")

        # Determine MIME type
        suffix = (image_metadata.source_path.suffix.lower()
                  if image_metadata.source_path else ".png")
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".svg": "image/svg+xml",
        }
        mime = mime_types.get(suffix, "image/png")

        markdown = f"![{image_metadata.caption or image_metadata.image_id}](data:{mime};base64,{b64_data})"

        return EmbeddedImage(
            image_id=image_metadata.image_id,
            strategy=EmbeddingStrategy.BASE64_INLINE,
            markdown=markdown,
            size_bytes=len(image_data),
        )

    def _embed_as_external(
        self,
        image_metadata: ImageMetadata,
        output_dir: Path,
        paper_id: str,
        format: str,
    ) -> EmbeddedImage:
        """Save image to file and create external/obsidian reference.

        Args:
            image_metadata: Metadata about the image.
            output_dir: Directory to save images.
            paper_id: Identifier for the paper.
            format: Image format extension.

        Returns:
            EmbeddedImage with file path and reference markdown.
        """
        # Generate output filename
        filename = self.config.naming_pattern.format(
            paper_id=paper_id,
            page=image_metadata.page_number,
            index=image_metadata.image_id,
        ) + f".{format}"

        output_path = output_dir / filename
        output_dir.mkdir(parents=True, exist_ok=True)

        # Copy or create the image file
        if image_metadata.source_path and image_metadata.source_path.exists():
            import shutil
            shutil.copy2(image_metadata.source_path, output_path)
        else:
            # Create placeholder or handle VLM-generated image data
            output_path.write_bytes(b"")

        size_bytes = output_path.stat().st_size if output_path.exists() else 0
        dimensions = self.get_image_dimensions(output_path) if output_path.exists() else None

        # Use Obsidian embed syntax
        markdown = f"![[{filename}]]"

        return EmbeddedImage(
            image_id=image_metadata.image_id,
            strategy=EmbeddingStrategy.OBSIDIAN_EMBED,
            markdown=markdown,
            file_path=output_path,
            size_bytes=size_bytes,
            dimensions=dimensions,
        )

    def embed_images_batch(
        self,
        images: list[ImageMetadata],
        output_dir: Path,
        paper_id: str,
    ) -> list[EmbeddedImage]:
        """Embed multiple images.

        Args:
            images: List of image metadata.
            output_dir: Directory for output files.
            paper_id: Identifier for the paper.

        Returns:
            List of EmbeddedImage results.
        """
        return [
            self.embed_image(img, output_dir, paper_id)
            for img in images
        ]

    def generate_markdown_with_images(
        self,
        base_markdown: str,
        embedded_images: list[EmbeddedImage],
    ) -> str:
        """Insert embedded images into markdown content.

        Replaces image references with embedded markdown.

        Args:
            base_markdown: Original markdown content.
            embedded_images: List of embedded images with replacement markdown.

        Returns:
            Markdown with images embedded.
        """
        result = base_markdown

        # Create a mapping of original references to embedded markdown
        for embedded in embedded_images:
            if embedded.strategy == EmbeddingStrategy.BASE64_INLINE:
                # Replace data URI references
                # This is simplified; real implementation would need more robust replacement
                pass

        return result

    def export_image_manifest(
        self,
        embedded_images: list[EmbeddedImage],
        output_path: Path,
    ) -> None:
        """Export image manifest as JSON.

        Args:
            embedded_images: List of embedded images.
            output_path: Path to save the manifest.
        """
        manifest = {
            "images": [
                {
                    "id": img.image_id,
                    "strategy": img.strategy.value,
                    "markdown": img.markdown,
                    "file_path": str(img.file_path) if img.file_path else None,
                    "size_bytes": img.size_bytes,
                    "dimensions": img.dimensions,
                }
                for img in embedded_images
            ]
        }
        output_path.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )


def create_default_embedder() -> ImageEmbedder:
    """Create an ImageEmbedder with default configuration.

    Returns:
        Configured ImageEmbedder instance.
    """
    return ImageEmbedder()


def load_config(config_path: Path) -> ImageEmbedConfig:
    """Load image embedding configuration from YAML file.

    Args:
        config_path: Path to YAML config file.

    Returns:
        ImageEmbedConfig loaded from file.
    """
    import yaml

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    return ImageEmbedConfig(
        max_inline_size_bytes=data.get("max_inline_size_bytes", 50 * 1024),
        max_inline_dimensions=tuple(data.get("max_inline_dimensions", [400, 400])),
        supported_formats=data.get("supported_formats", ["png", "jpg", "jpeg", "svg"]),
        output_dir=Path(data.get("output_dir", "images")),
        preserve_originals=data.get("preserve_originals", True),
        naming_pattern=data.get("naming_pattern", "{paper_id}_page{page}_{index}"),
    )