"""
Configuration management for Supabase vector indexing functionality.

This module handles loading and validating environment variables required
for Supabase vector database integration.
"""

import os
import logging
from typing import Optional, List
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class VectorIndexingConfig:
    """Configuration class for Supabase vector indexing settings."""
    
    supabase_url: str
    supabase_anon_key: str
    table_name: str = "documents"
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    
    @classmethod
    def from_environment(cls) -> Optional['VectorIndexingConfig']:
        """
        Load configuration from environment variables with comprehensive error handling.
        
        Returns:
            VectorIndexingConfig instance if required variables are present,
            None if required configuration is missing.
        """
        logger.debug("Loading vector indexing configuration from environment variables")
        
        # Check for required environment variables
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        # Validate required configuration
        missing_vars = []
        if not supabase_url:
            missing_vars.append('SUPABASE_URL')
        if not supabase_anon_key:
            missing_vars.append('SUPABASE_ANON_KEY')
        
        if missing_vars:
            logger.info(f"Vector indexing disabled: Missing required environment variables: {', '.join(missing_vars)}")
            logger.debug("To enable vector indexing, set the following environment variables:")
            for var in missing_vars:
                logger.debug(f"  - {var}")
            return None
        
        # Validate URL format
        if not cls._is_valid_url(supabase_url):
            logger.warning(f"Vector indexing disabled: Invalid SUPABASE_URL format: {supabase_url}")
            return None
        
        # Validate API key format
        if not cls._is_valid_api_key(supabase_anon_key):
            logger.warning("Vector indexing disabled: Invalid SUPABASE_ANON_KEY format")
            return None
        
        # Load optional configuration with defaults
        table_name = os.getenv('SUPABASE_TABLE_NAME', 'documents')
        embedding_provider = os.getenv('EMBEDDING_PROVIDER', 'openai')
        embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        
        # Validate optional configuration
        if not cls._is_valid_table_name(table_name):
            logger.warning(f"Invalid table name '{table_name}', using default 'documents'")
            table_name = 'documents'
        
        if not cls._is_valid_embedding_provider(embedding_provider):
            logger.warning(f"Unsupported embedding provider '{embedding_provider}', using default 'openai'")
            embedding_provider = 'openai'
        
        config = cls(
            supabase_url=supabase_url,
            supabase_anon_key=supabase_anon_key,
            table_name=table_name,
            embedding_provider=embedding_provider,
            embedding_model=embedding_model
        )
        
        logger.info("Vector indexing configuration loaded successfully")
        logger.debug(f"Configuration: {config}")
        
        return config
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Validate Supabase URL format."""
        if not url:
            return False
        return url.startswith('https://') and '.supabase.co' in url
    
    @staticmethod
    def _is_valid_api_key(key: str) -> bool:
        """Validate Supabase API key format."""
        if not key:
            return False
        # Basic validation - should be a long string
        return len(key) > 50 and key.replace('-', '').replace('_', '').replace('.', '').isalnum()
    
    @staticmethod
    def _is_valid_table_name(name: str) -> bool:
        """Validate table name format."""
        if not name:
            return False
        # Basic SQL identifier validation
        return name.replace('_', '').isalnum() and not name[0].isdigit()
    
    @staticmethod
    def _is_valid_embedding_provider(provider: str) -> bool:
        """Validate embedding provider."""
        supported_providers = ['openai']
        return provider in supported_providers
    
    def is_valid(self) -> bool:
        """
        Validate that all required configuration fields are present and properly formatted.
        
        Returns:
            True if configuration is valid, False otherwise.
        """
        validation_errors = self.get_validation_errors()
        
        if validation_errors:
            logger.error("Vector indexing configuration validation failed:")
            for error in validation_errors:
                logger.error(f"  - {error}")
            return False
        
        logger.debug("Vector indexing configuration validation passed")
        return True
    
    def get_validation_errors(self) -> List[str]:
        """
        Get a list of validation errors for the current configuration.
        
        Returns:
            List of validation error messages.
        """
        errors = []
        
        if not self.supabase_url:
            errors.append("SUPABASE_URL is empty")
        elif not self._is_valid_url(self.supabase_url):
            errors.append(f"SUPABASE_URL has invalid format: {self.supabase_url}")
        
        if not self.supabase_anon_key:
            errors.append("SUPABASE_ANON_KEY is empty")
        elif not self._is_valid_api_key(self.supabase_anon_key):
            errors.append("SUPABASE_ANON_KEY has invalid format")
        
        if not self.table_name:
            errors.append("Table name is empty")
        elif not self._is_valid_table_name(self.table_name):
            errors.append(f"Table name has invalid format: {self.table_name}")
        
        if not self.embedding_provider:
            errors.append("Embedding provider is empty")
        elif not self._is_valid_embedding_provider(self.embedding_provider):
            errors.append(f"Unsupported embedding provider: {self.embedding_provider}")
        
        if not self.embedding_model:
            errors.append("Embedding model is empty")
        
        return errors
    
    def check_embedding_service_availability(self) -> bool:
        """
        Check if the configured embedding service is available.
        
        Returns:
            True if embedding service is available, False otherwise.
        """
        try:
            if self.embedding_provider == "openai":
                openai_key = os.getenv('OPENAI_API_KEY')
                if not openai_key:
                    logger.warning("Vector indexing: OpenAI API key not found in environment variables")
                    return False
                
                # Basic validation of OpenAI API key format
                if not openai_key.startswith('sk-') or len(openai_key) < 20:
                    logger.warning("Vector indexing: Invalid OpenAI API key format")
                    return False
                
                logger.debug("OpenAI embedding service configuration appears valid")
                return True
            else:
                logger.error(f"Unsupported embedding provider: {self.embedding_provider}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking embedding service availability: {str(e)}")
            return False
    
    def __str__(self) -> str:
        """String representation with masked sensitive data."""
        masked_key = f"{self.supabase_anon_key[:8]}..." if len(self.supabase_anon_key) > 8 else "***"
        return (
            f"VectorIndexingConfig("
            f"url={self.supabase_url}, "
            f"key={masked_key}, "
            f"table={self.table_name}, "
            f"provider={self.embedding_provider}, "
            f"model={self.embedding_model})"
        )