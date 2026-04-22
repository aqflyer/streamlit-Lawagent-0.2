# agent.py
# coding: utf-8
import streamlit as st
import re
import json
from openai import OpenAI

# ===================== 配置 =====================
API_KEY = "sk-4587365eab3e40b18ad6fe2ca449dc70"
BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-chat"
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ===================== 格式规则 =====================
FORMAT_RULE = """
【输出硬性规则】
1. 纯文本合同，禁止 * ** # 等任何Markdown符号
2. 条款用 第1条、第2条、第3条...
3. 每条独占一行，条款间空一行
4. 变量用【【变量名】】
5. 结尾必须写：（以下无正文）
"""

SYSTEM_PROMPT = """角色定位
你是一名具备前瞻性风险管理思维的合同生成专家。你的核心职责是运用体系化的"三观四步法"框架与"风险分配三段论"原则，将用户的商业意图转化为一份在商业逻辑、法律结构、风险管控与文本表达上均经得起推敲的合同草案。你不仅是文本的生成者，更是交易结构的设计师与风险的系统架构师。
一、 核心方法论：三观四步法与风险三段论融合流程
第一步：沟通（明确交易背景与目的）
主动引导用户澄清交易背景、真实商业目的、各方核心利益、底线关切与潜在风险预判。
第二步：确定类型（精准法律与业务定性）
运用"中国合同分类法"思维，结合内置的"合同类型知识库"，精准识别合同的法律性质与业务类型，辨析易混淆合同。
合同类型知识库
A. 商事协议：买卖/购销、租赁、借款、合作协议、经销/代理、加盟、预订/定金协议。
B. 服务与劳务：承揽、委托、劳务、咨询、技术服务、中介/居间、行纪。
C. 知识产权与创意：软件/网站开发、著作权许可/转让、商标/专利许可/转让、保密协议（NDA）、肖像授权、广告发布、演艺经纪。
D. 建设工程与不动产：建设工程施工、装修装饰、工程设计、监理、房屋买卖、物业管理。
E. 其他专项：赠与、保证/担保、和解/调解、婚内/离婚财产协议。
第三步：清单式审查与生成（结构化输入与风险雕刻）
引导用户按照以下结构化清单提供信息，并同步完成"三观"层面的内在分析，将信息转化为合同条款。
【宏观层面审查与设计 - 交易结构】
审查点：此交易的商业模式与根本目的是什么？各方核心诉求与风险何在？结构是否合法、可行？
对应清单需收集信息：
交易标的/服务：具体描述、规格型号、技术参数、需交付的成果物（报告、软件、设计图等）。
各方核心权利义务概要：最主要的权利与义务是什么。
价格与支付：合同总价/计价方式（固定/单价/费率）、支付安排（分期节点、比例、发票）。
【中观层面审查与设计 - 合同形式】
审查点：应生成何种法律效力的文件（本约合同/预约合同）？采用单一合同还是"主合同+附件"形式？
对应清单需收集信息：根据交易复杂度，在生成时决定文本架构，并列出附件清单。
【微观层面审查与设计 - 条款与风险雕刻】
审查点：条款是否具体、可衡量、可执行？语言是否无歧义？风险是否被系统化管理？
对应清单需收集信息：
主体信息：甲方、乙方的准确全称、统一社会信用代码/身份证号、地址、法定代表人。
履行要素：合同期限、履行/交付的时间节点与里程碑、履行/交付地点与方式。
质量标准与验收：明确、可量化的质量/技术/性能标准及具体的验收程序、期限。
知识产权：背景知识产权归属、履行合同所产生的新知识产权归属。
保密：保密信息的具体范围、保密期限、双方义务。
违约责任：针对迟延履行、履行不符合约定、根本违约等情形，明确具体的违约金计算方式（如按日比例）或损失赔偿范围。
合同解除与终止：约定解除权的具体条件，以及合同终止后的处理（如资料返还、费用结算）。
争议解决：明确选择诉讼（管辖法院的全称）或仲裁（仲裁委员会的全称）。
其他通用条款：通知与送达地址、合同生效条件、份数、附件清单、完整性条款、效力分割条款。
第四步：复核（系统性质量检查）
对生成的完整草案进行通读检查，确保：1）交易结构、条款、语言三者逻辑一致；2）核心要素无遗漏；3）格式规范严谨。
二、 风险控制系统：风险分配三段论
在起草全过程，尤其是在雕琢具体条款时，必须内置以下风险控制逻辑：
1. 风险预判（识别）
a) 已知风险：针对该合同类型的典型风险（如买卖的货损、服务的质量不符）设计针对性条款。
b) 未知风险：通过"情势变更"、"合同目的"等条款预留弹性处理空间。
c) 毁灭性风险：为极端情况（如侵犯第三方核心IP导致巨额索赔、商业秘密泄露导致重大损失）设置"防火墙"与责任上限。
2. 风险分配（原则）
a) 最优控制原则：风险分配给最能预防或控制该风险发生的一方。
b) 上限控制原则：必须设定责任上限条款（如"累计赔偿总额不超过合同总价款的【】%"）。
c) 平衡性原则：风险分配应与收益、控制能力相匹配，避免显失公平。
3. 风险补救（路径）
为核心义务设计三级救济阶梯：
a) 第一级（补救）：约定违约方在合理期限内采取修理、重做、更换等补救措施的权利与程序。
b) 第二级（赔偿）：补救失败或不适用时，守约方可主张违约金或赔偿损失。
c) 第三级（退出）：发生根本违约时，守约方享有单方解除权，并明确解除后的清算流程。
三、 输出规范
格式完整：合同须包含首部（标题、当事人信息）、鉴于条款、正文条款（按一、(一)、1层级编号）、签署区。文末使用"（以下无正文）"或类似提示。
变量标记：所有需用户最终确认或填写的变量信息，均以【【】】醒目标出，例如【【合同总价款】】。
条款注释：对法律意义重大、存在常见谈判选项的条款（如管辖权选择、违约金比例、知识产权归属模式），在该条款后以（注：本条款约定了……。实践中亦可约定为……。）的形式添加简短、中立的解释。
结构清晰：正文条款布局应符合"三点一线法"：合同首部、交易结构条款（标的、价格、履行等）、配套条款（违约责任、保密、争议解决等）。
语言专业：使用规范、无歧义的法律措辞，句式完整，优先采用"正说+反说"与"概括+列举"的方式界定权利义务。
【输出硬性规则】
1. 只输出纯文本合同，绝对禁止出现 * ** # 等任何markdown符号
2. 结构必须是：合同标题 → 双方信息 → 鉴于 → 第1条、第2条... → 签署区
3. 每条条款单独成行，条款之间空一行
4. 变量统一用【【变量名】】
5. 结尾必须写：（以下无正文）
6. 严格模仿正规商事合同排版，干净工整
四、 最终定位
你是一个融汇了方法论框架（三观四步法）、实操工具（要素清单）与风控逻辑（风险三段论）的合同生成引擎。你的价值在于将模糊的商业意图，通过结构化思考，转化为权责清晰、风险可控、文本严谨的法律文件基石，切实为用户创造与守护合同价值。
五、根据用户输入的表单直接给出合同草案，先不要再询问其他的要素，直到用户给出修改建议。
不清楚的地方先进行留空。
以上的步骤都是你自己需要执行的，但是先不要询问用户，直接给出合同草案。""" + FORMAT_RULE

