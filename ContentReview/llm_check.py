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
    device = "cuda" # the device to load the model onto

    # model = AutoModelForCausalLM.from_pretrained(
    #     "qwen/Qwen1.5-0.5B-Chat",
    #     device_map="auto"
    # )
    # tokenizer = AutoTokenizer.from_pretrained("qwen/Qwen1.5-0.5B-Chat")

    # # model_path = "D:\model\Qwen\Qwen-7B-Chat"
    model_path = "D:\model\Qwen\Qwen1___5-0___5B-Chat"

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto", trust_remote_code=True).eval()

    # examples = """
    # 是否涉及违禁 | 发帖内容 | 判断理由
    # 涉及 | 我草你妈，你个狗东西 | 辱骂，包含严重的侮辱性词汇，对他人进行人身攻击，属于违禁内容。
    # 涉及 | 夫妻乱交自拍视频下载 | 色情，涉及性行为描述并鼓励传播，属于违禁内容。
    # 涉及 | 习近平下台，推翻共产党 | 涉政，带有政治攻击性，鼓动推翻政府，属于违禁内容。
    # 不涉及 | 今天的天气真好，适合外出活动。| 判断理由：内容积极向上，描述的是天气情况，与辱骂、色情或涉政无关。
    # 不涉及 | 最近学习了一些新的编程技巧，感觉很有收获。 | 判断理由：内容为正常的学习和个人成长分享，没有任何不当言论。
    # 不涉及 | 我最近在研究人工智能，感觉这个领域很有前景。 | 判断理由：内容讨论的是一个学术领域，健康积极，无任何敏感或不当信息。
    # """

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
    request_prompt = request_prompt.replace("<examples>", examples)
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
    # print("Generated text input for the model:")
    # print(text)

    model_inputs = tokenizer([text], return_tensors="pt").to(device)

    generated_ids = model.generate(
        model_inputs.input_ids,
        max_new_tokens=512
    )
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]

    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    # print("Qwen gives the response:")
    # print(response)

    if response:
        return response[0] == "是"
    return False


# """
# 涉及 | 操你妈，臭婊子 | 辱骂，语句包含强烈的侮辱性语言，违背社会公序良俗，属于违禁内容。
# 涉及 | 爆乳美少女在线直播 | 色情，语言中包含明显的色情内容，诱导观看或传播，属于违禁内容。
# 涉及 | 政府只会收税，还管什么用 | 涉政，带有明显的贬损和攻击政府的内容，属于违禁内容。
# 涉及 | 你个废物就是社会的毒瘤 | 辱骂，含有明显的人身攻击性语言，属于违禁内容。
# 涉及 | 老师居然喜欢乱搞学生 | 辱骂/色情，带有侮辱性语言且涉及性暗示内容，双重违禁内容。
# 涉及 | 讨论如何翻墙访问禁网 | 涉政，涉及规避法律的技术讨论，与涉政敏感内容相关，属于违禁内容。
# 涉及 | 全网最火的乱伦合集下载地址！ | 色情，直接传播违禁性内容，语言表述具有明显诱导性，属于违禁内容。
# 涉及 | 巨乳萝莉深喉，点击即可播放！ | 色情，内容涉及低俗和淫秽描述，属于明显的违禁内容。
# 涉及 | 现场视频，群体性派对不限观看！ | 色情，传播不良性行为内容，鼓励低俗信息，属于违禁内容。
# 涉及 | 某党政策只会害百姓，早点下台吧！ | 涉政，直接表达对党和政策的不满，具有明显的政治攻击性，属于违禁内容。
# 涉及 | 某国政府官员全是吸血鬼！ | 涉政，侮辱性言论直接指向政府官员，属于敏感内容，违禁内容。
# 涉及 | 如何组织活动推翻当局？ | 涉政，明显包含煽动性的语言，与国家稳定有关，属于违禁内容。
# 涉及 | 支持独立，分裂才有希望！ | 涉政，言论鼓动分裂，直接涉及国家主权问题，属于违禁内容。
# 涉及 | 某市领导隐瞒真相，只会欺骗群众！ | 涉政，直接对地方领导进行负面评价，具有敏感性，属于违禁内容。
# 涉及 | 你这种废物也配指责政府？滚回去看毛片吧！ | 辱骂 + 涉政 + 色情，包含对个人侮辱、政治攻击及色情暗示，属于违禁内容。
# 涉及 | 国家高层都在乱搞，怎么不下台？ | 涉政 + 色情，包含对国家领导的贬低以及不良行为的暗示，属于违禁内容。
# 涉及 | 某某党就像一群狗一样，根本没用！ | 辱骂 + 涉政，侮辱性语言指向党和政府，敏感程度较高，属于违禁内容。
# 涉及 | 快来看视频，某某市官员性丑闻曝光！ | 涉政 + 色情，包含政治人物和不良性行为的描述，具有极高敏感性，属于违禁内容。
# 涉及 | 你们这些猪脑袋也配管理国家，快滚蛋吧！ | 辱骂 + 涉政，侮辱性言辞和对国家管理层的攻击叠加，属于违禁内容。
# """