import re
from django.core.exceptions import ValidationError

def validate_listing_title(value):
    """
    Comprehensive validation for listing titles
    """
    value = value.strip()
    
    # Length validation
    if len(value) < 3:
        raise ValidationError('Title must be at least 3 characters long.')
    
    if len(value) > 200:
        raise ValidationError('Title cannot exceed 200 characters.')
    
    # Character validation
    if not re.match(r'^[\w\s\-\.,!?\'"@#$%&*()+=:;/\\]+$', value):
        raise ValidationError(
            'Title can only contain letters, numbers, spaces, and common punctuation marks.'
        )
    
    # Check for excessive capitalization (shouting)
    uppercase_words = re.findall(r'\b[A-Z]{3,}\b', value)
    if len(uppercase_words) > 2:
        raise ValidationError('Please avoid excessive capitalization in the title.')
    
    # Check for repetitive characters
    if re.search(r'(.)\1{3,}', value):  # 4 or more repeated characters
        raise ValidationError('Title contains repetitive characters.')
    
    # Check for URL-like patterns
    if re.search(r'https?://|www\.|\.(com|org|net)', value, re.IGNORECASE):
        raise ValidationError('Title should not contain URLs or website addresses.')
    
    return value