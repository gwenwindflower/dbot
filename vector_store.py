import os
from typing import List

import tiktoken
from dotenv import load_dotenv
from halo import Halo
from langchain.docstore.document import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma

from document_crawler import Chunk
from markdown_crawler import MarkdownCrawler

load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

spinner = Halo(text="Loading", spinner="dots")


class VectorStore:
    def __init__(
        self,
        name: str,
        sources_path: str,
        reindex: bool,
    ) -> None:
        embedder = OpenAIEmbeddings(client=OPENAI_API_KEY)
        self.initialize_db(
            name,
            sources_path,
            embedder,
            reindex,
        )

    def initialize_db(
        self,
        name: str,
        sources_path: str,
        embedder: OpenAIEmbeddings,
        reindex: bool,
    ):
        """Initialize a new vector store or load an existing one."""
        if not os.path.exists(f"./{name}"):
            os.makedirs(f"./{name}")
        self.database: Chroma = Chroma(
            persist_directory=f"./{name}", embedding_function=embedder
        )
        if reindex:
            self.add_docs(name, sources_path, embedder)

    def make_docs(self, chunks: List[Chunk]) -> List[Document]:
        """Convert a list of chunks into Documents."""
        documents: List[Document] = []
        spinner.start("Chunk context sources into Documents")
        for chunk in chunks:
            documents.append(
                Document(
                    page_content=chunk["content"],
                    metadata={
                        "id": chunk["chunk_id"],
                        "source": chunk["source"],
                    },
                )
            )
        spinner.succeed("Chunked context sources into Documents")
        return documents

    def add_docs(self, db_name: str, sources_path: str, embedder: OpenAIEmbeddings):
        """Add a collection of split chunks to the vector store as Documents."""
        if not os.path.exists(sources_path):
            print(f"Directory {sources_path} does not exist.")
            return

        crawler: MarkdownCrawler = MarkdownCrawler(sources_path)
        chunks: List[Chunk] = crawler.crawl_and_chunk()
        docs: List[Document] = self.make_docs(chunks)
        spinner.start(f"Adding documents to vector store {db_name}")
        self.database.add_documents(docs)
        spinner.succeed(f"Added documents to vector store {db_name}")
        # will this update the existing document if the id is the same?
        # this is a hack to avoid hitting the embeddings API
        # for documents that are already in the database
        # loop over docs and do this check? or filter docs to just ids
        # that don't get returned?
        # for doc in tqdm(docs, desc=f"Adding documents to {db_name}"):
        #     self.database.add_documents([doc])
        # if self.database._collection.get(
        #     ids=[id],
        # ):
        #     continue
        # else:

    def num_tokens_from_string(
        self, string: str, encoding_name: str = "cl100k_base"
    ) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens: int = len(encoding.encode(string))
        return num_tokens

    def get_similar_documents(self, question: str):
        """Returns a list of documents similar to a question with a similarity score."""
        results = self.database.similarity_search_with_score(question)
        return results

    def format_source_links(self, source: str) -> str:
        """Formats a file path into a  source link on the dbt docs site."""
        return source.replace("./docs", "https://docs.getdbt.com").replace(".md", "")

    def choose_relevant_documents(self, question: str, max_tokens: int = 3000):
        """Chooses relevant documents to answer a question within a max_tokens limit."""
        SEPARATOR: str = "\n* "
        SEPARATOR_LEN: int = 3
        results = self.get_similar_documents(question)
        # TODO: make a TypedDict for this
        chosen_sections = {
            "content": "",
            "source_links": [],
            "length": 0,
        }

        for result in sorted(results, key=lambda x: x[1], reverse=True):
            result_data = result[0]
            result_content = result_data.page_content.replace("\n", " ")
            result_source = result_data.metadata["source"]
            result_source_link = self.format_source_links(result_source)
            result_slug = result_data.metadata["slug"]

            if (
                chosen_sections["length"]
                + self.num_tokens_from_string(result_content)
                + SEPARATOR_LEN
                > max_tokens
            ):
                break

            chosen_sections["content"] += SEPARATOR + result_content

            chosen_sections["source_links"].append(
                f"{result_source_link}#{result_slug}"
            )

            chosen_sections["length"] += SEPARATOR_LEN + self.num_tokens_from_string(
                result_content
            )

        return chosen_sections
