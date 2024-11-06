from models.llama import Llama


def test_llama():
    llama = Llama()
    llama.set_parameters({"model_name": "llama-3.1-8b", "precision": "bfloat16"})
    llama.load_model()

    results_stream = llama.run(iter([
        {"x": "bear", "query": "What is the best kind of bear? Only say its name."},
        {"x": "toad", "query": "What is the best kind of toad? Only say its name."}
    ]))

    results = list(results_stream)

    assert results[0]["x"] == "bear"
    assert results[0]["query"] == "What is the best kind of bear? Only say its name."
    assert results[0]["responses"]
    assert results[0]["question number"] == 0
    assert results[0]["top tokens"]
    assert results[0]["top tokens logprobs"]
    assert results[0]["input token count"] == 14
    assert results[0]["output token count"]

    assert results[1]["x"] == "toad"
    assert results[1]["query"] == "What is the best kind of toad? Only say its name."
    assert results[1]["responses"]
    assert results[1]["question number"] == 1
    assert results[1]["top tokens"]
    assert results[1]["top tokens logprobs"]
    assert results[1]["input token count"] == 15
    assert results[1]["output token count"]
