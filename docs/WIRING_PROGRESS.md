# 回路図配線進捗（2026-09-14）

## 今回接続した範囲

- `+VIN_RAW` → IC9（AMS1117）→ `+5V5_PRE` のプリレギュレータと分圧抵抗 R3/R4
- `+5V5_PRE` から IC1/IC2/IC3/IC4/IC8/IC10/IC11 の入力・EN・GND
- 各LDO出力から `+3V3_XU`、`+1V8_XU`、`+0V9_XU`、`+3V3_4490`、`+3V3A_4490`、`+5V_4490_L`、`+5V_4490_R`
- AK4490 の DVDD/DVSS、AVDD/AVSS、VDDL/VSSL、VDDR/VSSR、VCML/VCMR と C8〜C13
- XU316 の XIN/XOUT と 24 MHz 水晶、XU316リセット
- USB-C SBU、ISOUSB211 V1OK/V2OK、未使用XU316 GPIOへ明示的なNC指定

## 整理・修正

- C8〜C13をAK4490基準電圧ブロックへ集約。
- R3/R4をIC9の近くへ移動し、分圧関係が読める配置に変更。
- 重複していたリセットICの参照番号を U8/U9 に変更。
- 旧AK4118用リセットを `XU_RST_N` としてXU316へ転用。
- IC11は可変型ではなく固定0.9 V品 `TPS7A2009PDBVR` に修正。R29/R30はDNP表記。
- 過去のレイアウト整理で残っていた電気的に空の電源スタブを除去。

## ERC結果

変更前は135件、変更後は17件。

| 種類 | 件数 | 残件の意味 |
|---|---:|---|
| lib_symbol_mismatch | 5 | 標準ライブラリと回路図キャッシュの差分 |
| pin_not_connected | 5 | U1の2ピン、ISOUSB211 Side 1の内部LDO端子3ピン |
| power_pin_not_driven | 3 | `+VIN_RAW`、VBUS、USB_GNDにPWR_FLAGが未配置 |
| pin_not_driven | 1 | 未使用のU1入力 |
| missing_power_pin | 1 | U1の電源ユニット未配置 |
| missing_input_pin | 1 | U1の未配置ゲート |
| missing_unit | 1 | U1の未配置ゲート |

## 次に必要な設計判断

1. ISOUSB211 Side 1の V3P3V1 と2本の V1P8V1 に、データシート指定の個別デカップリングを追加する。
2. 各LDOの安定性確保用に、入力・出力コンデンサを追加して容量と定格を確定する。
3. 用途不明で全ゲート未使用の U1（74LS06）を削除するか、使用回路を決める。
4. `+VIN_RAW`、VBUS、USB_GNDへERC用PWR_FLAGを追加する。
5. XU316のI2S GPIO割り当てはファームウェア仕様確定後に再確認する。

ERCは接続規則の機械検査であり、電源容量、起動シーケンス、音質、部品定格の妥当性までは保証しない。

## 追記（2026-09-14、Claude担当分）

Codexの引継ぎ（`docs/HANDOFF_CLAUDE_WIRING.md`）を受けて、「次に必要な設計判断」1〜4を実施。

### 1. U1（SN74LS06N）を削除

- 全ピン未接続・全ユニット未配置のまま放置されていた残骸コンポーネント。使用箇所なしと判断し、シンボルインスタンスと`lib_symbols`キャッシュを削除。
- これだけでERC違反が17件→10件に減少（missing_unit/missing_input_pin/missing_power_pin/pin_not_driven/pin_not_connectedのU1関連7件が解消）。

### 2. PWR_FLAGを3箇所に追加

`power:PWR_FLAG`シンボルを新規に`lib_symbols`へ登録し、以下3ネットへ配置：

- `+VIN_RAW`（IC9 VIピン付近）
- `VBUS`（U3 VBUS1ピン付近）
- `USB_GND`（U3 GND1ピン付近）

→ `power_pin_not_driven`の3件が解消（10件→7件）。

### 3. ISOUSB211（U3）Side 1のデコップリングを追加

