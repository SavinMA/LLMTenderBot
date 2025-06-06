from typing import List, Dict
from semantic_text_splitter import TextSplitter
from tokenizers import Tokenizer

class SemanticSplitter():
    """Semantic text splitter implementation using semantic-text-splitter"""
    
    def __init__(self, chunk_size: int = 2048, chunk_overlap: int = 256):
        """Initialize semantic splitter
        
        Args:
            chunk_size: Size of each text chunk
            chunk_overlap: Number of characters to overlap between chunks
        """ 
        self.model_name = "ai-forever/sbert_large_nlu_ru" #"ai-forever/sbert_large_nlu_ru", "bert-base-uncased"
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        tokenizer = Tokenizer.from_pretrained(self.model_name)
        self.splitter = TextSplitter.from_huggingface_tokenizer(
            tokenizer=tokenizer,
            capacity=chunk_size,
            overlap=chunk_overlap
        )

    def _get_additional_info(self) -> Dict[str, any]:
        """Get additional information about the splitter
        
        Returns:
            Dictionary with additional information
        """
        return {
            "size": self.chunk_size,
            "overlap": self.chunk_overlap,
            "model": self.model_name
        }
    
    def split_text(self, text: str) -> List[str]:
        """Split text into chunks using semantic boundaries
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
        """

        chunks = self.splitter.chunks(text)
        return chunks