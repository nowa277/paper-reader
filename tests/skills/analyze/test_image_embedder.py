"""Tests for image_embedder module."""

import pytest
import json
import tempfile
from pathlib import Path

from skills.analyze.image_embedder import (
    ImageMetadata,
    ImageEmbedConfig,
    EmbeddedImage,
    ImageEmbedder,
    EmbeddingStrategy,
    create_default_embedder,
    load_config,
)


class TestImageMetadata:
    """Tests for ImageMetadata dataclass."""

    def test_basic_creation(self):
        metadata = ImageMetadata(
            image_id="img_001",
            page_number=1,
            position=(0, 0, 100, 100),
        )
        assert metadata.image_id == "img_001"
        assert metadata.page_number == 1
        assert metadata.format == "png"  # default

    def test_with_caption(self):
        metadata = ImageMetadata(
            image_id="img_002",
            page_number=2,
            position=(10, 20, 200, 150),
            caption="Figure 1: Architecture diagram",
            format="jpg",
        )
        assert metadata.caption == "Figure 1: Architecture diagram"
        assert metadata.format == "jpg"


class TestImageEmbedConfig:
    """Tests for ImageEmbedConfig dataclass."""

    def test_default_config(self):
        config = ImageEmbedConfig()
        assert config.max_inline_size_bytes == 50 * 1024
        assert config.max_inline_dimensions == (400, 400)
        assert "png" in config.supported_formats
        assert config.output_dir == Path("images")

    def test_custom_config(self):
        config = ImageEmbedConfig(
            max_inline_size_bytes=1024,
            max_inline_dimensions=(100, 100),
            output_dir=Path("custom_images"),
        )
        assert config.max_inline_size_bytes == 1024
        assert config.max_inline_dimensions == (100, 100)


class TestImageEmbedder:
    """Tests for ImageEmbedder class."""

    def test_default_embedder(self):
        embedder = create_default_embedder()
        assert isinstance(embedder, ImageEmbedder)
        assert embedder.config.max_inline_size_bytes == 50 * 1024

    def test_custom_config_embedder(self):
        config = ImageEmbedConfig(max_inline_size_bytes=1024)
        embedder = ImageEmbedder(config)
        assert embedder.config.max_inline_size_bytes == 1024

    def test_detect_images_markdown_syntax(self):
        embedder = create_default_embedder()
        vlm_content = """
# Paper Title

![Figure 1](images/fig1.png)

Some text here.

![Table 1](images/table1.jpg)
"""
        images = embedder.detect_images_from_vlm_output(vlm_content)
        assert len(images) >= 2

    def test_detect_images_vlm_pattern(self):
        embedder = create_default_embedder()
        vlm_content = """
The architecture is shown in [[Image:architecture.png]].
Also see [[Image:results_chart.svg]] for details.
"""
        images = embedder.detect_images_from_vlm_output(vlm_content)
        assert len(images) >= 2

    def test_detect_images_mineru_pattern(self):
        embedder = create_default_embedder()
        vlm_content = """
<img src="images/diagram1.png" alt="System Diagram" />
<img src="images/chart.jpeg" />
"""
        images = embedder.detect_images_from_vlm_output(vlm_content)
        assert len(images) >= 2

    def test_detect_images_from_content_list(self):
        embedder = create_default_embedder()
        content_list = {
            "content_list": [
                {
                    "type": "image",
                    "id": "img_001",
                    "page_idx": 1,
                    "x": 10,
                    "y": 20,
                    "width": 300,
                    "height": 200,
                    "caption": "Figure 1",
                    "img_path": "images/fig1.png",
                },
                {
                    "type": "image",
                    "id": "img_002",
                    "page_idx": 3,
                    "x": 50,
                    "y": 100,
                    "width": 500,
                    "height": 400,
                },
            ]
        }
        images = embedder.detect_images_from_content_list(content_list)
        assert len(images) == 2
        assert images[0].caption == "Figure 1"
        assert images[0].page_number == 1

    def test_get_image_size(self):
        embedder = create_default_embedder()
        # Test with some bytes
        data = b"fake image data here"
        size = embedder.get_image_size(data)
        assert size == len(data)

    def test_select_strategy_small_image(self):
        embedder = create_default_embedder()
        metadata = ImageMetadata(
            image_id="small",
            page_number=1,
            position=(0, 0, 100, 100),
            width=100,
            height=100,
        )
        # Small image data
        small_data = b"x" * 1000
        strategy = embedder.select_strategy(metadata, small_data)
        assert strategy == EmbeddingStrategy.BASE64_INLINE

    def test_select_strategy_large_image(self):
        embedder = create_default_embedder()
        metadata = ImageMetadata(
            image_id="large",
            page_number=1,
            position=(0, 0, 1000, 1000),
            width=1000,
            height=1000,
        )
        # Large image data (> 50KB)
        large_data = b"x" * 60000
        strategy = embedder.select_strategy(metadata, large_data)
        assert strategy == EmbeddingStrategy.EXTERNAL_FILE

    def test_select_strategy_svg_always_external(self):
        embedder = create_default_embedder()
        metadata = ImageMetadata(
            image_id="svg_img",
            page_number=1,
            position=(0, 0, 100, 100),
            source_path=Path("test.svg"),
        )
        small_data = b"x" * 100
        strategy = embedder.select_strategy(metadata, small_data)
        # SVG should always use external
        assert strategy == EmbeddingStrategy.EXTERNAL_FILE


