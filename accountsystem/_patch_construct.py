from pathlib import Path

p = Path(r"d:/Code/code/accounting/accountsystem/construct.md")
lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
replacements = {
    "context_prepare": "| `context_prepare` | 合并历史与本轮输入；结构化确认由外壳预写入 state | 否 |\n",
    "mutation_check": "| `mutation_check` | 抽 `BillLocator` 条件 → `search_bills` 定位；0 条报错、1/多条待确认 | LLM + Tool |\n",
    "human_confirm": "| `human_confirm` | 输出确认卡片数据（action + candidates），本轮结束 | 否 |\n",
}
out = []
for line in lines:
    key = None
    for k in replacements:
        if line.startswith(f"| `{k}` |"):
            key = k
            break
    out.append(replacements[key] if key else line)
p.write_text("".join(out), encoding="utf-8")
print("ok")
