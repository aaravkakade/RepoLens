from app.parser import chunk_python_source


def test_top_level_function_produces_one_function_chunk():
    source = '''def greet():
    return "hi"
'''
    chunks = chunk_python_source(source, "example.py")

    assert len(chunks) == 1
    assert chunks[0].name == "greet"
    assert chunks[0].kind == "function"
    assert chunks[0].parent_class is None
    assert chunks[0].file_path == "example.py"


def test_class_with_two_methods_produces_class_and_method_chunks():
    source = '''class Widget:
    """A widget."""
    x = 1

    def alpha(self):
        pass

    def beta(self):
        pass
'''
    chunks = chunk_python_source(source, "widget.py")

    class_chunks = [c for c in chunks if c.kind == "class"]
    method_chunks = [c for c in chunks if c.kind == "method"]

    assert len(class_chunks) == 1
    assert len(method_chunks) == 2
    assert class_chunks[0].name == "Widget"
    assert class_chunks[0].parent_class is None

    method_names = {chunk.name for chunk in method_chunks}
    assert method_names == {"alpha", "beta"}
    assert all(chunk.parent_class == "Widget" for chunk in method_chunks)


def test_class_with_no_methods_produces_only_class_chunk():
    source = '''class Empty:
    """No methods here."""
    value = 42
'''
    chunks = chunk_python_source(source, "empty.py")

    assert len(chunks) == 1
    assert chunks[0].kind == "class"
    assert chunks[0].name == "Empty"
    assert not any(chunk.kind == "method" for chunk in chunks)


def test_async_function_chunked_as_function():
    source = '''async def fetch():
    return await thing()
'''
    chunks = chunk_python_source(source, "async_example.py")

    assert len(chunks) == 1
    assert chunks[0].name == "fetch"
    assert chunks[0].kind == "function"
    assert chunks[0].parent_class is None


def test_line_numbers_and_source_slice_for_top_level_function():
    source = '''def add(a, b):
    """Add two numbers."""
    return a + b
'''
    chunks = chunk_python_source(source, "math.py")
    chunk = chunks[0]

    assert chunk.start_line == 1
    assert chunk.end_line == 3
    assert chunk.source == source.rstrip("\n")


def test_class_header_ends_before_first_method_line():
    source = '''class Counter:
    """Counts things."""
    total = 0

    def increment(self):
        self.total += 1
'''
    chunks = chunk_python_source(source, "counter.py")
    class_chunk = next(chunk for chunk in chunks if chunk.kind == "class")
    method_chunk = next(chunk for chunk in chunks if chunk.kind == "method")

    assert class_chunk.start_line == 1
    assert class_chunk.end_line == 4
    assert method_chunk.start_line == 5
    assert method_chunk.end_line == 6
    assert "def increment" not in class_chunk.source
    assert "def increment" in method_chunk.source
