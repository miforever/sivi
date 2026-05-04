"""Pagination classes."""

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """
    Standard pagination with page size parameter.
    """

    page_size = 20
    page_size_query_param = "page_size"
    page_size_query_description = "Number of results to return per page."
    max_page_size = 100
    page_query_param = "page"
    page_query_description = "Page number."

    def get_paginated_response(self, data):
        """
        Return paginated response with custom envelope.
        """
        from rest_framework.response import Response

        return Response(
            {
                "success": True,
                "data": data,
                "meta": {
                    "page": self.page.number,
                    "page_size": self.page_size,
                    "total": self.page.paginator.count,
                    "total_pages": self.page.paginator.num_pages,
                },
            }
        )
