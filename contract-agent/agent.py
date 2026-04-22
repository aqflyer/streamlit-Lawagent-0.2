# agent.py
# coding: utf-8
import streamlit as st
import re
import json
from openai import OpenAI

# ===================== 导入配置 =====================
from config import API_KEY, BASE_URL, MODEL, FORMAT_RULE, SYSTEM_PROMPT, EVAL_PROMPT

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ===================== 格式清理 =====================
def clean(text):
    text = text.replace("*", "").replace("#", "")
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'(第\d+条)', r'\n\1', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return '\n\n'.join(lines)


# ===================== 流式生成 =====================
# ===================== 流式生成 =====================
def stream_generate(prompt):
    res = ""
    placeholder = st.empty()

    try:
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            temperature=0.3,
            stream=True
        )

        for chunk in stream:
            # 确保chunk.choices存在且有内容
            if chunk.choices and len(chunk.choices) > 0:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    res += content
                    placeholder.code(clean(res), language="text")
    except Exception as e:
        st.error(f"生成合同时发生错误: {str(e)}")
        return f"生成失败: {str(e)}"

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

        # 获取模型返回的内容
        content = r.choices[0].message.content.strip()

        # 尝试直接解析JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 如果解析失败，尝试从文本中提取JSON
            import re
            # 查找JSON对象
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass

            # 如果没有找到JSON，尝试提取分数和建议
            score_match = re.search(r'"score"\s*:\s*(\d+)', content)
            suggestion_match = re.search(r'"suggestion"\s*:\s*"([^"]*)"', content)

            if score_match and suggestion_match:
                return {
                    "score": int(score_match.group(1)),
                    "suggestion": suggestion_match.group(1)
                }

            # 尝试其他格式
            score_match2 = re.search(r'score[:\s]*(\d+)', content, re.IGNORECASE)
            suggestion_match2 = re.search(r'suggestion[:\s]*(.*?)(?:\n\n|$)', content, re.IGNORECASE | re.DOTALL)

            if score_match2 and suggestion_match2:
                return {
                    "score": int(score_match2.group(1)),
                    "suggestion": suggestion_match2.group(1).strip()
                }

            # 如果以上都失败，返回默认值
            st.warning("模型返回格式异常，已使用默认评分")
            return {"score": 0, "suggestion": "无法解析模型返回的评分结果"}

    except Exception as e:
        st.error(f"评分失败: {str(e)}")
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