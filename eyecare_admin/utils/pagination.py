"""
Pagination utility for API responses
"""
from flask import request, url_for
from math import ceil


class Pagination:
    """Pagination helper class"""
    
    def __init__(self, query, page=None, per_page=None, total=None, items=None):
        """
        Initialize pagination
        
        Args:
            query: SQLAlchemy query object
            page: Current page number (1-indexed)
            per_page: Items per page
            total: Total number of items (optional, will be calculated from query)
            items: List of items (optional, will be fetched from query)
        """
        self.query = query
        self.page = page or self._get_page()
        self.per_page = per_page or self._get_per_page()
        self.total = total if total is not None else query.count()
        self.items = items if items is not None else self._get_items()
        self.pages = ceil(self.total / self.per_page) if self.per_page > 0 else 0
    
    def _get_page(self):
        """Get page number from request"""
        try:
            page = request.args.get('page', 1, type=int)
            return max(1, page)
        except:
            return 1
    
    def _get_per_page(self):
        """Get per_page from request, with max limit"""
        try:
            per_page = request.args.get('per_page', 20, type=int)
            return min(max(1, per_page), 100)  # Between 1 and 100
        except:
            return 20
    
    def _get_items(self):
        """Fetch items for current page"""
        offset = (self.page - 1) * self.per_page
        return self.query.limit(self.per_page).offset(offset).all()
    
    @property
    def has_prev(self):
        """Check if there's a previous page"""
        return self.page > 1
    
    @property
    def has_next(self):
        """Check if there's a next page"""
        return self.page < self.pages
    
    @property
    def prev_page(self):
        """Get previous page number"""
        return self.page - 1 if self.has_prev else None
    
    @property
    def next_page(self):
        """Get next page number"""
        return self.page + 1 if self.has_next else None
    
    def to_dict(self, endpoint=None, **kwargs):
        """
        Convert pagination to dictionary for JSON response
        
        Args:
            endpoint: Flask endpoint name for generating URLs
            **kwargs: Additional URL parameters
        """
        data = {
            'page': self.page,
            'per_page': self.per_page,
            'total': self.total,
            'pages': self.pages,
            'has_prev': self.has_prev,
            'has_next': self.has_next,
            'prev_page': self.prev_page,
            'next_page': self.next_page
        }
        
        if endpoint:
            data['links'] = {
                'self': self._get_url(endpoint, self.page, **kwargs),
                'first': self._get_url(endpoint, 1, **kwargs),
                'last': self._get_url(endpoint, self.pages, **kwargs)
            }
            
            if self.has_prev:
                data['links']['prev'] = self._get_url(endpoint, self.prev_page, **kwargs)
            
            if self.has_next:
                data['links']['next'] = self._get_url(endpoint, self.next_page, **kwargs)
        
        return data
    
    def _get_url(self, endpoint, page, **kwargs):
        """Generate URL for pagination link"""
        try:
            return url_for(endpoint, page=page, per_page=self.per_page, _external=True, **kwargs)
        except:
            return None


def paginate(query, page=None, per_page=None):
    """
    Convenience function to paginate a query
    
    Args:
        query: SQLAlchemy query
        page: Page number (optional, reads from request)
        per_page: Items per page (optional, reads from request)
    
    Returns:
        Pagination object
    """
    return Pagination(query, page=page, per_page=per_page)