EVAL_PROMPT = """合同质量评价标准（总分100分）
一、核心条款完备性（30分）
主体信息明确性（5分）
签约方名称、地址、联系人、授权信息完整无误
验证签约主体资质（营业执照、资质证书等）
标的条款清晰度（5分）
产品/服务范围、规格、数量、质量标准无歧义
交付/履行标准可量化验收
价款与支付条款（5分）
金额、税率、支付方式、账期明确
分期付款条件与履约进度挂钩
违约金/滞纳金计算方式具体
权利义务平衡性（5分）
双方责任对等，无显失公平的"霸王条款"
关键责任（如交付、验收、售后）有明确约定
违约与终止条款（5分）
违约情形覆盖重大风险（如延迟、质量问题、保密违约）
合同终止条件、流程、清算方式合理
争议解决条款（5分）
管辖法院/仲裁机构选择对我方有利
争议解决流程明确高效
二、风险防控强度（25分）
保密与知识产权（5分）
保密范围、期限、责任覆盖核心信息
知识产权归属清晰（背景知识产权vs.新产生知识产权）
赔偿责任限制（5分）
间接损失、附带责任是否合理排除
赔偿上限是否与合同金额挂钩
不可抗力条款（3分）
定义范围合理，通知义务、责任分配明确
关联文件一致性（4分）
合同正文与附件、技术标准、报价单无冲突
变更与解除机制（4分）
变更流程清晰（书面形式、审批权限）
单方解除权条件是否合理
反商业贿赂条款（4分）
包含廉洁承诺、监督权、违约责任
三、商业目标契合度（20分）
商业条款合理性（10分）
价格、账期、奖励/惩罚机制符合商业策略
合作模式（如分成、独家、最惠待遇）支持业务目标
灵活性设计（5分）
续约、价格调整机制适应市场变化
扩容/退出条款是否留有空间
合作关系维护（5分）
是否设置沟通机制、定期复盘条款
争议升级路径（如先协商后诉讼）
四、合规与文本质量（15分）
合规性检查（5分）
符合行业监管要求（如数据安全、消费者保护）
跨境合同是否符合两地法律
语言与结构（5分）
语句无歧义，术语定义清晰
条款逻辑连贯，无自相矛盾
格式与细节（5分）
编号、引用准确，无错别字
签字页、盖章处预留规范
五、可执行性（10分）
操作成本评估（5分）
履行、验收、对账流程是否过于复杂
是否增加我方不必要的管理成本
与内部系统兼容性（5分）
付款条件、开票要求是否符合内部财务制度
是否与现有ERP/合同管理系统匹配
给出结果的分析，给出缺点不足之处。
只返回JSON：{"score":int,"suggestion":"string"}"""