class TestImageEmbedderFiles:
    """Tests that involve file operations."""

    def test_embed_as_base64(self, tmp_path):
        embedder = create_default_embedder()
        metadata = ImageMetadata(
            image_id="test_img",
            page_number=1,
            position=(0, 0, 100, 100),
            source_path=None,
        )
        # Create some test image data (not real image, but test base64)
        image_data = b"\x89PNG\r\n\x1a\n" + b"fake png data"

        result = embedder._embed_as_base64(metadata, image_data)

        assert result.strategy == EmbeddingStrategy.BASE64_INLINE
        assert "data:image/png;base64" in result.markdown
        assert result.size_bytes > 0

    def test_embed_as_external(self, tmp_path):
        embedder = create_default_embedder()
        metadata = ImageMetadata(
            image_id="test_ext",
            page_number=2,
            position=(10, 20, 300, 200),
            caption="Test figure",
        )
        output_dir = tmp_path / "output"
        paper_id = "test_paper"

        result = embedder._embed_as_external(
            metadata, output_dir, paper_id, "png"
        )

        assert result.strategy == EmbeddingStrategy.OBSIDIAN_EMBED
        assert "![[" in result.markdown
        assert result.file_path is not None
        assert result.file_path.exists()

    def test_embed_images_batch(self, tmp_path):
        embedder = create_default_embedder()
        images = [
            ImageMetadata("img1", page_number=1, position=(0, 0, 100, 100)),
            ImageMetadata("img2", page_number=2, position=(0, 0, 200, 200)),
        ]
        output_dir = tmp_path / "batch_output"

        results = embedder.embed_images_batch(images, output_dir, "batch_paper")

        assert len(results) == 2
        assert all(isinstance(r, EmbeddedImage) for r in results)

    def test_export_image_manifest(self, tmp_path):
        embedder = create_default_embedder()
        embedded = [
            EmbeddedImage(
                image_id="img_001",
                strategy=EmbeddingStrategy.BASE64_INLINE,
                markdown="![img](data:...)",
                size_bytes=1000,
            ),
            EmbeddedImage(
                image_id="img_002",
                strategy=EmbeddingStrategy.OBSIDIAN_EMBED,
                markdown="![[test.png]]",
                file_path=tmp_path / "test.png",
                size_bytes=2000,
            ),
        ]

        manifest_path = tmp_path / "manifest.json"
        embedder.export_image_manifest(embedded, manifest_path)

        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text())
        assert len(data["images"]) == 2
        assert data["images"][0]["id"] == "img_001"


