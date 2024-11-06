from models.llama import Llama


def test_llama():
    llama = Llama()
    llama.set_parameters({"model_name": "llama-3.1-8b", "precision": "float8"})
    llama.load_model()

    results_stream = llama.run(iter([
        {"x": "bear", "query": "What is the best kind of bear? Only say its name."},
        {"x": "toad", "query": "What is the best kind of toad? Only say its name."}
    ]))

    results = list(results_stream)

    assert len(results) == 2

    result = results[0]
    assert result["x"] == "bear"
    assert result["query"] == "What is the best kind of bear? Only say its name."
    assert result["question number"] == 0
    assert result["input token count"] == 14
    assert len(result["top tokens"]) == 5
    assert len(result["top tokens logprobs"]) == 5

    assert list(result.keys()) == [
        "x", "query", "question number", "input", "responses", "top tokens", "top tokens logprobs", "input token count", "output token count"
    ]

    result = results[1]
    assert result["x"] == "toad"
    assert result["query"] == "What is the best kind of toad? Only say its name."
    assert result["question number"] == 1
    assert result["input token count"] == 15
    assert len(result["top tokens"]) == 5
    assert len(result["top tokens logprobs"]) == 5

    assert list(result.keys()) == [
        "x", "query", "question number", "input", "responses", "top tokens", "top tokens logprobs", "input token count", "output token count"
    ]
