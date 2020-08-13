import os
import re
from pathlib import Path


def func_path_normalizer(path):
    return str(path)
def add_sink(app, prefix, resource, func_path_normalizer=func_path_normalizer):
    def _sink(request, response):
        path = func_path_normalizer(Path(re.sub(f'^/{prefix}/', '', request.path)))
        if not path:
            return resource.on_index(request, response)
        return getattr(resource, f'on_{request.method.lower()}')(request, response, path)
    app.add_sink(_sink, prefix=f'/{prefix}/')

def func_path_normalizer_no_extension(path):
    return os.path.join(str(path.parent), path.stem).strip('./')
