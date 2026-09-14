# Claude向け引継ぎ資料：AK4490DAC 回路図配線

作成日: 2026-09-14  
作成者: Codex

## 依頼内容

ユーザーからの依頼は「回路図で配線を進められそうな部分は進める。都度、部品位置は見やすいように変更してよい」。

不確かな仕様を推測で確定せず、公式データシートと既存の部品Descriptionから意図を判断できる部分まで配線した。

## 作業対象

現在の編集済みプロジェクト:

```text
C:\Users\ftomo\Documents\ChatGPT\AK4490DAC
```

主要ファイル:

```text
AK4490DAC.kicad_sch       編集済み回路図（作業継続対象）
AK4490DAC.kicad_sym       プロジェクト専用シンボル
AK4490DAC.kicad_pro       KiCadプロジェクト設定
AK4490DAC.kicad_pcb       基板。今回未編集
AK4490DAC_wired.pdf       編集後の確認用PDF
docs/WIRING_PROGRESS.md   今回の変更概要
```

コピー元は次の既存リポジトリ。ただし、コピー元にはユーザーまたは別セッションの未コミット変更があったため、今回の編集結果はまだ戻していない。

```text
C:\Users\ftomo\Documents\GitHub\AK4490DAC
```

コピー元の確認時点の状態:

```text
 M AK4490DAC.kicad_sch
 M AK4490DAC.kicad_sym
?? .codex-work/
?? .wiring-cleanup/
?? docs/
?? hardware/
```

コピー元を上書きする場合は、双方の差分を確認してからマージすること。単純コピーで上書きしないこと。

## 現在の回路構成

```text
USB-C J2
  -> ISOUSB211 U3
  -> XU316 U2
  -> I2S (BICK/LRCK/SDATA/MCLK)
  -> AK4490 U6
  -> MUSES8920 IC5
  -> LINE_OUT_L / LINE_OUT_R
```

電源はJ1の9〜12 V入力からIC9で約5.5 Vを作り、複数の低ノイズLDOへ分配する構成。

## 今回実施した変更

### 1. 電源配線

- J1 `+VIN_RAW` → IC9 AMS1117入力を接続。
- IC9のR3/R4分圧を配線し、出力を `+5V5_PRE` と命名。
- `+5V5_PRE` をIC1/IC2/IC3/IC4/IC8/IC10/IC11のINとENへ接続。
- 各LDOのGNDを接続。
- 各LDO出力を以下のレールへ接続。

| LDO | 出力ネット | 用途 |
|---|---|---|
| IC1 | `+3V3_XU` | XU316 I/O、ISOUSB211 Side 2、QSPI |
| IC10 | `+1V8_XU` | XU316 1.8 V系、ISOUSB211 Side 2 |
| IC11 | `+0V9_XU` | XU316コア |
| IC2 | `+3V3_4490` | AK4490 DVDD・制御系 |
| IC3 | `+3V3A_4490` | AK4490 AVDD |
| IC4 | `+5V_4490_L` | AK4490 VDDL/VDDL* |
| IC8 | `+5V_4490_R` | AK4490 VDDR/VDDR* |

### 2. AK4490周辺

- U6のDVDD/DVSS、AVDD/AVSSを接続。
- VDDL/VDDL*、VSSL/VSSL*を接続。
- VDDR/VDDR*、VSSR/VSSR*を接続。
- VCML/VCMRとC8/C9を接続。
- C10〜C13を各電源レールとGNDへ接続。
- C8〜C13をDAC/REFERENCEブロックへ移動し、基準電圧周辺をまとめた。

### 3. XU316周辺

- U2 XIN/XOUTをY1 24 MHz水晶およびC34/C35へ接続。
- 旧AK4118用だったリセット監視回路をXU316用に転用。
- リセットネットを `XU_RST_N` に変更し、U2 RST_Nへ接続。
- 未使用と判断できるGPIOにNo Connectを配置。

I2SのGPIO割り当ては既存の暫定値を維持した。ファームウェア仕様確定前に変更しないこと。

### 4. USB・ISOUSB211周辺

- USB-CのSBU1/SBU2をNo Connect指定。
- ISOUSB211の未使用ステータス出力V1OK/V2OKをNo Connect指定。
- Side 2の既存電源接続は維持。
- Side 1のV3P3V1、V1P8V1_A、V1P8V1_Bは必要なデカップリング部品が存在しないため未接続のまま残した。

### 5. 参照番号・部品修正

- 重複していたTCM809の参照番号を次のように変更。

```text
XU316用リセット: U3 -> U8
AK4490用リセット: U4 -> U9
```

- IC11は「TPS7A20-ADJ」とされていたが、TPS7A20は固定出力品のみ。公式の0.9 V固定SOT-23-5品 `TPS7A2009PDBVR` へ変更。
- IC11用として置かれていたR29/R30は `DNP` 表記に変更。現在も回路図上には残しているので、次の整理時に削除してよい。
- 過去のレイアウト作業で残っていた電気的に空の電源スタブを除去。

## ERC結果

KiCad 10.0.3で確認。

```text
変更前: 135件（error 128 / warning 7）
変更後:  17件（error 10 / warning 7）
```

