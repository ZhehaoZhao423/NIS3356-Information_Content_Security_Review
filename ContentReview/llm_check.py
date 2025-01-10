from modelscope import AutoModelForCausalLM, AutoTokenizer
import copy

PROMPT_TEMPLATE = """你将接收用户的发帖内容并分析其是否涉及辱骂、色情或涉政等违禁内容。请基于以下要求完成任务：

分析要求：
全面对比：结合参考案例，通过关键词、语义及潜在含义分析用户发帖是否涉及违禁内容。
逐步推理：详细说明你的分析过程，包括是否与参考案例存在类似模式或逻辑，但是最终输出中不要输出你的分析过程。
具体说明：明确违禁类型（辱骂、色情、涉政）及其判断理由。

下面是“参考案例”即被标注的正确结果，你需要参考这些案例来对用户发帖内容：“<input>”进行判断，其中第一项为是否涉及违禁内容的标注，第二项为参考案例的发帖内容：
<examples>

你需要进行判断的用户发帖内容为：
<input>

回复格式：只回答是或否，不要输出你的分析过程和判断理由。
是否包含违禁内容：
"""

def check(input):
    device = "cuda"

    # model = AutoModelForCausalLM.from_pretrained(
    #     "qwen/Qwen1.5-0.5B-Chat",
    #     device_map="auto"
    # )
    # tokenizer = AutoTokenizer.from_pretrained("qwen/Qwen1.5-0.5B-Chat")

    model_path = "D:\model\Qwen\Qwen-7B-Chat"

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto", trust_remote_code=True).eval()


    examples = """
    是否涉及违禁 | 发帖内容
    涉及 | 操你妈大傻逼
    涉及 | 我草你妈，你个狗东西 
    涉及 | 夫妻乱交自拍视频下载 
    涉及 | 习近平下台，推翻共产党  
    涉及 | 操你妈，臭婊子 
    涉及 | 爆乳美少女在线直播 
    涉及 | 共产党政府只会收税，还管什么用 
    涉及 | 你个废物就是社会的毒瘤 
    涉及 | 老师居然喜欢乱搞学生 
    涉及 | 讨论如何翻墙访问禁网 
    涉及 | 全网最火的乱伦合集下载地址！ 
    涉及 | 巨乳萝莉深喉，点击即可播放！ 
    涉及 | 现场视频，群体性派对不限观看！ 
    涉及 | 共产党政策只会害百姓，早点下台吧！ 
    涉及 | 中国政府官员全是吸血鬼！ 
    涉及 | 如何组织活动推翻中国共产党当局？ 
    涉及 | 支持台湾独立、新疆独立、西藏独立，分裂才有希望！ 
    涉及 | 上海市领导隐瞒真相，只会欺骗群众！ 
    涉及 | 国家高层都在乱搞，怎么不下台？ 
    涉及 | 某某党就像一群狗一样，根本没用！ 
    涉及 | 快来看视频，北京市官员性丑闻曝光！ 
    涉及 | 你们这些猪逼也配管理国家，快滚蛋吧！ 
    """

    # input = "大学生要认真学习"

    request_prompt= copy.deepcopy(PROMPT_TEMPLATE)
    # request_prompt = request_prompt.replace("<examples>", examples)
    request_prompt = request_prompt.replace("<input>", input)

    # prompt = "请用简短的语言介绍一下大型语言模型。"
    messages = [
        {"role": "system", "content": "你是一个专业的内容审核专家，能够高效、准确地判断用户发帖内容是否涉及辱骂、色情、涉政等违禁内容。你的判断需要基于严格的分析和案例对比，确保结果具有一致性和解释性。"},
        {"role": "user", "content": request_prompt},
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    print("Generated text input for the model:")
    print(text)

    model_inputs = tokenizer([text], return_tensors="pt").to(device)

    generated_ids = model.generate(
        model_inputs.input_ids,
        max_new_tokens=512
    )
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    print("Qwen gives the response:")
    print(response)

    if response:
        return response[0] == "是"
    return False

