"""
Search utilities for advanced filtering
"""
from sqlalchemy import or_, and_
from datetime import datetime, timedelta


class SearchFilter:
    """Advanced search filter builder"""
    
    def __init__(self, model):
        """
        Initialize search filter
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model
        self.filters = []
    
    def add_text_search(self, columns, search_term):
        """
        Add text search across multiple columns
        
        Args:
            columns: List of column objects to search
            search_term: Search text
        """
        if search_term:
            conditions = [col.ilike(f'%{search_term}%') for col in columns]
            self.filters.append(or_(*conditions))
        return self
    
    def add_exact_match(self, column, value):
        """Add exact match filter"""
        if value is not None:
            self.filters.append(column == value)
        return self
    
    def add_in_filter(self, column, values):
        """Add IN filter for multiple values"""
        if values:
            self.filters.append(column.in_(values))
        return self
    
    def add_range_filter(self, column, min_value=None, max_value=None):
        """Add range filter (between min and max)"""
        if min_value is not None:
            self.filters.append(column >= min_value)
        if max_value is not None:
            self.filters.append(column <= max_value)
        return self
    
    def add_date_range(self, column, start_date=None, end_date=None):
        """Add date range filter"""
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            self.filters.append(column >= start_date)
        
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            # Add one day to include the end date
            end_date = end_date + timedelta(days=1)
            self.filters.append(column < end_date)
        return self
    
    def add_boolean_filter(self, column, value):
        """Add boolean filter"""
        if value is not None:
            if isinstance(value, str):
                value = value.lower() in ['true', '1', 'yes']
            self.filters.append(column == value)
        return self
    
    def build(self, base_query):
        """
        Build query with all filters applied
        
        Args:
            base_query: Base SQLAlchemy query
        
        Returns:
            Filtered query
        """
        if self.filters:
            return base_query.filter(and_(*self.filters))
        return base_query


def parse_sort_params(allowed_columns, default_column='created_at', default_order='desc'):
    """
    Parse sort parameters from request
    
    Args:
        allowed_columns: Dict of {param_name: column_object}
        default_column: Default column name
        default_order: Default order ('asc' or 'desc')
    
    Returns:
        Tuple of (column_object, order)
    """
    from flask import request
    
    sort_by = request.args.get('sort_by', default_column)
    sort_order = request.args.get('sort_order', default_order).lower()
    
    # Validate sort column
    if sort_by not in allowed_columns:
        sort_by = default_column
    
    # Validate sort order
    if sort_order not in ['asc', 'desc']:
        sort_order = default_order
    
    column = allowed_columns[sort_by]
    
    return column, sort_order


def apply_sorting(query, column, order='asc'):
    """
    Apply sorting to query
    
    Args:
        query: SQLAlchemy query
        column: Column to sort by
        order: Sort order ('asc' or 'desc')
    
    Returns:
        Sorted query
    """
    if order == 'desc':
        return query.order_by(column.desc())
    return query.order_by(column.asc())