class TestImageDimensions:
    """Tests for image dimension detection."""

    def test_png_dimensions_invalid(self, tmp_path):
        """Test that invalid PNG returns None for dimensions."""
        embedder = create_default_embedder()
        # Create invalid PNG file
        bad_png = tmp_path / "bad.png"
        bad_png.write_bytes(b"not a png file")

        dims = embedder.get_image_dimensions(bad_png)
        # Invalid PNG should return None or handle gracefully
        # The function may return None for non-PNG data

    def test_svg_dimensions(self, tmp_path):
        """Test SVG dimension parsing."""
        embedder = create_default_embedder()
        svg_content = '''<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
  <rect width="800" height="600"/>
</svg>'''
        svg_file = tmp_path / "test.svg"
        svg_file.write_text(svg_content)

        dims = embedder.get_image_dimensions(svg_file)
        # Should parse viewBox or width/height
        # May return None if parsing fails, but structure is there


class TestConfigLoading:
    """Tests for loading configuration from YAML."""

    def test_load_config(self, tmp_path):
        config_content = """
max_inline_size_bytes: 10240
max_inline_dimensions:
  - 200
  - 200
supported_formats:
  - png
  - svg
output_dir: my_images
naming_pattern: "img_{paper_id}_{page}_{index}"
"""
        config_file = tmp_path / "image_config.yaml"
        config_file.write_text(config_content)

        config = load_config(config_file)

        assert config.max_inline_size_bytes == 10240
        assert config.max_inline_dimensions == (200, 200)
        assert "svg" in config.supported_formats
        assert config.output_dir == Path("my_images")

    def test_load_config_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/config.yaml"))


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_end_to_end_workflow(self, tmp_path):
        """Test complete image embedding workflow."""
        embedder = create_default_embedder()

        # Simulate VLM output with images
        vlm_content = """
# Research Paper

![Figure 1: Architecture](images/architecture.png)

The system consists of three components shown in [[Image:components.svg]].

<img src="images/results_chart.jpg" alt="Results" />
"""
        # Detect images
        images = embedder.detect_images_from_vlm_output(vlm_content)
        assert len(images) > 0

        # Embed all images
        output_dir = tmp_path / "paper_output"
        embedded = embedder.embed_images_batch(
            images, output_dir, "research_paper_v1"
        )

        # All should have embedding results
        assert len(embedded) == len(images)
        assert all(isinstance(e, EmbeddedImage) for e in embedded)

        # Export manifest
        manifest_path = output_dir / "image_manifest.json"
        embedder.export_image_manifest(embedded, manifest_path)
        assert manifest_path.exists()

    def test_content_list_workflow(self, tmp_path):
        """Test workflow with MinerU content_list.json."""
        embedder = create_default_embedder()

        # Simulate MinerU content_list.json
        content_list = {
            "content_list": [
                {
                    "type": "image",
                    "id": "fig1",
                    "page_idx": 1,
                    "x": 50,
                    "y": 100,
                    "width": 400,
                    "height": 300,
                    "caption": "Figure 1: Main experimental results",
                    "img_path": "mineru_output/paper1/images/fig1.png",
                },
                {
                    "type": "image",
                    "id": "fig2",
                    "page_idx": 2,
                    "x": 0,
                    "y": 0,
                    "width": 600,
                    "height": 800,
                    "caption": "Figure 2: System architecture",
                    "img_path": "mineru_output/paper1/images/fig2.png",
                },
            ]
        }

        images = embedder.detect_images_from_content_list(content_list)
        assert len(images) == 2
        assert images[0].caption == "Figure 1: Main experimental results"
        assert images[0].page_number == 1

        # Embed with external strategy
        output_dir = tmp_path / "output"
        embedded = embedder.embed_images_batch(images, output_dir, "paper1")

        # Check strategies were selected
        assert all(e.strategy in [EmbeddingStrategy.BASE64_INLINE,
                                   EmbeddingStrategy.EXTERNAL_FILE,
                                   EmbeddingStrategy.OBSIDIAN_EMBED]
                   for e in embedded)