TIデータシート指定通り、Side 1の3ピンに個別コンデンサを追加（新規 C36〜C38、フットプリントは他のC0603系に合わせて`Capacitor_SMD:C_0603_1608Metric`、GND側はローカルラベル`USB_GND`で接続）：

- C36: V3P3V1 - USB_GND、1uF
- C37: V1P8V1_A - USB_GND、0.1uF
- C38: V1P8V1_B - USB_GND、0.1uF

→ `pin_not_connected`の3件が解消（7件→4件、残りは全て既存のlib_symbol_mismatch警告のみ）。

### 4. 全LDO（IC1/IC2/IC3/IC4/IC8/IC9/IC10/IC11）へ入出力コンデンサを追加

これまで8個のLDO/プリレギュレータには入出力コンデンサが1個も無かった（ERCでは検出されない電気的な欠落）。新規 C39〜C54（16個）を追加：

| LDO | IN側 | OUT側 |
|---|---|---|
| IC1 (+3V3_XU) | C39 1uF | C40 1uF |
| IC2 (+3V3_4490) | C41 1uF | C42 1uF |
| IC3 (+3V3A_4490) | C43 1uF | C44 1uF |
| IC4 (+5V_4490_L, TPS7A2050) | C45 1uF | C46 1uF |
| IC8 (+5V_4490_R, TPS7A2050) | C47 1uF | C48 1uF |
| IC9 (+5V5_PRE, AMS1117プリレグ) | C53 10uF | C54 10uF |
| IC10 (+1V8_XU) | C49 1uF | C50 1uF |
| IC11 (+0V9_XU, TPS7A2009) | C51 1uF | C52 1uF |

全てIN/OUTピンから直接ワイヤーで分岐し、GND側はローカルラベル`GND`で接続（既存C10〜C13と同じ流儀）。値は各データシートの最小推奨値（LP5907系・TPS7A20系は1uF、AMS1117は10uF）。**実際の負荷電流・過渡応答・基板寄生を踏まえた最終値の確定は未実施**（次回課題）。

### 5. R29/R30（DNP）と`+0V9_XU_FB`ラベルを削除

IC11が固定0.9V品に変更済みでDNP指定されていた旧フィードバック分圧回路（R29・R30・関連ワイヤー4本・`+0V9_XU_FB`ラベル2箇所）を完全撤去。

### 最終ERC結果

```text
変更前（Codex引継ぎ時点）: 17件（error 10 / warning 7）
Claude作業後:              4件（error 0 / warning 4、全てlib_symbol_mismatch警告のみ）
```

`kicad-cli sch erc --format json --severity-all` / `sch export netlist` / `sch export pdf` を実行しエラーなしを確認済み。JSON各段階のログは `.codex-work/wiring/after-*-erc.json` に保存。

### まだ手つかずの項目（次回への引継ぎ）

- **LDO入出力コンデンサの最終値確定**: 今回追加したのはデータシート最小推奨値。実負荷・トランジェント・レイアウト寄生を踏まえた再検討が必要。
- **XU316のI2S GPIO / QSPI信号割り当て**: ファームウェア仕様確定後に照合すること（未着手、ハードウェアだけでは決められない）。
- **PCBへの反映**: `AK4490DAC.kicad_pcb`は今回未編集。回路図がある程度固まった段階でネットリストを反映すること。
- **AK4490の型番確認**: シンボルが旧AK4490EQ相当のまま。発注前に実際の調達型番と電源仕様を再確認。
- **C34/C35（XU316水晶負荷容量）**: 18pFは仮値、実部品のCLと基板寄生から再計算が必要。
- **XU316 QF60Bフットプリント**: 寸法・Pin1方向とも推定。機械図面で要検証。
- **このコピー（`C:\Users\ftomo\Documents\ChatGPT\AK4490DAC`）はコピー元の `C:\Users\ftomo\Documents\GitHub\AK4490DAC` にまだマージされていない**。マージ前に両者の差分を確認すること（コピー元にも別セッションの未コミット変更が残っている可能性がある）。
