exec(open('.wiring-cleanup/layout.py',encoding='utf-8-sig').read().split('if __name__')[0])
from collections import Counter
before=parse(Path('.wiring-cleanup/before.kicad_sch').read_text(encoding='utf-8'));after=parse(Path('AK4490DAC.kicad_sch').read_text(encoding='utf-8'))
def components(r):
 return {val(s,'uuid'):(val(s,'lib_id'),val(s,'unit'),tuple((p[1],p[2]) for p in children(s,'property')),tuple(tuple(p) for p in children(s,'pin'))) for s in children(r,'symbol')}
assert components(before)==components(after)
def erc(name):
 d=json.loads(Path('.wiring-cleanup/'+name+'-erc.json').read_text(encoding='utf-8'))
 vs=[v for s in d['sheets'] for v in s['violations']]
 return Counter(v['type'] for v in vs),Counter(v['severity'] for v in vs),Counter((v['type'],tuple(sorted(i.get('uuid','') for i in v['items']))) for v in vs)
b,a=erc('before'),erc('after');assert b==a
print('ERC counts and affected UUIDs identical:',a[:2]);print('All 95 symbol instance UUIDs, pins, values and footprints unchanged.')
report='''# 回路図レイアウト整理（2026-09-14）

## 変更内容

- 1枚の回路図上で、左から USB-C → ISOUSB211 → XMOS XU316 → AK4490 → 左右アナログ出力の順に配置。
- 7つの機能ブロックを枠線・見出しで区分。電源回路は下段に集約。
- 用紙外にあったXMOS、USBアイソレータ、QSPI、クロック、JTAGを用紙内に配置。
- XU316とISOUSB211のピン列を縦方向に2倍に広げ、余分なシンボル本体の空白を縮小。回路図キャッシュと専用シンボルライブラリの両方を更新。
- 抵抗・コンデンサの参照番号と定数を本体の右側に配置。
- ブロックをまたぐ信号は既存のネットラベルで接続。全体を一覧できるよう、階層シートは追加していない。

## 検証

- KiCad 10.0.3で回路図を再読込し、PDFを出力・目視確認。
- ネットリスト154ネットの接続端子集合（部品番号・ピン番号）は変更前後ですべて一致。
- 全95シンボルインスタンスのUUID、ユニット、ピン識別情報、定数、フットプリントなどのプロパティ値は変更なし。
- ERCの種類、件数、対象UUIDは変更前後で一致。
- 基板ファイルは変更していない。

| ERC種類 | 変更前 | 変更後 |
|---|---:|---:|
'''
for k,v in sorted(a[0].items()):report+=f'| {k} | {v} | {v} |\n'
report+='\n重大度別: '+', '.join(f'{k}: {v}' for k,v in a[1].items())+'。合計135件。\n'
report+='''
## 既存の未解決事項

U3（リセットIC / USBアイソレータ）とU4（リセットIC / QSPI）に参照番号の重複があり、ネットリスト出力時にアノテーション警告が出る。番号変更は今回行っていないため、上記ネットリスト比較はこの既存状態での比較である。電源未接続などの既存ERC違反も維持しており、電気設計の完成を意味しない。

確認用PDF: `AK4490DAC_layout.pdf`
'''
Path('docs/WIRING_CLEANUP_RESULT.md').write_text(report,encoding='utf-8')
import fitz
d=fitz.open('docs/AK4490DAC_layout.pdf');d[0].get_pixmap(matrix=fitz.Matrix(.8,.8)).save('.wiring-cleanup/final.png')