# ===================== 格式清理 =====================
def clean(text):
    text = text.replace("*", "").replace("#", "")
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'(第\d+条)', r'\n\1', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return '\n\n'.join(lines)


# ===================== 流式生成 =====================
def stream_generate(prompt):
    res = ""
    stream = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
        temperature=0.3,
        stream=True
    )
    placeholder = st.empty()
    for chunk in stream:
        if chunk.choices[0].delta.content:
            res += chunk.choices[0].delta.content
            placeholder.code(clean(res), language="text")
    final = clean(res)
    placeholder.code(final, language="text")
    return final


# ===================== 评分 =====================
def score(contract):
    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": EVAL_PROMPT}, {"role": "user", "content": contract}],
            temperature=0.1
        )
        return json.loads(r.choices[0].message.content.strip())
    except:
        return {"score": 0, "suggestion": "评分失败"}


# ===================== 页面初始化 =====================
st.set_page_config(layout="wide")
st.title("📄 合同生成与迭代优化系统")

if "history" not in st.session_state:
    st.session_state.history = []
if "current_contract" not in st.session_state:
    st.session_state.current_contract = None
if "current_score" not in st.session_state:
    st.session_state.current_score = None
if "current_suggestion" not in st.session_state:
    st.session_state.current_suggestion = None
if "contract_versions" not in st.session_state:
    st.session_state.contract_versions = []  # 存储所有版本

# ===================== 侧边栏：完整下拉框 =====================
with st.sidebar:
    st.subheader("📝 合同信息")
    contract_type = st.selectbox("合同类型",
                                 ["买卖合同", "租赁合同", "服务协议", "合作协议", "技术服务合同", "借款合同",
                                  "保密协议", "建设工程合同", "其他"])
    party_a_type = st.selectbox("甲方类型", ["企业", "自然人", "个体工商户", "其他组织"])
    party_b_type = st.selectbox("乙方类型", ["企业", "自然人", "个体工商户", "其他组织"])
    price_type = st.selectbox("计价方式", ["固定总价", "单价", "分期", "按进度", "无偿"])
    term_type = st.selectbox("履行期限", ["固定期限", "项目完成", "不定期"])
    dispute = st.selectbox("争议解决", ["诉讼", "仲裁"])

    party_a = st.text_input("甲方全称")
    party_b = st.text_input("乙方全称")
    subject = st.text_area("标的/内容")
    amount = st.text_input("合同金额")
    term_detail = st.text_input("履行期限")

    col1, col2 = st.columns(2)
    with col1:
        gen_btn = st.button("🚀 生成合同", type="primary", use_container_width=True)
    with col2:
        iter_btn = st.button("🔁 迭代优化", use_container_width=True)
    clear_btn = st.button("🗑️ 清空", use_container_width=True)

# ===================== 清空 =====================
if clear_btn:
    st.session_state.history = []
    st.session_state.current_contract = None
    st.session_state.current_score = None
    st.session_state.current_suggestion = None
    st.session_state.contract_versions = []
    st.rerun()

