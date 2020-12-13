from movie_search import OkkoSearcher, BaseSearcher


def get_platform_searcher(platform: str) -> BaseSearcher:
    """Get searcher from string"""
    if platform == 'Ökko':
        return OkkoSearcher()
    else:  # TODO: add another platforms
        return OkkoSearcher()
