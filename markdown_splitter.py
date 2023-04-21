import hashlib
import re

import frontmatter
from langchain.docstore.document import Document


class MarkdownSplitter:
    def __init__(self) -> None:
        pass

    def split_markdown(self, file_path: str) -> list:
        """Splits a markdown string into a list of markdown strings."""
        sections = []
        with open(file_path, "r") as f:
            markdown = f.read()
            chunks = re.findall(
                r"^#{2,}\s+(.*?)\n(.*?)(?=\n#{2,}|\Z)",
                markdown,
                flags=re.DOTALL | re.MULTILINE,
            )
            for chunk in chunks:
                if chunk[0] and chunk[1]:
                    sections.append(
                        {
                            "title": chunk[0],
                            "content": chunk[1],
                            "slug": self.slugify(chunk[0]),
                            "source": file_path,
                        }
                    )
        return sections

    def slugify(self, string: str) -> str:
        return (
            string.lower()
            .strip()
            .replace(" ", "-")
            .replace(":", "")
            .replace("*", "")
            .replace("'", "")
            .replace('"', "")
            .replace("’", "")
            .replace("‘", "")
            .replace("?", "")
            .replace("!", "")
            .replace("(", "")
            .replace(")", "")
            .replace(".", "")
            .replace("/", "")
            .replace("&", "and")
            .replace("`", "")
            .replace("“", "")
            .replace("”", "")
            .replace("`", "")
        )

    def create_md5_hash(self, string: str) -> str:
        """Creates an md5 hash from a string."""
        return hashlib.md5(string.encode()).hexdigest()

    def create_documents(self, file_path: str) -> list:
        """Creates a list of langchain documents from a markdown file."""
        documents = []
        sections = self.split_markdown(file_path)

        fm = frontmatter.loads(open(file_path).read())
        slug = ""
        if fm.get("slug"):
            slug = fm["slug"]
            file_path = re.sub(r"[^/]+$", slug, file_path)

        for section in sections:
            documents.append(
                Document(
                    page_content=section["content"],
                    metadata={
                        "id": self.create_md5_hash(
                            f"{file_path}{section['slug']}{section['content']}"
                        ),
                        "source": file_path,
                        "slug": section["slug"],
                        "title": section["title"],
                    },
                )
            )
        return documents