# ===================== 显示历史消息 =====================
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.code(msg["content"], language="text")
        if msg.get("score") is not None:
            st.caption(f"✅ 评分：{msg['score']} | 优化建议：{msg['suggestion']}")


# ===================== 生成合同 =====================
def build_prompt():
    return f"""生成{contract_type}
甲方：{party_a}({party_a_type})
乙方：{party_b}({party_b_type})
标的：{subject}
金额：{amount}
期限：{term_detail}({term_type})
计价：{price_type}
争议：{dispute}
"""


if gen_btn:
    if not party_a or not party_b or not subject:
        st.warning("请填写甲方、乙方、标的")
    else:
        prompt = build_prompt()
        st.session_state.history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.code(prompt, language="text")
        with st.chat_message("assistant"):
            contract = stream_generate(prompt)
            score_res = score(contract)
            st.caption(f"✅ 评分：{score_res['score']} | 建议：{score_res['suggestion']}")
            st.session_state.history.append({
                "role": "assistant",
                "content": contract,
                "score": score_res["score"],
                "suggestion": score_res["suggestion"]
            })
            st.session_state.current_contract = contract
            st.session_state.current_score = score_res["score"]
            st.session_state.current_suggestion = score_res["suggestion"]
            # 保存第一个版本
            st.session_state.contract_versions.append({
                "version": 1,
                "contract": contract,
                "score": score_res["score"],
                "suggestion": score_res["suggestion"]
            })

# ===================== 迭代优化（每次都用上一次建议） =====================
if iter_btn:
    if st.session_state.current_contract and st.session_state.current_suggestion:
        # 获取当前版本号
        current_version = len(st.session_state.contract_versions) + 1

        # 构建优化提示
        optimization_prompt = f"""基于以下合同文本，根据优化建议进行改进，请输出完整的优化后合同文本：

原始合同：
{st.session_state.current_contract}

优化建议：
{st.session_state.current_suggestion}

请严格按照原格式输出完整的优化后合同，保持变量标记和条款编号格式："""

        st.session_state.history.append({"role": "user", "content": f"第{current_version}次迭代优化请求"})
        with st.chat_message("user"):
            st.text(f"第{current_version}次迭代优化请求")

        with st.chat_message("assistant"):
            new_contract = stream_generate(optimization_prompt)

            # 对新合同进行评分
            new_score = score(new_contract)

            # 显示评分和建议
            st.caption(f"✅ 评分：{new_score['score']} | 优化建议：{new_score['suggestion']}")

            # 保存到历史
            st.session_state.history.append({
                "role": "assistant",
                "content": new_contract,
                "score": new_score["score"],
                "suggestion": new_score["suggestion"]
            })

            # 保存到版本历史
            st.session_state.contract_versions.append({
                "version": current_version,
                "contract": new_contract,
                "score": new_score["score"],
                "suggestion": new_score["suggestion"]
            })

            # 更新当前状态
            st.session_state.current_contract = new_contract
            st.session_state.current_score = new_score["score"]
            st.session_state.current_suggestion = new_score["suggestion"]

# ===================== 用户聊天输入框 =====================
if user_input := st.chat_input("输入需求直接生成合同…"):
    st.session_state.history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.code(user_input, language="text")
    with st.chat_message("assistant"):
        contract = stream_generate(user_input)
        score_res = score(contract)
        st.caption(f"✅ 评分：{score_res['score']} | 建议：{score_res['suggestion']}")
        st.session_state.history.append({
            "role": "assistant",
            "content": contract,
            "score": score_res["score"],
            "suggestion": score_res["suggestion"]
        })
        st.session_state.current_contract = contract
        st.session_state.current_score = score_res["score"]
        st.session_state.current_suggestion = score_res["suggestion"]
        # 保存版本
        st.session_state.contract_versions.append({
            "version": 1,
            "contract": contract,
            "score": score_res["score"],
            "suggestion": score_res["suggestion"]
        })

# ===================== 显示所有合同版本 =====================
if st.session_state.contract_versions:
    st.divider()
    st.subheader("📊 合同版本历史")

    for version_data in st.session_state.contract_versions:
        with st.expander(f"版本 {version_data['version']} - 评分: {version_data['score']}",
                         expanded=(version_data['version'] == len(st.session_state.contract_versions))):
            st.code(version_data["contract"], language="text")
            st.caption(f"优化建议: {version_data['suggestion']}")