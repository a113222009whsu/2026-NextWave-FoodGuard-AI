import os
import re
import requests
from typing import List

from llama_index.core import Document, Settings, TreeIndex, PromptTemplate
from llama_index.core.prompts.prompts import SimpleInputPrompt
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

DISCLAIMER = (
    "\n\n【免責聲明】本系統為法律資訊輔助工具，不構成正式法律意見，"
    "亦不判定店家是否違法；實際救濟與檢舉仍請依主管機關或專業人員評估。"
)

REFUSAL_TEXT = (
    "目前知識庫中查無足夠且明確的法規或條款依據可回答此問題，"
    "為避免提供錯誤資訊，系統不予臆測。建議洽詢地方衛生局、"
    "1919 全國食安專線或消保／法律諮詢管道。"
)


class FoodGuardLegalRAG:
    def __init__(
        self,
        model_name: str = "llama3:8b",
        embed_model_name: str = "mxbai-embed-large",
        base_url: str = "http://localhost:11434",
    ):
        self.model_name = model_name
        self.embed_model_name = embed_model_name
        self.base_url = base_url
        self.index = None

        self._check_ollama()
        self.llm = Ollama(model=self.model_name, base_url=self.base_url, request_timeout=120)
        self.embed_model = OllamaEmbedding(model_name=self.embed_model_name, base_url=self.base_url)

        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        Settings.chunk_size = 1024
        Settings.chunk_overlap = 100

        self.qa_template = SimpleInputPrompt(
            """你是「食安糾察隊 FoodGuard AI」的法規資訊整理助手。
請嚴格依據下方【法規與條款參考資料】回答問題，禁止自行編造法條或推測未出現的規定。

【法規與條款參考資料】
---------------------
{context_str}
---------------------

使用者問題：{query_str}

回答規則：
1. 只能使用【法規與條款參考資料】中有明確記載的內容作答，並註明法規名稱、條號與資料中的版本／日期資訊。
2. 若【法規與條款參考資料】不足以回答或完全沒有相關條文，請只回覆：
「目前知識庫中查無足夠且明確的法規或條款依據可回答此問題，為避免提供錯誤資訊，系統不予臆測。建議洽詢地方衛生局、1919 全國食安專線或消保／法律諮詢管道。」
3. 語氣客觀、清楚，使用繁體中文，不判定個案是否必然違法。
"""
        )

    def _check_ollama(self):
        resp = requests.get(f"{self.base_url}/api/tags", timeout=10)
        resp.raise_for_status()
        print(f"✅ Ollama 服務可連線：{self.base_url}")

    def build_index_from_markdown_files(self, md_paths: List[str]):
        docs = []
        for path in md_paths:
            if not os.path.exists(path):
                print(f"⚠️ 找不到檔案，已略過：{path}")
                continue
            with open(path, "r", encoding="utf-8") as f:
                text = f.read().strip()
            if text:
                docs.append(Document(text=text, metadata={"source_file": os.path.basename(path)}))

        if not docs:
            raise ValueError("沒有載入任何有效的法規／條款文件。")

        summary_tmpl = PromptTemplate(
            "請用繁體中文簡要摘要以下法規或條款片段，保留法規名稱、條號與日期：\n{context_str}"
        )
        self.index = TreeIndex.from_documents(docs, summary_template=summary_tmpl, insert_batch_size=1)
        print(f"✅ 已建立法規索引，共 {len(docs)} 份文件。")

    @staticmethod
    def _verify_citations(answer: str, source_texts: List[str]) -> bool:
        """簡單引用檢核：若回答提到「第XX條」，確認檢索出的參考資料中也有出現該條號。"""
        cited_articles = re.findall(r"第\s*\d+\s*條", answer)
        if not cited_articles:
            return True
        combined_sources = "\n".join(source_texts)
        return all(art in combined_sources for art in cited_articles)

    def query(self, question: str) -> str:
        if self.index is None:
            return "尚未建立索引，請先載入法規資料。" + DISCLAIMER

        query_engine = self.index.as_query_engine(text_qa_template=self.qa_template)
        response = query_engine.query(question)
        answer = (response.response or "").strip()

        source_texts = [node.get_content() for node in (response.source_nodes or [])]
        if not source_texts or not self._verify_citations(answer, source_texts):
            return REFUSAL_TEXT + DISCLAIMER

        if REFUSAL_TEXT[:15] in answer:
            return REFUSAL_TEXT + DISCLAIMER

        sources_summary = "\n".join(
            f"- 來源檔案：{node.metadata.get('source_file', 'N/A')}｜片段：{node.get_content()[:120].replace(chr(10), ' ')}..."
            for node in (response.source_nodes or [])
        )
        return f"{answer}\n\n【檢索依據】\n{sources_summary}{DISCLAIMER}"


if __name__ == "__main__":
    sample_files = [
        "data/food_safety_act.md",
        "data/consumer_protection_act.md",
    ]
    rag = FoodGuardLegalRAG(
        model_name="llama3:8b",
        embed_model_name="mxbai-embed-large",
    )
    rag.build_index_from_markdown_files(sample_files)

    while True:
        q = input("\n請輸入食安／消保問題（輸入 quit 結束）：").strip()
        if q.lower() == "quit":
            break