from dataclasses import dataclass
from typing import List

DISCLAIMER = (
    "【免責聲明】本草稿由法律資訊輔助工具產生，僅供參考，不構成正式法律意見，"
    "亦不代表主管機關或法院之認定；送出前請務必自行核對事實與個資。"
)


@dataclass
class IncidentInfo:
    channel: str          # "外送平台" 或 "校園餐廳"
    platform_or_place: str
    order_or_meal_time: str
    issue_type: str       # "異物" 或 "變質"
    detected_items: List[str]
    evidence_kept: List[str]
    desired_remedy: str   # 例如：退費、重新出餐、衛生稽查
    health_symptom: bool = False


def generate_complaint_letter(info: IncidentInfo) -> str:
    items_str = "、".join(info.detected_items) if info.detected_items else "餐點外觀／異物異常（待確認）"
    evidence_str = "、".join(info.evidence_kept) if info.evidence_kept else "餐點照片、包裝與訂單紀錄"

    if info.channel == "外送平台":
        recipient = f"{info.platform_or_place} 客服中心"
        subject = f"外送餐點食安問題反映與退款／處理申請（用餐／訂購時間：{info.order_or_meal_time}）"
        legal_hint = "可能涉及《食品安全衛生管理法》第 15 條第 1 項及《消費者保護法》相關規定與平台退款條款（實際適用以主管機關及契約條款為準）。"
    else:
        recipient = f"{info.platform_or_place} 經營單位／校內相關權責單位"
        subject = f"校園供餐食安問題反映（用餐時間：{info.order_or_meal_time}）"
        legal_hint = "可能涉及《食品安全衛生管理法》第 15 條第 1 項及《消費者保護法》相關規定（實際適用以主管機關及相關規範為準）。"

    symptom_note = (
        "\n- 身體狀況提醒：已出現身體不適，建議儘速就醫並妥善保存就診／診斷證明。"
        if info.health_symptom
        else ""
    )

    return f"""收件對象：{recipient}
主旨：{subject}

您好：

本人於 {info.order_or_meal_time} 透過／於「{info.platform_or_place}」取得餐點，發現餐點有「{info.issue_type}」情形（初步觀察／標註：{items_str}）。

為利查明與處理，本人已留存以下資料：{evidence_str}。{legal_hint}{symptom_note}

懇請貴方協助查明原因，並針對本案提供「{info.desired_remedy}」之具體處理方式與回覆。

此致
{recipient}

反映人：[請自行填寫姓名／聯絡方式，注意個資保護]
日期：[請填寫日期]

---
{DISCLAIMER}
"""


def generate_health_bureau_report(info: IncidentInfo) -> str:
    items_str = "、".join(info.detected_items) if info.detected_items else "餐點異物或變質跡象"
    evidence_str = "、".join(info.evidence_kept) if info.evidence_kept else "照片、包裝、訂單／消費明細"

    return f"""陳情／檢舉對象：地方政府衛生局（亦可撥打 1919 全國食安專線洽詢）
主旨：反映「{info.platform_or_place}」疑似供售{info.issue_type}餐點（時間：{info.order_or_meal_time}）

陳情說明：
1. 事件時間與場所：於 {info.order_or_meal_time} 在「{info.platform_or_place}」（來源：{info.channel}）取得餐點。
2. 反映事由：餐點出現疑似「{info.issue_type}」情況（{items_str}），疑涉《食品安全衛生管理法》第 15 條第 1 項有關食品衛生安全之規定（是否構成違規，仍請貴局依職權查核認定）。
3. 現有佐證資料：{evidence_str}。

敬請貴局卓參並依權責辦理稽查與輔導事宜。

陳情人：[請自行填寫姓名／聯絡方式]
日期：[請填寫日期]

---
{DISCLAIMER}
"""


if __name__ == "__main__":
    sample = IncidentInfo(
        channel="外送平台",
        platform_or_place="範例美食外送／某某便當店",
        order_or_meal_time="2026-11-25 12:30",
        issue_type="異物",
        detected_items=["疑似毛髮（待確認）"],
        evidence_kept=["餐點照片", "外包裝照片", "訂單截圖"],
        desired_remedy="依平台規範辦理退費與店家衛生改善",
        health_symptom=False,
    )
    print("=== 客訴信草稿 ===")
    print(generate_complaint_letter(sample))
    print("=== 衛生局檢舉函草稿 ===")
    print(generate_health_bureau_report(sample))