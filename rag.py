from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("SystemDesignInterview.pdf")

documents = loader.load()

print("Number of pages:", len(documents))
print(documents[0].page_content[:1000])