"""
Embedding service for generating vector embeddings from text content.

This module provides functionality to generate embeddings using various providers
(primarily OpenAI) and handle text chunking for large documents.
"""

import os
import logging
import time
from typing import List, Optional
import tiktoken
from openai import OpenAI


logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating vector embeddings from text content."""
    
    def __init__(self, provider: str = "openai", model: str = "text-embedding-3-small"):
        """
        Initialize the embedding service.
        
        Args:
            provider: The embedding provider to use (currently only "openai" supported)
            model: The embedding model to use
        """
        self.provider = provider
        self.model = model
        self._client = None
        self._encoding = None
        
        if provider == "openai":
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                try:
                    self._client = OpenAI(api_key=api_key)
                    logger.debug("OpenAI client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI client: {str(e)}")
                    self._client = None
                
                try:
                    # Initialize tokenizer for text chunking
                    self._encoding = tiktoken.encoding_for_model(model)
                    logger.debug(f"Tokenizer initialized for model {model}")
                except KeyError:
                    # Fallback to cl100k_base encoding if model not found
                    try:
                        self._encoding = tiktoken.get_encoding("cl100k_base")
                        logger.warning(f"Model {model} not found in tiktoken, using cl100k_base encoding")
                    except Exception as e:
                        logger.error(f"Failed to initialize tokenizer: {str(e)}")
                        self._encoding = None
                except Exception as e:
                    logger.error(f"Failed to initialize tokenizer: {str(e)}")
                    self._encoding = None
            else:
                logger.warning("OpenAI API key not found in environment variables")
                logger.debug("Set OPENAI_API_KEY environment variable to enable embedding service")
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
    
    def is_available(self) -> bool:
        """
        Check if the embedding service is available and properly configured.
        
        Returns:
            True if the service is available, False otherwise
        """
        try:
            if self.provider == "openai":
                if self._client is None:
                    logger.debug("OpenAI embedding service not available: client not initialized")
                    return False
                
                # Test the connection with a simple API call
                try:
                    # Make a minimal test call to verify API access
                    test_response = self._client.embeddings.create(
                        model=self.model,
                        input="test"
                    )
                    if test_response and test_response.data:
                        logger.debug("OpenAI embedding service is available and responding")
                        return True
                    else:
                        logger.warning("OpenAI embedding service test call returned invalid response")
                        return False
                        
                except Exception as e:
                    logger.warning(f"OpenAI embedding service availability test failed: {str(e)}")
                    return False
            else:
                logger.error(f"Unsupported embedding provider: {self.provider}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking embedding service availability: {str(e)}")
            return False
    
    def check_service_health(self) -> bool:
        """
        Quick health check without making API calls.
        
        Returns:
            True if service appears to be configured correctly, False otherwise
        """
        try:
            if self.provider == "openai":
                if self._client is None:
                    logger.debug("OpenAI service health check failed: client not initialized")
                    return False
                
                # Check if API key is present and has correct format
                api_key = os.getenv('OPENAI_API_KEY')
                if not api_key:
                    logger.debug("OpenAI service health check failed: no API key")
                    return False
                
                if not api_key.startswith('sk-') or len(api_key) < 20:
                    logger.debug("OpenAI service health check failed: invalid API key format")
                    return False
                
                logger.debug("OpenAI service health check passed")
                return True
            else:
                logger.error(f"Unsupported embedding provider for health check: {self.provider}")
                return False
                
        except Exception as e:
            logger.error(f"Error during service health check: {str(e)}")
            return False
    
    def generate_embedding(self, text: str, max_retries: int = 3, retry_delay: float = 1.0) -> List[float]:
        """
        Generate vector embedding for the given text with retry logic and error handling.
        
        Args:
            text: The text to generate embedding for
            max_retries: Maximum number of retries for transient failures
            retry_delay: Delay between retries in seconds
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            RuntimeError: If the embedding service is not available
            ValueError: If input validation fails
            Exception: If embedding generation fails after all retries
        """
        # Input validation
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty or whitespace-only text")
        
        # Check service availability (but don't do the expensive test call here)
        if self._client is None:
            raise RuntimeError(f"Embedding service ({self.provider}) is not initialized")
        
        # Truncate text if it's too long to avoid API errors
        max_length = 8000  # Conservative limit for most embedding models
        if len(text) > max_length:
            logger.warning(f"Text length ({len(text)}) exceeds maximum ({max_length}), truncating")
            text = text[:max_length]
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(f"Generating embedding (attempt {attempt + 1}/{max_retries + 1})")
                
                if self.provider == "openai":
                    response = self._client.embeddings.create(
                        model=self.model,
                        input=text
                    )
                    
                    if not response or not response.data or len(response.data) == 0:
                        raise RuntimeError("Invalid response from OpenAI embedding API")
                    
                    embedding = response.data[0].embedding
                    
                    if not embedding or len(embedding) == 0:
                        raise RuntimeError("Empty embedding returned from OpenAI API")
                    
                    if attempt > 0:
                        logger.info(f"Embedding generation succeeded on attempt {attempt + 1}")
                    
                    logger.debug(f"Successfully generated embedding of dimension {len(embedding)}")
                    return embedding
                else:
                    raise ValueError(f"Unsupported provider: {self.provider}")
                    
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                
                # Check if this is a retryable error
                retryable_patterns = [
                    'rate limit',
                    'timeout',
                    'connection',
                    'network',
                    'server error',
                    'internal error',
                    'service unavailable',
                    'too many requests',
                    '5xx'
                ]
                
                is_retryable = any(pattern in error_str for pattern in retryable_patterns)
                
                # Don't retry validation errors or authentication errors
                non_retryable_patterns = [
                    'invalid api key',
                    'authentication',
                    'unauthorized',
                    'invalid model',
                    'quota exceeded',
                    'billing'
                ]
                
                is_non_retryable = any(pattern in error_str for pattern in non_retryable_patterns)
                
                if is_non_retryable or not is_retryable:
                    logger.error(f"Non-retryable error generating embedding: {str(e)}")
                    raise e
                
                if attempt < max_retries:
                    delay = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Embedding generation failed on attempt {attempt + 1}, retrying in {delay}s: {str(e)}")
                    time.sleep(delay)
                else:
                    logger.error(f"Embedding generation failed after {max_retries + 1} attempts: {str(e)}")
        
        raise last_exception
    
    def chunk_text(self, text: str, max_tokens: int = 8000) -> List[str]:
        """
        Split text into chunks that fit within the token limit with error handling.
        
        Args:
            text: The text to chunk
            max_tokens: Maximum number of tokens per chunk
            
        Returns:
            List of text chunks
        """
        try:
            if not text or not text.strip():
                logger.debug("Empty text provided for chunking")
                return []
            
            if max_tokens <= 0:
                logger.warning(f"Invalid max_tokens value: {max_tokens}, using default 8000")
                max_tokens = 8000
            
            logger.debug(f"Chunking text of length {len(text)} with max_tokens {max_tokens}")
            
            if not self._encoding:
                logger.warning("No tokenizer available, falling back to character-based chunking")
                return self._chunk_by_characters(text, max_tokens * 4)  # Rough estimate: 4 chars per token
            
            # Tokenize the text
            try:
                tokens = self._encoding.encode(text)
            except Exception as e:
                logger.warning(f"Tokenization failed, falling back to character-based chunking: {str(e)}")
                return self._chunk_by_characters(text, max_tokens * 4)
            
            if len(tokens) <= max_tokens:
                logger.debug("Text fits in single chunk")
                return [text]
            
            logger.debug(f"Text has {len(tokens)} tokens, splitting into chunks")
            
            chunks = []
            current_chunk_tokens = []
            
            # Split by sentences first to maintain coherence
            try:
                sentences = self._split_into_sentences(text)
            except Exception as e:
                logger.warning(f"Sentence splitting failed, using simple chunking: {str(e)}")
                return self._chunk_by_tokens_simple(tokens, max_tokens)
            
            for sentence in sentences:
                try:
                    sentence_tokens = self._encoding.encode(sentence)
                    
                    # If adding this sentence would exceed the limit, save current chunk
                    if len(current_chunk_tokens) + len(sentence_tokens) > max_tokens:
                        if current_chunk_tokens:
                            chunk_text = self._encoding.decode(current_chunk_tokens)
                            chunks.append(chunk_text)
                            current_chunk_tokens = []
                        
                        # If single sentence is too long, split it further
                        if len(sentence_tokens) > max_tokens:
                            sentence_chunks = self._chunk_long_sentence(sentence, max_tokens)
                            chunks.extend(sentence_chunks)
                        else:
                            current_chunk_tokens = sentence_tokens
                    else:
                        current_chunk_tokens.extend(sentence_tokens)
                        
                except Exception as e:
                    logger.warning(f"Error processing sentence, skipping: {str(e)}")
                    continue
            
            # Add the last chunk if it has content
            if current_chunk_tokens:
                try:
                    chunk_text = self._encoding.decode(current_chunk_tokens)
                    chunks.append(chunk_text)
                except Exception as e:
                    logger.warning(f"Error decoding final chunk: {str(e)}")
            
            logger.debug(f"Successfully created {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Text chunking failed: {str(e)}")
            # Final fallback: return the original text as a single chunk
            logger.warning("Falling back to single chunk due to chunking errors")
            return [text] if text and text.strip() else []
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using simple heuristics."""
        import re
        
        # Simple sentence splitting - can be improved with more sophisticated NLP
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _chunk_by_tokens_simple(self, tokens: List[int], max_tokens: int) -> List[str]:
        """Simple token-based chunking as fallback."""
        try:
            chunks = []
            for i in range(0, len(tokens), max_tokens):
                chunk_tokens = tokens[i:i + max_tokens]
                chunk_text = self._encoding.decode(chunk_tokens)
                chunks.append(chunk_text)
            return chunks
        except Exception as e:
            logger.error(f"Simple token chunking failed: {str(e)}")
            return []
    
    def _chunk_long_sentence(self, sentence: str, max_tokens: int) -> List[str]:
        """Chunk a sentence that's too long for the token limit with error handling."""
        try:
            if not self._encoding:
                logger.debug("No encoding available for sentence chunking, using character-based")
                return self._chunk_by_characters(sentence, max_tokens * 4)
            
            tokens = self._encoding.encode(sentence)
            chunks = []
            
            for i in range(0, len(tokens), max_tokens):
                chunk_tokens = tokens[i:i + max_tokens]
                try:
                    chunk_text = self._encoding.decode(chunk_tokens)
                    chunks.append(chunk_text)
                except Exception as e:
                    logger.warning(f"Error decoding sentence chunk: {str(e)}")
                    continue
            
            return chunks
            
        except Exception as e:
            logger.warning(f"Sentence chunking failed, using character-based fallback: {str(e)}")
            return self._chunk_by_characters(sentence, max_tokens * 4)
    
    def _chunk_by_characters(self, text: str, max_chars: int) -> List[str]:
        """Fallback method to chunk text by character count with error handling."""
        try:
            if max_chars <= 0:
                logger.warning("Invalid max_chars for character chunking, using default 1000")
                max_chars = 1000
            
            chunks = []
            for i in range(0, len(text), max_chars):
                chunk = text[i:i + max_chars]
                if chunk.strip():  # Only add non-empty chunks
                    chunks.append(chunk)
            
            logger.debug(f"Character-based chunking created {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Character-based chunking failed: {str(e)}")
            # Ultimate fallback: return original text as single chunk
            return [text] if text and text.strip() else []