from args import Params
from models.llama import Llama


def test_llama():
    llama = Llama(Params(model_name="llama-3.2-1b-instruct", precision="float16"))
    llama.load_model()

    results_stream = llama.run(iter([
        {"creature": "bear", "prompt": "What is the best kind of bear? Only say its name."},
        {"creature": "toad", "prompt": "What is the best kind of toad? Only say its name."}
    ]))

    results = list(results_stream)
    assert len(results) == 2

    result = results[0]
    assert result["creature"] == "bear"
    assert result["prompt"] == "What is the best kind of bear? Only say its name."
    assert len(result["top_tokens"]) == 5
    assert len(result["top_tokens_logprobs"]) == 5

    assert list(result.keys()) == [
        "creature", "prompt", "responses", "top_tokens", "top_tokens_logprobs", "input_token_count", "output_token_count"
    ]

    result = results[1]
    assert result["creature"] == "toad"
    assert result["prompt"] == "What is the best kind of toad? Only say its name."
    assert len(result["top_tokens"]) == 5
    assert len(result["top_tokens_logprobs"]) == 5

    assert list(result.keys()) == [
        "creature", "prompt", "responses", "top_tokens", "top_tokens_logprobs", "input_token_count", "output_token_count"
    ]


def test_llama_batch():
    llama = Llama(Params(model_name="llama-3.2-1b-instruct",
                  precision="float16", batch_size=5))
    llama.load_model()
    queries = [
        {"genus": "Neoechinorhynchus", "specificepithet": "lingulatus", "country": "United States", "stateprovince": "Florida",
            "county": "Hillsborough County", "prompt": "Does Neoechinorhynchus lingulatus naturally occur in Hillsborough County, Florida, United States?"},
        {"genus": "Neoechinorhynchus", "specificepithet": "robertbaueri", "country": "United States", "stateprovince": "Wisconsin",
            "county": "Kenosha County", "prompt": "Does Neoechinorhynchus robertbaueri naturally occur in Kenosha County, Wisconsin, United States?"},
        {"genus": "Neoechinorhynchus", "specificepithet": "chrysemydis", "country": "United States", "stateprovince": "Alabama",
            "county": "Tallapoosa County", "prompt": "Does Neoechinorhynchus chrysemydis naturally occur in Tallapoosa County, Alabama, United States?"},
        {"genus": "Neoechinorhynchus", "specificepithet": "prolixoides", "country": "United States", "stateprovince": "Wisconsin",
            "county": "Kenosha County", "prompt": "Does Neoechinorhynchus prolixoides naturally occur in Kenosha County, Wisconsin, United States?"},
        {"genus": "Octospiniferoides", "specificepithet": "chandleri", "country": "Mexico", "stateprovince": "Quintana Roo",
            "county": "Solidaridad", "prompt": "Does Octospiniferoides chandleri naturally occur in Solidaridad, Quintana Roo, Mexico?"},
        {"genus": "Atactorhynchus", "specificepithet": "duranguensis", "country": "Mexico", "stateprovince": "Durango",
            "county": "Durango", "prompt": "Does Atactorhynchus duranguensis naturally occur in Durango, Durango, Mexico?"},
        {"genus": "Paulisentis", "specificepithet": "fractu", "country": "United States", "stateprovince": "Ohio",
            "county": "Wayne County", "prompt": "Does Paulisentis fractu naturally occur in Wayne County, Ohio, United States?"},
        {"genus": "Octospinifer", "specificepithet": "torosu", "country": "United States", "stateprovince": "California",
            "county": "Lake County", "prompt": "Does Octospinifer torosu naturally occur in Lake County, California, United States?"},
        {"genus": "Neoechinorhynchus", "specificepithet": "pungitius", "country": "United States",
            "stateprovince": "Wisconsin (State)", "county": "Barron Co.", "prompt": "Does Neoechinorhynchus pungitius naturally occur in Barron Co., Wisconsin (State), United States?"},
        {"genus": "Neoechinorhynchus", "specificepithet": "rutili", "country": "Canada",
            "stateprovince": "British Columbia (Prov.)", "county": "Cariboo Land Distr.", "prompt": "Does Neoechinorhynchus rutili naturally occur in Cariboo Land Distr., British Columbia (Prov.), Canada?"}
    ]
    results_stream = llama.run(iter(queries))
    results_1 = list(results_stream)
    results_stream = llama.run(iter(queries))
    results_2 = list(results_stream)

    assert len(results_1) == len(queries)
    assert len(results_2) == len(queries)
    assert results_1 == results_2