最終内訳:

| ERC種類 | 件数 | 状態 |
|---|---:|---|
| lib_symbol_mismatch | 5 | 既存の標準ライブラリ差分 |
| pin_not_connected | 5 | U1の2ピン、ISOUSB211 Side 1の3ピン |
| power_pin_not_driven | 3 | `+VIN_RAW`、VBUS、USB_GNDにPWR_FLAGなし |
| pin_not_driven | 1 | U1入力 |
| missing_power_pin | 1 | U1電源ユニット未配置 |
| missing_input_pin | 1 | U1の未配置ゲート |
| missing_unit | 1 | U1の未配置ゲート |

最終ERC JSON:

```text
.codex-work/wiring/final-erc.json
```

実行コマンド:

```powershell
& 'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe' sch erc `
  --format json --severity-all `
  -o '.codex-work\wiring\final-erc.json' `
  'AK4490DAC.kicad_sch'
```

`kicad-cli`実行時にHKCUレジストリへの書き込み拒否メッセージが多数出るが、ERC・ネットリスト・PDFの生成自体は成功している。

## 次に進められる作業

優先順:

1. ISOUSB211 Side 1のデカップリング回路を追加する。
   - V3P3V1からUSB_GND
   - V1P8V1_AからUSB_GND
   - V1P8V1_BからUSB_GND
   - TIデータシートでは各1.8 Vピンに個別のコンデンサ群を要求しているため、既存部品の流用ではなく部品追加が必要。
2. 全LDOの入力・出力コンデンサを追加する。
   - 特にTPS7A20は出力に最低1 µFが必要。
   - 現在のC10〜C13はAK4490近傍の0.1 µFデカップリングであり、LDO安定化コンデンサの代用にはしない。
3. U1（SN74LS06NSR）の用途を決める。
   - 現在はAユニットだけ配置され、全く接続されていない。
   - 旧回路の残骸ならシンボル全体を削除する。
   - 使用するなら全ユニットと電源ユニットを配置して接続する。
4. `+VIN_RAW`、VBUS、USB_GNDにPWR_FLAGを配置してERCの供給元判定を明示する。
5. R29/R30（DNP）と関連する `+0V9_XU_FB` ラベルを削除して表示を整理する。
6. XU316のI2S GPIOとQSPI信号割り当てをファームウェア側と照合する。
7. 回路図確定後にPCBへ反映する。現時点のPCBは今回の変更を反映していない。

## 注意すべき設計課題

- ISOUSB211 Side 1をデカップリングなしで完成扱いにしない。
- TPS7A2009の入力上限は6 V。必ずIC9後段の `+5V5_PRE` から給電し、`+VIN_RAW`へ直結しない。
- AK4490の品種表記が旧AK4490EQ相当のシンボルになっている。調達対象の型番と電源仕様を発注前に再確認する。
- C34/C35の18 pFは仮値。Y1の実部品と基板寄生容量から再計算する。
- XU316 QF60Bフットプリント寸法・Pin 1方向は推定情報を含むため、機械図面で再検証する。
- ERCが17件まで減っていても、電源容量、起動シーケンス、熱、USB SI、アナログ音質を保証するものではない。

## 作業補助ファイル

```text
.codex-work/wiring/before-wiring.kicad_sch  今回変更前の回路図
.codex-work/wiring/baseline-erc.json        変更前ERC
.codex-work/wiring/final-erc.json           変更後ERC
.codex-work/wiring/baseline.net             変更前ネットリスト
.codex-work/wiring/final.net                変更後ネットリスト
.codex-work/wiring/final.png                レンダリング確認画像
```

以下のスクリプトは変更過程の再現・調査用。ただし `wire_schematic.py` は追記型で非冪等なので、編集済み回路図に再実行しないこと。

```text
.codex-work/wiring/analyze.py
.codex-work/wiring/list_components.py
.codex-work/wiring/list_labels.py
.codex-work/wiring/netlist_analyze.py
.codex-work/wiring/wire_schematic.py
.codex-work/wiring/cleanup_stubs.py
```

## 参照した公式資料

- XMOS XU316-1024-QF60B Datasheet: https://www.xmos.com/file/xu316-1024-qf60b-datasheet?version=latest
- TI ISOUSB211 Datasheet: https://www.ti.com/lit/ds/symlink/isousb211.pdf
- TI TPS7A20 Datasheet: https://www.ti.com/lit/ds/symlink/tps7a20.pdf
- TPS7A2009PDBVR製品ページ: https://www.ti.com/product/TPS7A20/part-details/TPS7A2009PDBVR

## 完了条件の目安

- ISOUSB211と全LDOに必要なデカップリング部品が追加されている。
- U1を使用または削除する判断が完了している。
- 意図的なNC以外の `pin_not_connected` が0件。
- PWR_FLAG追加後、意図しない `power_pin_not_driven` が0件。
- ネットリストで電源ドメイン（USB_GNDとメインGND）が絶縁されたまま。
- PDFレンダリングでラベル重なりや用紙外部品がない。
- PCB更新前にユーザーへ、追加部品と型番変更の確認を求める。
