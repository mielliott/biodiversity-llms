# from transformers import T5Tokenizer, T5ForConditionalGeneration
# from torch.nn.functional import softmax

# def prep_local_model():
#     global tokenizer, model, qa
#     tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-xxl")
#     model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-xxl", device_map="auto")

#     def qa(question):
#         i = tokenizer(question, return_tensors="pt", padding=True).input_ids.to("cuda")
#         o = model.generate(i, max_new_tokens=200, return_dict_in_generate=True, output_scores=True)
#         print(tokenizer.decode(o.sequences[0], skip_special_tokens=True))

# def run_local_model():
#     print("response", "tokens", "log scores", "softmax scores", sep="\t")

#     batch_size = 4
#     for batch in batched(questions, batch_size):
#         i = tokenizer(batch, return_tensors="pt", padding=True).input_ids.to("cuda")
#         o = model.generate(i, max_new_tokens=20, return_dict_in_generate=True, output_scores=True)
        
#         for iseq, seq in enumerate(o.sequences):
#             response = seq[1:-1]
#             log_scores = [o.scores[it][iseq][t] for it, t in enumerate(response)]
#             softmax_scores = [softmax(o.scores[it][iseq], dim=0)[t] for it, t in enumerate(response)]

#             print(tokenizer.decode(response),
#                 " ".join([str(id) for id in response.tolist()]),
#                 " ".join(["{:.3f}".format(score.tolist()) for score in log_scores]),
#                 " ".join(["{:.3f}".format(score.tolist()) for score in softmax_scores]),
#                 sep="\t",
=#                 flush=True)
